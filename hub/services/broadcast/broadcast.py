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

class Broadcast(object):
    def __init__(self, host, product_id, device_name, device_secret,
                    websocket=False, tls=True, logger=None):
        self.__provider = ConnClientProvider(host, product_id, device_name, device_secret,
                                                websocket=websocket, tls=tls, logger=logger)
        self.__protocol = self.__provider.protocol
        self.__topic = TopicProvider(product_id, device_name)
        self.__logger = logger
        self.__user_callback = {}

    def __assert(self, param):
        if param is None or len(param) == 0:
            raise ValueError('Invalid param.')

    def handle_broadcast(self, topic, qos, payload, userdata):
        if self.__user_callback[topic] is not None:
                self.__user_callback[topic](topic, qos, payload, userdata)
        else:
            self.__logger.error("no callback for topic %s" % topic)

    def broadcast_init(self, broadcast_cb):
        self.__user_callback[self.__topic.broadcast_topic_sub] = broadcast_cb
        return self.__protocol.subscribe(self.__topic.broadcast_topic_sub, 0)