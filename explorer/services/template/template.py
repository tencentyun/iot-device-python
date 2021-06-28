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

class Template(object):
    def __init__(self, hub_handle, logger=None):
        self.__logger = logger
        self.__hub_handle = hub_handle
        self._template_token_num = 0

    def __assert(self, param):
        if param is None or len(param) == 0:
            raise ValueError('Invalid param.')

    def __build_empty_json(self, info_in, method_in):
        if info_in is None or len(info_in) == 0:
            raise ValueError('Invalid Parameter.')
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

    def template_init(self, property_topic, action_topic, event_topic, callback):
        topic_list = []
        topic_list.append(property_topic)
        topic_list.append(action_topic)
        topic_list.append(event_topic)
        self.__hub_handle.register_explorer_callback(topic_list, callback)

        topic_list.clear()
        topic_list.append((property_topic, 0))
        topic_list.append((action_topic, 0))
        topic_list.append((event_topic, 0))
        return self.__hub_handle.subscribe(topic_list, 0)

    def template_report(self, topic, qos, message):
        if message is None or len(message) == 0:
            raise ValueError('Invalid message.')
        return self.__hub_handle.publish(topic, message, qos)

    def template_get_status(self, topic, id):
        token = self.__build_empty_json(id, "get_status")
        return self.__hub_handle.publish(topic, token, 0)

    def template_action_reply(self, topic, qos, clientToken, response, replyPara):
        self.__assert(topic)
        self.__assert(clientToken)
        self.__assert(response)
        json_out = self.__build_action_reply(clientToken, response, replyPara)
        rc, mid = self.__hub_handle.publish(topic, json_out, qos)
        # should deal mid
        self.__logger.debug("mid:%d" % mid)
        if rc != 0:
            self.__logger.error("topic_publish error:rc:%d,topic:%s" % (rc, template_topic_pub))
            return 2
        else:
            return 0
        pass