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
# import re
import paho.mqtt.client as mqtt
from enum import Enum
from enum import IntEnum
# from paho.mqtt.client import MQTTMessage
from Crypto.Cipher import AES
from hub.hub import QcloudHub

class QcloudExplorer(object):

    def __init__(self, device_file, tls=True, userdata=None):
        self.__hub = QcloudHub(device_file, tls)
        # 用户回调注册到hub层
        self.__register_hub_event_callback()

        self.__logger = self.__hub._logger
        self.__PahoLog = logging.getLogger("Paho")
        self.__PahoLog.setLevel(logging.DEBUG)
        self.__device_file = self.__hub.DeviceInfo(device_file, self.__logger)
        self.__topic_info = None

        # set state initialized
        self.__explorer_state = self.__hub.HubState.INITIALIZED

        # 用户传参
        self.__userdata = userdata

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
        self.__on_subscribe_service_post = None

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

    def dynregDevice(self, timeout=10):
        """
        dynamic device to tencent cloud
        :param timeout: http/https timeout
        :return: (code, msg): code 0 is success, msg is psk. Other is failed.
        """
        return self.__hub.dynregDevice(timeout)

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
                    user_callback(payload, self.__userdata)
                    return 0
                else:
                    self.__logger.warring('topic not registed')
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
        self.__logger.debug("gateway payload:%s" % message)
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
        self.__logger.debug("reply payload:%s" % payload)

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
                rc, mid = self.publish(topic_pub, message, 0)
                # should deal mid
                self.__logger.debug("mid:%d" % mid)
                if rc != 0:
                    self.__logger.error("topic_publish error:rc:%d,topic:%s" % (rc, topic_pub))
            else:
                self.__replyAck = replyAck
                self.__logger.debug("replyAck:%d" % replyAck)

        else:
            self.__replyAck = replyAck
        pass

    def __handle_control(self, payload):
        clientToken = payload["clientToken"]
        params = payload["params"]
        self.__topic_info.control_clientToken = clientToken
        # 调用用户回调,回调中应调用template_control_reply()
        self.__on_template_prop_changed(params, self.__userdata)

    def __handle_action(self, payload):
        """
        clientToken = payload["clientToken"]
        actionId = payload["actionId"]
        timestamp = payload["timestamp"]
        params = payload["params"]
        """

        # 调用用户回调,回调中应调用IOT_ACTION_REPLY()
        # self.__on_template_action(clientToken, actionId, timestamp, params, self.__user_data)
        self.__on_template_action(payload, self.__userdata)
        pass

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

    def protocolInit(self, domain=None, useWebsocket=False):
        return self.__hub.protocolInit(domain, useWebsocket)

    # start thread to connect and loop
    def connect(self):
        return self.__hub.connect()

    def disconnect(self):
        self.__hub.disconnect()

    # user callback
    def __user_thread_on_connect_callback(self, value):
        # client, user_data, session_flag, rc = value
        session_flag, rc = value
        if self.__user_on_connect is not None:
            try:
                self.__user_on_connect(session_flag['session present'], rc, self.__userdata)
            except Exception as e:
                self.__logger.error("on_connect process raise exception:%r" % e)
        pass

    def __user_thread_on_disconnect_callback(self, value):
        self.__user_on_disconnect(value, self.__userdata)
        pass

    def __user_thread_on_publish_callback(self, value):
        self.__user_on_publish(value, self.__userdata)
        pass

    def __user_thread_on_subscribe_callback(self, value):
        qos, mid = value
        self.__user_on_subscribe(qos, mid, self.__userdata)
        pass

    def __user_thread_on_unsubscribe_callback(self, value):
        self.__user_on_unsubscribe(value, self.__userdata)
        pass

    #云端下发指令
    def __user_thread_on_message_callback(self, value):
        # client, user_data, message = value
        message = value
        topic = message.topic
        qos = message.qos
        mid = message.mid
        payload = json.loads(message.payload.decode('utf-8'))

        # self.__logger.info("__user_thread_on_message_callback,topic:%s,payload:%s,mid:%d" % (topic, payload, mid))

        if topic == self.__topic_info.template_property_topic_sub:
            method = payload["method"]
            if method == "control":
                self.__handle_control(payload)
            else:
                self.__handle_reply(method, payload)

        elif topic == self.__topic_info.template_event_topic_sub:
            try:
                self.__on_template_event_post(payload, self.__userdata)
            except Exception as e:
                self.__logger.error("on_template_event_post raise exception:%s" % e)
            pass

        elif topic == self.__topic_info.template_action_topic_sub:
            method = payload["method"]

            if method != "action":
                self.__logger.error("method error:%s" % method)
            else:
                self.__handle_action(payload)
            pass

        elif topic == self.__topic_info.template_service_topic_sub:
            self.__logger.info("--------Reserved: template service topic")

            try:
                self.__on_subscribe_service_post(payload, self.__userdata)
            except Exception as e:
                self.__logger.error("__on_subscribe_service_post raise exception:%s" % e)
            pass

        elif topic == self.__topic_info.template_raw_topic_sub:
            self.__logger.info("Reserved: template raw topic")

        elif topic in self.__user_topics and self.__user_on_message is not None:
            try:
                self.__user_on_message(topic, payload, qos, self.__userdata)
            except Exception as e:
                self.__logger.error("user_on_message process raise exception:%s" % e)
            pass
        elif topic == self.__topic_info.template_topic_sub:
            self.__user_on_message(topic, payload, qos, self.__userdata)
        elif topic == self.__topic_info.sys_topic_sub:
            self.__user_on_message(topic, payload, qos, self.__userdata)
        elif topic == self.__topic_info.gateway_topic_sub:
            self.__handle_gateway(payload)
        elif topic == self.__topic_info.ota_update_topic_sub:
            self.__handle_ota(payload)
        elif self.__topic_info.rrpc_topic_sub_prefix in topic:
            self.__handle_rrpc(topic, payload)
        elif self.__topic_info.shadow_topic_sub in topic:
            self.__user_on_message(topic, payload, qos, self.__userdata)
        elif self.__topic_info.broadcast_topic_sub in topic:
            self.__user_on_message(topic, payload, qos, self.__userdata)
        else:
            rc = self.__handle_nonStandard_topic(topic, payload)
            if rc != 0:
                self.__logger.error("unknow topic:%s" % topic)
        pass

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

    def templateSetup(self, config_file=None):
        """
        if self.__explorer_state is not QcloudExplorer.HubState.INITIALIZED:
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

                    p_event = self.__hub.template_event()

                    p_event.event_name = cfg["events"][index]["id"]
                    p_event.type = cfg["events"][index]["type"]
                    p_event.timestamp = 0
                    p_event.eventDataNum = len(params)

                    i = 0
                    while i < p_event.eventDataNum:
                        event_prop = self.__hub.template_property()
                        event_prop.key = params[i]["id"]
                        event_prop.type = params[i]["define"]["type"]

                        if event_prop.type == "int" or event_prop.type == "bool":
                            event_prop.data = 0
                        elif event_prop.type == "float":
                            event_prop.data = 0.0
                        elif event_prop.type == "string":
                            event_prop.data = ''
                        else:
                            self.__logger.error("type not support")
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

                    p_action = self.__hub.template_action()
                    p_action.action_id = cfg["actions"][index]["id"]
                    p_action.input_num = len(inputs)
                    p_action.output_num = len(outputs)
                    p_action.timestamp = 0

                    i = 0
                    while i < p_action.input_num:
                        action_prop = self.__hub.template_property()
                        action_prop.key = inputs[i]["id"]
                        action_prop.type = inputs[i]["define"]["type"]

                        if action_prop.type == "int" or action_prop.type == "bool":
                            action_prop.data = 0
                        elif action_prop.type == "float":
                            action_prop.data = 0.0
                        elif action_prop.type == "string":
                            action_prop.data = ''
                        else:
                            self.__logger.error("type not support")
                            action_prop.data = None
                        p_action.action_input_append(action_prop)
                        i += 1
                    pass

                    i = 0
                    while i < p_action.output_num:
                        action_prop = self.__hub.template_property()
                        action_prop.key = outputs[i]["id"]
                        action_prop.type = outputs[i]["define"]["type"]

                        if action_prop.type == "int" or action_prop.type == "bool":
                            action_prop.data = 0
                        elif action_prop.type == "float":
                            action_prop.data = 0.0
                        elif action_prop.type == "string":
                            action_prop.data = ''
                        else:
                            self.__logger.error("type not support")
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
                    p_prop = self.__hub.template_property()
                    p_prop.key = cfg["properties"][index]["id"]
                    p_prop.type = cfg["properties"][index]["define"]["type"]

                    if p_prop.type == "int" or p_prop.type == "bool" or p_prop.type == "enum":
                        p_prop.data = 0
                    elif p_prop.type == "float":
                        p_prop.data = 0.0
                    elif p_prop.type == "string":
                        p_prop.data = ''
                    else:
                        self.__logger.error("type not support")
                        p_prop.data = None

                    self.template_property_list.append(p_prop)
                    index += 1
                pass

                '''
                for prop in self.template_property_list:
                    print("key:%s" % (prop.key))
                '''

        except Exception as e:
            self.__logger.error("config file open error:" + str(e))
            return 2
        self.__template_setup_state = True
        return 0

    # 暂定传入json格式
    def templateEventPost(self, message):
        if self.__explorer_state is not self.__hub.HubState.CONNECTED:
            raise self.__hub.StateError("current state is not CONNECTED")
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
        rc, mid = self.publish(template_topic_pub, json_out, 1)
        # should deal mid
        self.__logger.debug("mid:%d" % mid)
        if rc != 0:
            return 2
        else:
            return 0
        pass

    def __template_event_init(self):
        template_topic_sub = self.__topic_info.template_event_topic_sub
        sub_res, mid = self.subscribe(template_topic_sub, 0)
        # should deal mid
        self.__logger.debug("mid:%d" % mid)
        if sub_res != 0:
            self.__logger.error("topic_subscribe error:rc:%d,topic:%s" % (sub_res, template_topic_sub))
            return 1
        else:
            return 0
        pass

    def __template_action_init(self):
        template_topic_sub = self.__topic_info.template_action_topic_sub
        sub_res, mid = self.subscribe(template_topic_sub, 0)
        # should deal mid
        self.__logger.debug("mid:%d" % mid)
        if sub_res != 0:
            self.__logger.error("topic_subscribe error:rc:%d,topic:%s" % (sub_res, template_topic_sub))
            return 1
        else:
            return 0
        pass


    # 暂定传入的message为json格式(json/属性列表?)
    # 传入json格式时该函数应改为内部函数,由template_report()调用
    def templateJsonConstructReportArray(self, payload):
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

    def templateReportSysInfo(self, sysinfo):
        if self.__explorer_state is not self.__hub.HubState.CONNECTED:
            raise self.__hub.StateError("current state is not CONNECTED")
        if sysinfo is None or len(sysinfo) == 0:
            raise ValueError('Invalid sysinfo.')

        template_topic_pub = self.__topic_info.template_property_topic_pub
        rc, json_out = self.__json_construct_sysinfo(sysinfo)
        if rc != 0:
            self.__logger.error("__json_construct_sysinfo error:rc:%d,topic:%s" % (rc, template_topic_pub))
            return 1
        rc, mid = self.publish(template_topic_pub, json_out, 0)
        # should deal mid
        self.__logger.debug("mid:%d" % mid)
        if rc != 0:
            self.__logger.error("topic_publish error:rc:%d,topic:%s" % (rc, template_topic_pub))
            return 2
        return 0

    def templateControlReply(self, replyPara):
        if self.__explorer_state is not self.__hub.HubState.CONNECTED:
            raise self.__hub.StateError("current state is not CONNECTED")

        template_topic_pub = self.__topic_info.template_property_topic_pub
        json_out = self.__build_control_reply(replyPara)
        rc, mid = self.publish(template_topic_pub, json_out, 0)
        # should deal mid
        self.__logger.debug("mid:%d" % mid)
        if rc != 0:
            self.__logger.error("topic_publish error:rc:%d,topic:%s" % (rc, template_topic_pub))
            return 2
        else:
            return 0
        pass

    def templateActionReply(self, clientToken, response, replyPara):
        if self.__explorer_state is not self.__hub.HubState.CONNECTED:
            raise self.__hub.StateError("current state is not CONNECTED")

        template_topic_pub = self.__topic_info.template_action_topic_pub
        json_out = self.__build_action_reply(clientToken, response, replyPara)
        rc, mid = self.publish(template_topic_pub, json_out, 0)
        # should deal mid
        self.__logger.debug("mid:%d" % mid)
        if rc != 0:
            self.__logger.error("topic_publish error:rc:%d,topic:%s" % (rc, template_topic_pub))
            return 2
        else:
            return 0
        pass

    # 回调中处理IOT_Template_ClearControl
    def templateGetStatus(self):
        if self.__explorer_state is not self.__hub.HubState.CONNECTED:
            raise self.__hub.StateError("current state is not CONNECTED")

        template_topic_pub = self.__topic_info.template_property_topic_pub

        token = self.__build_empty_json(self.__device_file.product_id, "get_status")
        rc, mid = self.publish(template_topic_pub, token, 0)
        # should deal mid
        self.__logger.debug("mid:%d" % mid)
        if rc != 0:
            self.__logger.error("topic_publish error:rc:%d,topic:%s" % (rc, template_topic_pub))
            return 2
        else:
            return 0
        pass

    def templateReport(self, message):
        if self.__explorer_state is not self.__hub.HubState.CONNECTED:
            raise self.__hub.StateError("current state is not CONNECTED")
        if message is None or len(message) == 0:
            raise ValueError('Invalid message.')
        # 判断下行topic是否订阅
        if self.__is_subscribed_property_topic is False:
            template_topic_sub = self.__topic_info.template_property_topic_sub
            sub_res, mid = self.subscribe(template_topic_sub, 0)
            # should deal mid
            self.__logger.debug("mid:%d" % mid)
            if sub_res != 0:
                self.__logger.error("topic_subscribe error:rc:%d,topic:%s" % (sub_res, template_topic_sub))
                return 1
            self.__is_subscribed_property_topic = True
            pass

        template_topic_pub = self.__topic_info.template_property_topic_pub
        rc, mid = self.publish(template_topic_pub, message, 0)
        if rc != 0:
            self.__logger.error("topic_publish error:rc:%d,topic:%s" % (rc, template_topic_pub))
            return 2
        else:
            return 0
        pass

    def templateInit(self):
        if self.__explorer_state is not self.__hub.HubState.CONNECTED:
            raise self.__hub.StateError("current state is not CONNECTED")

        template_topic_sub = self.__topic_info.template_property_topic_sub
        sub_res, mid = self.subscribe(template_topic_sub, 0)
        # should deal mid
        self.__logger.debug("mid:%d" % mid)
        if sub_res != 0:
            self.__logger.error("topic_subscribe error:rc:%d,topic:%s" % (sub_res, template_topic_sub))
            return 1

        self.__is_subscribed_property_topic = True
        rc = self.__template_event_init()
        if rc != 0:
            return 1
        rc = self.__template_action_init()
        if rc != 0:
            return 1
        return 0

    def clearControl(self):
        topic_pub = self.__topic_info.template_property_topic_pub
        clientToken = self.__topic_info.control_clientToken

        # IOT_Template_ClearControl
        message = {
            "method": "clear_control",
            "clientToken": clientToken
        }
        rc, mid = self.publish(topic_pub, message, 0)
        # should deal mid
        self.__logger.debug("mid:%d" % mid)
        if rc != 0:
            self.__logger.error("topic_publish error:rc:%d,topic:%s" % (rc, topic_pub))
        pass

    def templateDeinit(self):
        if self.__explorer_state is not self.__hub.HubState.CONNECTED:
            raise self.__hub.StateError("current state is not CONNECTED")


        template_topic_sub = self.__topic_info.template_property_topic_sub
        sub_res, mid = self.unsubscribe(template_topic_sub)
        # should deal mid
        self.__logger.debug("mid:%d" % mid)
        if sub_res != 0:
            self.__logger.error("topic_subscribe error:rc:%d,topic:%s" % (sub_res, template_topic_sub))
            return 1

        self.__is_subscribed_property_topic = False

        
        template_topic_sub = self.__topic_info.template_event_topic_sub
        sub_res, mid = self.unsubscribe(template_topic_sub)
        # should deal mid
        self.__logger.debug("mid:%d" % mid)
        if sub_res != 0:
            self.__logger.error("topic_subscribe error:rc:%d,topic:%s" % (sub_res, template_topic_sub))
            return 1

        template_topic_sub = self.__topic_info.template_action_topic_sub
        sub_res, mid = self.unsubscribe(template_topic_sub)
        # should deal mid
        self.__logger.debug("mid:%d" % mid)
        if sub_res != 0:
            self.__logger.error("topic_subscribe error:rc:%d,topic:%s" % (sub_res, template_topic_sub))
            return 1
        else:
            return 0
        pass

    # gateway
    # 网关子设备数据模板回调注册
    def registerUserPropertyCallback(self, product_id, callback):
        with self.__register_property_cb_lock:
            self.__on_gateway_subdev_prop_cb_dict[product_id] = callback

    def registerUserActionCallback(self, product_id, callback):
        with self.__register_action_cb_lock:
            self.__on_gateway_subdev_action_cb_dict[product_id] = callback

    def registerUserEventCallback(self, product_id, callback):
        with self.__register_event_cb_lock:
            self.__on_gateway_subdev_event_cb_dict[product_id] = callback

    def gatewaySubdevSubscribe(self, product_id, topic_prop, topic_action, topic_event):
        # 网关子设备数据模板
        sub_res, mid = self.subscribe(topic_prop, 0)
        # should deal mid
        self.__logger.debug("mid:%d" % mid)
        if sub_res != 0:
            self.__logger.error("topic_subscribe error:rc:%d,topic:%s" % (sub_res, topic_prop))
            return 1
        else:
            # 将product id和topic对加到列表保存
            with self.__gateway_subdev_append_lock:
                for topic, qos in topic_prop:
                    tup = (product_id, topic)
                    self.__gateway_subdev_property_topic_list.append(tup)

        sub_res, mid = self.subscribe(topic_action, 0)
        # should deal mid
        self.__logger.debug("mid:%d" % mid)
        if sub_res != 0:
            self.__logger.error("topic_subscribe error:rc:%d,topic:%s" % (sub_res, topic_action))
            return 1
        else:
            # 将product id和topic对加到列表保存
            with self.__gateway_subdev_append_lock:
                for topic, qos in topic_action:
                    tup = (product_id, topic)
                    self.__gateway_subdev_action_topic_list.append(tup)

        sub_res, mid = self.subscribe(topic_event, 0)
        # should deal mid
        self.__logger.debug("mid:%d" % mid)
        if sub_res != 0:
            self.__logger.error("topic_subscribe error:rc:%d,topic:%s" % (sub_res, topic_event))
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

            # 计算二进制
            sign = hmac.new(bind_secret.encode("utf-8"), sign_content.encode("utf-8"), hashlib.sha1).digest()
            sign_base64 = base64.b64encode(sign).decode('utf-8')

            self.__logger.debug('sign base64 {}'.format(sign_base64))
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

    def gatewayInit(self):
        if self.__explorer_state is not self.__hub.HubState.CONNECTED:
            raise self.__hub.StateError("current state is not CONNECTED")

        # 解析网关子设备信息,并添加到list
        json_data = self.__device_file.json_data
        subdev_num = json_data['subDev']['subdev_num']
        subdev_list = json_data['subDev']['subdev_list']

        index = 0
        while index < subdev_num:
            p_subdev = self.__hub.gateway_subdev()
            p_subdev.sub_productId = subdev_list[index]['sub_productId']
            p_subdev.sub_devName = subdev_list[index]['sub_devName']
            p_subdev.session_status = self.__hub.SessionState.SUBDEV_SEESION_STATUS_INIT

            self.gateway_subdev_list.append(p_subdev)
            index += 1

        gateway_topic_sub = self.__topic_info.gateway_topic_sub
        sub_res, mid = self.subscribe(gateway_topic_sub, 0)
        # should deal mid
        self.__logger.debug("mid:%d" % mid)
        if sub_res != 0:
            self.__logger.error("topic_subscribe error:rc:%d,topic:%s" % (sub_res, gateway_topic_sub))
            return 1
        return 0

    def gatewaySubdevOnline(self, sub_productId, sub_devName):
        if sub_productId is None or len(sub_productId) == 0:
            raise ValueError('Invalid sub_productId.')
        if sub_devName is None or len(sub_devName) == 0:
            raise ValueError('Invalid sub_devName.')

        # 保存当前会话的设备client_id
        # self.__gateway_session_client_id = sub_productId + "/" + sub_devName
        client_id = sub_productId + "/" + sub_devName

        gateway_topic_pub = self.__topic_info.gateway_topic_pub
        payload = self.__build_session_payload("online", sub_productId, sub_devName, None)

        rc, mid = self.publish(gateway_topic_pub, payload, 0)
        if rc != 0:
            self.__logger.error("topic_publish error:rc:%d,topic:%s" % (rc, gateway_topic_pub))
            return 2

        rc = self.__wait_for_session_reply(client_id, "online")
        if rc == 0:
            self.__logger.debug("client:%s %s success" % (client_id, "online"))
        else:
            self.__logger.debug("client:%s %s fail" % (client_id, "online"))

        return rc

    def gatewaySubdevOffline(self, sub_productId, sub_devName):
        if sub_productId is None or len(sub_productId) == 0:
            raise ValueError('Invalid sub_productId.')
        if sub_devName is None or len(sub_devName) == 0:
            raise ValueError('Invalid sub_devName.')

        # 保存当前会话的设备client_id
        # self.__gateway_session_client_id = sub_productId + "/" + sub_devName
        client_id = sub_productId + "/" + sub_devName

        gateway_topic_pub = self.__topic_info.gateway_topic_pub
        payload = self.__build_session_payload("offline", sub_productId, sub_devName, None)

        rc, mid = self.publish(gateway_topic_pub, payload, 0)
        if rc != 0:
            self.__logger.error("topic_publish error:rc:%d,topic:%s" % (rc, gateway_topic_pub))
            return 2

        rc = self.__wait_for_session_reply(client_id, "offline")
        if rc == 0:
            self.__logger.debug("client:%s %s success" % (client_id, "offline"))
        else:
            self.__logger.debug("client:%s %s fail" % (client_id, "offline"))

        return rc

    def gatewaySubdevBind(self, sub_productId, sub_devName, sub_secret):
        if sub_productId is None or len(sub_productId) == 0:
            raise ValueError('Invalid sub_productId.')
        if sub_devName is None or len(sub_devName) == 0:
            raise ValueError('Invalid sub_devName.')

        if sub_secret is None or len(sub_secret) == 0:
            raise ValueError('Invalid sub_secret.')

        client_id = sub_productId + "/" + sub_devName

        gateway_topic_pub = self.__topic_info.gateway_topic_pub
        payload = self.__build_session_payload("bind", sub_productId, sub_devName, sub_secret)

        rc, mid = self.publish(gateway_topic_pub, payload, 0)
        if rc != 0:
            self.__logger.error("topic_publish error:rc:%d,topic:%s" % (rc, gateway_topic_pub))
            return 2

        rc = self.__wait_for_session_reply(client_id, "bind")
        if rc == 0:
            self.__logger.debug("client:%s %s success" % (client_id, "bind"))
        else:
            self.__logger.debug("client:%s %s fail" % (client_id, "bind"))

        return rc
    
    def gatewaySubdevUnbind(self, sub_productId, sub_devName, sub_secret):
        if sub_productId is None or len(sub_productId) == 0:
            raise ValueError('Invalid sub_productId.')
        if sub_devName is None or len(sub_devName) == 0:
            raise ValueError('Invalid sub_devName.')

        client_id = sub_productId + "/" + sub_devName

        gateway_topic_pub = self.__topic_info.gateway_topic_pub
        payload = self.__build_session_payload("unbind", sub_productId, sub_devName, None)

        rc, mid = self.publish(gateway_topic_pub, payload, 0)
        if rc != 0:
            self.__logger.error("topic_publish error:rc:%d,topic:%s" % (rc, gateway_topic_pub))
            return 2

        rc = self.__wait_for_session_reply(client_id, "unbind")
        if rc == 0:
            self.__logger.debug("client:%s %s success" % (client_id, "unbind"))
        else:
            self.__logger.debug("client:%s %s fail" % (client_id, "unbind"))

        return rc

    # ota
    def __ota_publish(self, message, qos):
        topic = self.__topic_info.ota_report_topic_pub
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

        ota_topic_sub = self.__topic_info.ota_update_topic_sub
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

        rrpc_topic_sub = self.__topic_info.rrpc_topic_sub_prefix + "+"
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
        topic = self.__topic_info.rrpc_topic_pub_prefix + self.__process_id
        rc, mid = self.publish(topic, reply, 0)
        if rc != 0:
            self.__logger.error("topic_publish error:rc:%d,topic:%s" % (rc, topic))
            return -1, mid
        return rc, mid

    def shadowInit(self):
        if self.__explorer_state is not self.__hub.HubState.CONNECTED:
            raise self.__hub.StateError("current state is not connect")

        shadow_topic_sub = self.__topic_info.shadow_topic_sub
        sub_res, mid = self.subscribe(shadow_topic_sub, 0)
        if sub_res != 0:
            self.__logger.error("topic_publish error:rc:%d,topic:%s" % (sub_res, shadow_topic_sub))
            return -1
        return 0

    def getShadow(self):
        topic_pub = self.__topic_info.shadow_topic_pub

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
        topic = self.__topic_info.shadow_topic_pub
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

        broadcast_topic_sub = self.__topic_info.broadcast_topic_sub
        sub_res, mid = self.subscribe(broadcast_topic_sub, 0)
        if sub_res != 0:
            self.__logger.error("topic_publish error:rc:%d,topic:%s" % (sub_res, broadcast_topic_sub))
            return -1
        return 0

    def subscribeInit(self):

        if self.__explorer_state is not self.__hub.HubState.CONNECTED:
            raise self.__hub.StateError("current state is not CONNECTED")

        subscribe_topic_sub = self.__topic_info.template_service_topic_sub
        sub_res, mid = self.subscribe(subscribe_topic_sub, 1)
        # should deal mid
        self.__logger.debug("mid:%d" % mid)
        if sub_res != 0:
            self.__logger.error("topic_subscribe error:rc:%d,topic:%s" % (sub_res, subscribe_topic_sub))
            return 1
        return 0