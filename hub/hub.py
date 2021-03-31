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
from enum import Enum
from enum import IntEnum
from Crypto.Cipher import AES

class QcloudHub(object):
    class HubState(Enum):
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
    class UserCallBackTask(object):
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

    class LoopThread(object):
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

    class ExplorerLog(object):
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

    class DeviceInfo(object):
        def __init__(self, file_path, logger=None):
            self.__logger = logger
            self.__logger.info('device_info file {}'.format(file_path))

            self.__device_name = None
            self.__product_id = None
            self.__product_secret = None
            self.__device_secret = None
            if self.__logger is not None:
                self.__logger.info('device_info file {}'.format(file_path))
            with open(file_path, 'r', encoding='utf-8') as f:
                self.__json_data = json.loads(f.read())
                self.__device_name = self.__json_data['deviceName']
                self.__product_id = self.__json_data['productId']
                self.__product_secret = self.__json_data['productSecret']
                self.__device_secret = self.__json_data['key_deviceinfo']['deviceSecret']
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

    class Topic(object):
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
