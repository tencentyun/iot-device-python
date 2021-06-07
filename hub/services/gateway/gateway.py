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
import random
from enum import Enum
from hub.utils.codec import Codec

class Gateway(object):
    def __init__(self, protocol, logger=None):
        self.__logger = logger
        self.__protocol = protocol
        self.__codec = Codec()

        self.__gateway_session_client_id = None
        self.__gateway_session_online_reply = {}
        self.__gateway_session_offline_reply = {}
        self.__gateway_session_bind_reply = {}
        self.__gateway_session_unbind_reply = {}
        self.__gateway_raply = False

        # 网关子设备property topic订阅的子设备列表
        self.__gateway_subdev_bind_list = []
        self.__gateway_subdev_action_topic_list = []
        self.__gateway_subdev_event_topic_list = []

        # 网关子设备property回调字典(["product_id":callback])
        self.__on_gateway_subdev_prop_cb_dict = {}
        self.__on_gateway_subdev_action_cb_dict = {}
        self.__on_gateway_subdev_event_cb_dict = {}

        self.__gateway_session_online_lock = threading.Lock()
        self.__gateway_session_offline_lock = threading.Lock()
        self.__gateway_session_bind_lock = threading.Lock()
        self.__gateway_session_unbind_lock = threading.Lock()

        self.gateway_subdev_list = []

    class SessionState(Enum):
        SUBDEV_SEESION_STATUS_INIT = 0
        SUBDEV_SEESION_STATUS_ONLINE = 1
        SUBDEV_SEESION_STATUS_OFFLINE = 2

    # 网关子设备信息(是否需加入设备online/offline状态?)
    class gateway_subdev(object):
        def __init__(self):
            self.sub_productId = None
            self.sub_devName = None
            self.session_status = 0

    def handle_gateway(self, message):
        self.__logger.debug("gateway payload:%s" % message)

        self.__gateway_raply = True
        ptype = message["type"]
        payload = message["payload"]
        devices = payload["devices"]

        if ptype == "describe_sub_devices":
            for subdev in devices:
                dev = (subdev.product_id, subdev.device_name)
                self.__gateway_subdev_bind_list.append(dev)
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
                if not self.__gateway_subdev_bind_list:
                    return 0
                else:
                    break
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
            sign_base64 = self.__codec.Base64.encode(self.__codec.Hmac.sha256_encode(bind_secret.encode("utf-8"),
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
        elif ptype == "describe_sub_devices"
            payload = {
                "type": ptype
            }
        pass

        return payload

    def gateway_init(self, topic, qos, device_info):
        # 解析网关子设备信息,并添加到list
        subdev_num = device_info['subDev']['subdev_num']
        subdev_list = device_info['subDev']['subdev_list']

        index = 0
        while index < subdev_num:
            p_subdev = self.gateway_subdev()
            p_subdev.sub_productId = subdev_list[index]['sub_productId']
            p_subdev.sub_devName = subdev_list[index]['sub_devName']
            p_subdev.session_status = self.SessionState.SUBDEV_SEESION_STATUS_INIT

            self.gateway_subdev_list.append(p_subdev)
            index += 1
        pass

        rc, mid = self.__protocol.subscribe(topic, qos)
        if rc != 0:
            self.__logger.error("topic_subscribe error:rc:%d,topic:%s" % (rc, topic))
        return rc, mid

    def gateway_subdev_online(self, topic, qos, sub_productId, sub_devName):
        # 保存当前会话的设备client_id
        client_id = sub_productId + "/" + sub_devName
        payload = self.__build_session_payload("online", sub_productId, sub_devName, None)

        rc, mid = self.__protocol.publish(topic, payload, qos)
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

        rc, mid = self.__protocol.publish(topic, payload, qos)
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

        rc, mid = self.__protocol.publish(topic, payload, qos)
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

        rc, mid = self.__protocol.publish(topic, payload, qos)
        if rc != 0:
            self.__logger.error("topic_publish error:rc:%d,topic:%s" % (rc, topic))
            return rc, mid

        rc = self.__wait_for_session_reply(client_id, "unbind")
        if rc == 0:
            self.__logger.debug("client:%s %s success" % (client_id, "unbind"))
        else:
            self.__logger.debug("client:%s %s fail" % (client_id, "unbind"))

        return rc, mid
    
    def gateway_get_subdev_list(self, topic, qos, product_id, device_name, bind_list):
        client_id = product_id + "/" + device_name
        payload = self.__build_session_payload("describe_sub_devices", product_id, device_name, None)

        rc, mid = self.__protocol.publish(topic, payload, qos)
        if rc != 0:
            self.__logger.error("topic_publish error:rc:%d,topic:%s" % (rc, topic))
            return rc, mid

        rc = self.__wait_for_session_reply(client_id, "describe_sub_devices")
        if rc == 0:
            self.__logger.debug("client:%s %s success" % (client_id, "unbind"))
        else:
            self.__logger.debug("client:%s %s fail" % (client_id, "unbind"))

        # 直接使用赋值操作以节省空间,要求user不能修改该空间
        bind_list = self.__gateway_subdev_bind_list
        return rc, mid