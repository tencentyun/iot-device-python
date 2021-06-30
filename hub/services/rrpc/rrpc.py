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

class Rrpc(object):
    def __init__(self, protocol, logger=None):
        self.__protocol = protocol
        self.__logger = logger
        self.__process_id = None

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

    def handle_rrpc(self, topic, payload):
        return self.__rrpc_get_process_id(topic)

    def rrpc_init(self, topic, qos):
        self.__assert(topic)

        return self.__protocol.subscribe(topic, qos)

    def rrpc_reply(self, topic_prefix, qos, reply):
        self.__assert(self.__process_id)
        self.__assert(reply)

        topic = topic_prefix + self.__process_id
        return self.__protocol.publish(topic, json.dumps(reply), qos)