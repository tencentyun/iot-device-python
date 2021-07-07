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
from hub.utils.providers import ConnClientProvider
from hub.utils.providers import TopicProvider

class Rrpc(object):
    def __init__(self, host, product_id, device_name, device_secret,
                    websocket=False, tls=True, logger=None):
        self.__provider = ConnClientProvider(host, product_id, device_name, device_secret,
                                                websocket=websocket, tls=tls, logger=logger)
        self.__protocol = self.__provider.protocol
        self.__topic = TopicProvider(product_id, device_name)
        self.__logger = logger
        self.__process_id = None
        self.__user_callback = {}

    def __assert(self, param):
        if param is None or len(param) == 0:
            raise ValueError('Invalid param.')

    def __rrpc_get_process_id(self, topic):
        pos = topic.rfind("/")
        if pos > 0:
            self.__process_id = topic[pos + 1:len(topic)]
            return 0
        else:
            self.__logger.error("cannot found process id from topic:%s" % topic)
            return -1

    def handle_rrpc(self, topic, qos, payload, userdata):
        self.__rrpc_get_process_id(topic)

        pos = topic.rfind("/")
        topic_split = topic[0:pos]
        if self.__user_callback[topic_split] is not None:
                self.__user_callback[topic_split](topic_split, qos, payload, userdata)
        else:
            self.__logger.error("no callback for topic_split %s" % topic_split)

    def rrpc_init(self, rrpc_cb):
        topic = self.__topic.rrpc_topic_sub_prefix + "/+"
        self.__user_callback[self.__topic.rrpc_topic_sub_prefix] = rrpc_cb
        

        return self.__protocol.subscribe(topic, 0)

    def rrpc_reply(self, reply):
        self.__assert(self.__process_id)
        self.__assert(reply)

        topic = self.__topic.rrpc_topic_pub_prefix + "/" + self.__process_id
        return self.__protocol.publish(topic, json.dumps(reply), 0)