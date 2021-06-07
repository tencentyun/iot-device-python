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
from hub.protocol.protocol import AsyncConnClient
from hub.manager.manager import TaskManager
from hub.services.gateway.gateway import Gateway


class QcloudHub(object):
    """事件核心处理层
    作为explorer/user层与协议层的中间层,负责上下层通道建立、消息分发等事物
    """
    def __init__(self, device_file, userdata=None, tls=True):
        self.__tls = tls
        self.__key_mode = True
        self.__userdata = userdata
        self.__protocol = None
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

        self.__user_topics_subscribe_request = {}
        self.__user_topics_unsubscribe_request = {}
        self.__user_topics_request_lock = threading.Lock()
        self.__user_topics_unsubscribe_request_lock = threading.Lock()

        self.__loop_worker = self.LoopWorker(self._logger)
        self.__event_worker = self.EventWorker(self._logger)
        self.__register_event_callback()
        # self.__utils = Utils()

        """存放通用回调
        explorer和用户层都可能注册的回调在此存放
        """
        self.__user_on_connect = None
        self.__user_on_disconnect = None
        self.__user_on_publish = None
        self.__user_on_subscribe = None
        self.__user_on_unsubscribe = None
        self.__user_on_message = None

    @property
    def user_on_connect(self):
        return self.__user_on_connect

    @user_on_connect.setter
    def user_on_connect(self, value):
        self.__user_on_connect = value
        pass

    @property
    def user_on_disconnect(self):
        return self.__user_on_disconnect

    @user_on_disconnect.setter
    def user_on_disconnect(self, value):
        self.__user_on_disconnect = value
        pass

    @property
    def user_on_publish(self):
        return self.__user_on_publish

    @user_on_publish.setter
    def user_on_publish(self, value):
        self.__user_on_publish = value
        pass

    @property
    def user_on_subscribe(self):
        return self.__user_on_subscribe

    @user_on_subscribe.setter
    def user_on_subscribe(self, value):
        self.__user_on_subscribe = value
        pass

    @property
    def user_on_unsubscribe(self):
        return self.__user_on_unsubscribe

    @user_on_unsubscribe.setter
    def user_on_unsubscribe(self, value):
        self.__user_on_unsubscribe = value
        pass

    @property
    def user_on_message(self):
        return self.__user_on_message

    @user_on_message.setter
    def user_on_message(self, value):
        self.__user_on_message = value
        pass

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

    class OtaState(Enum):
        IOT_OTAS_UNINITED = 0
        IOT_OTAS_INITED = 1
        IOT_OTAS_FETCHING = 2
        IOT_OTAS_FETCHED = 3
        IOT_OTAS_DISCONNECTED = 4

    class OtaCmdType(Enum):
        IOT_OTAG_FETCHED_SIZE = 0
        IOT_OTAG_FILE_SIZE = 1
        IOT_OTAG_MD5SUM = 2
        IOT_OTAG_VERSION = 3
        IOT_OTAG_CHECK_FIRMWARE = 4

    class OtaProgressCode(Enum):
        IOT_OTAP_BURN_FAILED = -4
        IOT_OTAP_CHECK_FALIED = -3
        IOT_OTAP_FETCH_FAILED = -2
        IOT_OTAP_GENERAL_FAILED = -1
        IOT_OTAP_FETCH_PERCENTAGE_MIN = 0
        IOT_OTAP_FETCH_PERCENTAGE_MAX = 100

    class OtaReportType(IntEnum):
        IOT_OTAR_DOWNLOAD_TIMEOUT = -1
        IOT_OTAR_FILE_NOT_EXIST = -2
        IOT_OTAR_AUTH_FAIL = -3
        IOT_OTAR_MD5_NOT_MATCH = -4
        IOT_OTAR_UPGRADE_FAIL = -5
        IOT_OTAR_NONE = 0
        IOT_OTAR_DOWNLOAD_BEGIN = 1
        IOT_OTAR_DOWNLOADING = 2
        IOT_OTAR_UPGRADE_BEGIN = 3
        IOT_OTAR_UPGRADE_SUCCESS = 4

    # property结构
    class template_property(object):
        def __init__(self):
            self.key = None
            self.data = None
            self.data_buff_len = 0
            self.type = None

    class template_action(object):
        def __init__(self):
            self.action_id = None
            self.timestamp = 0
            self.input_num = 0
            self.output_num = 0
            self.actions_input_prop = []
            self.actions_output_prop = []

        def action_input_append(self, prop):
            self.actions_input_prop.append(prop)

        def action_output_append(self, prop):
            self.actions_output_prop.append(prop)

    # event结构(sEvent)
    class template_event(object):
        def __init__(self):
            self.event_name = None
            self.type = None
            self.timestamp = 0
            self.eventDataNum = 0
            self.events_prop = []

        def event_append(self, prop):
            self.events_prop.append(prop)

    class ota_manage(object):
        def __init__(self):
            self.channel = None
            self.state = 0
            self.size_fetched = 0
            self.size_last_fetched = 0
            self.file_size = 0
            self.purl = None
            self.version = None
            self.md5sum = None
            self.md5 = None
            self.host = None
            self.is_https = False

            self.report_timestamp = 0

            # http连接管理
            self.http_manager = None

    class http_manage(object):
        def __init__(self):
            self.handle = None
            self.request = None
            self.header = None
            self.host = None
            self.https_context = None

            self.err_reason = None
            self.err_code = 0
            pass

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

    # user callback
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
        # 从explorer接入时,在此调用explorer注册进来的对应回调
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
        mid = message.mid
        payload = json.loads(message.payload.decode('utf-8'))
        self._logger.info("payload:%s\n" % payload)

        if topic == self._topic.template_property_topic_sub:
            # 回调到explorer层处理
            if self.__explorer_callback[topic] is not None:
                self.__explorer_callback[topic](payload)

        elif topic == self._topic.template_event_topic_sub:
            # 回调到explorer层处理
            if self.__explorer_callback[topic] is not None:
                self.__explorer_callback[topic](payload)

        elif topic == self._topic.template_action_topic_sub:
            # 回调到explorer层处理
            if self.__explorer_callback[topic] is not None:
                self.__explorer_callback[topic](payload)

        elif topic == self._topic.template_service_topic_sub:
            self._logger.info("--------Reserved: template service topic")

            try:
                self.__on_subscribe_service_post(payload, self.__userdata)
            except Exception as e:
                self._logger.error("__on_subscribe_service_post raise exception:%s" % e)
            pass

        elif topic == self._topic.template_raw_topic_sub:
            # 调用explorer向hub注册的回调处理
            self._logger.info("Reserved: template raw topic")

        elif topic in self.__user_topics and self.__user_on_message is not None:
            try:
                self.__user_on_message(topic, payload, qos, self.__userdata)
            except Exception as e:
                self._logger.error("user_on_message process raise exception:%s" % e)
            pass
        elif topic == self._topic.template_topic_sub:
            self.__user_on_message(topic, payload, qos, self.__userdata)
        elif topic == self._topic.sys_topic_sub:
            self.__user_on_message(topic, payload, qos, self.__userdata)
        elif topic == self._topic.gateway_topic_sub:
            self.__gateway.handle_gateway(payload)
        elif topic == self._topic.ota_update_topic_sub:
            self.__handle_ota(payload)
        elif self._topic.rrpc_topic_sub_prefix in topic:
            self.__handle_rrpc(topic, payload)
        elif self._topic.shadow_topic_sub in topic:
            self.__user_on_message(topic, payload, qos, self.__userdata)
        elif self._topic.broadcast_topic_sub in topic:
            self.__user_on_message(topic, payload, qos, self.__userdata)
        else:
            rc = self.__handle_nonStandard_topic(topic, payload)
            if rc != 0:
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
            sub_res, mid = self.subscribe(sys_topic_sub, qos)
            self._logger.debug("mid:%d" % mid)
            if sub_res == 0:
                payload = {
                    "type": "get",
                    "resource": [
                        "time"
                    ],
                }
                self.publish(sys_topic_pub, payload, qos)
            else:
                self._logger.error("topic_subscribe error:rc:%d" % (sub_res))
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

        # todo:资源清理
        # self.__template_prop_report_reply_mid.clear()
        # self.__user_topics.clear()
        # self.__gateway_session_online_reply.clear()
        # self.__gateway_session_offline_reply.clear()
        # self.__gateway_session_bind_reply.clear()
        # self.__gateway_session_unbind_reply.clear()
        # self.__on_gateway_subdev_prop_cb_dict.clear()
        # self.__on_gateway_subdev_action_cb_dict.clear()
        # self.__on_gateway_subdev_event_cb_dict.clear()

        # self.__user_thread.post_message(self.__user_cmd_on_disconnect, (client, user_data, rc))
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
        # self.__ota_subscribe_res[mid] = qos
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
                    # self.__handler_task.stop()
                    self.__hub_state = self.HubState.DESTRUCTED
                break
            try:
                self.__hub_state = self.HubState.CONNECTING
                self.__protocol.reconnect()
            except (socket.error, OSError) as e:
                self._logger.error("mqtt reconnect error:" + str(e))
                # 失败处理 待添加
                if self.__hub_state == self.HubState.CONNECTING:
                    self.__hub_state = self.HubState.DISCONNECTED
                    # self.__on__connect_safe(None, None, 0, 9)
                    if self.__hub_state == self.HubState.DESTRUCTING:
                        # self.__handler_task.stop()
                        self.__hub_state = self.HubState.DESTRUCTED
                        break
                    self.__protocol.reconnect_wait()
                continue
            self.__protocol.loop()
        pass

    def enableLogger(self, level):
        self._logger.set_level(level)
        self._logger.enable_logger()
        self.__protocol.enable_logger(self.__paholog)
        self.__paholog.setLevel(level)

    def isMqttConnected(self):
        return self.__hub_state == self.HubState.CONNECTED

    def register_explorer_callback(self, topic, callback):
        if topic is not None or len(topic) > 0:
            self.__explorer_callback[topic] = callback

    # 连接协议(mqtt/websocket)初始化
    def protocolInit(self, domain=None, useWebsocket=False):
        auth_mode = self.__device_info.auth_mode
        device_name = self.__device_info.device_name
        product_id = self.__device_info.product_id
        device_secret = self.__device_info.device_secret
        ca = self.__device_info.ca_file
        cert = self.__device_info.cert_file
        key = self.__device_info.private_key_file

        if useWebsocket is False:
            host = ""
            if domain is None or domain == "":
                host = product_id + ".iotcloud.tencentdevices.com"
            else:
                host = product_id + domain
            self.__protocol = AsyncConnClient(host, product_id, device_name, device_secret, logger=self._logger)
        else:
            if self.__tls:
                host = "wss:" + product_id + ".ap-guangzhou.iothub.tencentdevices.com"
            else:
                host = "ws:" + product_id + ".ap-guangzhou.iothub.tencentdevices.com"
            self.__protocol = AsyncConnClient(host, product_id, device_name, device_secret, websocket=True, logger=self._logger)

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

    def connect(self):
        self.__loop_worker.__connect_async_req = True
        with self.__loop_worker._exit_req_lock:
            self.__loop_worker._exit_req = False
        return self.__loop_worker._thread.start(self._loop)

    def disconnect(self):
        self._logger.debug("disconnect")
        if self.__hub_state is not self.HubState.CONNECTED:
            raise self.StateError("current state is not CONNECTED")
        self.__hub_state = self.HubState.DISCONNECTING
        if self.__loop_worker._connect_async_req:
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

        # self.__logger.debug('sign base64 {}'.format(sign_base64))
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
            if reply_obj['Response']['Len'] > 0:
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
                self._logger.error('code: {}, error message: {}'.format(
                    reply_obj['code'], reply_obj['message']))
                return -1, reply_obj['message']

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
        return self.__gateway.gateway_get_subdev_list(gateway_topic_pub, 0, product_id, device_name, bind_list)

    def gatewayInit(self):
        if self.__hub_state is not self.HubState.CONNECTED:
            raise self.StateError("current state is not CONNECTED")

        # 将class AsyncConnClient实例传入gateway,方便其直接使用AsyncConnClient提供的能力
        self.__gateway = Gateway(self.__protocol, self._logger)
        json_data = self.__device_info.json_data
        gateway_topic_sub = self._topic.gateway_topic_sub

        return self.__gateway.gateway_init(gateway_topic_sub, 0, json_data)

        
        
    


