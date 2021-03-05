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
#
#

# import os
import logging
import threading
import queue
import urllib.request
import urllib.parse
import urllib.error
import json
import hashlib
import hmac
import base64
import random
import ssl
import socket
import string
import time
# import re
import paho.mqtt.client as mqtt
from enum import Enum
from enum import IntEnum
# from paho.mqtt.client import MQTTMessage
from Crypto.Cipher import AES


class QcloudExplorer(object):

    class ExplorerState(Enum):
        INITIALIZED = 1
        CONNECTING = 2
        CONNECTED = 3
        DISCONNECTING = 4
        DISCONNECTED = 5
        DESTRUCTING = 6
        DESTRUCTED = 7

    class StateError(Exception):
        def __init__(self, err):
            Exception.__init__(self, err)

    # 用户注册回调分发线程
    class __UserCallBackTask(object):
        def __init__(self, logger=None):
            self.__logger = logger
            if self.__logger is not None:
                self.__logger.info("UserCallBackTask init")
            self.__message_queue = queue.Queue(20)
            self.__cmd_callback = {}
            self.__started = False
            self.__exited = False
            self.__thread = None
            pass

        def register_callback_with_cmd(self, cmd, callback):
            if self.__started is False:
                if cmd != "req_exit":
                    self.__cmd_callback[cmd] = callback
                    return 0
                else:
                    return 1
                pass
            else:
                return 2
            pass

        def post_message(self, cmd, value):
            # self.__logger.debug("post_message :%r " % cmd)
            if self.__started and self.__exited is False:
                try:
                    self.__message_queue.put((cmd, value), timeout=5)
                except queue.Full as e:
                    self.__logger.error("queue full: %r" % e)
                    return False
                # self.__logger.debug("post_message success")
                return True
            self.__logger.debug("post_message fail started:%r,exited:%r" % (self.__started, self.__exited))
            return False

        def start(self):
            if self.__logger is not None:
                self.__logger.info("UserCallBackTask start")
            if self.__started is False:
                if self.__logger is not None:
                    self.__logger.info("UserCallBackTask try start")
                self.__exited = False
                self.__started = True
                self.__message_queue = queue.Queue(20)
                self.__thread = threading.Thread(target=self.__user_cb_thread)
                self.__thread.daemon = True
                self.__thread.start()
                return 0
            return 1

        def stop(self):
            if self.__started and self.__exited is False:
                self.__exited = True
                self.__message_queue.put(("req_exit", None))

        def wait_stop(self):
            if self.__started is True:
                self.__thread.join()

        def __user_cb_thread(self):
            if self.__logger is not None:
                self.__logger.debug("thread runnable enter")
            while True:
                cmd, value = self.__message_queue.get()
                # self.__logger.debug("thread runnable pop cmd:%r" % cmd)
                if cmd == "req_exit":
                    break
                if self.__cmd_callback[cmd] is not None:
                    try:
                        # print("cmd:%s,value:%s" % (cmd, value))
                        self.__cmd_callback[cmd](value)
                    except Exception as e:
                        if self.__logger is not None:
                            self.__logger.error("thread runnable raise exception:%s" % e)
            self.__started = False
            if self.__logger is not None:
                self.__logger.debug("thread runnable exit")
            pass

    class __LoopThread(object):
        def __init__(self, logger=None):
            self.__logger = logger
            if logger is not None:
                self.__logger.info("LoopThread init enter")
            self.__callback = None
            self.__thread = None
            self.__started = False
            self.__req_wait = threading.Event()
            if logger is not None:
                self.__logger.info("LoopThread init exit")

        def start(self, callback):
            if self.__started:
                self.__logger.info("LoopThread already ")
                return 1
            else:
                self.__callback = callback
                self.__thread = threading.Thread(target=self.__thread_main)
                self.__thread.daemon = True
                self.__thread.start()
                return 0

        def __thread_main(self):
            self.__started = True
            try:
                if self.__logger is not None:
                    self.__logger.debug("LoopThread thread enter")
                if self.__callback is not None:
                    self.__callback()
                if self.__logger is not None:
                    self.__logger.debug("LoopThread thread exit")
            except Exception as e:
                self.__logger.error("LoopThread thread Exception:" + str(e))
            self.__started = False
            self.__req_wait.set()

        def stop(self):
            self.__req_wait.wait()
            self.__req_wait.clear()

    class __ExplorerLog(object):
        def __init__(self):
            self.__logger = logging.getLogger("QcloudExplorer")
            self.__enabled = False
            pass

        def enable_logger(self):
            self.__enabled = True

        def disable_logger(self):
            self.__enabled = False

        def is_enabled(self):
            return self.__enabled

        def set_level(self, level):
            self.__logger.setLevel(level)

        def debug(self, fmt, *args):
            if self.__enabled:
                self.__logger.debug(fmt, *args)

        def warring(self, fmt, *args):
            if self.__enabled:
                self.__logger.warning(fmt, *args)

        def info(self, fmt, *args):
            if self.__enabled:
                self.__logger.info(fmt, *args)

        def error(self, fmt, *args):
            if self.__enabled:
                self.__logger.error(fmt, *args)

        def critical(self, fmt, *args):
            if self.__enabled:
                self.__logger.critical(fmt, *args)

    class __DeviceInfo(object):
        def __init__(self, file_path, logger=None):
            self.__logger = logger
            self.__logger.info('device_info file {}'.format(file_path))

            self.__device_name = None
            self.__product_id = None
            self.__product_secret = None
            self.__device_secret = None
            self.__region = None
            if self.__logger is not None:
                self.__logger.info('device_info file {}'.format(file_path))
            with open(file_path, 'r', encoding='utf-8') as f:
                self.__json_data = json.loads(f.read())
                self.__device_name = self.__json_data['deviceName']
                self.__product_id = self.__json_data['productId']
                self.__product_secret = self.__json_data['productSecret']
                self.__device_secret = self.__json_data['key_deviceinfo']['deviceSecret']
                self.__region = self.__json_data["region"]
            if self.__logger is not None:
                self.__logger.info(
                    "device name: {}, product id: {}, product secret: {}, device secret: {}".
                    format(self.__device_name, self.__product_id,
                           self.__product_secret, self.__device_secret))

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
        def region(self):
            return self.__region

        @property
        def json_data(self):
            return self.__json_data

    class _AESUtil:
        __BLOCK_SIZE_16 = BLOCK_SIZE_16 = AES.block_size

        '''
        @staticmethod
        def encryt(str, key, iv):
            cipher = AES.new(key, AES.MODE_CBC, iv)
            x = AESUtil.__BLOCK_SIZE_16 - (len(str) % AESUtil.__BLOCK_SIZE_16)
            if x != 0:
                str = str + chr(x) * x
            msg = cipher.encrypt(str)
            msg = base64.b64encode(msg)
            return msg
        '''

        @staticmethod
        def decrypt(encrypt_str, key, init_vector):
            cipher = AES.new(key, AES.MODE_CBC, init_vector)
            decrypt_bytes = base64.b64decode(encrypt_str)
            return cipher.decrypt(decrypt_bytes)

    class __Topic(object):
        def __init__(self, product_id, device_name):

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

    __IOT_CA_CRT = "\
-----BEGIN CERTIFICATE-----\n\
MIIDxTCCAq2gAwIBAgIJALM1winYO2xzMA0GCSqGSIb3DQEBCwUAMHkxCzAJBgNV\n\
BAYTAkNOMRIwEAYDVQQIDAlHdWFuZ0RvbmcxETAPBgNVBAcMCFNoZW5aaGVuMRAw\n\
DgYDVQQKDAdUZW5jZW50MRcwFQYDVQQLDA5UZW5jZW50IElvdGh1YjEYMBYGA1UE\n\
AwwPd3d3LnRlbmNlbnQuY29tMB4XDTE3MTEyNzA0MjA1OVoXDTMyMTEyMzA0MjA1\n\
OVoweTELMAkGA1UEBhMCQ04xEjAQBgNVBAgMCUd1YW5nRG9uZzERMA8GA1UEBwwI\n\
U2hlblpoZW4xEDAOBgNVBAoMB1RlbmNlbnQxFzAVBgNVBAsMDlRlbmNlbnQgSW90\n\
aHViMRgwFgYDVQQDDA93d3cudGVuY2VudC5jb20wggEiMA0GCSqGSIb3DQEBAQUA\n\
A4IBDwAwggEKAoIBAQDVxwDZRVkU5WexneBEkdaKs4ehgQbzpbufrWo5Lb5gJ3i0\n\
eukbOB81yAaavb23oiNta4gmMTq2F6/hAFsRv4J2bdTs5SxwEYbiYU1teGHuUQHO\n\
iQsZCdNTJgcikga9JYKWcBjFEnAxKycNsmqsq4AJ0CEyZbo//IYX3czEQtYWHjp7\n\
FJOlPPd1idKtFMVNG6LGXEwS/TPElE+grYOxwB7Anx3iC5ZpE5lo5tTioFTHzqbT\n\
qTN7rbFZRytAPk/JXMTLgO55fldm4JZTP3GQsPzwIh4wNNKhi4yWG1o2u3hAnZDv\n\
UVFV7al2zFdOfuu0KMzuLzrWrK16SPadRDd9eT17AgMBAAGjUDBOMB0GA1UdDgQW\n\
BBQrr48jv4FxdKs3r0BkmJO7zH4ALzAfBgNVHSMEGDAWgBQrr48jv4FxdKs3r0Bk\n\
mJO7zH4ALzAMBgNVHRMEBTADAQH/MA0GCSqGSIb3DQEBCwUAA4IBAQDRSjXnBc3T\n\
d9VmtTCuALXrQELY8KtM+cXYYNgtodHsxmrRMpJofsPGiqPfb82klvswpXxPK8Xx\n\
SuUUo74Fo+AEyJxMrRKlbJvlEtnpSilKmG6rO9+bFq3nbeOAfat4lPl0DIscWUx3\n\
ajXtvMCcSwTlF8rPgXbOaSXZidRYNqSyUjC2Q4m93Cv+KlyB+FgOke8x4aKAkf5p\n\
XR8i1BN1OiMTIRYhGSfeZbVRq5kTdvtahiWFZu9DGO+hxDZObYGIxGHWPftrhBKz\n\
RT16Amn780rQLWojr70q7o7QP5tO0wDPfCdFSc6CQFq/ngOzYag0kJ2F+O5U6+kS\n\
QVrcRBDxzx/G\n\
-----END CERTIFICATE-----"

    def __init__(self, device_file, tls=True, user_data=None):
        self.__explorer_log = QcloudExplorer.__ExplorerLog()
        self.__PahoLog = logging.getLogger("Paho")
        self.__PahoLog.setLevel(logging.DEBUG)
        self.__device_file = QcloudExplorer.__DeviceInfo(device_file, self.__explorer_log)
        self.__topic_info = None

        # set state initialized
        self.__explorer_state = QcloudExplorer.ExplorerState.INITIALIZED

        self.__iot_ca_crt = self.__IOT_CA_CRT
        self.__tls = tls

        self.__mqtt_client = None
        self.__host = None

        # 用户传参
        self.__user_data = user_data

        # mqtt set
        self.__set_mqtt_param()

        # topic
        self.__user_topics_subscribe_request = {}
        self.__user_topics_unsubscribe_request = {}
        self.__user_topics_request_lock = threading.Lock()
        self.__user_topics_unsubscribe_request_lock = threading.Lock()

        self.__template_prop_report_reply_mid = {}
        self.__template_prop_report_reply_mid_lock = threading.Lock()
        self.__user_topics = {}

        # gateway
        self.__gateway_session_client_id = None
        self.__gateway_session_online_reply = {}
        self.__gateway_session_offline_reply = {}
        self.__gateway_session_bind_reply = {}
        self.__gateway_session_unbind_reply = {}
        self.__gateway_raply = False

        # 网关子设备property topic订阅的子设备列表
        self.__gateway_subdev_property_topic_list = []
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

        # 防止多线程同时调用同一注册函数
        self.__register_property_cb_lock = threading.Lock()
        self.__register_action_cb_lock = threading.Lock()
        self.__register_event_cb_lock = threading.Lock()

        self.__gateway_subdev_append_lock = threading.Lock()
        self.__handle_topic_lock = threading.Lock()

        # data template
        self.__template_setup_state = False
        self.__is_subscribed_property_topic = False
        self.template_token_num = 0
        self.__clientToken = None

        self.template_events_list = []
        self.template_action_list = []
        self.template_property_list = []
        self.gateway_subdev_list = []

        # data template reply
        self.__replyAck = -1

        # user data template callback
        # 做成回调函数字典，通过topic调用对应回调(针对网关有不同数据模板设备的情况)
        self.__on_template_prop_changed = None
        self.__on_template_action = None
        self.__on_template_event_post = None

        # ota
        # 保存__on_subscribe()返回的mid和qos对,用以判断订阅是否成功
        self.__ota_subscribe_res = {}
        self.__ota_manager = None
        self.__ota_version_len_min = 1
        self.__ota_version_len_max = 32
        self.http_manager = None

        # connect with async
        self.__connect_async_req = False
        self.__worker_loop_exit_req = False
        self.__worker_loop_runing_state = False
        self.__worker_loop_exit_req_lock = threading.Lock()

        # user mqtt callback
        self.__user_on_connect = None
        self.__user_on_disconnect = None
        self.__user_on_publish = None
        self.__user_on_subscribe = None
        self.__user_on_unsubscribe = None
        self.__user_on_message = None

        # ota callback
        self.__user_on_ota_report = None

        # rrpc callback
        self.__user_on_rrpc_message = None
        self.__process_id = None

        # construct thread handle
        self.__loop_thread = QcloudExplorer.__LoopThread(self.__explorer_log)
        self.__user_thread = QcloudExplorer.__UserCallBackTask(self.__explorer_log)
        self.__user_cmd_cb_init()
        pass

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

    @property
    def user_on_ota_report(self):
        return self.__user_on_ota_report

    @user_on_ota_report.setter
    def user_on_ota_report(self, value):
        self.__user_on_ota_report = value
        pass

    @property
    def user_on_rrpc_message(self):
        return self.__user_on_rrpc_message

    @user_on_rrpc_message.setter
    def user_on_rrpc_message(self, value):
        self.__user_on_rrpc_message = value

    @property
    def on_template_prop_changed(self):
        return self.__on_template_prop_changed

    @on_template_prop_changed.setter
    def on_template_prop_changed(self, value):
        self.__on_template_prop_changed = value

    @property
    def on_template_action(self):
        return self.__on_template_action

    @on_template_action.setter
    def on_template_action(self, value):
        self.__on_template_action = value

    @property
    def on_template_event_post(self):
        return self.__on_template_event_post

    @on_template_event_post.setter
    def on_template_event_post(self, value):
        self.__on_template_event_post = value

    def __user_cmd_cb_init(self):
        self.__user_thread = QcloudExplorer.__UserCallBackTask(self.__explorer_log)
        self.__user_cmd_on_connect = "user_on_connect"
        self.__user_cmd_on_disconnect = "user_on_disconnect"
        self.__user_cmd_on_message = "user_on_message"
        self.__user_cmd_on_publish = "user_on_publish"
        self.__user_cmd_on_subscribe = "user_on_subscribe"
        self.__user_cmd_on_unsubscribe = "user_on_unsubscribe"
        self.__user_thread.register_callback_with_cmd(self.__user_cmd_on_connect,
                                                      self.__user_thread_on_connect_callback)
        self.__user_thread.register_callback_with_cmd(self.__user_cmd_on_disconnect,
                                                      self.__user_thread_on_disconnect_callback)
        self.__user_thread.register_callback_with_cmd(self.__user_cmd_on_message,
                                                      self.__user_thread_on_message_callback)
        self.__user_thread.register_callback_with_cmd(self.__user_cmd_on_publish,
                                                      self.__user_thread_on_publish_callback)
        self.__user_thread.register_callback_with_cmd(self.__user_cmd_on_subscribe,
                                                      self.__user_thread_on_subscribe_callback)
        self.__user_thread.register_callback_with_cmd(self.__user_cmd_on_unsubscribe,
                                                      self.__user_thread_on_unsubscribe_callback)
        self.__user_thread.start()

        pass

    def enable_logger(self, level):
        self.__explorer_log.set_level(level)
        self.__explorer_log.enable_logger()
        if self.__mqtt_client is not None:
            self.__mqtt_client.enable_logger(self.__PahoLog)
        self.__PahoLog.setLevel(level)

    def __set_mqtt_callback(self):
        self.__mqtt_client.on_connect = self.__on_connect
        self.__mqtt_client.on_disconnect = self.__on_disconnect
        self.__mqtt_client.on_message = self.__on_message
        self.__mqtt_client.on_publish = self.__on_publish
        self.__mqtt_client.on_subscribe = self.__on_subscribe
        self.__mqtt_client.on_unsubscribe = self.__on_unsubscribe

    def __set_mqtt_param(self):
        self.__mqtt_tls_port = 8883
        self.__mqtt_tcp_port = 1883
        self.__mqtt_protocol = "MQTTv31"
        self.__mqtt_transport = "TCP"
        self.__mqtt_secure = "TLS"
        self.__mqtt_clean_session = True
        self.__mqtt_keep_alive = 60

        self.__mqtt_auto_reconnect_min_sec = 1
        self.__mqtt_auto_reconnect_max_sec = 60
        self.__mqtt_max_queued_message = 40
        self.__mqtt_max_inflight_message = 20
        self.__mqtt_auto_reconnect_sec = 0
        self.__mqtt_request_timeout = 10

        # default MQTT/CoAP timeout value when connect/pub/sub
        self.__mqtt_command_timeout = 5
        pass

    def dynreg_device(self, timeout=10):
        """
        dynamic device to tencent cloud
        :param timeout: http/https timeout
        :return: (code, msg): code 0 is success, msg is psk. Other is failed.
        """

        sign_format = 'deviceName=%s&nonce=%d&productId=%s&timestamp=%d'
        request_format = '%s://gateway.tencentdevices.com/register/dev'
        header = {'Accept': 'text/xml,application/json;*/*'}

        device_name = self.__device_file.device_name
        product_id = self.__device_file.product_id
        product_secret = self.__device_file.product_secret

        nonce = random.randrange(2147483647)
        timestamp = int(time.time())
        sign_content = sign_format % (
            device_name, nonce, product_id, timestamp)
        sign = hmac.new(product_secret.encode("utf-8"),
                        sign_content.encode("utf-8"), hashlib.sha1).hexdigest()
        sign_base64 = base64.b64encode(sign.encode('utf-8')).decode('utf-8')
        self.__explorer_log.debug('sign base64 {}'.format(sign_base64))

        requset_data = {
            "deviceName": device_name,
            "nonce": nonce,
            "productId": product_id,
            "timestamp": timestamp,
            "signature": sign_base64
        }
        data = bytes(json.dumps(requset_data), encoding='utf-8')

        context = None
        if self.__tls:
            request_url = request_format % 'https'
            context = ssl.create_default_context(
                ssl.Purpose.CLIENT_AUTH, cadata=self.__iot_ca_crt)
        else:
            request_url = request_format % 'http'
        self.__explorer_log.info('dynreg url {}'.format(request_url))
        req = urllib.request.Request(request_url, data=data, headers=header)
        with urllib.request.urlopen(req, timeout=timeout, context=context) as url_file:
            reply_data = url_file.read().decode('utf-8')
            reply_obj = json.loads(reply_data)
            if reply_obj['code'] == 0:
                reply_obj_data = reply_obj["payload"]
                if reply_obj_data is not None:
                    psk = self._AESUtil.decrypt(reply_obj_data, product_secret[:self._AESUtil.BLOCK_SIZE_16],
                                                '0000000000000000')
                    psk = str(psk, encoding='utf-8')[:reply_obj['len']]
                    user_dict = json.loads(psk)
                    self.__explorer_log.info('encrypt type: {}'.format(
                        user_dict['encryptionType']))
                    return 0, user_dict['psk']
                else:
                    self.__explorer_log.warring('payload is null')
                    return -1, 'payload is null'
            else:
                self.__explorer_log.error('code: {}, error message: {}'.format(
                    reply_obj['code'], reply_obj['message']))
                return -1, reply_obj['message']

    # 遍历逻辑待优化
    def __topic_match(self, payload, topic, plist, pdict):
        for tup in plist:
            tup_product = tup[0]
            tup_topic = tup[1]
            # 网关子设备的订阅
            if topic == tup_topic:
                if tup_product in pdict:
                    # params = payload["params"]
                    user_callback = pdict[tup_product]
                    print("call user_callback")
                    user_callback(payload, self.__user_data)
                    return 0
                else:
                    self.__explorer_log.warring('topic not registed')
                    return 1
            else:
                continue
        return 2

    def __handle_nonStandard_topic(self, topic, payload):
        # 判断topic类型(property/action/event)
        with self.__handle_topic_lock:
            rc = self.__topic_match(payload,
                                    topic,
                                    self.__gateway_subdev_property_topic_list,
                                    self.__on_gateway_subdev_prop_cb_dict)
            if rc == 0:
                return 0

            rc = self.__topic_match(payload,
                                    topic,
                                    self.__gateway_subdev_action_topic_list,
                                    self.__on_gateway_subdev_action_cb_dict)
            if rc == 0:
                return 0

            rc = self.__topic_match(payload,
                                    topic,
                                    self.__gateway_subdev_event_topic_list,
                                    self.__on_gateway_subdev_event_cb_dict)
            if rc == 0:
                return 0

        return 1

    def __handle_gateway(self, message):
        self.__explorer_log.debug("gateway payload:%s" % message)
        ptype = message["type"]
        payload = message["payload"]
        devices = payload["devices"]
        result = devices[0]["result"]
        product_id = devices[0]["product_id"]
        device_name = devices[0]["device_name"]
        client_id = product_id + "/" + device_name

        self.__gateway_raply = True
        if ptype == "online":
            self.__gateway_session_online_reply[client_id] = result
        elif ptype == "offline":
            self.__gateway_session_offline_reply[client_id] = result
        elif ptype == "bind":
            self.__gateway_session_bind_reply[client_id] = result
        elif ptype == "unbind":
            self.__gateway_session_unbind_reply[client_id] = result
        pass

    def __handle_reply(self, method, payload):
        self.__explorer_log.debug("reply payload:%s" % payload)

        clientToken = payload["clientToken"]
        replyAck = payload["code"]
        if method == "get_status_reply":
            if replyAck == 0:
                topic_pub = self.__topic_info.template_property_topic_pub
                self.__topic_info.control_clientToken = clientToken

                # IOT_Template_ClearControl
                message = {
                    "method": "clear_control",
                    "clientToken": clientToken
                }
                rc, mid = self.topic_publish(topic_pub, message, 0)
                # should deal mid
                self.__explorer_log.debug("mid:%d" % mid)
                if rc != 0:
                    self.__explorer_log.error("topic_publish error:rc:%d,topic:%s" % (rc, topic_pub))
            else:
                self.__replyAck = replyAck
                self.__explorer_log.debug("replyAck:%d" % replyAck)

        else:
            self.__replyAck = replyAck
        pass

    def __handle_control(self, payload):
        clientToken = payload["clientToken"]
        params = payload["params"]
        self.__topic_info.control_clientToken = clientToken
        # 调用用户回调,回调中应调用template_control_reply()
        self.__on_template_prop_changed(params, self.__user_data)

    def __handle_action(self, payload):
        """
        clientToken = payload["clientToken"]
        actionId = payload["actionId"]
        timestamp = payload["timestamp"]
        params = payload["params"]
        """

        # 调用用户回调,回调中应调用IOT_ACTION_REPLY()
        # self.__on_template_action(clientToken, actionId, timestamp, params, self.__user_data)
        self.__on_template_action(payload, self.__user_data)
        pass

    def __handle_ota(self, payload):
        ptype = payload["type"]
        if ptype == "report_version_rsp":
            self.__user_on_ota_report(payload, self.__user_data)
        elif ptype == "update_firmware":
            self.__ota_info_get(payload)

    def __rrpc_get_process_id(self, topic):
        pos = topic.rfind("/")
        if pos > 0:
            self.__process_id = topic[pos + 1:len(topic)]
            return 0
        else:
            self.__explorer_log.error("cannot found process id from topic:%s" % topic)
            return -1

    def __handle_rrpc(self, topic, payload):
        rc = self.__rrpc_get_process_id(topic)
        if rc < 0:
            raise QcloudExplorer.StateError("cannot found process id")

        # 调用用户注册的回调
        if self.__user_on_rrpc_message is not None:
            self.__user_on_rrpc_message(payload, self.__user_data)

    def topic_subscribe(self, topic, qos):
        self.__explorer_log.debug("sub topic:%s,qos:%d" % (topic, qos))
        if self.__explorer_state is not QcloudExplorer.ExplorerState.CONNECTED:
            raise QcloudExplorer.StateError("current state is not CONNECTED")
        if isinstance(topic, tuple):
            topic, qos = topic
        if isinstance(topic, str):
            if qos < 0:
                raise ValueError('Invalid QoS level.')
            if topic is None or len(topic) == 0:
                raise ValueError('Invalid topic.')
            pass
            self.__user_topics_request_lock.acquire()
            rc, mid = self.__mqtt_client.subscribe(topic, qos)
            if rc == mqtt.MQTT_ERR_SUCCESS:
                self.__explorer_log.debug("subscribe success topic:%s" % topic)
                self.__user_topics_subscribe_request[mid] = [(topic, qos)]
            self.__user_topics_request_lock.release()
            if rc == mqtt.MQTT_ERR_SUCCESS:
                return 0, mid
            if rc == mqtt.MQTT_ERR_NO_CONN:
                return 2, None
            else:
                self.__explorer_log.debug("subscribe error topic:%s" % topic)
                return -1, None
        # topic format [(topic1, qos),(topic2,qos)]
        if isinstance(topic, list):
            self.__user_topics_request_lock.acquire()
            sub_res, mid = self.__mqtt_client.subscribe(topic)
            if sub_res == mqtt.MQTT_ERR_SUCCESS:
                self.__user_topics_subscribe_request[mid] = [topic]
                self.__user_topics_request_lock.release()
                return 0, mid
            else:
                self.__user_topics_request_lock.release()
                return 1, mid
        pass

    def topic_unsubscribe(self, topic):
        if self.__explorer_state is not QcloudExplorer.ExplorerState.CONNECTED:
            raise QcloudExplorer.StateError("current state is not CONNECTED")
        unsubscribe_topics = []
        if topic is None or topic == "":
            raise ValueError('Invalid topic.')
        if isinstance(topic, str):
            # topic判断
            unsubscribe_topics.append(topic)
        with self.__user_topics_unsubscribe_request_lock:
            if len(unsubscribe_topics) == 0:
                return 2, None
            rc, mid = self.__mqtt_client.unsubscribe(unsubscribe_topics)
            if rc == mqtt.MQTT_ERR_SUCCESS:
                self.__user_topics_unsubscribe_request[mid] = unsubscribe_topics
                return 0, mid
            else:
                return 1, None
        pass

    def topic_publish(self, topic, payload, qos):
        self.__explorer_log.debug("pub topic:%s,payload:%s,qos:%d" % (topic, payload, qos))
        if self.__explorer_state is not QcloudExplorer.ExplorerState.CONNECTED:
            raise QcloudExplorer.StateError("current state is not CONNECTED")
        if topic is None or len(topic) == 0:
            raise ValueError('Invalid topic.')
        if qos < 0:
            raise ValueError('Invalid QoS level.')
        rc, mid = self.__mqtt_client.publish(topic, json.dumps(payload), qos)
        if rc == mqtt.MQTT_ERR_SUCCESS:
            self.__explorer_log.debug("publish success")
            return 0, mid
        else:
            self.__explorer_log.debug("publish failed")
            return 1, None
        pass

    def is_mqtt_connected(self):
        if self.__explorer_state is QcloudExplorer.ExplorerState.CONNECTED:
            return True
        else:
            return False

    def mqtt_init(self, mqtt_domain):
        self.__explorer_log.debug("mqtt_init")
        timestamp = str(int(round(time.time() * 1000)))

        device_name = self.__device_file.device_name
        product_id = self.__device_file.product_id
        device_secret = self.__device_file.device_secret

        self.__topic_info = QcloudExplorer.__Topic(product_id, device_name)

        self.__psk = base64.b64decode(device_secret.encode("utf-8"))
        self.__psk_id = product_id + device_name
        sha1_key = self.__psk

        client_id = product_id + device_name
        conn_id = ''.join(random.sample(string.ascii_letters + string.digits, 5))
        username = client_id + ";21010406;" + conn_id + ";" + timestamp
        sign = hmac.new(sha1_key, username.encode("utf-8"), hashlib.sha1).hexdigest()
        password = "%s;hmacsha1" % (sign)

        if mqtt_domain is None or mqtt_domain == "":
            self.__host = product_id + ".iotcloud.tencentdevices.com"
        else:
            self.__host = product_id + mqtt_domain
        pass

        # c-sdk中sub_handles的设置待完成

        # AUTH_MODE_CERT 待添加

        # construct mqtt client
        mqtt_protocol_version = mqtt.MQTTv311
        if self.__mqtt_protocol == "MQTTv311":
            mqtt_protocol_version = mqtt.MQTTv311
        elif self.__mqtt_protocol == "MQTTv31":
            mqtt_protocol_version = mqtt.MQTTv31
        self.__mqtt_client = mqtt.Client(client_id=client_id,
                                         clean_session=self.__mqtt_clean_session,
                                         protocol=mqtt_protocol_version)

        if self.__explorer_log.is_enabled():
            self.__mqtt_client.enable_logger(self.__PahoLog)

        # set username,password for connect()
        self.__mqtt_client.username_pw_set(username, password)

        # mqtt callback set
        self.__set_mqtt_callback()

        self.__mqtt_client.reconnect_delay_set(self.__mqtt_auto_reconnect_min_sec, self.__mqtt_auto_reconnect_max_sec)
        self.__mqtt_client.max_queued_messages_set(self.__mqtt_max_queued_message)
        self.__mqtt_client.max_inflight_messages_set(self.__mqtt_max_inflight_message)

    # start thread to connect and loop
    def connect_async(self):
        if self.__explorer_state not in (QcloudExplorer.ExplorerState.INITIALIZED,
                                         QcloudExplorer.ExplorerState.DISCONNECTED):
            raise QcloudExplorer.StateError("current state is not in INITIALIZED or DISCONNECTED")
        self.__connect_async_req = True
        with self.__worker_loop_exit_req_lock:
            self.__worker_loop_exit_req = False
        return self.__loop_thread.start(self.__loop_forever)

    def __ssl_init(self):
        context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH, cadata=self.__iot_ca_crt)
        self.__mqtt_client.tls_set_context(context)
    pass

    def disconnect(self):
        self.__explorer_log.debug("disconnect")
        if self.__explorer_state is not QcloudExplorer.ExplorerState.CONNECTED:
            raise QcloudExplorer.StateError("current state is not CONNECTED")
        self.__explorer_state = QcloudExplorer.ExplorerState.DISCONNECTING
        if self.__connect_async_req:
            with self.__worker_loop_exit_req_lock:
                self.__worker_loop_exit_req = True

        self.__mqtt_client.disconnect()
        self.__loop_thread.stop()

    def __on_connect(self, client, user_data, session_flag, rc):
        # self.__explorer_log.info("__on_connect:rc:%d" % (rc))
        if rc == 0:
            self.__reset_reconnect_wait()
            self.__explorer_state = QcloudExplorer.ExplorerState.CONNECTED

            self.__user_thread.post_message(self.__user_cmd_on_connect, (session_flag, rc))

            sys_topic_sub = self.__topic_info.sys_topic_sub
            sys_topic_pub = self.__topic_info.sys_topic_pub
            qos = 0
            sub_res, mid = self.topic_subscribe(sys_topic_sub, qos)
            # should deal mid
            self.__explorer_log.debug("mid:%d" % mid)
            if sub_res == 0:
                payload = {
                    "type": "get",
                    "resource": [
                        "time"
                    ],
                }
                self.topic_publish(sys_topic_pub, payload, qos)
            else:
                self.__explorer_log.error("__topic_subscibe error:rc:%d" % (sub_res))
        pass

    def __on_disconnect(self, client, user_data, rc):
        self.__explorer_log.info("__on_disconnect,rc:%d" % (rc))

        if self.__explorer_state == QcloudExplorer.ExplorerState.DISCONNECTING:
            self.__explorer_state = QcloudExplorer.ExplorerState.DISCONNECTED
        elif self.__explorer_state == QcloudExplorer.ExplorerState.DESTRUCTING:
            self.__explorer_state = QcloudExplorer.ExplorerState.DESTRUCTED
        elif self.__explorer_state == QcloudExplorer.ExplorerState.CONNECTED:
            self.__explorer_state = QcloudExplorer.ExplorerState.DISCONNECTED
        else:
            self.__explorer_log.error("state error:%r" % self.__explorer_state)
            return

        self.__user_topics_subscribe_request.clear()
        self.__user_topics_unsubscribe_request.clear()
        self.__template_prop_report_reply_mid.clear()
        self.__user_topics.clear()
        self.__gateway_session_online_reply.clear()
        self.__gateway_session_offline_reply.clear()
        self.__gateway_session_bind_reply.clear()
        self.__gateway_session_unbind_reply.clear()
        self.__on_gateway_subdev_prop_cb_dict.clear()
        self.__on_gateway_subdev_action_cb_dict.clear()
        self.__on_gateway_subdev_event_cb_dict.clear()

        # self.__user_thread.post_message(self.__user_cmd_on_disconnect, (client, user_data, rc))
        self.__user_thread.post_message(self.__user_cmd_on_disconnect, (rc))
        if self.__explorer_state == QcloudExplorer.ExplorerState.DESTRUCTED:
            self.__user_thread.stop()
    pass

    def __on_message(self, client, user_data, message):
        self.__user_thread.post_message(self.__user_cmd_on_message, (message))
    pass

    def __on_publish(self, client, user_data, mid):
        # self.__user_thread.post_message(self.__user_cmd_on_publish, (client, user_data, mid))
        self.__user_thread.post_message(self.__user_cmd_on_publish, (mid))
    pass

    def __on_subscribe(self, client, user_data, mid, granted_qos):
        self.__explorer_log.info("__on_subscribe:user_data:%s,mid:%d,qos:%s" % (user_data, mid, granted_qos))
        qos = granted_qos[0]
        # __ota_subscribe_res可以用于所有订阅,mid必不相同
        self.__ota_subscribe_res[mid] = qos
        self.__user_thread.post_message(self.__user_cmd_on_subscribe, (qos, mid))

    pass

    def __on_unsubscribe(self, client, user_data, mid):
        self.__user_thread.post_message(self.__user_on_unsubscribe, (mid))

    pass

    # user callback
    def __user_thread_on_connect_callback(self, value):
        # client, user_data, session_flag, rc = value
        session_flag, rc = value
        if self.__user_on_connect is not None:
            try:
                self.__user_on_connect(session_flag['session present'], rc, self.__user_data)
            except Exception as e:
                self.__explorer_log.error("on_connect process raise exception:%r" % e)
        pass

    def __user_thread_on_disconnect_callback(self, value):
        self.__user_on_disconnect(value, self.__user_data)
        pass

    def __user_thread_on_publish_callback(self, value):
        self.__user_on_publish(value, self.__user_data)
        pass

    def __user_thread_on_subscribe_callback(self, value):
        qos, mid = value
        self.__user_on_subscribe(qos, mid, self.__user_data)
        pass

    def __user_thread_on_unsubscribe_callback(self, value):
        self.__user_on_unsubscribe(value, self.__user_data)
        pass

    def __user_thread_on_message_callback(self, value):
        # client, user_data, message = value
        message = value
        topic = message.topic
        qos = message.qos
        mid = message.mid
        payload = json.loads(message.payload.decode('utf-8'))

        self.__explorer_log.info("__user_thread_on_message_callback,topic:%s,payload:%s,mid:%d" % (topic, payload, mid))

        if topic == self.__topic_info.template_property_topic_sub:
            method = payload["method"]
            if method == "control":
                self.__handle_control(payload)
            else:
                self.__handle_reply(method, payload)

        elif topic == self.__topic_info.template_event_topic_sub:
            try:
                self.__on_template_event_post(payload, self.__user_data)
            except Exception as e:
                self.__explorer_log.error("on_template_event_post raise exception:%s" % e)
            pass

        elif topic == self.__topic_info.template_action_topic_sub:
            method = payload["method"]

            if method != "action":
                self.__explorer_log.error("method error:%s" % method)
            else:
                self.__handle_action(payload)
            pass

        elif topic == self.__topic_info.template_service_topic_sub:
            self.__explorer_log.info("3")

        elif topic == self.__topic_info.template_raw_topic_sub:
            self.__explorer_log.info("4")

        elif topic in self.__user_topics and self.__user_on_message is not None:
            try:
                self.__user_on_message(topic, payload, qos, self.__user_data)
            except Exception as e:
                self.__explorer_log.error("user_on_message process raise exception:%s" % e)
            pass
        elif topic == self.__topic_info.template_topic_sub:
            print("5")
        elif topic == self.__topic_info.sys_topic_sub:
            print("6")
        elif topic == self.__topic_info.gateway_topic_sub:
            self.__handle_gateway(payload)
        elif topic == self.__topic_info.ota_update_topic_sub:
            self.__handle_ota(payload)
        elif self.__topic_info.rrpc_topic_sub_prefix in topic:
            self.__handle_rrpc(topic, payload)
        else:
            rc = self.__handle_nonStandard_topic(topic, payload)
            if rc != 0:
                self.__explorer_log.error("unknow topic:%s" % topic)
        pass

    def __reconnect_wait(self):
        if self.__mqtt_auto_reconnect_sec == 0:
            self.__mqtt_auto_reconnect_sec = self.__mqtt_auto_reconnect_min_sec
        else:
            self.__mqtt_auto_reconnect_sec = min(self.__mqtt_auto_reconnect_sec * 2, self.__mqtt_auto_reconnect_max_sec)
            self.__mqtt_auto_reconnect_sec += random.randint(1, self.__mqtt_auto_reconnect_sec)
        time.sleep(self.__mqtt_auto_reconnect_sec)
        pass

    def __reset_reconnect_wait(self):
        self.__mqtt_auto_reconnect_sec = 0

    def __loop_forever(self):
        self.__explorer_log.info("__loop_forever")
        self.__explorer_state = QcloudExplorer.ExplorerState.CONNECTING

        mqtt_port = self.__mqtt_tls_port
        if self.__tls:
            try:
                mqtt_port = self.__mqtt_tls_port
                self.__ssl_init()
            except ssl.SSLError as e:
                self.__explorer_log.error("ssl init error:" + str(e))
                self.__explorer_state = QcloudExplorer.ExplorerState.INITIALIZED
                # connect again 待添加

                return
        else:
            mqtt_port = self.__mqtt_tcp_port

        try:
            self.__explorer_log.debug("connect_async...")
            self.__mqtt_client.connect_async(host=self.__host, port=mqtt_port, keepalive=self.__mqtt_keep_alive)
        except Exception as e:
            self.__explorer_log.error("mqtt connect with async error:" + str(e))
            self.__explorer_state = QcloudExplorer.ExplorerState.INITIALIZED
            # connect again 待添加

            return
        while True:
            if self.__worker_loop_exit_req:
                if self.__explorer_state == QcloudExplorer.ExplorerState.DESTRUCTING:
                    # self.__handler_task.stop()
                    self.__explorer_state = QcloudExplorer.ExplorerState.DESTRUCTED
                break
            try:
                self.__explorer_state = QcloudExplorer.ExplorerState.CONNECTING
                self.__mqtt_client.reconnect()
            except (socket.error, OSError) as e:
                self.__explorer_log.error("mqtt reconnect error:" + str(e))
                # 失败处理 待添加
                if self.__explorer_state == QcloudExplorer.ExplorerState.CONNECTING:
                    self.__explorer_state = QcloudExplorer.ExplorerState.DISCONNECTED
                    # self.__on__connect_safe(None, None, 0, 9)
                    if self.__explorer_state == QcloudExplorer.ExplorerState.DESTRUCTING:
                        # self.__handler_task.stop()
                        self.__explorer_state = QcloudExplorer.ExplorerState.DESTRUCTED
                        break
                    self.__reconnect_wait()

                continue

            rc = mqtt.MQTT_ERR_SUCCESS
            while rc == mqtt.MQTT_ERR_SUCCESS:
                rc = self.__mqtt_client.loop(self.__mqtt_command_timeout, 1)

    # data template
    def __build_empty_json(self, info_in, method_in):
        if info_in is None or len(info_in) == 0:
            raise ValueError('Invalid topic.')
        client_token = info_in + "-" + str(self.template_token_num)
        self.template_token_num += 1
        if method_in is None or len(method_in) == 0:
            json_out = {
                "clientToken": client_token
            }
        else:
            json_out = {
                "method": method_in,
                "clientToken": client_token
            }
        return json_out

    def __build_control_reply(self, replyPara):
        token = self.__topic_info.control_clientToken

        json_out = None
        if len(replyPara.status_msg) > 0:
            json_out = {
                "code": replyPara.code,
                "clientToken": token,
                "status": replyPara.status_msg
            }
        else:
            json_out = {
                "code": replyPara.code,
                "clientToken": token
            }
        return json_out

    def __build_action_reply(self, clientToken, response, replyPara):
        json_out = None
        json_out = {
            "method": "action_reply",
            "code": replyPara.code,
            "clientToken": clientToken,
            "status": replyPara.status_msg,
            "response": response
        }

        return json_out

    # 构建系统信息上报的json消息
    def __json_construct_sysinfo(self, info_in):
        if info_in is None or len(info_in) == 0:
            raise ValueError('Invalid info.')

        json_token = self.__build_empty_json(self.__device_file.product_id, None)
        client_token = json_token["clientToken"]
        info_out = {
            "method": "report_info",
            "clientToken": client_token,
            "params": info_in
        }

        return 0, info_out

    def template_setup(self, config_file=None):
        """
        if self.__explorer_state is not QcloudExplorer.ExplorerState.INITIALIZED:
            raise QcloudExplorer.StateError("current state is not INITIALIZED")
        if self.__template_setup_state:
            return 1
        """
        try:
            with open(config_file, encoding='utf-8') as f:
                cfg = json.load(f)
                index = 0
                while index < len(cfg["events"]):
                    # 解析events json
                    params = cfg["events"][index]["params"]

                    p_event = QcloudExplorer.template_event()

                    p_event.event_name = cfg["events"][index]["id"]
                    p_event.type = cfg["events"][index]["type"]
                    p_event.timestamp = 0
                    p_event.eventDataNum = len(params)

                    i = 0
                    while i < p_event.eventDataNum:
                        event_prop = QcloudExplorer.template_property()
                        event_prop.key = params[i]["id"]
                        event_prop.type = params[i]["define"]["type"]

                        if event_prop.type == "int" or event_prop.type == "bool":
                            event_prop.data = 0
                        elif event_prop.type == "float":
                            event_prop.data = 0.0
                        elif event_prop.type == "string":
                            event_prop.data = ''
                        else:
                            self.__explorer_log.error("type not support")
                            event_prop.data = None

                        p_event.event_append(event_prop)
                        i += 1
                    pass

                    self.template_events_list.append(p_event)
                    index += 1

                '''
                for event in self.template_events_list:
                    print("event_name:%s" % (event.event_name))
                    for prop in event.events_prop:
                        print("key:%s" % (prop.key))
                '''

                index = 0
                while index < len(cfg["actions"]):
                    # 解析actions json
                    inputs = cfg["actions"][index]["input"]
                    outputs = cfg["actions"][index]["output"]

                    p_action = QcloudExplorer.template_action()
                    p_action.action_id = cfg["actions"][index]["id"]
                    p_action.input_num = len(inputs)
                    p_action.output_num = len(outputs)
                    p_action.timestamp = 0

                    i = 0
                    while i < p_action.input_num:
                        action_prop = QcloudExplorer.template_property()
                        action_prop.key = inputs[i]["id"]
                        action_prop.type = inputs[i]["define"]["type"]

                        if action_prop.type == "int" or action_prop.type == "bool":
                            action_prop.data = 0
                        elif action_prop.type == "float":
                            action_prop.data = 0.0
                        elif action_prop.type == "string":
                            action_prop.data = ''
                        else:
                            self.__explorer_log.error("type not support")
                            action_prop.data = None
                        p_action.action_input_append(action_prop)
                        i += 1
                    pass

                    i = 0
                    while i < p_action.output_num:
                        action_prop = QcloudExplorer.template_property()
                        action_prop.key = outputs[i]["id"]
                        action_prop.type = outputs[i]["define"]["type"]

                        if action_prop.type == "int" or action_prop.type == "bool":
                            action_prop.data = 0
                        elif action_prop.type == "float":
                            action_prop.data = 0.0
                        elif action_prop.type == "string":
                            action_prop.data = ''
                        else:
                            self.__explorer_log.error("type not support")
                            action_prop.data = None
                        p_action.action_output_append(action_prop)
                        i += 1
                    pass

                    self.template_action_list.append(p_action)
                    index += 1

                pass

                '''
                for action in self.template_action_list:
                    print("input_num:%s" % (action.input_num))
                    for inp in action.actions_input_prop:
                        print("key:%s" % (inp.key))
                    print("output_num:%s" % (action.output_num))
                    for out in action.actions_output_prop:
                        print("key:%s" % (out.key))
                '''

                index = 0
                while index < len(cfg["properties"]):
                    # 解析properties json
                    p_prop = QcloudExplorer.template_property()
                    p_prop.key = cfg["properties"][index]["id"]
                    p_prop.type = cfg["properties"][index]["define"]["type"]

                    if p_prop.type == "int" or p_prop.type == "bool" or p_prop.type == "enum":
                        p_prop.data = 0
                    elif p_prop.type == "float":
                        p_prop.data = 0.0
                    elif p_prop.type == "string":
                        p_prop.data = ''
                    else:
                        self.__explorer_log.error("type not support")
                        p_prop.data = None

                    self.template_property_list.append(p_prop)
                    index += 1
                pass

                '''
                for prop in self.template_property_list:
                    print("key:%s" % (prop.key))
                '''

        except Exception as e:
            self.__explorer_log.error("config file open error:" + str(e))
            return 2
        self.__template_setup_state = True
        return 0

    # 暂定传入json格式
    def template_event_post(self, message):
        if self.__explorer_state is not QcloudExplorer.ExplorerState.CONNECTED:
            raise QcloudExplorer.StateError("current state is not CONNECTED")
        if message is None or len(message) == 0:
            raise ValueError('Invalid message.')

        json_token = self.__build_empty_json(self.__device_file.product_id, None)
        client_token = json_token["clientToken"]
        events = message["events"]
        json_out = {
            "method": "events_post",
            "clientToken": client_token,
            "events": events
        }

        template_topic_pub = self.__topic_info.template_event_topic_pub
        rc, mid = self.topic_publish(template_topic_pub, json_out, 1)
        # should deal mid
        self.__explorer_log.debug("mid:%d" % mid)
        if rc != 0:
            return 2
        else:
            return 0
        pass

    def __template_event_init(self):
        template_topic_sub = self.__topic_info.template_event_topic_sub
        sub_res, mid = self.topic_subscribe(template_topic_sub, 0)
        # should deal mid
        self.__explorer_log.debug("mid:%d" % mid)
        if sub_res != 0:
            self.__explorer_log.error("__topic_subscibe error:rc:%d,topic:%s" % (sub_res, template_topic_sub))
            return 1
        else:
            return 0
        pass

    def __template_action_init(self):
        template_topic_sub = self.__topic_info.template_action_topic_sub
        sub_res, mid = self.topic_subscribe(template_topic_sub, 0)
        # should deal mid
        self.__explorer_log.debug("mid:%d" % mid)
        if sub_res != 0:
            self.__explorer_log.error("__topic_subscibe error:rc:%d,topic:%s" % (sub_res, template_topic_sub))
            return 1
        else:
            return 0
        pass

    # 暂定传入的message为json格式(json/属性列表?)
    # 传入json格式时该函数应改为内部函数,由template_report()调用
    def template_json_construct_report_array(self, payload):
        if payload is None or len(payload) == 0:
            raise ValueError('Invalid payload.')

        json_token = self.__build_empty_json(self.__device_file.product_id, None)
        client_token = json_token["clientToken"]
        json_out = {
            "method": "report",
            "clientToken": client_token,
            "params": payload
        }

        return json_out

    def template_report_sys_info(self, sysinfo):
        if self.__explorer_state is not QcloudExplorer.ExplorerState.CONNECTED:
            raise QcloudExplorer.StateError("current state is not CONNECTED")
        if sysinfo is None or len(sysinfo) == 0:
            raise ValueError('Invalid sysinfo.')

        template_topic_pub = self.__topic_info.template_property_topic_pub
        rc, json_out = self.__json_construct_sysinfo(sysinfo)
        if rc != 0:
            self.__explorer_log.error("__json_construct_sysinfo error:rc:%d,topic:%s" % (rc, template_topic_pub))
            return 1
        rc, mid = self.topic_publish(template_topic_pub, json_out, 0)
        # should deal mid
        self.__explorer_log.debug("mid:%d" % mid)
        if rc != 0:
            self.__explorer_log.error("topic_publish error:rc:%d,topic:%s" % (rc, template_topic_pub))
            return 2
        return 0

    def template_control_reply(self, replyPara):
        if self.__explorer_state is not QcloudExplorer.ExplorerState.CONNECTED:
            raise QcloudExplorer.StateError("current state is not CONNECTED")

        template_topic_pub = self.__topic_info.template_property_topic_pub
        json_out = self.__build_control_reply(replyPara)
        rc, mid = self.topic_publish(template_topic_pub, json_out, 0)
        # should deal mid
        self.__explorer_log.debug("mid:%d" % mid)
        if rc != 0:
            self.__explorer_log.error("topic_publish error:rc:%d,topic:%s" % (rc, template_topic_pub))
            return 2
        else:
            return 0
        pass

    def template_action_reply(self, clientToken, response, replyPara):
        if self.__explorer_state is not QcloudExplorer.ExplorerState.CONNECTED:
            raise QcloudExplorer.StateError("current state is not CONNECTED")

        template_topic_pub = self.__topic_info.template_action_topic_pub
        json_out = self.__build_action_reply(clientToken, response, replyPara)
        rc, mid = self.topic_publish(template_topic_pub, json_out, 0)
        # should deal mid
        self.__explorer_log.debug("mid:%d" % mid)
        if rc != 0:
            self.__explorer_log.error("topic_publish error:rc:%d,topic:%s" % (rc, template_topic_pub))
            return 2
        else:
            return 0
        pass

    # 回调中处理IOT_Template_ClearControl
    def template_get_status(self):
        if self.__explorer_state is not QcloudExplorer.ExplorerState.CONNECTED:
            raise QcloudExplorer.StateError("current state is not CONNECTED")

        template_topic_pub = self.__topic_info.template_property_topic_pub

        token = self.__build_empty_json(self.__device_file.product_id, "get_status")
        rc, mid = self.topic_publish(template_topic_pub, token, 0)
        # should deal mid
        self.__explorer_log.debug("mid:%d" % mid)
        if rc != 0:
            self.__explorer_log.error("topic_publish error:rc:%d,topic:%s" % (rc, template_topic_pub))
            return 2
        else:
            return 0
        pass

    def template_report(self, message):
        if self.__explorer_state is not QcloudExplorer.ExplorerState.CONNECTED:
            raise QcloudExplorer.StateError("current state is not CONNECTED")
        if message is None or len(message) == 0:
            raise ValueError('Invalid message.')
        # 判断下行topic是否订阅
        if self.__is_subscribed_property_topic is False:
            template_topic_sub = self.__topic_info.template_property_topic_sub
            sub_res, mid = self.topic_subscribe(template_topic_sub, 0)
            # should deal mid
            self.__explorer_log.debug("mid:%d" % mid)
            if sub_res != 0:
                self.__explorer_log.error("__topic_subscibe error:rc:%d,topic:%s" % (sub_res, template_topic_sub))
                return 1
            self.__is_subscribed_property_topic = True
            pass

        template_topic_pub = self.__topic_info.template_property_topic_pub
        rc, mid = self.topic_publish(template_topic_pub, message, 0)
        if rc != 0:
            self.__explorer_log.error("topic_publish error:rc:%d,topic:%s" % (rc, template_topic_pub))
            return 2
        else:
            return 0
        pass

    def template_init(self):
        if self.__explorer_state is not QcloudExplorer.ExplorerState.CONNECTED:
            raise QcloudExplorer.StateError("current state is not CONNECTED")

        template_topic_sub = self.__topic_info.template_property_topic_sub
        sub_res, mid = self.topic_subscribe(template_topic_sub, 0)
        # should deal mid
        self.__explorer_log.debug("mid:%d" % mid)
        if sub_res != 0:
            self.__explorer_log.error("__topic_subscibe error:rc:%d,topic:%s" % (sub_res, template_topic_sub))
            return 1

        self.__is_subscribed_property_topic = True
        rc = self.__template_event_init()
        if rc != 0:
            return 1
        rc = self.__template_action_init()
        if rc != 0:
            return 1
        return 0

    # gateway
    # 网关子设备数据模板回调注册
    def register_user_property_callback(self, product_id, callback):
        with self.__register_property_cb_lock:
            self.__on_gateway_subdev_prop_cb_dict[product_id] = callback

    def register_user_action_callback(self, product_id, callback):
        with self.__register_action_cb_lock:
            self.__on_gateway_subdev_action_cb_dict[product_id] = callback

    def register_user_event_callback(self, product_id, callback):
        with self.__register_event_cb_lock:
            self.__on_gateway_subdev_event_cb_dict[product_id] = callback

    def gateway_subdev_template_subscribe(self, product_id, topic_prop, topic_action, topic_event):
        # 网关子设备数据模板
        sub_res, mid = self.topic_subscribe(topic_prop, 0)
        # should deal mid
        self.__explorer_log.debug("mid:%d" % mid)
        if sub_res != 0:
            self.__explorer_log.error("topic_subscibe error:rc:%d,topic:%s" % (sub_res, topic_prop))
            return 1
        else:
            # 将product id和topic对加到列表保存
            with self.__gateway_subdev_append_lock:
                for topic, qos in topic_prop:
                    tup = (product_id, topic)
                    self.__gateway_subdev_property_topic_list.append(tup)

        sub_res, mid = self.topic_subscribe(topic_action, 0)
        # should deal mid
        self.__explorer_log.debug("mid:%d" % mid)
        if sub_res != 0:
            self.__explorer_log.error("topic_subscibe error:rc:%d,topic:%s" % (sub_res, topic_action))
            return 1
        else:
            # 将product id和topic对加到列表保存
            with self.__gateway_subdev_append_lock:
                for topic, qos in topic_action:
                    tup = (product_id, topic)
                    self.__gateway_subdev_action_topic_list.append(tup)

        sub_res, mid = self.topic_subscribe(topic_event, 0)
        # should deal mid
        self.__explorer_log.debug("mid:%d" % mid)
        if sub_res != 0:
            self.__explorer_log.error("topic_subscibe error:rc:%d,topic:%s" % (sub_res, topic_event))
            return 1
        else:
            # 将product id和topic对加到列表保存
            with self.__gateway_subdev_append_lock:
                for topic, qos in topic_event:
                    tup = (product_id, topic)
                    self.__gateway_subdev_event_topic_list.append(tup)

        return 0

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
        pass

    def __build_session_payload(self, ptype, pid, name, bind_secret):
        if ptype == "online" or ptype == "offline" or ptype == "unbind":
            payload = {
                "type": ptype,
                "payload": {
                    "devices": [
                        {
                            "product_id": pid,
                            "device_name": name
                        }
                    ]
                }
            }
        elif ptype == "bind":
            nonce = random.randrange(2147483647)
            timestamp = int(time.time())
            sign_format = '%s%s;%d;%d'
            sign_content = sign_format % (pid, name, nonce, timestamp)
            print("sign_content:%s" % sign_content)
            print("bind_secret:%s" % bind_secret)

            # 计算二进制
            sign = hmac.new(bind_secret.encode("utf-8"), sign_content.encode("utf-8"), hashlib.sha1).digest()
            sign_base64 = base64.b64encode(sign).decode('utf-8')

            self.__explorer_log.debug('sign base64 {}'.format(sign_base64))
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
        pass

        return payload

    def gateway_init(self):
        if self.__explorer_state is not QcloudExplorer.ExplorerState.CONNECTED:
            raise QcloudExplorer.StateError("current state is not CONNECTED")

        # 解析网关子设备信息,并添加到list
        json_data = self.__device_file.json_data
        subdev_num = json_data['subDev']['subdev_num']
        subdev_list = json_data['subDev']['subdev_list']

        index = 0
        while index < subdev_num:
            p_subdev = QcloudExplorer.gateway_subdev()
            p_subdev.sub_productId = subdev_list[index]['sub_productId']
            p_subdev.sub_devName = subdev_list[index]['sub_devName']
            p_subdev.session_status = QcloudExplorer.SessionState.SUBDEV_SEESION_STATUS_INIT

            self.gateway_subdev_list.append(p_subdev)
            index += 1

        gateway_topic_sub = self.__topic_info.gateway_topic_sub
        sub_res, mid = self.topic_subscribe(gateway_topic_sub, 0)
        # should deal mid
        self.__explorer_log.debug("mid:%d" % mid)
        if sub_res != 0:
            self.__explorer_log.error("topic_subscibe error:rc:%d,topic:%s" % (sub_res, gateway_topic_sub))
            return 1
        return 0

    def gateway_subdev_online_offline(self, ptype, sub_productId, sub_devName):
        if sub_productId is None or len(sub_productId) == 0:
            raise ValueError('Invalid sub_productId.')
        if sub_devName is None or len(sub_devName) == 0:
            raise ValueError('Invalid sub_devName.')

        # 保存当前会话的设备client_id
        # self.__gateway_session_client_id = sub_productId + "/" + sub_devName
        client_id = sub_productId + "/" + sub_devName

        gateway_topic_pub = self.__topic_info.gateway_topic_pub
        payload = self.__build_session_payload(ptype, sub_productId, sub_devName, None)

        rc, mid = self.topic_publish(gateway_topic_pub, payload, 0)
        if rc != 0:
            self.__explorer_log.error("topic_publish error:rc:%d,topic:%s" % (rc, gateway_topic_pub))
            return 2

        rc = self.__wait_for_session_reply(client_id, ptype)
        if rc == 0:
            self.__explorer_log.debug("client:%s %s success" % (client_id, ptype))
        else:
            self.__explorer_log.debug("client:%s %s fail" % (client_id, ptype))

        return rc

    def gateway_subdev_bind_unbind(self, ptype, sub_productId, sub_devName, sub_secret):
        if sub_productId is None or len(sub_productId) == 0:
            raise ValueError('Invalid sub_productId.')
        if sub_devName is None or len(sub_devName) == 0:
            raise ValueError('Invalid sub_devName.')

        if ptype == "bind":
            if sub_secret is None or len(sub_secret) == 0:
                raise ValueError('Invalid sub_secret.')

        client_id = sub_productId + "/" + sub_devName

        gateway_topic_pub = self.__topic_info.gateway_topic_pub
        payload = self.__build_session_payload(ptype, sub_productId, sub_devName, sub_secret)

        rc, mid = self.topic_publish(gateway_topic_pub, payload, 0)
        if rc != 0:
            self.__explorer_log.error("topic_publish error:rc:%d,topic:%s" % (rc, gateway_topic_pub))
            return 2

        rc = self.__wait_for_session_reply(client_id, ptype)
        if rc == 0:
            self.__explorer_log.debug("client:%s %s success" % (client_id, ptype))
        else:
            self.__explorer_log.debug("client:%s %s fail" % (client_id, ptype))

        return rc

    def gateway_subscribe(self, topic):
        if self.__explorer_state is not QcloudExplorer.ExplorerState.CONNECTED:
            raise QcloudExplorer.StateError("current state is not CONNECTED")

        if topic is None or len(topic) == 0:
            raise ValueError('Invalid topic.')

        sub_res, mid = self.topic_subscribe(topic, 0)
        # should deal mid
        self.__explorer_log.debug("mid:%d" % mid)
        if sub_res != 0:
            self.__explorer_log.error("__topic_subscibe error:rc:%d,topic:%s" % (sub_res, topic))
            return 1
        return 0

    def gateway_publish(self, topic, message):
        if self.__explorer_state is not QcloudExplorer.ExplorerState.CONNECTED:
            raise QcloudExplorer.StateError("current state is not CONNECTED")

        if topic is None or len(topic) == 0:
            raise ValueError('Invalid topic.')
        if message is None or len(message) == 0:
            raise ValueError('Invalid message.')

        rc, mid = self.topic_publish(topic, message, 0)
        if rc != 0:
            self.__explorer_log.error("topic_publish error:rc:%d,topic:%s" % (rc, topic))
            return 2
        return 0

    # ota
    def __ota_publish(self, message, qos):
        topic = self.__topic_info.ota_report_topic_pub
        rc, mid = self.topic_publish(topic, message, qos)
        return rc, mid

    def __ota_info_get(self, payload):
        size = payload["file_size"]
        if size > 0:
            self.__ota_manager.file_size = size
        version = payload["version"]
        if version is not None and len(version) > 0:
            self.__ota_manager.version = version
        url = payload["url"]
        if url is not None and len(url) > 0:
            self.__ota_manager.purl = url
            pos = url.find("https://")
            last_pos = url.rfind("/")
            if pos >= 0:
                self.__ota_manager.is_https = True
                host = url[8:last_pos]
            else:
                host = url[7:last_pos]
            self.__ota_manager.host = host

        md5sum = payload["md5sum"]
        if md5sum is not None and len(md5sum) > 0:
            self.__ota_manager.md5sum = md5sum

        self.__ota_manager.state = QcloudExplorer.OtaState.IOT_OTAS_FETCHING

    def ota_init(self):
        if self.__explorer_state is not QcloudExplorer.ExplorerState.CONNECTED:
            raise QcloudExplorer.StateError("current state is not CONNECTED")

        self.__ota_manager = QcloudExplorer.ota_manage()
        self.__ota_manager.state = QcloudExplorer.OtaState.IOT_OTAS_UNINITED

        ota_topic_sub = self.__topic_info.ota_update_topic_sub
        sub_res, mid = self.topic_subscribe(ota_topic_sub, 1)
        if sub_res != 0:
            self.__explorer_log.error("topic_subscibe error:rc:%d,topic:%s" % (sub_res, ota_topic_sub))
            return 1

        cnt = 0
        while cnt < 10:
            if mid in self.__ota_subscribe_res:
                # 收到该mid回调,且其qos>=0说明订阅完成,qos=0需另做判断
                if self.__ota_subscribe_res[mid] >= 1:
                    break

            time.sleep(0.2)
            cnt += 1
            pass
        if cnt >= 10:
            return 1

        self.__ota_manager.state = QcloudExplorer.OtaState.IOT_OTAS_INITED
        self.__ota_manager.md5 = hashlib.md5()

        return 0

    # 是否应将ota句柄传入(支持多个下载进程?)
    def ota_is_fetching(self):
        return (self.__ota_manager.state == QcloudExplorer.OtaState.IOT_OTAS_FETCHING)

    def ota_is_fetch_finished(self):
        return (self.__ota_manager.state == QcloudExplorer.OtaState.IOT_OTAS_FETCHED)

    def __message_splice(self, state, progress, result_code, result_msg, version, ptype):
        message = None
        code = "%d" % (result_code)
        if ptype == 1:
            message = {
                "type": "report_progress",
                "report": {
                    "progress": {
                        "state": state,
                        "percent": str(progress),
                        "result_code": code,
                        "result_msg": result_msg
                    },
                    "version": version
                }
            }
        elif ptype == 0:
            message = {
                "type": "report_progress",
                "report": {
                    "progress": {
                        "state": state,
                        "result_code": code,
                        "result_msg": result_msg
                    },
                    "version": version
                }
            }

        return message

    def __ota_gen_report_msg(self, version, progress, report_type):
        message = None
        if report_type == QcloudExplorer.OtaReportType.IOT_OTAR_DOWNLOAD_BEGIN:
            message = self.__message_splice("downloading", 0, 0, "", version, 1)
        elif report_type == QcloudExplorer.OtaReportType.IOT_OTAR_DOWNLOADING:
            message = self.__message_splice("downloading", progress, 0, "", version, 1)
        elif ((report_type == QcloudExplorer.OtaReportType.IOT_OTAR_DOWNLOAD_TIMEOUT)
                or (report_type == QcloudExplorer.OtaReportType.IOT_OTAR_FILE_NOT_EXIST)
                or (report_type == QcloudExplorer.OtaReportType.IOT_OTAR_MD5_NOT_MATCH)
                or (report_type == QcloudExplorer.OtaReportType.IOT_OTAR_AUTH_FAIL)
                or (report_type == QcloudExplorer.OtaReportType.IOT_OTAR_UPGRADE_FAIL)):
            message = self.__message_splice("fail", progress, report_type, "time_out", version, 0)
        elif report_type == QcloudExplorer.OtaReportType.IOT_OTAR_UPGRADE_BEGIN:
            message = self.__message_splice("burning", progress, 0, "", version, 0)
        elif report_type == QcloudExplorer.OtaReportType.IOT_OTAR_UPGRADE_SUCCESS:
            message = self.__message_splice("done", progress, 0, "", version, 0)
        else:
            self.__explorer_log.error("not support report_type:%d" % report_type)
            message = None

        return message

    def ota_report_upgrade_result(self, version, report_type):
        if self.__ota_manager.state == QcloudExplorer.OtaState.IOT_OTAS_UNINITED:
            raise ValueError('ota handle is uninitialized')
        message = self.__ota_gen_report_msg(version, 1, report_type)
        if message is not None:
            return self.__ota_publish(message, 1)
        else:
            self.__explorer_log.error("message is none")
            return 1, -1

    def ota_report_progress(self, progress, version, report_type):
        if self.__ota_manager.state == QcloudExplorer.OtaState.IOT_OTAS_UNINITED:
            raise ValueError('ota handle is uninitialized')
        message = self.__ota_gen_report_msg(version, progress, report_type)
        if message is not None:
            return self.__ota_publish(message, 0)
        else:
            self.__explorer_log.error("message is none")
            return 3

    def ota_report_upgrade_success(self, version):
        if version is None:
            rc, mid = self.ota_report_upgrade_result(self.__ota_manager.version,
                                                     QcloudExplorer.OtaReportType.IOT_OTAR_UPGRADE_SUCCESS)
        else:
            rc, mid = self.ota_report_upgrade_result(version, QcloudExplorer.OtaReportType.IOT_OTAR_UPGRADE_SUCCESS)
        if rc != 0:
            self.__explorer_log.error("ota_report_upgrade_success fail")
            return -1
        return mid

    def ota_report_upgrade_fail(self, version):
        if version is None:
            rc, mid = self.ota_report_upgrade_result(self.__ota_manager.version,
                                                     QcloudExplorer.OtaReportType.IOT_OTAR_UPGRADE_FAIL)
        else:
            rc, mid = self.ota_report_upgrade_result(version, QcloudExplorer.OtaReportType.IOT_OTAR_UPGRADE_FAIL)
        if rc != 0:
            self.__explorer_log.error("ota_report_upgrade_success fail")
            return -1
        return mid

    def ota_ioctl_number(self, cmd_type):
        if ((self.__ota_manager.state == QcloudExplorer.OtaState.IOT_OTAS_INITED)
                or (self.__ota_manager.state == QcloudExplorer.OtaState.IOT_OTAS_UNINITED)):
            return -1, "state error"

        if cmd_type == QcloudExplorer.OtaCmdType.IOT_OTAG_FETCHED_SIZE:
            return self.__ota_manager.size_fetched, "success"
        elif cmd_type == QcloudExplorer.OtaCmdType.IOT_OTAG_FILE_SIZE:
            return self.__ota_manager.file_size, "success"
        elif cmd_type == QcloudExplorer.OtaCmdType.IOT_OTAG_CHECK_FIRMWARE:
            if self.__ota_manager.state is not QcloudExplorer.OtaState.IOT_OTAS_FETCHED:
                return -1, "state error"
            md5sum = self.__ota_manager.md5.hexdigest()
            if md5sum == self.__ota_manager.md5sum:
                return 0, "success"
            else:
                self.ota_report_upgrade_result(self.__ota_manager.version,
                                               QcloudExplorer.OtaReportType.IOT_OTAR_MD5_NOT_MATCH)
                return -1, "md5 error"
            pass

        return -1, "cmd type error"

    def ota_ioctl_string(self, cmd_type, length):
        if ((self.__ota_manager.state == QcloudExplorer.OtaState.IOT_OTAS_INITED)
                or (self.__ota_manager.state == QcloudExplorer.OtaState.IOT_OTAS_UNINITED)):
            return "nll", "state error"

        if cmd_type == QcloudExplorer.OtaCmdType.IOT_OTAG_VERSION:
            if len(self.__ota_manager.version) > length:
                return "null", "version length error"
            else:
                return self.__ota_manager.version, "success"
        elif cmd_type == QcloudExplorer.OtaCmdType.IOT_OTAG_MD5SUM:
            if len(self.__ota_manager.md5sum) > length:
                return "null", "md5sum length error"
            else:
                return self.__ota_manager.md5sum, "success"

        return "null", "cmd type error"

    def ota_reset_md5(self):
        self.__ota_manager.md5 = None
        self.__ota_manager.md5 = hashlib.md5()

    def ota_md5_update(self, buf):
        if buf is None:
            self.__explorer_log.error("buf is none")
            return -1
        if self.__ota_manager.md5 is None:
            self.__explorer_log.error("md5 handle is uninitialized")
            return -1

        # self.__ota_manager.md5.update(buf.encode(encoding='utf-8'))
        self.__ota_manager.md5.update(buf)

    def __ota_http_deinit(self, http):
        print("__ota_http_deinit do nothing")

    def http_init(self, host, url, offset, size, timeout_sec):
        range_format = "bytes=%d-%d"
        srange = range_format % (offset, size)

        header = {}
        header["Host"] = host
        header["Accept"] = "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        header["Accept-Encoding"] = "gzip, deflate"
        header["Range"] = srange

        self.http_manager = QcloudExplorer.http_manage()
        self.http_manager.header = header
        self.http_manager.host = host

        if self.__ota_manager.is_https:
            context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH, cadata=self.__iot_ca_crt)
            self.http_manager.https_context = context
            try:
                self.http_manager.request = urllib.request.Request(url=url, headers=header)
                self.http_manager.handle = urllib.request.urlopen(self.http_manager.request,
                                                                  context=context,
                                                                  timeout=timeout_sec)
            except urllib.error.HTTPError as e:
                self.__explorer_log.error("https connect error:%d" % e.code)
                self.http_manager.err_code = e.code
                return 1
            except urllib.error.URLError as e:
                self.__explorer_log.error("https connect error:%s" % e.reason)
                self.http_manager.err_reason = e.reason
                return 1
        else:
            try:
                self.http_manager.request = urllib.request.Request(url=url, headers=header)
                self.http_manager.handle = urllib.request.urlopen(self.http_manager.request,
                                                                  timeout=timeout_sec)
            except Exception as e:
                self.__explorer_log.error("http connect error:%s" % str(e))
                return 1
        return 0

    def http_fetch(self, buf_len):
        if self.http_manager.handle is None:
            return None, -1
        try:
            buf = self.http_manager.handle.read(buf_len)
            return buf, len(buf)
        except Exception as e:
            self.__explorer_log.error("http read error:%s" % str(e))
            return None, -2

    def ota_report_version(self, version):
        if version is None or len(version) == 0:
            raise ValueError('Invalid version.')
        if len(version) < self.__ota_version_len_min or len(version) > self.__ota_version_len_max:
            raise ValueError('Invalid version length')
        if self.__ota_manager.state == QcloudExplorer.OtaState.IOT_OTAS_UNINITED:
            raise ValueError('ota handle is uninitialized')
        report = {
            "type": "report_version",
            "report": {
                "version": version
            }
        }
        rc, mid = self.__ota_publish(report, 1)
        if rc != 0:
            self.__explorer_log.error("__ota_publish fail")
            return 1, mid
        return 0, mid

    def ota_download_start(self, offset, size):
        if offset < 0 or size <= 0:
            raise ValueError('Invalid length.')
        if offset == 0:
            self.ota_reset_md5()
        self.__ota_http_deinit(self.__ota_manager.http_manager)
        # 断点续传初始值不为0
        self.__ota_manager.size_fetched += offset

        rc = self.http_init(self.__ota_manager.host, self.__ota_manager.purl, offset, size, 10000 / 1000)
        if rc != 0:
            if self.http_manager.err_code == 403:
                self.ota_report_upgrade_result(self.__ota_manager.version,
                                               QcloudExplorer.OtaReportType.IOT_OTAR_AUTH_FAIL)
            elif self.http_manager.err_code == 404:
                self.ota_report_upgrade_result(self.__ota_manager.version,
                                               QcloudExplorer.OtaReportType.IOT_OTAR_FILE_NOT_EXIST)
            elif self.http_manager.err_code == 408:
                self.ota_report_upgrade_result(self.__ota_manager.version,
                                               QcloudExplorer.OtaReportType.IOT_OTAR_DOWNLOAD_TIMEOUT)
            else:
                # 其他错误判断(error.reason)
                self.__explorer_log.error("http_init error:%d" % self.http_manager.err_code)

        return rc

    def ota_fetch_yield(self, buf_len):
        if self.__ota_manager.state != QcloudExplorer.OtaState.IOT_OTAS_FETCHING:
            self.__explorer_log.error("ota state is not fetching")
            return None, -1
        # http read
        buf, rv_len = self.http_fetch(buf_len)
        if rv_len < 0:
            if rv_len == -2:
                self.ota_report_upgrade_result(self.__ota_manager.version,
                                               QcloudExplorer.OtaReportType.IOT_OTAR_DOWNLOAD_TIMEOUT)
            return None, -2
        else:
            if self.__ota_manager.size_fetched == 0:
                self.ota_report_progress(QcloudExplorer.OtaProgressCode.IOT_OTAP_FETCH_PERCENTAGE_MIN,
                                         self.__ota_manager.version,
                                         QcloudExplorer.OtaReportType.IOT_OTAR_DOWNLOAD_BEGIN)
                self.__ota_manager.report_timestamp = int(time.time())
            pass
        self.__ota_manager.size_last_fetched = rv_len
        self.__ota_manager.size_fetched += rv_len

        percent = int((self.__ota_manager.size_fetched * 100) / self.__ota_manager.file_size)
        if percent == 100:
            self.ota_report_progress(percent, self.__ota_manager.version,
                                     QcloudExplorer.OtaReportType.IOT_OTAR_DOWNLOADING)
        else:
            timestamp = int(time.time())
            # 间隔1秒上报一次
            if (((timestamp - self.__ota_manager.report_timestamp) >= 1)
                    and (self.__ota_manager.size_last_fetched > 0)):
                self.__ota_manager.report_timestamp = timestamp
                self.ota_report_progress(percent, self.__ota_manager.version,
                                         QcloudExplorer.OtaReportType.IOT_OTAR_DOWNLOADING)

        if self.__ota_manager.size_fetched >= self.__ota_manager.file_size:
            self.__ota_manager.state = QcloudExplorer.OtaState.IOT_OTAS_FETCHED

        self.__ota_manager.md5.update(buf)

        return buf, rv_len

    def rrpc_init(self):
        if self.__explorer_state is not QcloudExplorer.ExplorerState.CONNECTED:
            raise QcloudExplorer.StateError("current state is not CONNECTED")

        rrpc_topic_sub = self.__topic_info.rrpc_topic_sub_prefix + "+"
        sub_res, mid = self.topic_subscribe(rrpc_topic_sub, 0)
        if sub_res != 0:
            self.__explorer_log.error("topic_subscibe error:rc:%d,topic:%s" % (sub_res, rrpc_topic_sub))
            return 1

        # 判断订阅是否成功(qos0)
        return 0

    def rrpc_reply(self, reply, length):
        if reply is None or length == 0:
            raise ValueError('Invalid length.')
        if self.__process_id is None:
            raise ValueError('no process id')
        topic = self.__topic_info.rrpc_topic_pub_prefix + self.__process_id
        rc, mid = self.topic_publish(topic, reply, 0)
        if rc != 0:
            self.__explorer_log.error("topic_publish error:rc:%d,topic:%s" % (rc, topic))
            return -1, mid
        return rc, mid
