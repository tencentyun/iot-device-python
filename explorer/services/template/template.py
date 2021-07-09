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

import json
from explorer.providers.providers import Providers
from hub.utils.providers import TopicProvider

class Template(object):
    def __init__(self, device_file, tls, productId, deviceName, logger=None):
        self.__logger = logger
        self.__provider = Providers(device_file, tls)
        self.__hub = self.__provider.hub

        self.__topic = TopicProvider(productId, deviceName)
        self._template_token_num = 0

        self.__template_events_list = []
        self.__template_action_list = []
        self.__template_property_list = []
        self.__template_setup_state = False

        """
        保存用户注册的回调
        """
        self.__user_callback = {}

        # data template reply
        self.__replyAck = -1

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

    def __assert(self, param):
        if param is None or len(param) == 0:
            raise ValueError('Invalid param.')

    def __build_empty_json(self, info_in, method_in):
        client_token = info_in + "-" + str(self._template_token_num)
        self._template_token_num += 1
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

    def __build_control_reply(self, token, replyPara):
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

    # 构建系统信息上报的json消息
    def __json_construct_sysinfo(self, id, info_in):
        json_token = self.__build_empty_json(id, None)
        client_token = json_token["clientToken"]
        info_out = {
            "method": "report_info",
            "clientToken": client_token,
            "params": info_in
        }

        return info_out

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

    def get_events_list(self):
        return self.__template_events_list

    def get_action_list(self):
        return self.__template_action_list

    def get_property_list(self):
        return self.__template_property_list

    def handle_template(self, topic, qos, payload, userdata):
        if topic == self.__topic.template_property_topic_sub:
            # __handle_reply回调到用户，由用户调用clearContrl()
            self.__handle_property(payload)

        """
        回调用户数据模板topic对应回调
        """
        if self.__user_callback[topic] is not None:
                self.__user_callback[topic](topic, qos, payload, userdata)
        else:
            self.__logger.error("no callback for topic %s" % topic)

    def template_reset(self):
        self._template_token_num = 0
        self.__template_events_list.clear()
        self.__template_action_list.clear()
        self.__template_property_list.clear()
        self.__template_setup_state = False
        self.__replyAck = -1

    def template_deinit(self):
        topic_list = []
        topic_list.append(self.__topic.template_property_topic_sub)
        topic_list.append(self.__topic.template_event_topic_sub)
        topic_list.append(self.__topic.template_action_topic_sub)
        return self.__hub.unsubscribe(topic_list)

    def template_init(self, callback, peopery_cb, action_cb, event_cb, service_cb):
        property_topic = self.__topic.template_property_topic_sub
        action_topic = self.__topic.template_action_topic_sub
        event_topic = self.__topic.template_event_topic_sub
        service_topic = self.__topic.template_service_topic_sub
        self.__user_callback[property_topic] = peopery_cb
        self.__user_callback[action_topic] = action_cb
        self.__user_callback[event_topic] = event_cb
        self.__user_callback[service_topic] = event_cb

        topic_list = []
        topic_list.append(property_topic)
        topic_list.append(action_topic)
        topic_list.append(event_topic)
        topic_list.append(service_topic)

        self.__hub.register_explorer_callback(topic_list, callback)

        topic_list.clear()
        topic_list.append((property_topic, 0))
        topic_list.append((action_topic, 0))
        topic_list.append((event_topic, 0))
        topic_list.append((service_topic, 1))
        return self.__hub.subscribe(topic_list, 0)

    def template_report(self, message):
        self.__assert(message)
        return self.__hub.publish(self.__topic.template_property_topic_pub, message, 0)

    def template_get_status(self, id):
        token = self.__build_empty_json(id, "get_status")
        return self.__hub.publish(self.__topic.template_property_topic_pub, token, 0)

    def template_action_reply(self, clientToken, response, replyPara):
        self.__assert(clientToken)
        self.__assert(response)
        json_out = self.__build_action_reply(clientToken, response, replyPara)
        return self.__hub.publish(self.__topic.template_action_topic_pub, json_out, 0)

    # IOT_Template_ClearControl
    def template_clear_control(self, clientToken):
        self.__assert(clientToken)
        message = {
            "method": "clear_control",
            "clientToken": clientToken
        }
        return self.__hub.publish(self.__topic.template_property_topic_pub, message, 0)

    def template_control_reply(self, replyPara):
        json_out = self.__build_control_reply(self.__topic.control_clientToken, replyPara)
        return self.__hub.publish(self.__topic.template_property_topic_pub, json_out, 0)

    def template_report_sys_info(self, pid, sysInfo):
        self.__assert(sysInfo)

        json_out = self.__json_construct_sysinfo(pid, sysInfo)
        return self.__hub.publish(self.__topic.template_property_topic_pub, json_out, 0)

    def template_json_construct_report_array(self, pid, payload):
        self.__assert(pid)
        self.__assert(payload)

        json_token = self.__build_empty_json(pid, None)
        client_token = json_token["clientToken"]
        json_out = {
            "method": "report",
            "clientToken": client_token,
            "params": payload
        }

        return json_out

    def template_event_post(self, pid, message):
        self.__assert(pid)
        self.__assert(message)

        json_token = self.__build_empty_json(pid, None)
        client_token = json_token["clientToken"]
        events = message["events"]
        json_out = {
            "method": "events_post",
            "clientToken": client_token,
            "events": events
        }
        return self.__hub.publish(self.__topic.template_event_topic_pub, json_out, 1)

    def template_setup(self, config_file=None):
        if self.__template_setup_state:
            return 0
        try:
            with open(config_file, encoding='utf-8') as f:
                cfg = json.load(f)
                index = 0
                while index < len(cfg["events"]):
                    # 解析events json
                    params = cfg["events"][index]["params"]

                    p_event = self.template_event()

                    p_event.event_name = cfg["events"][index]["id"]
                    p_event.type = cfg["events"][index]["type"]
                    p_event.timestamp = 0
                    p_event.eventDataNum = len(params)

                    i = 0
                    while i < p_event.eventDataNum:
                        event_prop = self.template_property()
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

                    self.__template_events_list.append(p_event)
                    index += 1

                index = 0
                while index < len(cfg["actions"]):
                    # 解析actions json
                    inputs = cfg["actions"][index]["input"]
                    outputs = cfg["actions"][index]["output"]

                    p_action = self.template_action()
                    p_action.action_id = cfg["actions"][index]["id"]
                    p_action.input_num = len(inputs)
                    p_action.output_num = len(outputs)
                    p_action.timestamp = 0

                    i = 0
                    while i < p_action.input_num:
                        action_prop = self.template_property()
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
                        action_prop = self.template_property()
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

                    self.__template_action_list.append(p_action)
                    index += 1
                pass

                index = 0
                while index < len(cfg["properties"]):
                    # 解析properties json
                    p_prop = self.template_property()
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

                    self.__template_property_list.append(p_prop)
                    index += 1
                pass

        except Exception as e:
            self.__logger.error("config file open error:" + str(e))
            return 2
        self.__template_setup_state = True
        return 0
     