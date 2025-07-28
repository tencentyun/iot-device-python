#
# Tencent is pleased to support the open source community by making IoT Hub available.
# Copyright (C) 2016 Tencent. All rights reserved.

# Licensed under the MIT License (the "License"); you may not use this file except in
# compliance with the License. You may obtain a copy of the License at
# http://opensource.org/licenses/MIT

# Unless required by applicable law or agreed to in writing, software distributed under the License is
# distributed on an "AS IS" basis, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
# either express or implied. See the License for the specific language governing permissions and
# limitations under the License.

import queue
import threading
from hub.utils.providers import LoggerProvider

class TaskManager(object):
    def __init__(self):
        self.__init = True

    class LoopThread(object):
        def __init__(self):
            self.__provider = LoggerProvider()
            self.__logger = self.__provider.logger
            self.__callback = None
            self.__thread = None
            self.__started = False
            self.__req_wait = threading.Event()

        def start(self, callback):
            if self.__started:
                self.__logger.info("LoopThread already")
                return 1
            else:
                self.__callback = callback
                self.__thread = threading.Thread(target=self.__thread_main)
                self.__thread.daemon = True
                self.__thread.start()
                return 0

        def __thread_main(self):
            self.__started = True
            try:
                if self.__logger is not None:
                    self.__logger.debug("LoopThread thread enter")
                if self.__callback is not None:
                    self.__callback()
                if self.__logger is not None:
                    self.__logger.debug("LoopThread thread exit")
            except Exception as e:
                self.__logger.error("LoopThread thread Exception:" + str(e))
            self.__started = False
            self.__req_wait.set()

        def stop(self):
            self.__req_wait.wait()
            self.__req_wait.clear()

    # 用户注册回调分发线程
    class EventCbThread(object):
        def __init__(self):
            self.__provider = LoggerProvider()
            self.__logger = self.__provider.logger
            self.__message_queue = queue.Queue(20)
            self.__event_callback = {}
            self.__started = False
            self.__exited = False
            self.__thread = None
            pass

        def register_event_callback(self, event, callback):
            if self.__started is False:
                if event != "req_exit":
                    self.__event_callback[event] = callback
                    return 0
                else:
                    return 1
                pass
            else:
                return 2
            pass

        def post_message(self, event, value):
            # self.__logger.debug("post_message :%r " % event)
            if self.__started and self.__exited is False:
                try:
                    self.__message_queue.put((event, value), timeout=5)
                except queue.Full as e:
                    self.__logger.error("queue full: %r" % e)
                    return False
                # self.__logger.debug("post_message success")
                return True
            self.__logger.debug("post_message fail started:%r,exited:%r" % (self.__started, self.__exited))
            return False

        def start(self):
            if self.__logger is not None:
                self.__logger.info("EventCbThread start")
            if self.__started is False:
                if self.__logger is not None:
                    self.__logger.info("EventCbThread try start")
                self.__exited = False
                self.__started = True
                self.__message_queue = queue.Queue(20)
                self.__thread = threading.Thread(target=self.__event_thread)
                self.__thread.daemon = True
                self.__thread.start()
                return 0
            return 1

        def stop(self):
            if self.__started and self.__exited is False:
                self.__exited = True
                self.__message_queue.put(("req_exit", None))

        def wait_stop(self):
            if self.__started is True:
                self.__thread.join()

        def __event_thread(self):
            if self.__logger is not None:
                self.__logger.debug("thread runnable enter")
            while True:
                event, value = self.__message_queue.get()
                if event == "req_exit":
                    break
                if self.__event_callback[event] is not None:
                    try:
                        self.__event_callback[event](value)
                    except Exception as e:
                        if self.__logger is not None:
                            self.__logger.error("thread runnable raise exception:%s" % e)
            self.__started = False
            if self.__logger is not None:
                self.__logger.debug("thread runnable exit")
            pass