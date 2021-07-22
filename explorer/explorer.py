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
        pass

    def setReconnectInterval(self, max_sec, min_sec):
        """Set mqtt reconnect interval

        Set mqtt reconnect interval
        Args:
            max_sec: reconnect max time
            min_sec: reconnect min time
        Returns:
            success: default
            fail: default
        """
        self.__hub.setReconnectInterval(max_sec, min_sec)

    def setMessageTimout(self, timeout):
        """Set message overtime time

        Set message overtime time
        Args:
            timeout: mqtt keepalive value
        Returns:
            success: default
            fail: default
        """
        self.__hub.setMessageTimout(timeout)

    def setKeepaliveInterval(self, interval):
        """Set mqtt keepalive interval

        Set mqtt keepalive interval
        Args:
            interval: mqtt keepalive interval
        Returns:
            success: default
            fail: default
        """
        self.__hub.setKeepaliveInterval(interval)

    def subscribe(self, topic, qos):
        """Subscribe topic

        Subscribe topic
        Args:
            topic: topic
            qos: mqtt qos
        Returns:
            success: zero and subscribe mid
            fail: negative number and subscribe mid
        """
        return self.__hub.subscribe(topic, qos)

    def unsubscribe(self, topic):
        """Unsubscribe topic

        Unsubscribe topic what is subscribed
        Args:
            topic: topic
        Returns:
            success: zero and unsubscribe mid
            fail: negative number and unsubscribe mid
        """
        return self.__hub.unsubscribe(topic)

    def publish(self, topic, payload, qos):
        """Publish message

        Publish message
        Args:
            topic: topic
            payload: publish message
            qos: mqtt qos
        Returns:
            success: zero and publish mid
            fail: negative number and publish mid
        """
        return self.__hub.publish(topic, payload, qos)

    def isMqttConnected(self):
        """Is mqtt connected

        Is mqtt connected
        Args: None
        Returns:
            success: True/False
        """
        return self.__hub.isMqttConnected()

    def getConnectState(self):
        """Get connect state

        Get device current connect state
        Args: None
        Returns:
            success: connect state
        """
        return self.__hub.getConnectState()

    def getNtpAccurateTime(self):
        """Get NTP time

        Get NTP time
        Args: None
        Returns:
            success: thread start result
            fail: thread start result
        """
        return self.__hub.getNtpAccurateTime()

    # start thread to connect and loop
    def connect(self):
        """Connect

        Device connect
        Args: None
        Returns:
            success: thread start result
            fail: thread start result
        """
        return self.__hub.connect()

    def disconnect(self):
        """Disconnect

        Device disconnect
        Args: None
        Returns:
            success: default
            fail: default
        """
        self.__hub.disconnect()

    def registerMqttCallback(self, on_connect, on_disconnect,
                            on_message, on_publish,
                            on_subscribe, on_unsubscribe):
        """Register user mqtt callback

        Register user mqtt callback for mqtt
        Args:
            on_connect: mqtt connect callback
            on_disconnect: mqtt disconnect callback
            on_message: mqtt message callback
            on_publish: mqtt publish callback
            on_subscribe: mqtt subscribe callback
            on_unsubscribe: mqtt unsubscribe callback
        Returns:
            success: default
            fail: default
        """
        self.__hub.registerMqttCallback(on_connect, on_disconnect,
                                        on_message, on_publish,
                                        on_subscribe, on_unsubscribe)

    def registerUserCallback(self, topic, callback):
        """Register user callback

        Register user callback for a topic
        Args:
            topic: topic
            callback: user callback
        Returns:
            success: default
            fail: default
        """
        self.__user_callback[topic] = callback

    def getEventsList(self, productId, deviceName):
        """Get template event list

        Get template event list from configuration file
        Args:
            productId: product id
            deviceName: device name
        Returns:
            success: template event list
            fail: empty list
        """
        client = productId + deviceName
        if (client not in self.__template_map.keys()
                or self.__template_map[client] is None):
            self.__logger.error("[template] not found template handle for client:%s" % (client))
            return None

        template = self.__template_map[client]
        return template.get_events_list()

    def getActionList(self, productId, deviceName):
        """Get template action list

        Get template action list from configuration file
        Args:
            productId: product id
            deviceName: device name
        Returns:
            success: template action list
            fail: empty list
        """
        client = productId + deviceName
        if (client not in self.__template_map.keys()
                or self.__template_map[client] is None):
            self.__logger.error("[template] not found template handle for client:%s" % (client))
            return None

        template = self.__template_map[client]
        return template.get_action_list()

    def getPropertyList(self, productId, deviceName):
        """Get template property list

        Get template property list from configuration file
        Args:
            productId: product id
            deviceName: device name
        Returns:
            success: template property list
            fail: empty list
        """
        client = productId + deviceName
        if (client not in self.__template_map.keys()
                or self.__template_map[client] is None):
            self.__logger.error("[template] not found template handle for client:%s" % (client))
            return None

        template = self.__template_map[client]
        return template.get_property_list()

    def getProductID(self):
        """Get product id

        Get product id
        Args: None
        Returns:
            success: product id
            fail: None
        """
        return self.__hub.getProductID()

    def getDeviceName(self):
        """Get device name

        Get device name
        Args: None
        Returns:
            success: device name
            fail: None
        """
        return self.__hub.getDeviceName()

    def templateSetup(self, productId, deviceName, config_file=None):
        """Parse json configuration file

        Parse json configuration file
        Args:
            productId: product id
            deviceName: device name
            config_file: configuration file path
        Returns:
            success: zero
            fail: negative number
        """
        client = productId + deviceName
        if (client not in self.__template_map.keys()
                or self.__template_map[client] is None):
            self.__logger.error("[template] not found template handle for client:%s" % (client))
            return -1, -1

        template = self.__template_map[client]
        return template.template_setup(config_file)

    # 暂定传入json格式
    def templateEventPost(self, productId, deviceName, message):
        """Report event/events infomation

        Report device event/events infomation
        Args:
            productId: product id
            deviceName: device name
            message: device event/events infomation
        Returns:
            success: zero and publish mid
            fail: negative number and publish mid
        """
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

    def templateJsonConstructReportArray(self, productId, deviceName, payload):
        """Construct json array

        Construct json array
        Args:
            productId: product id
            deviceName: device name
            payload: report message, json type
        Returns:
            success: json message
            fail: None
        """
        client = productId + deviceName
        if (client not in self.__template_map.keys()
                or self.__template_map[client] is None):
            self.__logger.error("[template] not found template handle for client:%s" % (client))
            return -1, -1

        template = self.__template_map[client]
        return template.template_json_construct_report_array(productId, payload)

    def templateReportSysInfo(self, productId, deviceName, sysInfo):
        """Report system infomation

        Report device system infomation
        Args:
            productId: product id
            deviceName: device name
            sysInfo: device system infomation
        Returns:
            success: zero and publish mid
            fail: negative number and publish mid
        """
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
        """Report control reply

        Report control reply after recvive control message
        Args:
            productId: product id
            deviceName: device name
            replyPara: description infomation, type is class ReplyPara()
        Returns:
            success: zero and publish mid
            fail: negative number and publish mid
        """
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
        """Report action reply

        Report action reply after recvive action message
        Args:
            productId: product id
            deviceName: device name
            clientToken: client token
            response: report message
            replyPara: other description infomation, type is class ReplyPara()
        Returns:
            success: zero and publish mid
            fail: negative number and publish mid
        """
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
        """Get status

        Get device status
        Args:
            productId: product id
            deviceName: device name
        Returns:
            success: zero and publish mid
            fail: negative number and publish mid
        """
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
        """Template message report

        Report message to cloud
        Args:
            productId: product id
            deviceName: device name
            message: report message
        Returns:
            success: zero and publish mid
            fail: negative number and publish mid
        """
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
        """Template initialization

        Template initialization
        Args:
            productId: product id
            deviceName: device name
            propertyCb: user received property message callback
            actionCb: user received action message callback
            eventCb: user received event message callback
            serviceCb: user received service message callback
        Returns:
            success: zero and subscribe mid
            fail: negative number and subscribe mid
        """
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
        """Clear control

        Clear control message
        Args:
            productId: device product_id
            deviceName: device device_name
        Returns:
            success: zero and publish mid
            fail: negative number and publish mid
        """
        client = productId + deviceName
        if (client not in self.__template_map.keys()
                or self.__template_map[client] is None):
            self.__logger.error("[template] not found template handle for client:%s" % (client))
            return -1, -1

        template = self.__template_map[client]

        # clientToken = self.__topic.control_clientToken
        rc, mid = template.template_clear_control()
        if rc != 0:
            self.__logger.error("[template] publish error:rc:%d" % (rc))
        return rc, mid

    def templateDeinit(self, productId, deviceName):
        """Template destroy

        Template destroy
        Args:
            productId: device product_id
            deviceName: device device_name
        Returns:
            success: zero and unsubscribe mid
            fail: negative number and unsubscribe mid
        """
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
        """Dynamic register

        Get the device secret from the Cloud
        Args:
            timeout: request timeout
        Returns:
            success: return zero and device secret
            fail: -1 and error message
        """
        return self.__hub.dynregDevice(timeout)

    # gateway
    def isSubdevStatusOnline(self, sub_productId, sub_devName):
        """Sub-device status

        Determine if the device is online
        Args:
            sub_productId: sub-device product_id
            sub_devName: sub-device device_name
        Returns:
            success: if device is online
        """
        return self.__hub.isSubdevStatusOnline(sub_productId, sub_devName)

    def updateSubdevStatus(self, sub_productId, sub_devName, status):
        """Update device status

        Update sub-device local status
        Args:
            sub_productId: sub-device product_id
            sub_devName: sub-device device_name
            status: new status
        Returns:
            success: None
        """
        return self.__hub.updateSubdevStatus(sub_productId, sub_devName, status)

    def gatewaySubdevGetConfigList(self):
        """Get sub-device list

        Get the list of sub-devices in the configuration file
        Args: None
        Returns:
            success: sub-device list
        """
        return self.__hub.gatewaySubdevGetConfigList()

    def gatewaySubdevSubscribe(self, topic):
        """Subscribe sub-device topic

        Subscribe sub-device topic
        Args: sub-device topic
        Returns:
            success: zero and subscribe mid
        """
        self.__hub.register_explorer_callback(topic, self.__handle_subdev_topic)
        return self.__hub.gatewaySubdevSubscribe(topic)

    def gatewaySubdevOnline(self, sub_productId, sub_devName):
        """Make sub-device online

        Make sub-device online
        Args:
            sub_productId: sub-device product_id
            sub_devName: sub-device device_name
        Returns:
            success: zero and publish mid
        """
        return self.__hub.gatewaySubdevOnline(sub_productId, sub_devName)

    def gatewaySubdevOffline(self, sub_productId, sub_devName):
        """Make sub-device offline

        Make sub-device offline
        Args:
            sub_productId: sub-device product_id
            sub_devName: sub-device device_name
        Returns:
            success: zero and publish mid
        """
        return self.__hub.gatewaySubdevOffline(sub_productId, sub_devName)

    def gatewaySubdevBind(self, sub_productId, sub_devName, sub_secret):
        """Bind sub-device

        Gateway device bind sub-device
        Args:
            sub_productId: sub-device product_id
            sub_devName: sub-device device_name
            sub_secret: sub-device secret
        Returns:
            success: zero and publish mid
        """
        return self.__hub.gatewaySubdevBind(sub_productId, sub_devName, sub_secret)

    def gatewaySubdevUnbind(self, sub_productId, sub_devName):
        """Unbind sub-device

        Gateway device unbind sub-device
        Args:
            sub_productId: sub-device product_id
            sub_devName: sub-device device_name
            sub_secret: sub-device secret
        Returns:
            success: zero and publish mid
        """
        return self.__hub.gatewaySubdevUnbind(sub_productId, sub_devName)

    def gatewayInit(self):
        """Gateway initialization

        Gateway initialization
        Args: None
        Returns:
            success: zero and subscribe mid
        """
        return self.__hub.gatewayInit()

    # ota
    def otaInit(self, productId, deviceName, callback):
        """Ota initialization

        Ota initialization
        Args:
            productId: product id
            deviceName: device name
            callback: user received message callback
        Returns:
            success: zero and subscribe mid
        """
        return self.__hub.otaInit(productId, deviceName, callback)

    def otaIsFetching(self, productId, deviceName):
        """Is downloading

        Is downloading
        Args:
            productId: product id
            deviceName: device name
        Returns:
            success: True
            fail: False
        """
        return self.__hub.otaIsFetching(productId, deviceName)

    def otaIsFetchFinished(self, productId, deviceName):
        """Is download finished

        Is download finished
        Args:
            productId: product id
            deviceName: device name
        Returns:
            success: True
            fail: False
        """
        return self.__hub.otaIsFetchFinished(productId, deviceName)

    def otaReportUpgradeSuccess(self, productId, deviceName, version):
        """Report success message

        Report upgrade success message to qcloud
        Args:
            productId: product id
            deviceName: device name
            version: firmware version
        Returns:
            success: zero and publish mid
            fail: negative number and publish mid
        """
        return self.__hub.otaReportUpgradeSuccess(productId, deviceName, version)

    def otaReportUpgradeFail(self, productId, deviceName, version):
        """Report fail message

        Report upgrade fail message to qcloud
        Args:
            productId: product id
            deviceName: device name
            version: firmware version
        Returns:
            success: zero and publish mid
            fail: negative number and publish mid
        """
        return self.__hub.otaReportUpgradeFail(productId, deviceName, version)

    def otaIoctlNumber(self, productId, deviceName, cmdType):
        """User interaction

        User interaction with SDK to get a number, like linux kernel ioctl
        Args:
            productId: product id
            deviceName: device name
            cmdType: interaction command
        Returns:
            success: the number you want and 'success' message
            fail: negative number and error message
        """
        return self.__hub.otaIoctlNumber(productId, deviceName, cmdType)

    def otaIoctlString(self, productId, deviceName, cmdType, length):
        """User interaction

        User interaction with SDK to get string, like linux kernel ioctl
        Args:
            productId: product id
            deviceName: device name
            cmdType: interaction command
            length: command length
        Returns:
            success: the string you want and 'success' message
            fail: negative number and error message
        """
        return self.__hub.otaIoctlString(productId, deviceName, cmdType, length)

    def otaResetMd5(self, productId, deviceName):
        """Reset md5 value

        Reset md5 value
        Args:
            productId: product id
            deviceName: device name
        Returns:
            success: zero
            fail: negative number
        """
        return self.__hub.otaResetMd5(productId, deviceName)

    def otaMd5Update(self, productId, deviceName, buf):
        """Update md5 value

        Calculate new message md5 and update old
        Args:
            productId: product id
            deviceName: device name
            buf: new message
        Returns:
            success: zero
            fail: negative number
        """
        return self.__hub.otaMd5Update(productId, deviceName, buf)

    def httpInit(self, productId, deviceName, host, url, offset, size, timeoutSec):
        """Http initialization

        Http initialization
        Args:
            productId: product id
            deviceName: device name
            host: http server host
            url: http url
            offset: http parameter 'Range' minimum
            size: http parameter 'Range' max
            timeoutSec: http overtime time
        Returns:
            success: zero
            fail: negative number
        """
        return self.__hub.httpInit(productId, deviceName, host, url, offset, size, timeoutSec)

    def httpFetch(self, productId, deviceName, buf_len):
        """Http download

        Http download
        Args:
            productId: product id
            deviceName: device name
            buf_len: download max length
        Returns:
            success: downloaded content and length
            fail: None and negative number
        """
        return self.__hub.httpFetch(productId, deviceName, buf_len)

    def otaReportVersion(self, productId, deviceName, version):
        """Report version

        Report local firmware version
        Args:
            productId: product id
            deviceName: device name
            version: local firmware version
        Returns:
            success: zero and publish mid
            fail: negative number and publish mid
        """
        return self.__hub.otaReportVersion(productId, deviceName, version)

    def otaDownloadStart(self, productId, deviceName, offset, size):
        """Start download

        Start download
        Args:
            productId: product id
            deviceName: device name
            offset: download offset
            size: download size
        Returns:
            success: zero
            fail: negative number
        """
        return self.__hub.otaDownloadStart(productId, deviceName, offset, size)

    def otaFetchYield(self, productId, deviceName, buf_len):
        """Http download

        Perform an http download
        Args:
            productId: product id
            deviceName: device name
            buf_len: download max length
        Returns:
            success: downloaded content and length
            fail: None and negative number
        """
        return self.__hub.otaFetchYield(productId, deviceName, buf_len)

    def logInit(self, level, enable=True):
        """Log initialization

        Log initialization
        Args:
            level: log level, type is class LoggerLevel()
            enable: enable switch
        Returns:
            success: logger handle
            fail: None
        """
        return self.__hub.logInit(level, enable)
