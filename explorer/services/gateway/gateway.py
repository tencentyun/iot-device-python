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

import threading

class Gateway(object):
    def __init__(self, protocol, logger=None):
        self.__logger = logger
        self.__protocol = protocol

    def gateway_subdev_subscribe(self, product_id, topic_prop, topic_action, topic_event):    
        rc, mid = self.__protocol.subscribe(topic_prop, 0)
        if rc != 0:
            self.__logger.error("topic_subscribe error:rc:%d,topic:%s" % (rc, topic_prop))
            return rc, mid

        rc, mid = self.__protocol.subscribe(topic_action, 0)
        if rc != 0:
            self.__logger.error("topic_subscribe error:rc:%d,topic:%s" % (rc, topic_action))
            return rc, mid

        rc, mid = self.__protocol.subscribe(topic_event, 0)
        if rc != 0:
            self.__logger.error("topic_subscribe error:rc:%d,topic:%s" % (rc, topic_event))
            return rc, mid

        return rc, mid