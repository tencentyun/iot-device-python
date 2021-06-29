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

class Template(object):
    def __init__(self, device_file, tls, logger=None):
        self.__logger = logger
        self.__provider = Providers(device_file, tls)
        self.__hub = self.__provider.hub
        self._template_token_num = 0

        self.__template_events_list = []
        self.__template_action_list = []
        self.__template_property_list = []
        self.__template_setup_state = False

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

    def get_events_list(self):
        return self.__template_events_list

    def get_action_list(self):
        return self.__template_action_list

    def get_property_list(self):
        return self.__template_property_list

    def template_deinit(self, topic):
        self.__assert(topic)
        return self.__hub.unsubscribe(topic)

    def template_init(self, property_topic, action_topic, event_topic, callback):
        topic_list = []
        topic_list.append(property_topic)
        topic_list.append(action_topic)
        topic_list.append(event_topic)
        self.__hub.register_explorer_callback(topic_list, callback)

        topic_list.clear()
        topic_list.append((property_topic, 0))
        topic_list.append((action_topic, 0))
        topic_list.append((event_topic, 0))
        return self.__hub.subscribe(topic_list, 0)

    def template_report(self, topic, qos, message):
        if message is None or len(message) == 0:
            raise ValueError('Invalid message.')
        return self.__hub.publish(topic, message, qos)

    def template_get_status(self, topic, id):
        token = self.__build_empty_json(id, "get_status")
        return self.__hub.publish(topic, token, 0)

    def template_action_reply(self, topic, qos, clientToken, response, replyPara):
        self.__assert(topic)
        self.__assert(clientToken)
        self.__assert(response)
        json_out = self.__build_action_reply(clientToken, response, replyPara)
        return self.__hub.publish(topic, json_out, qos)

    # IOT_Template_ClearControl
    def template_clear_control(self, topic, qos, clientToken):
        self.__assert(topic)
        self.__assert(clientToken)
        message = {
            "method": "clear_control",
            "clientToken": clientToken
        }
        return self.__hub.publish(topic, message, qos)

    def template_control_reply(self, topic, qos, token, replyPara):
        self.__assert(topic)
        # self.__assert(replyPara)
        json_out = self.__build_control_reply(token, replyPara)
        return self.__hub.publish(topic, json_out, qos)

    def template_report_sys_info(self, topic, qos, pid, sysInfo):
        self.__assert(topic)
        self.__assert(sysInfo)

        json_out = self.__json_construct_sysinfo(pid, sysInfo)
        return self.__hub.publish(topic, json_out, qos)

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

    def template_event_post(self, topic, qos, pid, message):
        self.__assert(topic)
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
        return self.__hub.publish(topic, json_out, qos)

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

                    self.__template_events_list.append(p_event)
                    index += 1

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

                    self.__template_action_list.append(p_action)
                    index += 1
                pass

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

                    self.__template_property_list.append(p_prop)
                    index += 1
                pass

        except Exception as e:
            self.__logger.error("config file open error:" + str(e))
            return 2
        self.__template_setup_state = True
        return 0
     