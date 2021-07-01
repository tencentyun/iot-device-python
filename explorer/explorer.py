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
# from paho.mqtt.client import MQTTMessage
from Crypto.Cipher import AES
# from hub.hub import QcloudHub
from explorer.providers.providers import Providers
# from explorer.services.gateway.gateway import Gateway
from explorer.services.template.template import Template

class QcloudExplorer(object):

    def __init__(self, device_file, tls=True, userdata=None):
        self.__device_file = device_file
        self.__tls = tls
        """ 用户传参 """
        self.__userdata = userdata
        """ 存放用户注册的回调函数 """
        self.__user_callback = {}

        # self.__hub = QcloudHub(device_file, tls)
        self.__provider = Providers(device_file, tls)
        self.__hub = self.__provider.hub

        """ 用户回调注册到hub层 """
        # self.__register_hub_event_callback()

        self.__logger = self.__hub._logger
        self.__PahoLog = logging.getLogger("Paho")
        self.__PahoLog.setLevel(logging.DEBUG)

        # self.__gateway = Gateway(device_file, tls, self.__logger)
        # self.__template = Template(self.__hub, self.__logger)
        
        # self.__template = Template(device_file, tls, self.__logger)
        self.__template_map = {}

        self.__topic = self.__hub._topic

        # set state initialized
        self.__explorer_state = self.__hub.HubState.INITIALIZED

        # data template
        self.__is_subscribed_property_topic = False

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

        # ota
        self.__user_on_ota_report = None

        pass

    class ReplyPara(object):
        def __init__(self):
            self.timeout_ms = 0
            self.code = -1
            self.status_msg = None

    def __handle_subdev_topic(self, topic, qos, payload):
        """ 回调用户处理 """
        if self.__user_callback[topic] is not None:
            self.__user_callback[topic](topic, qos, payload, self.__userdata)
        else:
            self.__logger.error("no callback for topic %s" % topic)

    def __handle_template(self, topic, qos, payload):
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
        template.handle_template(topic, payload)

        """ 回调用户处理 """
        if (topic in self.__user_callback.keys()
                and self.__user_callback[topic] is not None):
            self.__user_callback[topic](topic, qos, payload, self.__userdata)
        else:
            self.__logger.error("no callback for topic %s" % topic)

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
        return self.__explorer_state

    # def protocolInit(self, domain=None, useWebsocket=False):
        # return self.__hub.protocolInit(domain, useWebsocket)

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
        self.__hub.user_on_connect = on_connect
        self.__hub.user_on_disconnect = on_disconnect
        self.__hub.user_on_message = on_message
        self.__hub.user_on_publish = on_publish
        self.__hub.user_on_subscribe = on_subscribe
        self.__hub.user_on_unsubscribe = on_unsubscribe

    def registerUserCallback(self, topic, callback):
        """
        用户注册回调接口
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

    def templateInit(self, productId, deviceName):
        if self.__hub.getConnectState() is not self.__hub.HubState.CONNECTED:
            raise self.__hub.StateError("current state is not CONNECTED")

        """
        构造对应client的template对象并加入字典
        """
        client = productId + deviceName
        template = Template(self.__device_file, self.__tls, productId, deviceName, self.__logger)

        # rc, mid = self.__template.template_init(self.__topic.template_property_topic_sub,
        rc, mid = template.template_init(self.__handle_template)
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
    def otaInit(self):
        return self.__hub.otaInit()

    def otaIsFetching(self):
        return self.__hub.otaIsFetching()

    def otaIsFetchFinished(self):
        return self.__hub.otaIsFetchFinished()

    def otaReportUpgradeSuccess(self, version):
        return self.__hub.otaReportUpgradeSuccess(version)

    def otaReportUpgradeFail(self, version):
        return self.__hub.otaReportUpgradeFail(version)

    def otaIoctlNumber(self, cmdType):
        return self.__hub.otaIoctlNumber(cmdType)

    def otaIoctlString(self, cmdType, length):
        return self.__hub.otaIoctlString(cmdType, length)

    def otaResetMd5(self):
        return self.__hub.otaResetMd5()

    def otaMd5Update(self, buf):
        return self.__hub.otaMd5Update(buf)

    def httpInit(self, host, url, offset, size, timeoutSec):
        return self.__hub.httpInit(host, url, offset, size, timeoutSec)

    def httpFetch(self, buf_len):
        return self.__hub.httpFetch(buf_len)

    def otaReportVersion(self, version):
        return self.__hub.otaReportVersion(version)

    def otaDownloadStart(self, offset, size):
        return self.__hub.otaDownloadStart(offset, size)

    def otaFetchYield(self, buf_len):
        return self.__hub.otaFetchYield(buf_len)

    def subscribeInit(self):

        subscribe_topic_sub = self.__topic.template_service_topic_sub
        sub_res, mid = self.subscribe(subscribe_topic_sub, 1)
        # should deal mid
        self.__logger.debug("mid:%d" % mid)
        if sub_res != 0:
            self.__logger.error("topic_subscribe error:rc:%d,topic:%s" % (sub_res, subscribe_topic_sub))
            return 1
        return 0