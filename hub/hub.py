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

import logging
import threading
import queue
import json
import base64
import socket
import time
import random
import urllib.request
import urllib.parse
import urllib.error
from enum import Enum
from enum import IntEnum
from hub.log.log import Log
from hub.utils.codec import Codec
from hub.utils.providers import TopicProvider
from hub.utils.providers import DeviceInfoProvider
# from hub.protocol.protocol import AsyncConnClient
from hub.utils.providers import ConnClientProvider
from hub.manager.manager import TaskManager
from hub.services.gateway.gateway import Gateway
from hub.services.rrpc.rrpc import Rrpc
from hub.services.broadcast.broadcast import Broadcast
from hub.services.shadow.shadow import Shadow
from hub.services.ota.ota import Ota

class QcloudHub(object):
    """事件核心处理层
    作为explorer/user层与协议层的中间层,负责上下层通道建立、消息分发等事物
    """
    def __init__(self, device_file, userdata=None, tls=True, domain=None, useWebsocket=False):
        self.__tls = tls
        self.__useWebsocket = useWebsocket
        self.__key_mode = True
        self.__userdata = userdata
        self.__provider = None
        self.__protocol = None
        self.__host = ""
        self.__paholog = logging.getLogger("Paho")
        self._logger = Log()
        self.__codec = Codec()
        # 确保__protocol初始化后再初始化__gateway,以便传参
        self.__gateway = None
        self.__device_info = DeviceInfoProvider(device_file, self._logger)
        self.__hub_state = self.HubState.INITIALIZED
        self._topic = TopicProvider(self.__device_info.product_id, self.__device_info.device_name)

        """存放explorer层注册到hub层的回调函数
        只存放explorer层独有的功能所需的回调(诸如数据模板),
        类似on_connect等explorer和用户层都可能注册的回调在hub层使用专门的函数与之对应
        """
        self.__explorer_callback = {}

        """ 存放用户注册的回调函数 """
        self.__user_callback = {}

        """
        保存__on_subscribe()返回的mid和qos对,用以判断订阅是否成功
        """
        self.__subscribe_res = {}

        self.__ota_map = {}
        self.__rrpc_map = {}
        self.__shadow_map = {}
        self.__broadcast_map = {}

        self.__user_topics = {}
        self.__user_topics_subscribe_request = {}
        self.__user_topics_unsubscribe_request = {}
        self.__user_topics_request_lock = threading.Lock()
        self.__user_topics_unsubscribe_request_lock = threading.Lock()

        self.__loop_worker = self.LoopWorker(self._logger)
        self.__event_worker = self.EventWorker(self._logger)
        self.__register_event_callback()

        """
        hub层注册到mqtt的回调
        """
        self.__user_on_connect = None
        self.__user_on_disconnect = None
        self.__user_on_publish = None
        self.__user_on_subscribe = None
        self.__user_on_unsubscribe = None
        self.__user_on_message = None

        self.__protocol_init(domain, useWebsocket)

        # self.__rrpc = Rrpc(self.__host, self.__device_info.product_id, self.__device_info.device_name,
        #                         self.__device_info.device_secret, websocket=self.__useWebsocket,
        #                         tls=self.__tls, logger=self._logger)

        # self.__broadcast = Broadcast(self.__host, self.__device_info.product_id, self.__device_info.device_name,
        #                             self.__device_info.device_secret, websocket=self.__useWebsocket,
        #                             tls=self.__tls, logger=self._logger)

        self.__shadow = Shadow(self.__host, self.__device_info.product_id, self.__device_info.device_name,
                                    self.__device_info.device_secret, websocket=self.__useWebsocket,
                                    tls=self.__tls, logger=self._logger)

        # self.__ota = None

    class HubState(Enum):
        """ 连接状态 """
        INITIALIZED = 1
        CONNECTING = 2
        CONNECTED = 3
        DISCONNECTING = 4
        DISCONNECTED = 5
        DESTRUCTING = 6
        DESTRUCTED = 7
    
    class ErrorCode(Enum):
        ERR_NONE = 0  # 成功
        ERR_TOPIC_NONE = -1000  # topic为空
        
    
    class StateError(Exception):
        def __init__(self, err):
            Exception.__init__(self, err)

    # 管理连接相关资源
    class LoopWorker(object):
        """ mqtt连接管理维护 """
        def __init__(self, logger=None):
            self._connect_async_req = False
            self._exit_req = False
            self._runing_state = False
            self._exit_req_lock = threading.Lock()
            self._thread = TaskManager.LoopThread(logger)

    class EventWorker(object):
        """ 事件管理 """
        def __init__(self, logger=None):
            self._thread = TaskManager.EventCbThread(logger)
        
        def _register_event_callback(self, connect, disconnect,
                                        message, publish, subscribe, unsubscribe):
            self._thread.register_event_callback(self.EventPool.CONNECT, connect)
            self._thread.register_event_callback(self.EventPool.DISCONNECT, disconnect)
            self._thread.register_event_callback(self.EventPool.MESSAGE, message)
            self._thread.register_event_callback(self.EventPool.PUBLISH, publish)
            self._thread.register_event_callback(self.EventPool.SUBSCRISE, subscribe)
            self._thread.register_event_callback(self.EventPool.UNSUBSCRISE, unsubscribe)

            self._thread.start()

        class EventPool(object):
            CONNECT = "connect"
            DISCONNECT = "disconnect"
            MESSAGE = "message"
            PUBLISH = "publish"
            SUBSCRISE = "subscribe"
            UNSUBSCRISE = "unsubscribe"

    class sReplyPara(object):
        def __init__(self):
            self.timeout_ms = 0
            self.code = -1
            self.status_msg = None

    def __assert(self, param):
        if param is None or len(param) == 0:
            raise ValueError('Invalid param.')

    def __register_event_callback(self):
        self.__event_worker._register_event_callback(self.__user_connect,
                                                    self.__user_disconnect,
                                                    self.__user_message,
                                                    self.__user_publish,
                                                    self.__user_subscribe,
                                                    self.__user_unsubscribe)

    """
    处理用户回调
    基于explorer接入时会将用户回调赋值到本层用户回调函数
    """
    def __user_connect(self, value):
        # client, user_data, session_flag, rc = value
        session_flag, rc = value
        if self.__user_on_connect is not None:
            try:
                self.__user_on_connect(session_flag['session present'], rc, self.__userdata)
            except Exception as e:
                self._logger.error("on_connect process raise exception:%r" % e)
        pass

    def __user_disconnect(self, value):
        self.__user_on_disconnect(value, self.__userdata)
        pass

    def __user_publish(self, value):
        self.__user_on_publish(value, self.__userdata)
        pass

    def __user_subscribe(self, value):
        qos, mid = value
        self.__user_on_subscribe(qos, mid, self.__userdata)
        pass

    def __user_unsubscribe(self, value):
        self.__user_on_unsubscribe(value, self.__userdata)
        pass

    def __user_message(self, value):
        message = value
        topic = message.topic
        qos = message.qos
        payload = json.loads(message.payload.decode('utf-8'))
        # print(">>>>>>> from qcloud:%s, topic:%s" % (payload, topic))

        if topic == self._topic.template_property_topic_sub:
            if self.__explorer_callback[topic] is not None:
                self.__explorer_callback[topic](topic, qos, payload)
            else:
                self._logger.error("no callback for topic %s" % topic)

        elif topic == self._topic.template_event_topic_sub:
            if self.__explorer_callback[topic] is not None:
                self.__explorer_callback[topic](topic, qos, payload)
            else:
                self._logger.error("no callback for topic %s" % topic)

        elif topic == self._topic.template_action_topic_sub:
            if self.__explorer_callback[topic] is not None:
                self.__explorer_callback[topic](topic, qos, payload)
            else:
                self._logger.error("no callback for topic %s" % topic)

        elif topic == self._topic.template_service_topic_sub:
            if self.__explorer_callback[topic] is not None:
                self.__explorer_callback[topic](topic, qos, payload)
            else:
                self._logger.error("no callback for topic %s" % topic)

        elif topic == self._topic.template_raw_topic_sub:
            # 调用explorer向hub注册的回调处理
            self._logger.info("Reserved: template raw topic")

        elif topic in self.__user_topics:
            if self.__user_callback[topic] is not None:
                self.__user_callback[topic](topic, qos, payload, self.__userdata)
            else:
                self._logger.error("no callback for topic %s" % topic)

        elif topic == self._topic.template_topic_sub:
            if self.__user_callback[topic] is not None:
                self.__user_callback[topic](topic, qos, payload, self.__userdata)
            else:
                self._logger.error("no callback for topic %s" % topic)

        elif topic == self._topic.sys_topic_sub:
            # 获取时间暂作为内部服务，有message回调通知用户
            self.__user_on_message(topic, qos, payload, self.__userdata)
            # if self.__user_callback[topic] is not None:
            #     self.__user_callback[topic](topic, qos, payload, self.__userdata)
            # else:
            #     self._logger.error("no callback for topic %s" % topic)

        elif topic == self._topic.gateway_topic_sub:
            self.__gateway.handle_gateway(topic, payload)

        elif topic == self._topic.ota_update_topic_sub:
            ptype = payload["type"]
            if ptype == "report_version_rsp":
                """
                1.用户基于hub层接入,直接回调用户的注册函数
                2.用户基于explorer层接入,回调explorer的注册函数,由exporer调用用户的注册函数
                """
                if self.__user_callback[topic] is not None:
                    self.__user_callback[topic](topic, qos, payload, self.__userdata)
                elif self.__user_callback[topic] is not None:
                    self.__user_callback[topic](topic, qos, payload, self.__userdata)

            elif ptype == "update_firmware":
                pos = topic.rfind("/")
                device_name = topic[pos + 1:len(topic)]

                topic_split = topic[0:pos]
                pos = topic_split.rfind("/")
                product_id = topic_split[pos + 1:len(topic_split)]
                client = product_id + device_name
                if (client not in self.__ota_map.keys()
                        or self.__ota_map[client] is None):
                    self._logger.error("[ota] not found ota handle for client:%s" % (client))
                    return None

                ota = self.__ota_map[client]
                ota.handle_ota(topic, payload)

        elif self._topic.rrpc_topic_sub_prefix in topic:
            # topic:$rrpc/rxd/${productID}/${deviceName}/${processID}
            pos = topic.rfind("/")
            topic_split1 = topic[0:pos]

            pos = topic_split1.rfind("/")
            device_name = topic_split1[pos + 1:len(topic_split1)]

            topic_split = topic_split1[0:pos]
            pos = topic_split.rfind("/")
            product_id = topic_split[pos + 1:len(topic_split)]

            client = product_id + device_name
            if (client not in self.__rrpc_map.keys()
                    or self.__rrpc_map[client] is None):
                self._logger.error("[template] not found template handle for client:%s" % (client))
                return None

            rrpc = self.__rrpc_map[client]
            rrpc.handle_rrpc(topic, payload)
            if self.__user_callback[topic] is not None:
                self.__user_callback[topic](topic, qos, payload, self.__userdata)
            else:
                self._logger.error("no callback for topic %s" % topic)

        elif self._topic.shadow_topic_sub in topic:
            if self.__user_callback[topic] is not None:
                self.__user_callback[topic](topic, qos, payload, self.__userdata)
            else:
                self._logger.error("no callback for topic %s" % topic)

        elif self._topic.broadcast_topic_sub in topic:
            if self.__user_callback[topic] is not None:
                self.__user_callback[topic](topic, qos, payload, self.__userdata)
            else:
                self._logger.error("no callback for topic %s" % topic)

        else:
            if self.__explorer_callback[topic] is not None:
                self.__explorer_callback[topic](topic, qos, payload)
            else:
                self._logger.error("unknow topic:%s" % topic)
        pass

    def __on_connect(self, client, user_data, session_flag, rc):
        if rc == 0:
            self.__protocol.reset_reconnect_wait()
            self.__hub_state = self.HubState.CONNECTED
            self.__event_worker._thread.post_message(self.__event_worker.EventPool.CONNECT, (session_flag, rc))

            sys_topic_sub = self._topic.sys_topic_sub
            sys_topic_pub = self._topic.sys_topic_pub
            qos = 0
            rc, mid = self.subscribe(sys_topic_sub, qos)
            if rc == 0:
                payload = {
                    "type": "get",
                    "resource": [
                        "time"
                    ],
                }
                self.publish(sys_topic_pub, payload, qos)
            else:
                self._logger.error("topic_subscribe error:rc:%d" % (rc))
        pass

    def __on_disconnect(self, client, user_data, rc):
        if self.__hub_state == self.HubState.DISCONNECTING:
            self.__hub_state = self.HubState.DISCONNECTED
        elif self.__hub_state == self.HubState.DESTRUCTING:
            self.__hub_state = self.HubState.DESTRUCTED
        elif self.__hub_state == self.HubState.CONNECTED:
            self.__hub_state = self.HubState.DISCONNECTED
        else:
            self._logger.error("state error:%r" % self.__hub_state)
            return

        self.__user_topics_subscribe_request.clear()
        self.__user_topics_unsubscribe_request.clear()
        self.__user_topics.clear()

        self.__gateway.gateway_reset()

        """
        将disconnect事件通知到explorer
        """
        ex_topic = "$explorer/from/disconnect"
        if self.__user_callback[ex_topic] is not None:
            self.__user_callback[ex_topic](client, self.__userdata, rc)
        else:
            self._logger.error("no callback for topic %s" % ex_topic)

        self.__event_worker._thread.post_message(self.__event_worker.EventPool.DISCONNECT, (rc))
        if self.__hub_state == self.HubState.DESTRUCTED:
            self.__event_worker._thread.stop()

    def __on_message(self, client, user_data, message):
        self.__event_worker._thread.post_message(self.__event_worker.EventPool.MESSAGE, (message))

    def __on_publish(self, client, user_data, mid):
        self.__event_worker._thread.post_message(self.__event_worker.EventPool.PUBLISH, (mid))

    def __on_subscribe(self, client, user_data, mid, granted_qos):
        qos = granted_qos[0]
        # todo:mid,qos
        self.__subscribe_res[mid] = qos
        self.__event_worker._thread.post_message(self.__event_worker.EventPool.SUBSCRISE, (qos, mid))

    def __on_unsubscribe(self, client, user_data, mid):
        self.__event_worker._thread.post_message(self.__event_worker.EventPool.UNSUBSCRISE, (mid))

    def _loop(self):
        if self.__hub_state not in (self.HubState.INITIALIZED,
                                     self.HubState.DISCONNECTED):
            raise self.StateError("current state is not in INITIALIZED or DISCONNECTED")
        self.__hub_state = self.HubState.CONNECTING

        if self.__protocol.connect() is not True:
            self.__hub_state = self.HubState.INITIALIZED
            return

        while True:
            if self.__loop_worker._exit_req:
                if self.__hub_state == self.HubState.DESTRUCTING:
                    self.__loop_worker._thread.stop()
                    self.__hub_state = self.HubState.DESTRUCTED
                break
            try:
                self.__hub_state = self.HubState.CONNECTING
                """
                实际连接
                """
                self.__protocol.reconnect()
            except (socket.error, OSError) as e:
                self._logger.error("mqtt reconnect error:" + str(e))
                # 失败处理 待添加
                if self.__hub_state == self.HubState.CONNECTING:
                    self.__hub_state = self.HubState.DISCONNECTED
                    self.__protocol.reset_reconnect_wait()

                    if self.__hub_state == self.HubState.DESTRUCTING:
                        self.__loop_worker._thread.stop()
                        self.__hub_state = self.HubState.DESTRUCTED
                        break
                    self.__protocol.reconnect_wait()
                continue
            """
            调用循环调用mqtt loop读取消息
            """
            self.__protocol.loop()
            """
            mqtt loop接口失败(异常导致的disconnect)
            1.将disconnect事件通知到用户
            2.清理sdk相关资源
            """
            if self.__hub_state == self.HubState.CONNECTED:
                self.__on_disconnect(None, None, -1)
            """
            清理线程资源
            """
            if self.__loop_worker._exit_req:
                if self.__hub_state == self.HubState.DESTRUCTING:
                    self.__loop_worker._thread.stop()
                    self.__hub_state = self.HubState.DESTRUCTED
                break
            self.__protocol.reconnect_wait()

        pass

    def registerMqttCallback(self, on_connect, on_disconnect,
                            on_message, on_publish,
                            on_subscribe, on_unsubscribe):
        """
        注册用户层mqtt回调到hub层
        """
        self.__user_on_connect = on_connect
        self.__user_on_disconnect = on_disconnect
        self.__user_on_message = on_message
        self.__user_on_publish = on_publish
        self.__user_on_subscribe = on_subscribe
        self.__user_on_unsubscribe = on_unsubscribe

    def registerUserCallback(self, topic, callback):
        """
        用户注册回调接口
        """
        self.__user_callback[topic] = callback

    def enableLogger(self, level):
        self._logger.set_level(level)
        self._logger.enable_logger()
        self.__protocol.enable_logger(self.__paholog)
        self.__paholog.setLevel(level)

    def isMqttConnected(self):
        return self.__hub_state == self.HubState.CONNECTED

    def getConnectState(self):
        return self.__hub_state

    def register_explorer_callback(self, topic, callback):
        """
        注册explorer层回调到hub层
        topic可为单个topic或topic列表
        """
        if isinstance(topic, str):
            if topic is not None or len(topic) > 0:
                self.__explorer_callback[topic] = callback
        if isinstance(topic, list):
            for tp in topic:
                self.__explorer_callback[tp] = callback
        pass

    # 连接协议(mqtt/websocket)初始化
    def __protocol_init(self, domain=None, useWebsocket=False):
        auth_mode = self.__device_info.auth_mode
        device_name = self.__device_info.device_name
        product_id = self.__device_info.product_id
        device_secret = self.__device_info.device_secret
        ca = self.__device_info.ca_file
        cert = self.__device_info.cert_file
        key = self.__device_info.private_key_file

        if useWebsocket is False:
            if domain is None or domain == "":
                self.__host = product_id + ".iotcloud.tencentdevices.com"
            else:
                self.__host = product_id + domain
        else:
            if self.__tls:
                self.__host = "wss:" + product_id + ".ap-guangzhou.iothub.tencentdevices.com"
            else:
                self.__host = "ws:" + product_id + ".ap-guangzhou.iothub.tencentdevices.com"
        self.__provider = ConnClientProvider(self.__host, product_id, device_name, device_secret,
                                                websocket=useWebsocket, tls=self.__tls, logger=self._logger)
        self.__protocol = self.__provider.protocol

        if auth_mode == "CERT":
            self.__protocol.set_cert_file(ca, cert, key)
        
        self.__protocol.register_event_callbacks(self.__on_connect,
                                                    self.__on_disconnect,
                                                    self.__on_message,
                                                    self.__on_publish,
                                                    self.__on_subscribe,
                                                    self.__on_unsubscribe)
        pass

    def setReconnectInterval(self, max_sec, min_sec):
        if self.__protocol is None:
            self._logger.error("Set failed: client is None")
            return
        self.__protocol.set_reconnect_interval(max_sec, min_sec)
        self.__protocol.config_connect()

    def setMessageTimout(self, timeout):
        if self.__protocol is None:
            self._logger.error("Set failed: client is None")
            return
        self.__protocol.set_message_timout(timeout)
    
    def setKeepaliveInterval(self, interval):
        if self.__protocol is None:
            self._logger.error("Set failed: client is None")
            return
        self.__protocol.set_keepalive_interval(interval)

    def getProtocolHandle(self):
        return self.__protocol
    
    def getProductID(self):
        return self.__device_info.product_id
    
    def getDeviceName(self):
        return self.__device_info.device_name

    def connect(self):
        self.__loop_worker._connect_async_req = True
        with self.__loop_worker._exit_req_lock:
            self.__loop_worker._exit_req = False
        return self.__loop_worker._thread.start(self._loop)

    def disconnect(self):
        self._logger.debug("disconnect")
        if self.__hub_state is not self.HubState.CONNECTED:
            raise self.StateError("current state is not CONNECTED")
        self.__hub_state = self.HubState.DISCONNECTING
        if self.__loop_worker._connect_async_req is True:
            with self.__loop_worker._exit_req_lock:
                self.__loop_worker._exit_req = True

        self.__protocol.disconnect()
        self.__loop_worker._thread.stop()
    
    def subscribe(self, topic, qos):
        self._logger.debug("sub topic:%s,qos:%d" % (topic, qos))
        if self.__hub_state is not self.HubState.CONNECTED:
            raise self.StateError("current state is not CONNECTED")
        if isinstance(topic, tuple):
            topic, qos = topic
        if isinstance(topic, str):
            if qos < 0:
                raise ValueError('Invalid QoS level.')
            if topic is None or len(topic) == 0:
                raise ValueError('Invalid topic.')
            pass
            self.__user_topics_request_lock.acquire()
            rc, mid = self.__protocol.subscribe(topic, qos)
            if rc == 0:
                self.__user_topics_subscribe_request[mid] = [(topic, qos)]
            self.__user_topics_request_lock.release()
            return rc, mid
        # topic format [(topic1, qos),(topic2,qos)]
        if isinstance(topic, list):
            self.__user_topics_request_lock.acquire()
            rc, mid = self.__protocol.subscribe(topic)
            if rc == 0:
                self.__user_topics_subscribe_request[mid] = [topic]
            self.__user_topics_request_lock.release()
            return rc, mid
        pass

    def unsubscribe(self, topic):
        if self.__hub_state is not self.HubState.CONNECTED:
            raise self.StateError("current state is not CONNECTED")
        unsubscribe_topics = []
        if topic is None or len(topic) == 0:
            raise ValueError('Invalid topic.')
        if isinstance(topic, str):
            # topic判断
            unsubscribe_topics.append(topic)
        elif isinstance(topic, list):
            for tp in topic:
                unsubscribe_topics.append(tp)
            pass
        with self.__user_topics_unsubscribe_request_lock:
            if len(unsubscribe_topics) == 0:
                return self.ErrorCode.ERR_TOPIC_NONE, -1
            rc, mid = self.__protocol.unsubscribe(unsubscribe_topics)
            if rc == 0:
                self.__user_topics_unsubscribe_request[mid] = unsubscribe_topics
            return rc, mid
        pass

    def publish(self, topic, payload, qos):
        self._logger.debug("pub topic:%s,payload:%s,qos:%d" % (topic, payload, qos))
        if self.__hub_state is not self.HubState.CONNECTED:
            raise self.StateError("current state is not CONNECTED")
        if topic is None or len(topic) == 0:
            raise ValueError('Invalid topic.')
        if qos < 0:
            raise ValueError('Invalid QoS level.')

        return self.__protocol.publish(topic, json.dumps(payload), qos)
    
    def dynregDevice(self, timeout=10):
        sign_format = '%s\n%s\n%s\n%s\n%s\n%d\n%d\n%s'
        url_format = '%s://ap-guangzhou.gateway.tencentdevices.com/device/register'
        request_format = "{\"ProductId\":\"%s\",\"DeviceName\":\"%s\"}"

        device_name = self.__device_info.device_name
        product_id = self.__device_info.product_id
        product_secret = self.__device_info.product_secret

        request_text = request_format % (product_id, device_name)
        # request_hash = hashlib.sha256(request_text.encode("utf-8")).hexdigest()
        request_hash = self.__codec.Hash.sha256_encode(request_text.encode("utf-8"))

        nonce = random.randrange(2147483647)
        timestamp = int(time.time())
        sign_content = sign_format % (
            "POST", "ap-guangzhou.gateway.tencentdevices.com",
            "/device/register", "", "hmacsha256", timestamp,
            nonce, request_hash)

        # sign_base64 = base64.b64encode(hmac.new(product_secret.encode("utf-8"),
        #                 sign_content.encode("utf-8"), hashlib.sha256).digest())
        sign_base64 = self.__codec.Base64.encode(self.__codec.Hmac.sha256_encode(product_secret.encode("utf-8"),
                            sign_content.encode("utf-8")))

        header = {
            'Content-Type': 'application/json; charset=utf-8',
            "X-TC-Algorithm": "hmacsha256",
            "X-TC-Timestamp": timestamp,
            "X-TC-Nonce": nonce,
            "X-TC-Signature": sign_base64
        }
        data = bytes(request_text, encoding='utf-8')

        context = None
        if self.__tls:
            request_url = url_format % 'https'
            # context = ssl.create_default_context(
            #     ssl.Purpose.CLIENT_AUTH, cadata=self.__iot_ca_crt)
            context = self.__codec.Ssl().create_content()
        else:
            request_url = url_format % 'http'
        self._logger.info('dynreg url {}'.format(request_url))
        req = urllib.request.Request(request_url, data=data, headers=header)
        with urllib.request.urlopen(req, timeout=timeout, context=context) as url_file:
            reply_data = url_file.read().decode('utf-8')
            reply_obj = json.loads(reply_data)
            print("reply:%s" % reply_obj)
            resp = reply_obj['Response']
            if 'Len' in resp and resp['Len'] > 0:
                reply_obj_data = reply_obj['Response']["Payload"]
                if reply_obj_data is not None:
                    psk = self.__codec._AESUtil.decrypt(reply_obj_data.encode('UTF-8') , product_secret[:self.__codec._AESUtil.BLOCK_SIZE_16].encode('UTF-8'),
                                        '0000000000000000'.encode('UTF-8'))
                    psk = psk.decode('UTF-8', 'ignore').strip().strip(b'\x00'.decode())
                    user_dict = json.loads(psk)
                    self._logger.info('encrypt type: {}'.format(
                        user_dict['encryptionType']))
                    return 0, user_dict['psk']
                else:
                    self._logger.warring('payload is null')
                    return -1, 'payload is null'
            else:
                err_code = resp['Error']
                self._logger.error('code: {}, error message: {}'.format(
                    err_code, err_code['Message']))
                return -1, err_code['Message']

    def isSubdevStatusOnline(self, sub_productId, sub_devName):
        return self.__gateway.is_subdev_status_online(sub_productId, sub_devName)

    def updateSubdevStatus(self, sub_productId, sub_devName, status):
        return self.__gateway.update_subdev_status(sub_productId, sub_devName, status)

    def gatewaySubdevGetConfigList(self):
        return self.__gateway.gateway_get_subdev_config_list()

    def gatewaySubdevOnline(self, sub_productId, sub_devName):
        self.__assert(sub_productId)
        self.__assert(sub_devName)

        gateway_topic_pub = self._topic.gateway_topic_pub
        return self.__gateway.gateway_subdev_online(gateway_topic_pub, 0, sub_productId, sub_devName)

    def gatewaySubdevOffline(self, sub_productId, sub_devName):
        self.__assert(sub_productId)
        self.__assert(sub_devName)

        gateway_topic_pub = self._topic.gateway_topic_pub
        return self.__gateway.gateway_subdev_offline(gateway_topic_pub, 0, sub_productId, sub_devName)

    def gatewaySubdevBind(self, sub_productId, sub_devName, sub_secret):
        self.__assert(sub_productId)
        self.__assert(sub_devName)
        self.__assert(sub_secret)

        gateway_topic_pub = self._topic.gateway_topic_pub
        return self.__gateway.gateway_subdev_bind(gateway_topic_pub, 0, sub_productId, sub_devName, sub_secret)

    def gatewaySubdevUnbind(self, sub_productId, sub_devName):
        self.__assert(sub_productId)
        self.__assert(sub_devName)

        gateway_topic_pub = self._topic.gateway_topic_pub
        return self.__gateway.gateway_subdev_unbind(gateway_topic_pub, 0, sub_productId, sub_devName)

    def gatewaySubdevGetBindList(self, product_id, device_name, bind_list):
        self.__assert(product_id)
        self.__assert(device_name)

        gateway_topic_pub = self._topic.gateway_topic_pub
        return self.__gateway.gateway_get_subdev_bind_list(gateway_topic_pub, 0, product_id, device_name, bind_list)
    
    def gatewaySubdevSubscribe(self, topic):
        return self.__gateway.gateway_subdev_subscribe(topic)

    def gatewayInit(self):
        if self.__hub_state is not self.HubState.CONNECTED:
            raise self.StateError("current state is not CONNECTED")

        # 将class AsyncConnClient实例传入gateway,方便其直接使用AsyncConnClient提供的能力
        # self.__gateway = Gateway(self.__protocol, self._logger)
        self.__gateway = Gateway(self.__host, self.__device_info.product_id, self.__device_info.device_name,
                                    self.__device_info.device_secret, websocket=self.__useWebsocket,
                                    tls=self.__tls, logger=self._logger)
        json_data = self.__device_info.json_data
        gateway_topic_sub = self._topic.gateway_topic_sub

        return self.__gateway.gateway_init(gateway_topic_sub, 0, json_data)

    def rrpcInit(self, productId, deviceName):
        if self.__hub_state is not self.HubState.CONNECTED:
            raise self.StateError("current state is not CONNECTED")

        client = productId + deviceName
        rrpc = Rrpc(self.__host, productId, deviceName,
                        "", websocket=self.__useWebsocket,
                        tls=self.__tls, logger=self._logger)

        # rrpc_topic_sub = self._topic.rrpc_topic_sub_prefix + "+"
        rc, mid = rrpc.rrpc_init()
        if rc != 0:
            self._logger.error("[rrpc] subscribe error:rc:%d" % (rc))
        else:
            self.__rrpc_map[client] = rrpc
        return rc, mid

    def rrpcReply(self, productId, deviceName, reply, length):
        client = productId + deviceName
        if (client not in self.__rrpc_map.keys()
                or self.__rrpc_map[client] is None):
            self._logger.error("[template] not found template handle for client:%s" % (client))
            return None

        rrpc = self.__rrpc_map[client]
        # topic_prefix = self._topic.rrpc_topic_pub_prefix
        rc, mid = rrpc.rrpc_reply(reply)
        if rc != 0:
            self._logger.error("[rrpc] publish error:rc:%d" % (rc))
        return rc, mid
    
    def broadcastInit(self, productId, deviceName):
        if self.__hub_state is not self.HubState.CONNECTED:
            raise self.StateError("current state is not CONNECTED")

        client = productId + deviceName
        broadcast = Broadcast(self.__host, productId, deviceName,
                                "", websocket=self.__useWebsocket,
                                tls=self.__tls, logger=self._logger)

        rc, mid = broadcast.broadcast_init()
        if rc != 0:
            self._logger.error("[broadcast] publish error:rc:%d" % (rc))
        else:
            self.__broadcast_map[client] = broadcast
        return rc, mid

    def shadowInit(self):
        if self.__hub_state is not self.HubState.CONNECTED:
            raise self.StateError("current state is not CONNECTED")

        shadow_topic_sub = self._topic.shadow_topic_sub
        rc, mid = self.__shadow.shadow_init(shadow_topic_sub, 0)
        if rc != 0:
            self._logger.error("[shadow] publish error:rc:%d,topic:%s" % (rc, shadow_topic_sub))
        return rc, mid

    def getShadow(self):
        topic_pub = self._topic.shadow_topic_pub
        rc, mid = self.__shadow.get_shadow(topic_pub, 0, self.__device_info.product_id)
        if rc != 0:
            self._logger.error("[shadow] publish error:rc:%d,topic:%s" % (rc, topic_pub))
        return rc, mid

    def shadowJsonConstructDesireNull(self):
        return self.__shadow.shadow_json_construct_desire_null(self.__device_info.product_id)

    def shadowUpdate(self, shadow_docs, length):
        topic = self._topic.shadow_topic_pub
        rc, mid = self.__shadow.shadow_update(topic, 0, shadow_docs)
        if rc != 0:
            self._logger.error("topic_publish error:rc:%d,topic:%s" % (rc, topic))
        return rc, mid

    def shadowJsonConstructReport(self, *args):
        return self.__shadow.shadow_json_construct_report(self.__device_info.product_id, args)

    def otaInit(self, productId, deviceName):
        if self.__hub_state is not self.HubState.CONNECTED:
            raise self.StateError("current state is not CONNECTED")

        ota = Ota(self.__host, self.__device_info.product_id,
                            self.__device_info.device_name, self.__device_info.device_secret,
                            websocket=self.__useWebsocket, tls=self.__tls, logger=self._logger)
        topic_sub = self._topic.ota_update_topic_sub
        rc, mid = ota.ota_init(productId, deviceName)
        if rc != 0:
            self._logger.error("[ota] subscribe error:rc:%d,topic:%s" % (rc, topic_sub))
            return rc, mid

        """
        等待订阅成功
        """
        cnt = 0
        while cnt < 10:
            if mid in self.__subscribe_res:
                # 收到该mid回调,且其qos>=0说明订阅完成,qos=0需另做判断
                if self.__subscribe_res[mid] >= 1:
                    break
            time.sleep(0.2)
            cnt += 1
            pass
        if cnt >= 10:
            return -1, mid

        ota.ota_manager_init()

        client = productId + deviceName
        self.__ota_map[client] = ota

        return rc, mid

    # 是否应将ota句柄传入(支持多个下载进程?)
    def otaIsFetching(self, productId, deviceName):
        client = productId + deviceName
        if (client not in self.__ota_map.keys()
                or self.__ota_map[client] is None):
            self._logger.error("[ota] not found ota handle for client:%s" % (client))
            return False

        ota = self.__ota_map[client]
        return ota.ota_is_fetching()

    def otaIsFetchFinished(self, productId, deviceName):
        client = productId + deviceName
        if (client not in self.__ota_map.keys()
                or self.__ota_map[client] is None):
            self._logger.error("[ota] not found ota handle for client:%s" % (client))
            return False

        ota = self.__ota_map[client]
        return ota.ota_is_fetch_finished()

    def otaReportUpgradeSuccess(self, productId, deviceName, version):
        client = productId + deviceName
        if (client not in self.__ota_map.keys()
                or self.__ota_map[client] is None):
            self._logger.error("[ota] not found ota handle for client:%s" % (client))
            return -1, -1

        ota = self.__ota_map[client]
        rc, mid = ota.ota_report_upgrade_success(version)
        if rc != 0:
            self._logger.error("ota report upgrade(success) fail")
        return rc, mid

    def otaReportUpgradeFail(self, productId, deviceName, version):
        client = productId + deviceName
        if (client not in self.__ota_map.keys()
                or self.__ota_map[client] is None):
            self._logger.error("[ota] not found ota handle for client:%s" % (client))
            return -1, -1

        ota = self.__ota_map[client]
        rc, mid = ota.ota_report_upgrade_fail(version)
        if rc != 0:
            self._logger.error("ota report upgrade(fail) fail")
        return rc, mid

    def otaIoctlNumber(self, productId, deviceName, cmdType):
        client = productId + deviceName
        if (client not in self.__ota_map.keys()
                or self.__ota_map[client] is None):
            self._logger.error("[ota] not found ota handle for client:%s" % (client))
            return -1, "no handle"

        ota = self.__ota_map[client]
        return ota.ota_ioctl_number(cmdType)

    def otaIoctlString(self, productId, deviceName, cmdType, length):
        client = productId + deviceName
        if (client not in self.__ota_map.keys()
                or self.__ota_map[client] is None):
            self._logger.error("[ota] not found ota handle for client:%s" % (client))
            return "null", "no handle"

        ota = self.__ota_map[client]
        return ota.ota_ioctl_string(cmdType, length)

    def otaResetMd5(self, productId, deviceName):
        client = productId + deviceName
        if (client not in self.__ota_map.keys()
                or self.__ota_map[client] is None):
            self._logger.error("[ota] not found ota handle for client:%s" % (client))
            return -1

        ota = self.__ota_map[client]
        return ota.ota_reset_md5()

    def otaMd5Update(self, productId, deviceName,buf):
        client = productId + deviceName
        if (client not in self.__ota_map.keys()
                or self.__ota_map[client] is None):
            self._logger.error("[ota] not found ota handle for client:%s" % (client))
            return -1

        ota = self.__ota_map[client]
        return ota.ota_md5_update(buf)

    def __ota_http_deinit(self, productId, deviceName, http):
        print("__ota_http_deinit do nothing")

    def httpInit(self, productId, deviceName, host, url, offset, size, timeoutSec):
        client = productId + deviceName
        if (client not in self.__ota_map.keys()
                or self.__ota_map[client] is None):
            self._logger.error("[ota] not found ota handle for client:%s" % (client))
            return -1

        ota = self.__ota_map[client]
        return ota.http_init(host, url, offset, size, timeoutSec)

    def httpFetch(self, productId, deviceName, buf_len):
        client = productId + deviceName
        if (client not in self.__ota_map.keys()
                or self.__ota_map[client] is None):
            self._logger.error("[ota] not found ota handle for client:%s" % (client))
            return None, -1

        ota = self.__ota_map[client]
        return ota.http_fetch(buf_len)

    def otaReportVersion(self, productId, deviceName, version):
        client = productId + deviceName
        if (client not in self.__ota_map.keys()
                or self.__ota_map[client] is None):
            self._logger.error("[ota] not found ota handle for client:%s" % (client))
            return -1, -1

        ota = self.__ota_map[client]
        rc, mid = ota.ota_report_version(version)
        if rc != 0:
            self._logger.error("[ota] report version fail")
        return rc, mid

    def otaDownloadStart(self, productId, deviceName, offset, size):
        client = productId + deviceName
        if (client not in self.__ota_map.keys()
                or self.__ota_map[client] is None):
            self._logger.error("[ota] not found ota handle for client:%s" % (client))
            return -1

        ota = self.__ota_map[client]
        return ota.ota_download_start(offset, size)

    def otaFetchYield(self, productId, deviceName, buf_len):
        client = productId + deviceName
        if (client not in self.__ota_map.keys()
                or self.__ota_map[client] is None):
            self._logger.error("[ota] not found ota handle for client:%s" % (client))
            return None, -1

        ota = self.__ota_map[client]
        return ota.ota_fetch_yield(buf_len)
