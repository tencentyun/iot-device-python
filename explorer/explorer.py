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
from hub.hub import QcloudHub
from explorer.services.gateway.gateway import Gateway
from explorer.services.template.template import Template

class QcloudExplorer(object):

    def __init__(self, device_file, tls=True, userdata=None):
        """ 用户传参 """
        self.__userdata = userdata
        """ 存放用户注册的回调函数 """
        self.__user_callback = {}

        self.__hub = QcloudHub(device_file, tls)

        """ 用户回调注册到hub层 """
        self.__register_hub_event_callback()

        self.__logger = self.__hub._logger
        self.__PahoLog = logging.getLogger("Paho")
        self.__PahoLog.setLevel(logging.DEBUG)

        # 将hub句柄传入gateway,方便其直接使用hub提供的能力
        self.__gateway = Gateway(self.__hub, self.__logger)
        self.__template = Template(self.__hub, self.__logger)

        # self.__device_file = self.__hub.DeviceInfo(device_file, self.__logger)
        self.__topic = self.__hub._topic

        # set state initialized
        self.__explorer_state = self.__hub.HubState.INITIALIZED

        # data template
        self.__is_subscribed_property_topic = False
        
        # data template reply
        self.__replyAck = -1

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

        # rrpc callback
        self.__user_on_rrpc_message = None
        self.__process_id = None

        # shadow
        self._shadow_token_num = 0

        # construct thread handle
        # self.__loop_thread = self.__hub.LoopThread(self.__logger)
        # self.__user_thread = self.__hub.UserCallBackTask(self.__logger)
        # self.__user_cmd_cb_init()

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

    """
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

    @property
    def on_subscribe_service_post(self):
        return self.__on_subscribe_service_post

    @on_subscribe_service_post.setter
    def on_subscribe_service_post(self, value):
        self.__on_subscribe_service_post = value
    """

    # 处理从hub层调用的回调
    def __hub_on_connect(self, value):
        # client, user_data, session_flag, rc = value
        session_flag, rc = value
        # 调用客户注册到explorer的回调
        self.__user_on_connect(session_flag['session present'], rc, self.__userdata)

    def __hub_on_disconnect(self, value):
        self.__user_on_disconnect(value, self.__userdata)

    def __hub_on_publish(self, value):
        self.__user_on_publish(value, self.__userdata)

    def __hub_on_subscribe(self, value):
        qos, mid = value
        self.__user_on_subscribe(qos, mid, self.__userdata)

    def __hub_on_unsubscribe(self, value):
        self.__user_on_unsubscribe(value, self.__userdata)

    def __hub_on_message(self, value):
        self.__user_on_message(value, self.__userdata)

    # 将用户注册到exporer层的回调注册到hub层
    def __register_hub_event_callback(self):
        # self.__hub.user_on_connect = self.__hub_on_connect
        # self.__hub.user_on_disconnect = self.__hub_on_disconnect
        # self.__hub.user_on_message = self.__hub_on_message
        # self.__hub.user_on_publish = self.__hub_on_publish
        # self.__hub.user_on_subscribe = self.__hub_on_subscribe
        # self.__hub.user_on_unsubscribe = self.__hub_on_unsubscribe
        self.__hub.user_on_connect = self.__user_on_connect
        self.__hub.user_on_disconnect = self.__user_on_disconnect
        self.__hub.user_on_message = self.__user_on_message
        self.__hub.user_on_publish = self.__user_on_publish
        self.__hub.user_on_subscribe = self.__user_on_subscribe
        self.__hub.user_on_unsubscribe = self.__user_on_unsubscribe

    def __handle_subdev_topic(self, message):
        topic = message.topic
        """ 回调用户处理 """
        if self.__user_callback[topic] is not None:
            self.__user_callback[topic](message)
        else:
            self.__logger.error("no callback for topic %s" % topic)

    def __handle_reply(self, method, payload):
        clientToken = payload["clientToken"]
        replyAck = payload["code"]
        if method == "get_status_reply":
            if replyAck == 0:
                # update client token
                self.__topic.control_clientToken = clientToken
            else:
                self.__replyAck = replyAck
                self.__logger.debug("replyAck:%d" % replyAck)
        else:
            self.__replyAck = replyAck
        pass

    def __handle_control(self, payload):
        clientToken = payload["clientToken"]
        self.__topic.control_clientToken = clientToken

    def __handle_property(self, payload):
        method = payload["method"]
        if method == "control":
            self.__handle_control(payload)
        else:
            self.__handle_reply(method, payload)

    def __handle_template(self, message):
        topic = message.topic
        if topic == self.__topic.template_property_topic_sub:
            payload = json.loads(message.payload.decode('utf-8'))

            # __handle_reply回调到用户，由用户调用clearContrl()
            self.__handle_property(payload)

        """ 回调用户处理 """
        if self.__user_callback[topic] is not None:
            self.__user_callback[topic](message)
        else:
            self.__logger.error("no callback for topic %s" % topic)

    def __handle_ota(self, payload):
        ptype = payload["type"]
        if ptype == "report_version_rsp":
            self.__user_on_ota_report(payload, self.__userdata)
        elif ptype == "update_firmware":
            self.__ota_info_get(payload)

    def __rrpc_get_process_id(self, topic):
        pos = topic.rfind("/")
        if pos > 0:
            self.__process_id = topic[pos + 1:len(topic)]
            return 0
        else:
            self.__logger.error("cannot found process id from topic:%s" % topic)
            return -1

    def __handle_rrpc(self, topic, payload):
        rc = self.__rrpc_get_process_id(topic)
        if rc < 0:
            raise self.__hub.StateError("cannot found process id")

        # 调用用户注册的回调
        if self.__user_on_rrpc_message is not None:
            self.__user_on_rrpc_message(payload, self.__userdata)

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

    
    def registerUserCallback(self, topic, callback):
        """
        用户注册回调接口
        """
        self.__user_callback[topic] = callback

    def getEventsList(self):
        """
        获取数据模板配置文件event列表
        """
        return self.__template.get_events_list()

    def getActionList(self):
        """
        获取数据模板配置文件action列表
        """
        return self.__template.get_action_list()

    def getPropertyList(self):
        """
        获取数据模板配置文件property列表
        """
        return self.__template.get_property_list()

    def templateSetup(self, config_file=None):
        return self.__template.template_setup(config_file)

    # 暂定传入json格式
    def templateEventPost(self, message):
        if self.__hub.getConnectState() is not self.__hub.HubState.CONNECTED:
            raise self.__hub.StateError("current state is not CONNECTED")

        topic_pub = self.__topic.template_event_topic_pub
        rc, mid = self.__template.template_event_post(topic_pub, 1, self.__hub.getProductID(), message)
        if rc != 0:
            self.__logger.error("[template] publish error:rc:%d,topic:%s" % (rc, topic_pub))
        return rc, mid

    # 暂定传入的message为json格式(json/属性列表?)
    # 传入json格式时该函数应改为内部函数,由template_report()调用
    def templateJsonConstructReportArray(self, payload):
        return self.__template.template_json_construct_report_array(self.__hub.getProductID(), payload)

    def templateReportSysInfo(self, sysInfo):
        if self.__hub.getConnectState() is not self.__hub.HubState.CONNECTED:
            raise self.__hub.StateError("current state is not CONNECTED")

        topic_pub = self.__topic.template_property_topic_pub
        rc, mid = self.__template.template_report_sys_info(topic_pub, 0, self.__hub.getProductID(), sysInfo)
        if rc != 0:
            self.__logger.error("[template] publish error:rc:%d,topic:%s" % (rc, topic_pub))
        return rc, mid

    def templateControlReply(self, replyPara):
        if self.__hub.getConnectState() is not self.__hub.HubState.CONNECTED:
            raise self.__hub.StateError("current state is not CONNECTED")

        topic_pub = self.__topic.template_property_topic_pub
        token = self.__topic.control_clientToken
        rc, mid = self.__template.template_control_reply(topic_pub, 0, token, replyPara)
        if rc != 0:
            self.__logger.error("[template] publish error:rc:%d,topic:%s" % (rc, topic_pub))
        return rc, mid
        

    def templateActionReply(self, clientToken, response, replyPara):
        if self.__hub.getConnectState() is not self.__hub.HubState.CONNECTED:
            raise self.__hub.StateError("current state is not CONNECTED")

        topic_pub = self.__topic.template_action_topic_pub
        rc, mid = self.__template.template_action_reply(topic_pub,
                                                0, clientToken, response, replyPara)
        if rc != 0:
            self.__logger.error("[template] publish error:rc:%d,topic:%s" % (rc, topic_pub))
        return rc, mid

    # 回调中处理IOT_Template_ClearControl
    def templateGetStatus(self):
        if self.__hub.getConnectState() is not self.__hub.HubState.CONNECTED:
            raise self.__hub.StateError("current state is not CONNECTED")

        return self.__template.template_get_status(
                                                self.__topic.template_property_topic_pub,
                                                self.__hub.getProductID())

    def templateReport(self, message):
        if self.__hub.getConnectState() is not self.__hub.HubState.CONNECTED:
            raise self.__hub.StateError("current state is not CONNECTED")
        # 判断下行topic是否订阅
        if self.__is_subscribed_property_topic is False:
            self.__logger.error("Template is not initialization, please do it!")
            return -1, -1
        rc, mid = self.__template.template_report(self.__topic.template_property_topic_pub, 0, message)
        if rc != 0:
            self.__logger.error("template publish error:rc:%d,topic:%s" % (rc, self.__topic.template_property_topic_pub))

        return rc, mid

    def templateInit(self):
        if self.__hub.getConnectState() is not self.__hub.HubState.CONNECTED:
            raise self.__hub.StateError("current state is not CONNECTED")

        rc, mid = self.__template.template_init(self.__topic.template_property_topic_sub,
                                        self.__topic.template_action_topic_sub,
                                        self.__topic.template_event_topic_sub,
                                        self.__handle_template)
        if rc != 0:
            self.__logger.error("[template] subscribe error:rc:%d" % (rc))

        self.__is_subscribed_property_topic = True
        return rc, mid


    def clearControl(self):
        topic_pub = self.__topic.template_property_topic_pub
        clientToken = self.__topic.control_clientToken
        rc, mid = self.__template.template_clear_control(
                                                    topic_pub, 0, clientToken)
        if rc != 0:
            self.__logger.error("[template] publish error:rc:%d,topic:%s" % 
                                (rc, self.__topic.template_property_topic_pub))
        return rc, mid

    def templateDeinit(self):
        if self.__explorer_state is not self.__hub.HubState.CONNECTED:
            raise self.__hub.StateError("current state is not CONNECTED")


        template_topic_sub = self.__topic.template_property_topic_sub
        sub_res, mid = self.unsubscribe(template_topic_sub)
        # should deal mid
        self.__logger.debug("mid:%d" % mid)
        if sub_res != 0:
            self.__logger.error("topic_subscribe error:rc:%d,topic:%s" % (sub_res, template_topic_sub))
            return 1

        self.__is_subscribed_property_topic = False

        
        template_topic_sub = self.__topic.template_event_topic_sub
        sub_res, mid = self.unsubscribe(template_topic_sub)
        # should deal mid
        self.__logger.debug("mid:%d" % mid)
        if sub_res != 0:
            self.__logger.error("topic_subscribe error:rc:%d,topic:%s" % (sub_res, template_topic_sub))
            return 1

        template_topic_sub = self.__topic.template_action_topic_sub
        sub_res, mid = self.unsubscribe(template_topic_sub)
        # should deal mid
        self.__logger.debug("mid:%d" % mid)
        if sub_res != 0:
            self.__logger.error("topic_subscribe error:rc:%d,topic:%s" % (sub_res, template_topic_sub))
            return 1
        else:
            return 0
        pass

    def dynregDevice(self, timeout=10):
        """
        dynamic device to tencent cloud
        :param timeout: http/https timeout
        :return: (code, msg): code 0 is success, msg is psk. Other is failed.
        """
        return self.__hub.dynregDevice(timeout)

    # gateway
    def gatewaySubdevSubscribe(self, product_id, topic_prop, topic_action, topic_event):
        topic_list = []
        if len(topic_prop) != 0:
            topic_list.extend(topic_prop)
        if len(topic_action) != 0:
            topic_list.extend(topic_action)
        if len(topic_event) != 0:
            topic_list.extend(topic_event)
        self.__hub.register_explorer_callback(topic_list, self.__handle_subdev_topic)
        return self.__gateway.gateway_subdev_subscribe(product_id, topic_prop, topic_action, topic_event)

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
    def __ota_publish(self, message, qos):
        topic = self.__topic.ota_report_topic_pub
        rc, mid = self.publish(topic, message, qos)
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

        self.__ota_manager.state = self.__hub.OtaState.IOT_OTAS_FETCHING

    def otaInit(self):
        if self.__explorer_state is not self.__hub.HubState.CONNECTED:
            raise self.__hub.StateError("current state is not CONNECTED")

        self.__ota_manager = self.__hub.ota_manage()
        self.__ota_manager.state = self.__hub.OtaState.IOT_OTAS_UNINITED

        ota_topic_sub = self.__topic.ota_update_topic_sub
        sub_res, mid = self.subscribe(ota_topic_sub, 1)
        if sub_res != 0:
            self.__logger.error("topic_subscribe error:rc:%d,topic:%s" % (sub_res, ota_topic_sub))
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

        self.__ota_manager.state = self.__hub.OtaState.IOT_OTAS_INITED
        self.__ota_manager.md5 = hashlib.md5()

        return 0

    # 是否应将ota句柄传入(支持多个下载进程?)
    def otaIsFetching(self):
        return (self.__ota_manager.state == self.__hub.OtaState.IOT_OTAS_FETCHING)

    def otaIsFetchFinished(self):
        return (self.__ota_manager.state == self.__hub.OtaState.IOT_OTAS_FETCHED)

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
        if report_type == self.__hub.OtaReportType.IOT_OTAR_DOWNLOAD_BEGIN:
            message = self.__message_splice("downloading", 0, 0, "", version, 1)
        elif report_type == self.__hub.OtaReportType.IOT_OTAR_DOWNLOADING:
            message = self.__message_splice("downloading", progress, 0, "", version, 1)
        elif ((report_type == self.__hub.OtaReportType.IOT_OTAR_DOWNLOAD_TIMEOUT)
                or (report_type == self.__hub.OtaReportType.IOT_OTAR_FILE_NOT_EXIST)
                or (report_type == self.__hub.OtaReportType.IOT_OTAR_MD5_NOT_MATCH)
                or (report_type == self.__hub.OtaReportType.IOT_OTAR_AUTH_FAIL)
                or (report_type == self.__hub.OtaReportType.IOT_OTAR_UPGRADE_FAIL)):
            message = self.__message_splice("fail", progress, report_type, "time_out", version, 0)
        elif report_type == self.__hub.OtaReportType.IOT_OTAR_UPGRADE_BEGIN:
            message = self.__message_splice("burning", progress, 0, "", version, 0)
        elif report_type == self.__hub.OtaReportType.IOT_OTAR_UPGRADE_SUCCESS:
            message = self.__message_splice("done", progress, 0, "", version, 0)
        else:
            self.__logger.error("not support report_type:%d" % report_type)
            message = None

        return message

    def _ota_report_upgrade_result(self, version, report_type):
        if self.__ota_manager.state == self.__hub.OtaState.IOT_OTAS_UNINITED:
            raise ValueError('ota handle is uninitialized')
        message = self.__ota_gen_report_msg(version, 1, report_type)
        if message is not None:
            return self.__ota_publish(message, 1)
        else:
            self.__logger.error("message is none")
            return 1, -1

    def _ota_report_progress(self, progress, version, report_type):
        if self.__ota_manager.state == self.__hub.OtaState.IOT_OTAS_UNINITED:
            raise ValueError('ota handle is uninitialized')
        message = self.__ota_gen_report_msg(version, progress, report_type)
        if message is not None:
            return self.__ota_publish(message, 0)
        else:
            self.__logger.error("message is none")
            return 3

    def otaReportUpgradeSuccess(self, version):
        if version is None:
            rc, mid = self._ota_report_upgrade_result(self.__ota_manager.version,
                                                     self.__hub.OtaReportType.IOT_OTAR_UPGRADE_SUCCESS)
        else:
            rc, mid = self._ota_report_upgrade_result(version, self.__hub.OtaReportType.IOT_OTAR_UPGRADE_SUCCESS)
        if rc != 0:
            self.__logger.error("ota_report_upgrade_success fail")
            return -1
        return mid

    def otaReportUpgradeFail(self, version):
        if version is None:
            rc, mid = self._ota_report_upgrade_result(self.__ota_manager.version,
                                                     self.__hub.OtaReportType.IOT_OTAR_UPGRADE_FAIL)
        else:
            rc, mid = self._ota_report_upgrade_result(version, self.__hub.OtaReportType.IOT_OTAR_UPGRADE_FAIL)
        if rc != 0:
            self.__logger.error("ota_report_upgrade_success fail")
            return -1
        return mid

    def otaIoctlNumber(self, cmd_type):
        if ((self.__ota_manager.state == self.__hub.OtaState.IOT_OTAS_INITED)
                or (self.__ota_manager.state == self.__hub.OtaState.IOT_OTAS_UNINITED)):
            return -1, "state error"

        if cmd_type == self.__hub.OtaCmdType.IOT_OTAG_FETCHED_SIZE:
            return self.__ota_manager.size_fetched, "success"
        elif cmd_type == self.__hub.OtaCmdType.IOT_OTAG_FILE_SIZE:
            return self.__ota_manager.file_size, "success"
        elif cmd_type == self.__hub.OtaCmdType.IOT_OTAG_CHECK_FIRMWARE:
            if self.__ota_manager.state is not self.__hub.OtaState.IOT_OTAS_FETCHED:
                return -1, "state error"
            md5sum = self.__ota_manager.md5.hexdigest()
            if md5sum == self.__ota_manager.md5sum:
                return 0, "success"
            else:
                self._ota_report_upgrade_result(self.__ota_manager.version,
                                               self.__hub.OtaReportType.IOT_OTAR_MD5_NOT_MATCH)
                return -1, "md5 error"
            pass

        return -1, "cmd type error"

    def otaIoctlString(self, cmd_type, length):
        if ((self.__ota_manager.state == self.__hub.OtaState.IOT_OTAS_INITED)
                or (self.__ota_manager.state == self.__hub.OtaState.IOT_OTAS_UNINITED)):
            return "nll", "state error"

        if cmd_type == self.__hub.OtaCmdType.IOT_OTAG_VERSION:
            if len(self.__ota_manager.version) > length:
                return "null", "version length error"
            else:
                return self.__ota_manager.version, "success"
        elif cmd_type == self.__hub.OtaCmdType.IOT_OTAG_MD5SUM:
            if len(self.__ota_manager.md5sum) > length:
                return "null", "md5sum length error"
            else:
                return self.__ota_manager.md5sum, "success"

        return "null", "cmd type error"

    def otaResetMd5(self):
        self.__ota_manager.md5 = None
        self.__ota_manager.md5 = hashlib.md5()

    def otaMd5Update(self, buf):
        if buf is None:
            self.__logger.error("buf is none")
            return -1
        if self.__ota_manager.md5 is None:
            self.__logger.error("md5 handle is uninitialized")
            return -1

        # self.__ota_manager.md5.update(buf.encode(encoding='utf-8'))
        self.__ota_manager.md5.update(buf)

    def __ota_http_deinit(self, http):
        print("__ota_http_deinit do nothing")

    def httpInit(self, host, url, offset, size, timeout_sec):
        range_format = "bytes=%d-%d"
        srange = range_format % (offset, size)

        header = {}
        header["Host"] = host
        header["Accept"] = "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        header["Accept-Encoding"] = "gzip, deflate"
        header["Range"] = srange

        self.http_manager = self.__hub.http_manage()
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
                self.__logger.error("https connect error:%d" % e.code)
                self.http_manager.err_code = e.code
                return 1
            except urllib.error.URLError as e:
                self.__logger.error("https connect error:%s" % e.reason)
                self.http_manager.err_reason = e.reason
                return 1
        else:
            try:
                self.http_manager.request = urllib.request.Request(url=url, headers=header)
                self.http_manager.handle = urllib.request.urlopen(self.http_manager.request,
                                                                  timeout=timeout_sec)
            except Exception as e:
                self.__logger.error("http connect error:%s" % str(e))
                return 1
        return 0

    def httpFetch(self, buf_len):
        if self.http_manager.handle is None:
            return None, -1
        try:
            buf = self.http_manager.handle.read(buf_len)
            return buf, len(buf)
        except Exception as e:
            self.__logger.error("http read error:%s" % str(e))
            return None, -2

    def otaReportVersion(self, version):
        if version is None or len(version) == 0:
            raise ValueError('Invalid version.')
        if len(version) < self.__ota_version_len_min or len(version) > self.__ota_version_len_max:
            raise ValueError('Invalid version length')
        if self.__ota_manager.state == self.__hub.OtaState.IOT_OTAS_UNINITED:
            raise ValueError('ota handle is uninitialized')
        report = {
            "type": "report_version",
            "report": {
                "version": version
            }
        }
        rc, mid = self.__ota_publish(report, 1)
        if rc != 0:
            self.__logger.error("__ota_publish fail")
            return 1, mid
        return 0, mid

    def otaDownloadStart(self, offset, size):
        if offset < 0 or size <= 0:
            raise ValueError('Invalid length.')
        if offset == 0:
            self.otaResetMd5()
        self.__ota_http_deinit(self.__ota_manager.http_manager)
        # 断点续传初始值不为0
        self.__ota_manager.size_fetched += offset

        rc = self.httpInit(self.__ota_manager.host, self.__ota_manager.purl, offset, size, 10000 / 1000)
        if rc != 0:
            if self.http_manager.err_code == 403:
                self._ota_report_upgrade_result(self.__ota_manager.version,
                                               self.__hub.OtaReportType.IOT_OTAR_AUTH_FAIL)
            elif self.http_manager.err_code == 404:
                self._ota_report_upgrade_result(self.__ota_manager.version,
                                               self.__hub.OtaReportType.IOT_OTAR_FILE_NOT_EXIST)
            elif self.http_manager.err_code == 408:
                self._ota_report_upgrade_result(self.__ota_manager.version,
                                               self.__hub.OtaReportType.IOT_OTAR_DOWNLOAD_TIMEOUT)
            else:
                # 其他错误判断(error.reason)
                self.__logger.error("http_init error:%d" % self.http_manager.err_code)

        return rc

    def otaFetchYield(self, buf_len):
        if self.__ota_manager.state != self.__hub.OtaState.IOT_OTAS_FETCHING:
            self.__logger.error("ota state is not fetching")
            return None, -1
        # http read
        buf, rv_len = self.httpFetch(buf_len)
        if rv_len < 0:
            if rv_len == -2:
                self._ota_report_upgrade_result(self.__ota_manager.version,
                                               self.__hub.OtaReportType.IOT_OTAR_DOWNLOAD_TIMEOUT)
            return None, -2
        else:
            if self.__ota_manager.size_fetched == 0:
                self._ota_report_progress(self.__hub.OtaProgressCode.IOT_OTAP_FETCH_PERCENTAGE_MIN,
                                         self.__ota_manager.version,
                                         self.__hub.OtaReportType.IOT_OTAR_DOWNLOAD_BEGIN)
                self.__ota_manager.report_timestamp = int(time.time())
            pass
        self.__ota_manager.size_last_fetched = rv_len
        self.__ota_manager.size_fetched += rv_len

        percent = int((self.__ota_manager.size_fetched * 100) / self.__ota_manager.file_size)
        if percent == 100:
            self._ota_report_progress(percent, self.__ota_manager.version,
                                     self.__hub.OtaReportType.IOT_OTAR_DOWNLOADING)
        else:
            timestamp = int(time.time())
            # 间隔1秒上报一次
            if (((timestamp - self.__ota_manager.report_timestamp) >= 1)
                    and (self.__ota_manager.size_last_fetched > 0)):
                self.__ota_manager.report_timestamp = timestamp
                self._ota_report_progress(percent, self.__ota_manager.version,
                                         self.__hub.OtaReportType.IOT_OTAR_DOWNLOADING)

        if self.__ota_manager.size_fetched >= self.__ota_manager.file_size:
            self.__ota_manager.state = self.__hub.OtaState.IOT_OTAS_FETCHED

        self.__ota_manager.md5.update(buf)

        return buf, rv_len


    def rrpcInit(self):
        if self.__explorer_state is not self.__hub.HubState.CONNECTED:
            raise self.__hub.StateError("current state is not CONNECTED")

        rrpc_topic_sub = self.__topic.rrpc_topic_sub_prefix + "+"
        sub_res, mid = self.subscribe(rrpc_topic_sub, 0)
        if sub_res != 0:
            self.__logger.error("topic_subscribe error:rc:%d,topic:%s" % (sub_res, rrpc_topic_sub))
            return 1
        # 判断订阅是否成功(qos0)
        return 0

    def rrpcReply(self, reply, length):
        if reply is None or length == 0:
            raise ValueError('Invalid length.')
        if self.__process_id is None:
            raise ValueError('no process id')
        topic = self.__topic.rrpc_topic_pub_prefix + self.__process_id
        rc, mid = self.publish(topic, reply, 0)
        if rc != 0:
            self.__logger.error("topic_publish error:rc:%d,topic:%s" % (rc, topic))
            return -1, mid
        return rc, mid

    def shadowInit(self):
        if self.__explorer_state is not self.__hub.HubState.CONNECTED:
            raise self.__hub.StateError("current state is not connect")

        shadow_topic_sub = self.__topic.shadow_topic_sub
        sub_res, mid = self.subscribe(shadow_topic_sub, 0)
        if sub_res != 0:
            self.__logger.error("topic_publish error:rc:%d,topic:%s" % (sub_res, shadow_topic_sub))
            return -1
        return 0

    def getShadow(self):
        topic_pub = self.__topic.shadow_topic_pub

        client_token = self.__device_file.product_id + "-" + str(self._shadow_token_num)
        self._shadow_token_num += 1

        message = {
            "type": "get",
            "clientToken": client_token
        }
        rc, mid = self.publish(topic_pub, message, 0)
        if rc != 0:
            self.__logger.error("topic_publish error:rc:%d,topic:%s" % (rc, topic_pub))
            return -1, mid
        return rc, mid
    
    def shadowJsonConstructDesireNull(self):
        client_token = self.__device_file.product_id + "-" + str(self._shadow_token_num)
        self._shadow_token_num += 1
        json_out = {
            "type": "update",
            "state": {
                "desired": None
            },
            "clientToken": client_token
        }
        return json_out

    def shadowUpdate(self, shadow_docs, length):
        if shadow_docs is None or length == 0:
            raise ValueError('Invalid length.')
        topic = self.__topic.shadow_topic_pub
        rc, mid = self.publish(topic, shadow_docs, 0)
        if rc != 0:
            self.__logger.error("topic_publish error:rc:%d,topic:%s" % (rc, topic))
            return -1, mid
        return rc, mid

    def shadowJsonConstructReport(self, *args):
        format_string = '"%s":"%s"'
        format_int = '"%s":%d'
        report_string = '{"type": "update", "state": {"reported": {'
        arg_cnt = 0

        for arg in args:
            arg_cnt += 1
            if arg.type == "int" or arg.type == "float":
                report_string += format_int % (arg.key, arg.data)
            elif arg.type == "string":
                report_string += format_string % (arg.key, arg.data)
            else:
                self.__logger.error("type not support")
                arg.data = " "
            if arg_cnt < len(args):
                report_string += ","
        pass
        report_string += '}}, "clientToken": "%s"}'

        client_token = self.__device_file.product_id + "-" + str(self._shadow_token_num)
        self._shadow_token_num += 1

        report_out = report_string % (client_token)
        json_out = json.loads(report_out)

        return json_out

    def broadcastInit(self):
        if self.__explorer_state is not self.__hub.HubState.CONNECTED:
            raise self.__hub.StateError("current state is not connect")

        broadcast_topic_sub = self.__topic.broadcast_topic_sub
        sub_res, mid = self.subscribe(broadcast_topic_sub, 0)
        if sub_res != 0:
            self.__logger.error("topic_publish error:rc:%d,topic:%s" % (sub_res, broadcast_topic_sub))
            return -1
        return 0

    def subscribeInit(self):

        if self.__explorer_state is not self.__hub.HubState.CONNECTED:
            raise self.__hub.StateError("current state is not CONNECTED")

        subscribe_topic_sub = self.__topic.template_service_topic_sub
        sub_res, mid = self.subscribe(subscribe_topic_sub, 1)
        # should deal mid
        self.__logger.debug("mid:%d" % mid)
        if sub_res != 0:
            self.__logger.error("topic_subscribe error:rc:%d,topic:%s" % (sub_res, subscribe_topic_sub))
            return 1
        return 0