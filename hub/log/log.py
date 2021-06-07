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

import logging

class Log(object):
    def __init__(self):
        self.__logger = logging.getLogger("TecentQcloud")
        self.__enabled = False

    def enable_logger(self):
        self.__enabled = True

    def disable_logger(self):
        self.__enabled = False

    def is_enabled(self):
        return self.__enabled

    def set_level(self, level):
        self.__logger.setLevel(level)

    def debug(self, fmt, *args):
        if self.__enabled:
            self.__logger.debug(fmt, *args)

    def warring(self, fmt, *args):
        if self.__enabled:
            self.__logger.warning(fmt, *args)

    def info(self, fmt, *args):
        if self.__enabled:
            self.__logger.info(fmt, *args)

    def error(self, fmt, *args):
        if self.__enabled:
            self.__logger.error(fmt, *args)

    def critical(self, fmt, *args):
        if self.__enabled:
            self.__logger.critical(fmt, *args)
