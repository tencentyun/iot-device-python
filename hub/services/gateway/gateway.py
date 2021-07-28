#
# Tencent is pleased to support the open source community by making IoT Hub available.
# Copyright (C) 2016 THL A29 Limited, a Tencent company. All rights reserved.

# Licensed under the MIT License (the "License"); you may not use this file except in
# compliance with the License. You may obtain a copy of the License at
# http://opensource.org/licenses/MIT

# Unless required by applicable law or agreed to in writing, software distributed under the License is
# distributed on an "AS IS" basis, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
# either express or implied. See the License for the specific language governing permissions and
# limitations under the License.

import sys
import threading
import time
import json
import random
from enum import Enum
from hub.utils.codec import Codec
from hub.utils.providers import LoggerProvider
from hub.utils.providers import ConnClientProvider

class Gateway(object):
    def __init__(self, host, product_id, device_name, device_secret,
                    websocket=False, tls=True):
        # self.__logger = logger
        self.__log_provider = LoggerProvider()
        self.__logger = self.__log_provider.logger
        self.__provider = ConnClientProvider(host, product_id, device_name, device_secret,
                                                websocket=websocket, tls=tls)
        self.__protocol = self.__provider.protocol
        self.__codec = Codec()

        # self.__gateway_session_client_id = None
        self.__gateway_session_online_reply = {}
        self.__gateway_session_offline_reply = {}
        self.__gateway_session_bind_reply = {}
        self.__gateway_session_unbind_reply = {}
        self.__gateway_get_bind_list_reply = False
        self.__gateway_raply = False

        # 网关子设备property topic订阅的子设备列表
        self.__gateway_subdev_bind_list = []

        self.__gateway_session_online_lock = threading.Lock()
        self.__gateway_session_offline_lock = threading.Lock()
        self.__gateway_session_bind_lock = threading.Lock()
        self.__gateway_session_unbind_lock = threading.Lock()

        # 解析配置文件获取的子设备列表
        self.gateway_subdev_config_list = []

    class SessionState(Enum):
        SUBDEV_SEESION_STATUS_INIT = 0
        SUBDEV_SEESION_STATUS_ONLINE = 1
        SUBDEV_SEESION_STATUS_OFFLINE = 2

    # 网关子设备信息(是否需加入设备online/offline状态?)
    class gateway_subdev(object):
        def __init__(self):
            self.product_id = None
            self.device_name = None
            self.session_status = 0

    def handle_gateway(self, topic, message):
        self.__gateway_raply = True
        ptype = message["type"]
        payload = message["payload"]
        devices = payload["devices"]

        if ptype == "describe_sub_devices":
            for subdev in devices:
                dev = self.gateway_subdev()
                dev.product_id = subdev["product_id"]
                dev.device_name = subdev["device_name"]
                self.__gateway_subdev_bind_list.append(dev)
            self.__gateway_get_bind_list_reply = True
        else:
            result = devices[0]["result"]
            product_id = devices[0]["product_id"]
            device_name = devices[0]["device_name"]
            client_id = product_id + "/" + device_name
            
            if ptype == "online":
                self.__gateway_session_online_reply[client_id] = result
            elif ptype == "offline":
                self.__gateway_session_offline_reply[client_id] = result
            elif ptype == "bind":
                self.__gateway_session_bind_reply[client_id] = result
            elif ptype == "unbind":
                self.__gateway_session_unbind_reply[client_id] = result
        pass

    def __wait_for_session_reply(self, client_id, session):
        if client_id is None or len(client_id) == 0:
            raise ValueError('Invalid client_id.')
        if session is None or len(session) == 0:
            raise ValueError('Invalid session.')

        if session == "online":
            cnt = 0
            while cnt < 3:
                with self.__gateway_session_online_lock:
                    if client_id in self.__gateway_session_online_reply:
                        if self.__gateway_session_online_reply[client_id] == 0:
                            self.__gateway_session_online_reply.pop(client_id)
                            return 0
                        else:
                            break
                pass
                time.sleep(0.2)
                cnt += 1
            return 1
        elif session == "offline":
            cnt = 0
            while cnt < 3:
                with self.__gateway_session_offline_lock:
                    if client_id in self.__gateway_session_offline_reply:
                        if self.__gateway_session_offline_reply[client_id] == 0:
                            self.__gateway_session_offline_reply.pop(client_id)
                            return 0
                        else:
                            break
                pass
                time.sleep(0.2)
                cnt += 1
            return 1
        elif session == "bind":
            cnt = 0
            while cnt < 3:
                with self.__gateway_session_bind_lock:
                    if client_id in self.__gateway_session_bind_reply:
                        if self.__gateway_session_bind_reply[client_id] == 0:
                            self.__gateway_session_bind_reply.pop(client_id)
                            return 0
                        else:
                            break
                pass
                time.sleep(0.2)
                cnt += 1
            return 1
        elif session == "unbind":
            cnt = 0
            while cnt < 3:
                with self.__gateway_session_unbind_lock:
                    if client_id in self.__gateway_session_unbind_reply:
                        if self.__gateway_session_unbind_reply[client_id] == 0:
                            self.__gateway_session_unbind_reply.pop(client_id)
                            return 0
                        else:
                            break
                pass
                time.sleep(0.2)
                cnt += 1
            return 1
        elif session == "describe_sub_devices":
            cnt = 0
            while cnt < 3:
                if self.__gateway_get_bind_list_reply is True:
                    return 0
                pass
                time.sleep(0.2)
                cnt += 1
            return 1
        pass

    def __build_session_payload(self, ptype, pid, name, bind_secret):
        if ptype == "online" or ptype == "offline" or ptype == "unbind":
            payload = {
                "type": ptype,
                "payload": {
                    "devices": [{
                        "product_id": pid,
                        "device_name": name
                    }]
                }
            }
        elif ptype == "bind":
            nonce = random.randrange(2147483647)
            timestamp = int(time.time())
            sign_format = '%s%s;%d;%d'
            sign_content = sign_format % (pid, name, nonce, timestamp)

            # 计算二进制
            sign_base64 = self.__codec.Base64.encode(self.__codec.Hmac.sha1_encode(bind_secret.encode("utf-8"),
                            sign_content.encode("utf-8")))
            # sign = hmac.new(bind_secret.encode("utf-8"), sign_content.encode("utf-8"), hashlib.sha1).digest()
            # sign_base64 = base64.b64encode(sign).decode('utf-8')

            self.__logger.debug('sign base64 {}'.format(sign_base64))
            payload = {
                "type": ptype,
                "payload": {
                    "devices": [{
                        "product_id": pid,
                        "device_name": name,
                        "signature": sign_base64,
                        "random": nonce,
                        "timestamp": timestamp,
                        "signmethod": "hmacsha1",
                        "authtype": "psk"
                    }]
                }
            }
        elif ptype == "describe_sub_devices":
            payload = {
                "type": ptype
            }
        pass

        return payload

    def gateway_reset(self):
        self.__gateway_session_online_reply.clear()
        self.__gateway_session_offline_reply.clear()
        self.__gateway_session_bind_reply.clear()
        self.__gateway_session_unbind_reply.clear()
        self.__gateway_raply = False

        self.__gateway_subdev_bind_list.clear()
        self.gateway_subdev_config_list.clear()

    def gateway_init(self, topic, qos, device_info):
        # 解析网关子设备信息,并添加到list
        subdev_num = device_info['subDev']['subdev_num']
        subdev_list = device_info['subDev']['subdev_list']

        index = 0
        while index < subdev_num:
            p_subdev = self.gateway_subdev()
            p_subdev.product_id = subdev_list[index]['sub_productId']
            p_subdev.device_name = subdev_list[index]['sub_devName']
            p_subdev.session_status = self.SessionState.SUBDEV_SEESION_STATUS_INIT
            self.gateway_subdev_config_list.append(p_subdev)
            index += 1
        pass

        rc, mid = self.__protocol.subscribe(topic, qos)
        if rc != 0:
            self.__logger.error("topic_subscribe error:rc:%d,topic:%s" % (rc, topic))
        return rc, mid

    def is_subdev_status_online(self, sub_productId, sub_devName):
        """
        判断指定子设备SDK维护的状态是否为online
        """
        for sub in self.gateway_subdev_config_list:
            if (sub.product_id == sub_productId
                    and sub.device_name == sub_devName):
                return sub.session_status == self.SessionState.SUBDEV_SEESION_STATUS_ONLINE
        return False

    def update_subdev_status(self, sub_productId, sub_devName, status):
        """
        设置指定子设备SDK维护的状态
        """
        for subdev in self.gateway_subdev_config_list:
            if (subdev.product_id == sub_productId
                    and subdev.device_name == sub_devName):
                # self.gateway_subdev_config_list.remove(sub)
                subdev.product_id = sub_productId
                subdev.device_name = sub_devName
                if status == "online":
                    subdev.session_status = self.SessionState.SUBDEV_SEESION_STATUS_ONLINE
                elif status == "offline":
                    subdev.session_status = self.SessionState.SUBDEV_SEESION_STATUS_OFFLINE
            pass

    def gateway_subdev_online(self, topic, qos, sub_productId, sub_devName):
        # 保存当前会话的设备client_id
        client_id = sub_productId + "/" + sub_devName
        payload = self.__build_session_payload("online", sub_productId, sub_devName, None)

        rc, mid = self.__protocol.publish(topic, json.dumps(payload), qos)
        if rc != 0:
            self.__logger.error("topic_publish error:rc:%d,topic:%s" % (rc, topic))
            return rc, mid

        rc = self.__wait_for_session_reply(client_id, "online")
        if rc == 0:
            self.__logger.debug("client:%s %s success" % (client_id, "online"))
        else:
            self.__logger.debug("client:%s %s fail" % (client_id, "online"))

        return rc, mid

    def gateway_subdev_offline(self, topic, qos, sub_productId, sub_devName):
        client_id = sub_productId + "/" + sub_devName
        payload = self.__build_session_payload("offline", sub_productId, sub_devName, None)

        rc, mid = self.__protocol.publish(topic, json.dumps(payload), qos)
        if rc != 0:
            self.__logger.error("topic_publish error:rc:%d,topic:%s" % (rc, topic))
            return rc, mid

        rc = self.__wait_for_session_reply(client_id, "offline")
        if rc == 0:
            self.__logger.debug("client:%s %s success" % (client_id, "offline"))
        else:
            self.__logger.debug("client:%s %s fail" % (client_id, "offline"))

        return rc, mid

    def gateway_subdev_bind(self, topic, qos, sub_productId, sub_devName, sub_secret):
        client_id = sub_productId + "/" + sub_devName
        payload = self.__build_session_payload("bind", sub_productId, sub_devName, sub_secret)

        rc, mid = self.__protocol.publish(topic, json.dumps(payload), qos)
        if rc != 0:
            self.__logger.error("topic_publish error:rc:%d,topic:%s" % (rc, topic))
            return rc, mid

        rc = self.__wait_for_session_reply(client_id, "bind")
        if rc == 0:
            self.__logger.debug("client:%s %s success" % (client_id, "bind"))
        else:
            self.__logger.debug("client:%s %s fail" % (client_id, "bind"))

        return rc, mid
    
    def gateway_subdev_unbind(self, topic, qos, sub_productId, sub_devName):
        client_id = sub_productId + "/" + sub_devName
        payload = self.__build_session_payload("unbind", sub_productId, sub_devName, None)

        rc, mid = self.__protocol.publish(topic, json.dumps(payload), qos)
        if rc != 0:
            self.__logger.error("topic_publish error:rc:%d,topic:%s" % (rc, topic))
            return rc, mid

        rc = self.__wait_for_session_reply(client_id, "unbind")
        if rc == 0:
            self.__logger.debug("client:%s %s success" % (client_id, "unbind"))
        else:
            self.__logger.debug("client:%s %s fail" % (client_id, "unbind"))

        return rc, mid
    
    def gateway_get_subdev_bind_list(self, topic, qos, product_id, device_name):
        client_id = product_id + "/" + device_name
        payload = self.__build_session_payload("describe_sub_devices", product_id, device_name, None)

        rc, mid = self.__protocol.publish(topic, json.dumps(payload), qos)
        if rc != 0:
            self.__logger.error("topic_publish error:rc:%d,topic:%s" % (rc, topic))
            return rc, mid

        rc = self.__wait_for_session_reply(client_id, "describe_sub_devices")
        if rc == 0:
            self.__logger.debug("client:%s %s success" % (client_id, "get bind list"))
        else:
            self.__logger.debug("client:%s %s fail" % (client_id, "get bind list"))

        return rc, self.__gateway_subdev_bind_list

    def gateway_get_subdev_config_list(self):
        """
        获取配置文件中的子设备列表
        """
        return self.gateway_subdev_config_list

    def gateway_subdev_subscribe(self, topic):    
        rc, mid = self.__protocol.subscribe(topic, 0)
        if rc != 0:
            self.__logger.error("topic_subscribe error:rc:%d,topic:%s" % (rc, topic))
            return rc, mid

        return rc, mid
