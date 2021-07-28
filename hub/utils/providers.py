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

import string
import json
import threading
from hub.log.log import Log
from hub.protocol.protocol import AsyncConnClient

class SingletonType(type):
    _instance_lock = threading.Lock()
    def __call__(cls, *args, **kwargs):
        if not hasattr(cls, "_instance"):
            with SingletonType._instance_lock:
                if not hasattr(cls, "_instance"):
                    cls._instance = super(SingletonType,cls).__call__(*args, **kwargs)
        return cls._instance

class TopicProvider(object):
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
        self.__rrpc_topic_pub_prefix = "$rrpc/txd/%s/%s" % (product_id, device_name)
        self.__rrpc_topic_sub_prefix = "$rrpc/rxd/%s/%s" % (product_id, device_name)

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

class DeviceInfoProvider(object):
    def __init__(self, file_path):
        self.__file_path = file_path
        # self.__logger = logger
        self.__log_provider = LoggerProvider()
        self.__logger = self.__log_provider.logger
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

    def update_config_file(self, psk):
        with open(self.__file_path, '+r', encoding='utf-8') as f:
            t = f.read()
            t = t.replace(self.__device_secret, psk)
            f.seek(0, 0)
            f.write(t)
            f.truncate()

            self.__device_secret = psk
        pass

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

class ConnClientProvider(metaclass=SingletonType):
    """
    使用单例模式构建,保证对象只有一份
    """
    def __init__(self, host, product_id, device_name, device_secret, websocket=False, tls=True, logger=None):
        self.protocol = AsyncConnClient(host, product_id, device_name, device_secret, websocket, tls, logger)

    def __new__(cls, *args, **kwargs):
        return object.__new__(cls)

class LoggerProvider(metaclass=SingletonType):
    """
    使用单例模式构建,保证对象只有一份
    """
    def __init__(self):
        self.logger = Log()

    def __new__(cls, *args, **kwargs):
        return object.__new__(cls)