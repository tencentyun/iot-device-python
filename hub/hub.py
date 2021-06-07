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
from enum import Enum
from enum import IntEnum
# from Crypto.Cipher import AES
from hub.log.log import Log
from hub.utils.utils import Utils
from hub.protocol.protocol import AsyncConnClient
from hub.manager.manager import TaskManager

class QcloudHub(object):

    def __init__(self, device_file, userdata=None, tls=True):
        self.__tls = tls
        self.__key_mode = True
        self.__userdata = userdata
        self.__PahoLog = logging.getLogger("Paho")
        self.__hub_log = Log()
        self.__device_info = self.DeviceInfo(device_file, self.__hub_log)
        self.__protocol = None
        self.__hub_state = self.HubState.INITIALIZED
        self.__topic = self.Topic(self.__device_info.product_id, self.__device_info.device_name)

        self.__user_topics_subscribe_request = {}
        self.__user_topics_unsubscribe_request = {}
        self.__user_topics_request_lock = threading.Lock()
        self.__user_topics_unsubscribe_request_lock = threading.Lock()

        self.__loop_worker = self.LoopWorker(self.__hub_log)
        self.__event_worker = self.EventWorker(self.__hub_log)
        self.__register_event_callback()
        self.__utils = Utils()

        # user callback
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
        def __init__(self, logger=None):
            self._connect_async_req = False
            self._exit_req = False
            self._runing_state = False
            self._exit_req_lock = threading.Lock()
            self._thread = TaskManager.LoopThread(logger)

    class EventWorker(object):
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

        class EventPool(object):
            CONNECT = "connect"
            DISCONNECT = "disconnect"
            MESSAGE = "message"
            PUBLISH = "publish"
            SUBSCRISE = "subscribe"
            UNSUBSCRISE = "unsubscribe"

    class DeviceInfo(object):
        def __init__(self, file_path, logger=None):
            self.__logger = logger
            self.__logger.info('device_info file {}'.format(file_path))

            self.__auth_mode = None
            self.__device_name = None
            self.__product_id = None
            self.__product_secret = None
            self.__device_secret = None
            self.__ca_file = None
            self.__cert_file = None
            self.__private_key_file = None
            self.__region = None
            if self.__logger is not None:
                self.__logger.info('device_info file {}'.format(file_path))
            with open(file_path, 'r', encoding='utf-8') as f:
                self.__json_data = json.loads(f.read())
                self.__auth_mode = self.__json_data['auth_mode']
                self.__device_name = self.__json_data['deviceName']
                self.__product_id = self.__json_data['productId']
                self.__product_secret = self.__json_data['productSecret']
                self.__device_secret = self.__json_data['key_deviceinfo']['deviceSecret']
                self.__ca_file = self.__json_data['cert_deviceinfo']['devCaFile']
                self.__cert_file = self.__json_data['cert_deviceinfo']['devCertFile']
                self.__private_key_file = self.__json_data['cert_deviceinfo']['devPrivateKeyFile']
                self.__region = self.__json_data["region"]
            if self.__logger is not None:
                self.__logger.info(
                    "device name: {}, product id: {}, product secret: {}, device secret: {}".
                        format(self.__device_name, self.__product_id,
                               self.__product_secret, self.__device_secret))

        @property
        def auth_mode(self):
            return self.__auth_mode

        @property
        def device_name(self):
            return self.__device_name

        @property
        def product_id(self):
            return self.__product_id

        @property
        def product_secret(self):
            return self.__product_secret

        @property
        def device_secret(self):
            return self.__device_secret

        @property
        def ca_file(self):
            return self.__ca_file

        @property
        def cert_file(self):
            return self.__cert_file

        @property
        def private_key_file(self):
            return self.__private_key_file

        @property
        def region(self):
            return self.__region

        @property
        def json_data(self):
            return self.__json_data

    class Topic(object):
        def __init__(self, product_id, device_name):
            self.__clientToken = None

            # log topic
            self.__log_topic_pub = "$log/operation/%s/%s" % (product_id, device_name)
            self.__log_topic_sub = "$log/operation/result/%s/%s" % (product_id, device_name)
            self.__is_subscribed_log_topic = False

            # system topic
            self.__sys_topic_pub = "$sys/operation/%s/%s" % (product_id, device_name)
            self.__sys_topic_sub = "$sys/operation/result/%s/%s" % (product_id, device_name)

            # gateway topic
            self.__gateway_topic_pub = "$gateway/operation/%s/%s" % (product_id, device_name)
            self.__gateway_topic_sub = "$gateway/operation/result/%s/%s" % (product_id, device_name)

            # data template topic
            self.__template_topic_pub = "$template/operation/%s/%s" % (product_id, device_name)
            self.__template_topic_sub = "$template/operation/result/%s/%s" % (product_id, device_name)

            # thing topic
            self.__thing_property_topic_pub = "$thing/up/property/%s/%s" % (product_id, device_name)
            self.__thing_property_topic_sub = "$thing/down/property/%s/%s" % (product_id, device_name)
            # self.__is_subscribed_property_topic = False

            self.__thing_action_topic_pub = "$thing/up/action/%s/%s" % (product_id, device_name)
            self.__thing_action_topic_sub = "$thing/down/action/%s/%s" % (product_id, device_name)
            self.__thing_event_topic_pub = "$thing/up/event/%s/%s" % (product_id, device_name)
            self.__thing_event_topic_sub = "$thing/down/event/%s/%s" % (product_id, device_name)
            self.__thing_raw_topic_pub = "$thing/up/raw/%s/%s" % (product_id, device_name)
            self.__thing_raw_topic_sub = "$thing/down/raw/%s/%s" % (product_id, device_name)
            self.__thing_service_topic_pub = "$thing/up/service/%s/%s" % (product_id, device_name)
            self.__thing_service_topic_sub = "$thing/down/service/%s/%s" % (product_id, device_name)

            # ota topic
            self.__ota_report_topic_pub = "$ota/report/%s/%s" % (product_id, device_name)
            self.__ota_update_topic_sub = "$ota/update/%s/%s" % (product_id, device_name)

            # rrpc topic
            self.__rrpc_topic_pub_prefix = "$rrpc/txd/%s/%s/" % (product_id, device_name)
            self.__rrpc_topic_sub_prefix = "$rrpc/rxd/%s/%s/" % (product_id, device_name)

            # shadow
            self.__shadow_topic_pub = "$shadow/operation/%s/%s" % (product_id, device_name)
            self.__shadow_topic_sub = "$shadow/operation/result/%s/%s" % (product_id, device_name)

            # broadcast
            self.__broadcast_topic_sub = "$broadcast/rxd/%s/%s" % (product_id, device_name)
            pass

        @property
        def sys_topic_sub(self):
            return self.__sys_topic_sub

        @property
        def sys_topic_pub(self):
            return self.__sys_topic_pub

        @property
        def gateway_topic_sub(self):
            return self.__gateway_topic_sub

        @property
        def gateway_topic_pub(self):
            return self.__gateway_topic_pub

        @property
        def template_topic_sub(self):
            return self.__template_topic_sub

        @property
        def template_event_topic_sub(self):
            return self.__thing_event_topic_sub

        @property
        def template_event_topic_pub(self):
            return self.__thing_event_topic_pub

        @property
        def template_action_topic_sub(self):
            return self.__thing_action_topic_sub

        @property
        def template_property_topic_sub(self):
            return self.__thing_property_topic_sub

        @property
        def template_property_topic_pub(self):
            return self.__thing_property_topic_pub

        @property
        def template_action_topic_pub(self):
            return self.__thing_action_topic_pub

        @property
        def template_service_topic_sub(self):
            return self.__thing_service_topic_sub

        @property
        def template_raw_topic_sub(self):
            return self.__thing_raw_topic_sub

        @property
        def ota_update_topic_sub(self):
            return self.__ota_update_topic_sub

        @property
        def ota_report_topic_pub(self):
            return self.__ota_report_topic_pub

        @property
        def rrpc_topic_pub_prefix(self):
            return self.__rrpc_topic_pub_prefix

        @property
        def rrpc_topic_sub_prefix(self):
            return self.__rrpc_topic_sub_prefix

        @property
        def shadow_topic_pub(self):
            return self.__shadow_topic_pub

        @property
        def shadow_topic_sub(self):
            return self.__shadow_topic_sub

        @property
        def broadcast_topic_sub(self):
            return self.__broadcast_topic_sub

        @property
        def control_clientToken(self):
            return self.__clientToken

        # _on_template_downstream_topic_handler()中收到云端消息后保存client-token
        @control_clientToken.setter
        def control_clientToken(self, token):
            if token is None or len(token) == 0:
                raise ValueError('Invalid info.')
            self.__clientToken = token

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
                self.__hub_log.error("on_connect process raise exception:%r" % e)
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
        mid = message.mid
        payload = json.loads(message.payload.decode('utf-8'))
        self.__hub_log.info("payload:%s\n" % payload)

    def __on_connect(self, client, user_data, session_flag, rc):
        print("__on_connect,rc:%d\n" % rc)
        if rc == 0:
            self.__protocol.reset_reconnect_wait()
            self.__hub_state = self.HubState.CONNECTED

            self.__event_worker._thread.post_message(self.__event_worker.EventPool.CONNECT, (session_flag, rc))

            sys_topic_sub = self.__topic.sys_topic_sub
            sys_topic_pub = self.__topic.sys_topic_pub
            qos = 0
            sub_res, mid = self.subscribe(sys_topic_sub, qos)
            # should deal mid
            self.__hub_log.debug("mid:%d" % mid)
            if sub_res == 0:
                payload = {
                    "type": "get",
                    "resource": [
                        "time"
                    ],
                }
                self.publish(sys_topic_pub, payload, qos)
            else:
                self.__hub_log.error("topic_subscribe error:rc:%d" % (sub_res))
        pass

    def __on_disconnect(self, client, user_data, rc):
        if self.__hub_state == self.HubState.DISCONNECTING:
            self.__hub_state = self.HubState.DISCONNECTED
        elif self.__hub_state == self.HubState.DESTRUCTING:
            self.__hub_state = self.HubState.DESTRUCTED
        elif self.__hub_state == self.HubState.CONNECTED:
            self.__hub_state = self.HubState.DISCONNECTED
        else:
            self.__hub_log.error("state error:%r" % self.__hub_state)
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
                self.__hub_log.error("mqtt reconnect error:" + str(e))
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
        self.__hub_log.set_level(level)
        self.__hub_log.enable_logger()
        self.__protocol.enable_logger(self.__PahoLog)
        self.__PahoLog.setLevel(level)

    def isMqttConnected(self):
        return self.__hub_state == self.HubState.CONNECTED

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
            self.__protocol = AsyncConnClient(host, product_id, device_name, device_secret, logger=self.__hub_log)
        else:
            if self.__tls:
                host = "wss:" + product_id + ".ap-guangzhou.iothub.tencentdevices.com"
            else:
                host = "ws:" + product_id + ".ap-guangzhou.iothub.tencentdevices.com"
            self.__protocol = AsyncConnClient(host, product_id, device_name, device_secret, websocket=True, logger=self.__hub_log)

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
            self.__hub_log.error("Set failed: client is None")
            return
        self.__protocol.set_reconnect_interval(max_sec, min_sec)
        self.__protocol.config_connect()

    def setMessageTimout(self, timeout):
        if self.__protocol is None:
            self.__hub_log.error("Set failed: client is None")
            return
        self.__protocol.set_message_timout(timeout)
    
    def setKeepaliveInterval(self, interval):
        if self.__protocol is None:
            self.__hub_log.error("Set failed: client is None")
            return
        self.__protocol.set_keepalive_interval(interval)

    def connect(self):
        self.__loop_worker.__connect_async_req = True
        with self.__loop_worker._exit_req_lock:
            self.__loop_worker._exit_req = False
        return self.__loop_worker._thread.start(self._loop)

    def disconnect(self):
        self.__hub_log.debug("disconnect")
        if self.__hub_state is not self.HubState.CONNECTED:
            raise self.StateError("current state is not CONNECTED")
        self.__hub_state = self.HubState.DISCONNECTING
        if self.__loop_worker._connect_async_req:
            with self.__loop_worker._exit_req_lock:
                self.__loop_worker._exit_req = True

        self.__protocol.disconnect()
        self.__loop_worker._thread.stop()
    
    def subscribe(self, topic, qos):
        self.__hub_log.debug("sub topic:%s,qos:%d" % (topic, qos))
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
            if rc != 0:
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
        self.__hub_log.debug("pub topic:%s,payload:%s,qos:%d" % (topic, payload, qos))
        if self.__hub_state is not self.HubState.CONNECTED:
            raise self.StateError("current state is not CONNECTED")
        if topic is None or len(topic) == 0:
            raise ValueError('Invalid topic.')
        if qos < 0:
            raise ValueError('Invalid QoS level.')

        return self.__protocol.publish(topic, json.dumps(payload), qos)

    


