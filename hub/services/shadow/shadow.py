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
from utils.providers import ConnClientProvider
from utils.providers import TopicProvider

class Shadow(object):
    def __init__(self, host, product_id, device_name, device_secret,
                    websocket=False, tls=True, logger=None):
        self.__provider = ConnClientProvider(host, product_id, device_name, device_secret,
                                                websocket=websocket, tls=tls, logger=logger)
        self.__protocol = self.__provider.protocol
        self.__topic = TopicProvider(product_id, device_name)
        self.__logger = logger
        self.__shadow_token_num = 0
        self.__user_callback = {}

    def __assert(self, param):
        if param is None or len(param) == 0:
            raise ValueError('Invalid param.')

    def handle_shadow(self, topic, qos, payload, userdata):
        """
        回调用户
        """
        if self.__user_callback[topic] is not None:
                self.__user_callback[topic](topic, qos, payload, userdata)
        else:
            self.__logger.error("no callback for topic %s" % topic)

    def shadow_init(self, shadow_cb):
        self.__user_callback[self.__topic.shadow_topic_sub] = shadow_cb
        return self.__protocol.subscribe(self.__topic.shadow_topic_sub, 0)

    def get_shadow(self, product_id):
        self.__assert(product_id)

        client_token = product_id + "-" + str(self.__shadow_token_num)
        self.__shadow_token_num += 1

        message = {
            "type": "get",
            "clientToken": client_token
        }
        return self.__protocol.publish(self.__topic.shadow_topic_pub, json.dumps(message), 0)

    def shadow_json_construct_desire_null(self, product_id):
        self.__assert(product_id)
        client_token = product_id + "-" + str(self.__shadow_token_num)
        self.__shadow_token_num += 1
        json_out = {
            "type": "update",
            "state": {
                "desired": None
            },
            "clientToken": client_token
        }
        return json_out

    def shadow_update(self, shadow_docs):
        self.__assert(shadow_docs)

        return self.__protocol.publish(self.__topic.shadow_topic_pub,json.dumps(shadow_docs), 0)

    def shadow_json_construct_report(self, product_id, *args):
        self.__assert(product_id)

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

        client_token = product_id + "-" + str(self.__shadow_token_num)
        self.__shadow_token_num += 1

        report_out = report_string % (client_token)
        json_out = json.loads(report_out)

        return json_out