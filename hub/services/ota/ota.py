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
import time
import urllib.request
import urllib.parse
import urllib.error
import hashlib
from enum import Enum
from enum import IntEnum
from utils.codec import Codec
from utils.providers import TopicProvider
from utils.providers import ConnClientProvider

class Ota(object):
    def __init__(self, host, product_id, device_name, device_secret,
                    websocket=False, tls=True, logger=None):
        self.__provider = ConnClientProvider(host, product_id, device_name, device_secret,
                                                websocket=websocket, tls=tls, logger=logger)
        self.__protocol = self.__provider.protocol
        self.__logger = logger
        self.__codec = Codec()
        self.__topic = None

        self.__ota_manager = None
        self.__ota_version_len_min = 1
        self.__ota_version_len_max = 32
        self.http_manager = None
        self.__user_callback = {}

    class OtaState(Enum):
        IOT_OTAS_UNINITED = 0
        IOT_OTAS_INITED = 1
        IOT_OTAS_FETCHING = 2
        IOT_OTAS_FETCHED = 3
        IOT_OTAS_DISCONNECTED = 4

    class OtaCmdType(Enum):
        IOT_OTAG_FETCHED_SIZE = 0
        IOT_OTAG_FILE_SIZE = 1
        IOT_OTAG_MD5SUM = 2
        IOT_OTAG_VERSION = 3
        IOT_OTAG_CHECK_FIRMWARE = 4

    class OtaProgressCode(Enum):
        IOT_OTAP_BURN_FAILED = -4
        IOT_OTAP_CHECK_FALIED = -3
        IOT_OTAP_FETCH_FAILED = -2
        IOT_OTAP_GENERAL_FAILED = -1
        IOT_OTAP_FETCH_PERCENTAGE_MIN = 0
        IOT_OTAP_FETCH_PERCENTAGE_MAX = 100

    class OtaReportType(IntEnum):
        IOT_OTAR_DOWNLOAD_TIMEOUT = -1
        IOT_OTAR_FILE_NOT_EXIST = -2
        IOT_OTAR_AUTH_FAIL = -3
        IOT_OTAR_MD5_NOT_MATCH = -4
        IOT_OTAR_UPGRADE_FAIL = -5
        IOT_OTAR_NONE = 0
        IOT_OTAR_DOWNLOAD_BEGIN = 1
        IOT_OTAR_DOWNLOADING = 2
        IOT_OTAR_UPGRADE_BEGIN = 3
        IOT_OTAR_UPGRADE_SUCCESS = 4

    class ota_manage(object):
        def __init__(self):
            self.channel = None
            self.state = 0
            self.size_fetched = 0
            self.size_last_fetched = 0
            self.file_size = 0
            self.purl = None
            self.version = None
            self.md5sum = None
            self.md5 = None
            self.host = None
            self.is_https = False

            self.report_timestamp = 0

            # http连接管理
            self.http_manager = None

    class http_manage(object):
        def __init__(self):
            self.handle = None
            self.request = None
            self.header = None
            self.host = None
            self.https_context = None

            self.err_reason = None
            self.err_code = 0
            pass

    def __assert(self, param):
        if param is None or len(param) == 0:
            raise ValueError('Invalid param.')

    def __ota_publish(self, message, qos):
        topic_pub = self.__topic.ota_report_topic_pub
        rc, mid = self.__protocol.publish(topic_pub, json.dumps(message), qos)
        return rc, mid

    def __ota_info_get(self, payload):
        size = payload["file_size"]
        if size > 0:
            self.__ota_manager.file_size = size
        version = payload["version"]
        if version is not None and len(version) > 0:
            self.__ota_manager.version = version
        url = payload["url"]
        if url is not None and len(url) > 0:
            self.__ota_manager.purl = url
            pos = url.find("https://")
            last_pos = url.rfind("/")
            if pos >= 0:
                self.__ota_manager.is_https = True
                host = url[8:last_pos]
            else:
                host = url[7:last_pos]
            self.__ota_manager.host = host

        md5sum = payload["md5sum"]
        if md5sum is not None and len(md5sum) > 0:
            self.__ota_manager.md5sum = md5sum

        self.__ota_manager.state = self.OtaState.IOT_OTAS_FETCHING

    def __ota_http_deinit(self, http):
        print("__ota_http_deinit do nothing")

    def __message_splice(self, state, progress, result_code, result_msg, version, ptype):
        message = None
        code = "%d" % (result_code)
        if ptype == 1:
            message = {
                "type": "report_progress",
                "report": {
                    "progress": {
                        "state": state,
                        "percent": str(progress),
                        "result_code": code,
                        "result_msg": result_msg
                    },
                    "version": version
                }
            }
        elif ptype == 0:
            message = {
                "type": "report_progress",
                "report": {
                    "progress": {
                        "state": state,
                        "result_code": code,
                        "result_msg": result_msg
                    },
                    "version": version
                }
            }

        return message

    def __ota_gen_report_msg(self, version, progress, report_type):
        message = None
        if report_type == self.OtaReportType.IOT_OTAR_DOWNLOAD_BEGIN:
            message = self.__message_splice("downloading", 0, 0, "", version, 1)
        elif report_type == self.OtaReportType.IOT_OTAR_DOWNLOADING:
            message = self.__message_splice("downloading", progress, 0, "", version, 1)
        elif ((report_type == self.OtaReportType.IOT_OTAR_DOWNLOAD_TIMEOUT)
                or (report_type == self.OtaReportType.IOT_OTAR_FILE_NOT_EXIST)
                or (report_type == self.OtaReportType.IOT_OTAR_MD5_NOT_MATCH)
                or (report_type == self.OtaReportType.IOT_OTAR_AUTH_FAIL)
                or (report_type == self.OtaReportType.IOT_OTAR_UPGRADE_FAIL)):
            message = self.__message_splice("fail", progress, report_type, "time_out", version, 0)
        elif report_type == self.OtaReportType.IOT_OTAR_UPGRADE_BEGIN:
            message = self.__message_splice("burning", progress, 0, "", version, 0)
        elif report_type == self.OtaReportType.IOT_OTAR_UPGRADE_SUCCESS:
            message = self.__message_splice("done", progress, 0, "", version, 0)
        else:
            self.__logger.error("not support report_type:%d" % report_type)
            message = None

        return message

    def _ota_report_upgrade_result(self, version, report_type):
        if self.__ota_manager.state == self.OtaState.IOT_OTAS_UNINITED:
            raise ValueError('ota handle is uninitialized')
        message = self.__ota_gen_report_msg(version, 1, report_type)
        if message is not None:
            return self.__ota_publish(message, 1)
        else:
            self.__logger.error("message is none")
            return -1, -1

    def _ota_report_progress(self, progress, version, report_type):
        if self.__ota_manager.state == self.OtaState.IOT_OTAS_UNINITED:
            raise ValueError('ota handle is uninitialized')
        message = self.__ota_gen_report_msg(version, progress, report_type)
        if message is not None:
            self.__logger.debug("[ota report] %s" % (message))
            return self.__ota_publish(message, 0)
        else:
            self.__logger.error("message is none")
            return -1, -1

    def ota_report_upgrade_success(self, version):
        if version is None:
            rc, mid = self._ota_report_upgrade_result(self.__ota_manager.version,
                                                     self.OtaReportType.IOT_OTAR_UPGRADE_SUCCESS)
        else:
            rc, mid = self._ota_report_upgrade_result(version, self.OtaReportType.IOT_OTAR_UPGRADE_SUCCESS)

        return rc, mid

    def ota_report_upgrade_fail(self, version):
        if version is None:
            rc, mid = self._ota_report_upgrade_result(self.__ota_manager.version,
                                                     self.OtaReportType.IOT_OTAR_UPGRADE_FAIL)
        else:
            rc, mid = self._ota_report_upgrade_result(version, self.OtaReportType.IOT_OTAR_UPGRADE_FAIL)

        return rc, mid

    def ota_ioctl_number(self, cmd_type):
        if ((self.__ota_manager.state == self.OtaState.IOT_OTAS_INITED)
                or (self.__ota_manager.state == self.OtaState.IOT_OTAS_UNINITED)):
            return -1, "state error"

        if cmd_type.value == self.OtaCmdType.IOT_OTAG_FETCHED_SIZE.value:
            return self.__ota_manager.size_fetched, "success"
        elif cmd_type.value == self.OtaCmdType.IOT_OTAG_FILE_SIZE.value:
            return self.__ota_manager.file_size, "success"
        elif cmd_type.value == self.OtaCmdType.IOT_OTAG_CHECK_FIRMWARE.value:
            if self.__ota_manager.state is not self.OtaState.IOT_OTAS_FETCHED:
                return -1, "state error"
            md5sum = self.__ota_manager.md5.hexdigest()
            if md5sum == self.__ota_manager.md5sum:
                return 0, "success"
            else:
                self._ota_report_upgrade_result(self.__ota_manager.version,
                                               self.OtaReportType.IOT_OTAR_MD5_NOT_MATCH)
                return -1, "md5 error"
            pass

        return -1, "cmd type error"

    def ota_ioctl_string(self, cmd_type, length):
        if ((self.__ota_manager.state == self.OtaState.IOT_OTAS_INITED)
                or (self.__ota_manager.state == self.OtaState.IOT_OTAS_UNINITED)):
            return "null", "state error"

        if cmd_type.value == self.OtaCmdType.IOT_OTAG_VERSION.value:
            if len(self.__ota_manager.version) > length:
                return "null", "version length error"
            else:
                return self.__ota_manager.version, "success"
        elif cmd_type.value == self.OtaCmdType.IOT_OTAG_MD5SUM.value:
            if len(self.__ota_manager.md5sum) > length:
                return "null", "md5sum length error"
            else:
                return self.__ota_manager.md5sum, "success"

        return "null", "cmd type error"

    def ota_reset_md5(self):
        self.__ota_manager.md5 = None
        self.__ota_manager.md5 = hashlib.md5()
        return 0

    def ota_md5_update(self, buf):
        if buf is None:
            self.__logger.error("buf is none")
            return -1
        if self.__ota_manager.md5 is None:
            self.__logger.error("md5 handle is uninitialized")
            return -1

        # self.__ota_manager.md5.update(buf.encode(encoding='utf-8'))
        self.__ota_manager.md5.update(buf)
        return 0

    def handle_ota(self, topic, qos, payload, userdata):
        ptype = payload["type"]
        if ptype == "report_version_rsp":
            """
            回调用户
            """
            if self.__user_callback[topic] is not None:
                self.__user_callback[topic](topic, qos, payload, userdata)
            else:
                self.__logger.error("no callback for topic %s" % topic)

        elif ptype == "update_firmware":
            self.__ota_info_get(payload)

    def ota_init(self, product_id, device_name, ota_cb):
        """
        ota资源初始化
        """
        self.__topic = TopicProvider(product_id, device_name)
        topic_sub = self.__topic.ota_update_topic_sub
        self.__user_callback[topic_sub] = ota_cb

        self.__ota_manager = self.ota_manage()
        self.__ota_manager.state = self.OtaState.IOT_OTAS_UNINITED

        return self.__protocol.subscribe(topic_sub, 1)

    def ota_manager_init(self):
        self.__ota_manager.state = self.OtaState.IOT_OTAS_INITED
        self.__ota_manager.md5 = hashlib.md5()

    # 是否应将ota句柄传入(支持多个下载进程?)
    def ota_is_fetching(self):
        return (self.__ota_manager.state == self.OtaState.IOT_OTAS_FETCHING)

    def ota_is_fetch_finished(self):
        return (self.__ota_manager.state == self.OtaState.IOT_OTAS_FETCHED)

    def http_init(self, host, url, offset, size, timeout_sec):
        range_format = "bytes=%d-%d"
        srange = range_format % (offset, size)

        header = {}
        header["Host"] = host
        header["Accept"] = "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        header["Accept-Encoding"] = "gzip, deflate"
        header["Range"] = srange

        self.http_manager = self.http_manage()
        self.http_manager.header = header
        self.http_manager.host = host

        if self.__ota_manager.is_https:
            # context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH, cadata=self.__iot_ca_crt)
            context = self.__codec.Ssl().create_content()
            self.http_manager.https_context = context
            try:
                self.http_manager.request = urllib.request.Request(url=url, headers=header)
                self.http_manager.handle = urllib.request.urlopen(self.http_manager.request,
                                                                  context=context,
                                                                  timeout=timeout_sec)
            except urllib.error.HTTPError as e:
                self.__logger.error("https connect error:%d" % e.code)
                self.http_manager.err_code = e.code
                return 1
            except urllib.error.URLError as e:
                self.__logger.error("https connect error:%s" % e.reason)
                self.http_manager.err_reason = e.reason
                return 1
        else:
            try:
                self.http_manager.request = urllib.request.Request(url=url, headers=header)
                self.http_manager.handle = urllib.request.urlopen(self.http_manager.request,
                                                                  timeout=timeout_sec)
            except Exception as e:
                self.__logger.error("http connect error:%s" % str(e))
                return 1
        return 0

    def http_fetch(self, buf_len):
        if self.http_manager.handle is None:
            return None, -1
        try:
            buf = self.http_manager.handle.read(buf_len)
            return buf, len(buf)
        except Exception as e:
            self.__logger.error("http read error:%s" % str(e))
            return None, -2

    def ota_report_version(self, version):
        self.__assert(version)
        if len(version) < self.__ota_version_len_min or len(version) > self.__ota_version_len_max:
            raise ValueError('Invalid version length')
        if self.__ota_manager.state == self.OtaState.IOT_OTAS_UNINITED:
            raise ValueError('ota handle is uninitialized')
        report = {
            "type": "report_version",
            "report": {
                "version": version
            }
        }
        return self.__ota_publish(report, 1)

    def ota_download_start(self, offset, size):
        if offset < 0 or size <= 0:
            raise ValueError('Invalid length.')
        if offset == 0:
            self.ota_reset_md5()
        self.__ota_http_deinit(self.__ota_manager.http_manager)
        # 断点续传初始值不为0
        self.__ota_manager.size_fetched += offset

        rc = self.http_init(self.__ota_manager.host, self.__ota_manager.purl, offset, size, 10000 / 1000)
        if rc != 0:
            if self.http_manager.err_code == 403:
                self._ota_report_upgrade_result(self.__ota_manager.version,
                                               self.OtaReportType.IOT_OTAR_AUTH_FAIL)
            elif self.http_manager.err_code == 404:
                self._ota_report_upgrade_result(self.__ota_manager.version,
                                               self.OtaReportType.IOT_OTAR_FILE_NOT_EXIST)
            elif self.http_manager.err_code == 408:
                self._ota_report_upgrade_result(self.__ota_manager.version,
                                               self.OtaReportType.IOT_OTAR_DOWNLOAD_TIMEOUT)
            else:
                # 其他错误判断(error.reason)
                self.__logger.error("http_init error:%d" % self.http_manager.err_code)

        return rc

    def ota_fetch_yield(self, buf_len):
        if self.__ota_manager.state != self.OtaState.IOT_OTAS_FETCHING:
            self.__logger.error("ota state is not fetching")
            return None, -1
        # http read
        buf, rv_len = self.http_fetch(buf_len)
        if rv_len < 0:
            if rv_len == -2:
                self._ota_report_upgrade_result(self.__ota_manager.version,
                                               self.OtaReportType.IOT_OTAR_DOWNLOAD_TIMEOUT)
            return None, -2
        else:
            if self.__ota_manager.size_fetched == 0:
                self._ota_report_progress(self.OtaProgressCode.IOT_OTAP_FETCH_PERCENTAGE_MIN,
                                         self.__ota_manager.version,
                                         self.OtaReportType.IOT_OTAR_DOWNLOAD_BEGIN)
                self.__ota_manager.report_timestamp = int(time.time())
            pass
        self.__ota_manager.size_last_fetched = rv_len
        self.__ota_manager.size_fetched += rv_len

        percent = int((self.__ota_manager.size_fetched * 100) / self.__ota_manager.file_size)
        if percent == 100:
            self._ota_report_progress(percent, self.__ota_manager.version,
                                     self.OtaReportType.IOT_OTAR_DOWNLOADING)
        else:
            timestamp = int(time.time())
            # 间隔1秒上报一次
            if (((timestamp - self.__ota_manager.report_timestamp) >= 1)
                    and (self.__ota_manager.size_last_fetched > 0)):
                self.__ota_manager.report_timestamp = timestamp
                self._ota_report_progress(percent, self.__ota_manager.version,
                                         self.OtaReportType.IOT_OTAR_DOWNLOADING)

        if self.__ota_manager.size_fetched >= self.__ota_manager.file_size:
            self.__ota_manager.state = self.OtaState.IOT_OTAS_FETCHED

        self.__ota_manager.md5.update(buf)

        return buf, rv_len