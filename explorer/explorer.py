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
import paho.mqtt.client as mqtt
from enum import Enum
from enum import IntEnum
from Crypto.Cipher import AES
from explorer.providers.providers import Providers
from explorer.services.template.template import Template

class QcloudExplorer(object):

    def __init__(self, device_file, tls=True, userdata=None):
        self.__device_file = device_file
        self.__tls = tls
        """ 用户传参 """
        self.__userdata = userdata
        """ 存放用户注册的回调函数 """
        self.__user_callback = {}

        self.__provider = Providers(device_file, self.__userdata, tls)
        self.__hub = self.__provider.hub
        """
        向hub注册mqtt disconnect回调
        explorer层清理相关资源
        """
        self.__hub.register_explorer_callback("$explorer/from/disconnect", self.__on_disconnect)

        """ 用户回调注册到hub层 """
        # self.__register_hub_event_callback()

        self.__logger = self.__hub._logger
        self.__PahoLog = logging.getLogger("Paho")
        self.__PahoLog.setLevel(logging.DEBUG)

        self.__template_map = {}

        self.__topic = self.__hub._topic

        # data template
        self.__is_subscribed_property_topic = False

        # user mqtt callback
        self.__user_on_connect = None
        self.__user_on_disconnect = None
        self.__user_on_publish = None
        self.__user_on_subscribe = None
        self.__user_on_unsubscribe = None
        self.__user_on_message = None
        pass

    class ReplyPara(object):
        def __init__(self):
            self.timeout_ms = 0
            self.code = -1
            self.status_msg = None

    class LoggerLevel(Enum):
        INFO = "info"
        DEBUG = "debug"
        WARNING = "warring"
        ERROR = "error"

    def __on_disconnect(self, client, userdata, rc):
        """
        清理数据模板资源
        """
        for template in self.__template_map.values():
            if template is not None:
                template.template_reset()
        pass

    def __handle_subdev_topic(self, topic, qos, payload):
        """ 回调用户处理 """
        if self.__user_callback[topic] is not None:
            self.__user_callback[topic](topic, qos, payload, self.__userdata)
        else:
            self.__logger.error("no callback for topic %s" % topic)

    def __handle_template(self, topic, qos, payload, userdate):
        pos = topic.rfind("/")
        device_name = topic[pos + 1:len(topic)]

        topic_split = topic[0:pos]
        pos = topic_split.rfind("/")
        product_id = topic_split[pos + 1:len(topic_split)]

        client = product_id + device_name
        if (client not in self.__template_map.keys()
                or self.__template_map[client] is None):
            self.__logger.error("[template] not found template handle for client:%s" % (client))
            return None

        template = self.__template_map[client]
        template.handle_template(topic, qos, payload, userdate)

        # """ 回调用户处理 """
        # if (topic in self.__user_callback.keys()
        #         and self.__user_callback[topic] is not None):
        #     self.__user_callback[topic](topic, qos, payload, self.__userdata)
        # else:
        #     self.__logger.error("no callback for topic %s" % topic)

    def enableLogger(self, level):
        return self.__hub.enableLogger(level)

    def subscribe(self, topic, qos):
        return self.__hub.subscribe(topic, qos)

    def unsubscribe(self, topic):
        return self.__hub.unsubscribe(topic)

    def publish(self, topic, payload, qos):
        return self.__hub.publish(topic, payload, qos)

    def isMqttConnected(self):
        return self.__hub.isMqttConnected()

    def getConnectStatus(self):
        return self.__hub.getConnectState()

    def getNtpAccurateTime(self):
        return self.__hub.getNtpAccurateTime()

    # start thread to connect and loop
    def connect(self):
        return self.__hub.connect()

    def disconnect(self):
        self.__hub.disconnect()

    def registerMqttCallback(self, on_connect, on_disconnect,
                            on_message, on_publish,
                            on_subscribe, on_unsubscribe):
        """
        注册用户层mqtt回调到hub层
        """
        self.__hub.registerMqttCallback(on_connect, on_disconnect,
                                        on_message, on_publish,
                                        on_subscribe, on_unsubscribe)

    def registerUserCallback(self, topic, callback):
        """
        用户注册回调接口(非mqtt回调)
        """
        self.__user_callback[topic] = callback

    def getEventsList(self, productId, deviceName):
        """
        获取数据模板配置文件event列表
        """
        client = productId + deviceName
        if (client not in self.__template_map.keys()
                or self.__template_map[client] is None):
            self.__logger.error("[template] not found template handle for client:%s" % (client))
            return None

        template = self.__template_map[client]
        return template.get_events_list()

    def getActionList(self, productId, deviceName):
        """
        获取数据模板配置文件action列表
        """
        client = productId + deviceName
        if (client not in self.__template_map.keys()
                or self.__template_map[client] is None):
            self.__logger.error("[template] not found template handle for client:%s" % (client))
            return None

        template = self.__template_map[client]
        return template.get_action_list()

    def getPropertyList(self, productId, deviceName):
        """
        获取数据模板配置文件property列表
        """
        client = productId + deviceName
        if (client not in self.__template_map.keys()
                or self.__template_map[client] is None):
            self.__logger.error("[template] not found template handle for client:%s" % (client))
            return None

        template = self.__template_map[client]
        return template.get_property_list()

    def getProductID(self):
        return self.__hub.getProductID()

    def getDeviceName(self):
        return self.__hub.getDeviceName()

    def templateSetup(self, productId, deviceName, config_file=None):
        client = productId + deviceName
        if (client not in self.__template_map.keys()
                or self.__template_map[client] is None):
            self.__logger.error("[template] not found template handle for client:%s" % (client))
            return -1, -1

        template = self.__template_map[client]
        return template.template_setup(config_file)

    # 暂定传入json格式
    def templateEventPost(self, productId, deviceName, message):
        if self.__hub.getConnectState() is not self.__hub.HubState.CONNECTED:
            raise self.__hub.StateError("current state is not CONNECTED")

        client = productId + deviceName
        if (client not in self.__template_map.keys()
                or self.__template_map[client] is None):
            self.__logger.error("[template] not found template handle for client:%s" % (client))
            return -1, -1

        template = self.__template_map[client]
        rc, mid = template.template_event_post(productId, message)
        if rc != 0:
            self.__logger.error("[template] publish error:rc:%d" % (rc))
        return rc, mid

    # 暂定传入的message为json格式(json/属性列表?)
    # 传入json格式时该函数应改为内部函数,由template_report()调用
    def templateJsonConstructReportArray(self, productId, deviceName, payload):
        # return self.__template.template_json_construct_report_array(self.__hub.getProductID(), payload)
        client = productId + deviceName
        if (client not in self.__template_map.keys()
                or self.__template_map[client] is None):
            self.__logger.error("[template] not found template handle for client:%s" % (client))
            return -1, -1

        template = self.__template_map[client]
        return template.template_json_construct_report_array(productId, payload)

    def templateReportSysInfo(self, productId, deviceName, sysInfo):
        if self.__hub.getConnectState() is not self.__hub.HubState.CONNECTED:
            raise self.__hub.StateError("current state is not CONNECTED")

        client = productId + deviceName
        if (client not in self.__template_map.keys()
                or self.__template_map[client] is None):
            self.__logger.error("[template] not found template handle for client:%s" % (client))
            return -1, -1

        template = self.__template_map[client]
        rc, mid = template.template_report_sys_info(productId, sysInfo)
        if rc != 0:
            self.__logger.error("[template] publish error:rc:%d" % (rc))
        return rc, mid

    def templateControlReply(self, productId, deviceName, replyPara):
        if self.__hub.getConnectState() is not self.__hub.HubState.CONNECTED:
            raise self.__hub.StateError("current state is not CONNECTED")

        client = productId + deviceName
        if (client not in self.__template_map.keys()
                or self.__template_map[client] is None):
            self.__logger.error("[template] not found template handle for client:%s" % (client))
            return -1, -1

        template = self.__template_map[client]
        rc, mid = template.template_control_reply(replyPara)
        if rc != 0:
            self.__logger.error("[template] publish error:rc:%d" % (rc))
        return rc, mid
        

    def templateActionReply(self, productId, deviceName, clientToken, response, replyPara):
        if self.__hub.getConnectState() is not self.__hub.HubState.CONNECTED:
            raise self.__hub.StateError("current state is not CONNECTED")

        client = productId + deviceName
        if (client not in self.__template_map.keys()
                or self.__template_map[client] is None):
            self.__logger.error("[template] not found template handle for client:%s" % (client))
            return -1, -1

        template = self.__template_map[client]
        rc, mid = template.template_action_reply(clientToken, response, replyPara)
        if rc != 0:
            self.__logger.error("[template] publish error:rc:%d" % (rc))
        return rc, mid

    # 回调中处理IOT_Template_ClearControl
    def templateGetStatus(self, productId, deviceName):
        if self.__hub.getConnectState() is not self.__hub.HubState.CONNECTED:
            raise self.__hub.StateError("current state is not CONNECTED")

        client = productId + deviceName
        if (client not in self.__template_map.keys()
                or self.__template_map[client] is None):
            self.__logger.error("[template] not found template handle for client:%s" % (client))
            return -1, -1

        template = self.__template_map[client]
        return template.template_get_status(productId)

    def templateReport(self, productId, deviceName, message):
        if self.__hub.getConnectState() is not self.__hub.HubState.CONNECTED:
            raise self.__hub.StateError("current state is not CONNECTED")

        client = productId + deviceName
        if (client not in self.__template_map.keys()
                or self.__template_map[client] is None):
            self.__logger.error("[template] not found template handle for client:%s" % (client))
            return -1, -1

        # 判断下行topic是否订阅
        if self.__is_subscribed_property_topic is False:
            self.__logger.error("Template is not initialization, please do it!")
            return -1, -1

        template = self.__template_map[client]
        rc, mid = template.template_report(message)
        if rc != 0:
            self.__logger.error("template publish error:rc:%d" % (rc))

        return rc, mid

    def templateInit(self, productId, deviceName,
                        propertyCb, actionCb, eventCb, serviceCb):
        if self.__hub.getConnectState() is not self.__hub.HubState.CONNECTED:
            raise self.__hub.StateError("current state is not CONNECTED")

        """
        构造对应client的template对象并加入字典
        """
        client = productId + deviceName
        template = Template(self.__device_file, self.__tls, productId, deviceName, self.__logger)

        """
        注册用户数据模板topic(property/action/event)对应回调
        注册后用户不用再关注相关topic
        """
        rc, mid = template.template_init(self.__handle_template,
                                            propertyCb, actionCb, eventCb, serviceCb)
        if rc != 0:
            self.__logger.error("[template] subscribe error:rc:%d" % (rc))
            return rc, mid

        # save template client
        self.__template_map[client] = template
        self.__is_subscribed_property_topic = True
        return rc, mid

    def clearControl(self, productId, deviceName):
        client = productId + deviceName
        if (client not in self.__template_map.keys()
                or self.__template_map[client] is None):
            self.__logger.error("[template] not found template handle for client:%s" % (client))
            return -1, -1

        template = self.__template_map[client]
        # topic_pub = self.__topic.template_property_topic_pub
        clientToken = self.__topic.control_clientToken
        rc, mid = template.template_clear_control(clientToken)
        if rc != 0:
            self.__logger.error("[template] publish error:rc:%d" % (rc))
        return rc, mid

    def templateDeinit(self, productId, deviceName):
        if self.__hub.getConnectState() is not self.__hub.HubState.CONNECTED:
            raise self.__hub.StateError("current state is not CONNECTED")

        client = productId + deviceName
        if (client not in self.__template_map.keys()
                or self.__template_map[client] is None):
            self.__logger.error("[template] not found template handle for client:%s" % (client))
            return -1, -1

        template = self.__template_map[client]
        rc, mid = template.template_deinit()
        if rc != 0:
            self.__logger.error("[template] unsubscribe error:rc:%d" % (rc))
        else:
            self.__is_subscribed_property_topic = False

        self.__template_map.pop(client)
        return rc, mid

    def dynregDevice(self, timeout=10):
        """
        dynamic device to tencent cloud
        :param timeout: http/https timeout
        :return: (code, msg): code 0 is success, msg is psk. Other is failed.
        """
        return self.__hub.dynregDevice(timeout)

    # gateway
    def isSubdevStatusOnline(self, sub_productId, sub_devName):
        return self.__hub.isSubdevStatusOnline(sub_productId, sub_devName)

    def updateSubdevStatus(self, sub_productId, sub_devName, status):
        """
        更新本地维护的子设备状态(online/offline)
        """
        return self.__hub.updateSubdevStatus(sub_productId, sub_devName, status)

    def gatewaySubdevGetConfigList(self):
        return self.__hub.gatewaySubdevGetConfigList()

    def gatewaySubdevSubscribe(self, topic):
        self.__hub.register_explorer_callback(topic, self.__handle_subdev_topic)
        return self.__hub.gatewaySubdevSubscribe(topic)

    def gatewaySubdevOnline(self, sub_productId, sub_devName):
        return self.__hub.gatewaySubdevOnline(sub_productId, sub_devName)

    def gatewaySubdevOffline(self, sub_productId, sub_devName):
        return self.__hub.gatewaySubdevOffline(sub_productId, sub_devName)

    def gatewaySubdevBind(self, sub_productId, sub_devName, sub_secret):
        return self.__hub.gatewaySubdevBind(sub_productId, sub_devName, sub_secret)

    def gatewaySubdevUnbind(self, sub_productId, sub_devName):
        return self.__hub.gatewaySubdevUnbind(sub_productId, sub_devName)

    def gatewayInit(self):
        return self.__hub.gatewayInit()

    # ota
    def otaInit(self, productId, deviceName, callback):
        return self.__hub.otaInit(productId, deviceName, callback)

    def otaIsFetching(self, productId, deviceName):
        return self.__hub.otaIsFetching(productId, deviceName)

    def otaIsFetchFinished(self, productId, deviceName):
        return self.__hub.otaIsFetchFinished(productId, deviceName)

    def otaReportUpgradeSuccess(self, productId, deviceName, version):
        return self.__hub.otaReportUpgradeSuccess(productId, deviceName, version)

    def otaReportUpgradeFail(self, productId, deviceName, version):
        return self.__hub.otaReportUpgradeFail(productId, deviceName, version)

    def otaIoctlNumber(self, productId, deviceName, cmdType):
        return self.__hub.otaIoctlNumber(productId, deviceName, cmdType)

    def otaIoctlString(self, productId, deviceName, cmdType, length):
        return self.__hub.otaIoctlString(productId, deviceName, cmdType, length)

    def otaResetMd5(self, productId, deviceName):
        return self.__hub.otaResetMd5(productId, deviceName)

    def otaMd5Update(self, productId, deviceName, buf):
        return self.__hub.otaMd5Update(productId, deviceName, buf)

    def httpInit(self, productId, deviceName, host, url, offset, size, timeoutSec):
        return self.__hub.httpInit(productId, deviceName, host, url, offset, size, timeoutSec)

    def httpFetch(self, productId, deviceName, buf_len):
        return self.__hub.httpFetch(productId, deviceName, buf_len)

    def otaReportVersion(self, productId, deviceName, version):
        return self.__hub.otaReportVersion(productId, deviceName, version)

    def otaDownloadStart(self, productId, deviceName, offset, size):
        return self.__hub.otaDownloadStart(productId, deviceName, offset, size)

    def otaFetchYield(self, productId, deviceName, buf_len):
        return self.__hub.otaFetchYield(productId, deviceName, buf_len)

    def logInit(self, level, enable=True):
        return self.__hub.logInit(level, enable)
