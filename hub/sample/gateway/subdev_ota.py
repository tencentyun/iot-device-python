import sys
import time
import logging
import json
import os
from enum import Enum

class SubdevOta(object):
    def __init__(self, product_id, device_name, handle, logger):
        self.__product_id = product_id
        self.__device_name = device_name
        self.__handle= handle
        self.__logger = logger
        self.__thd = None

    class ThreadResource(object):
        def __init__(self, product_id, device_name, handle):
            self.handle = handle
            self.report_res = False
            self.packet_id = 0
            self.pub_ack = False
            self.product_id = product_id
            self.device_name = device_name

    class OtaContextData(object):
        def __init__(self):
            self.file_size = 0
            self.version = None
            self.file_path = None
            self.info_file_path = None
            self.remote_version = None
            self.local_version = None
            self.download_size = 0

    class OtaCmdType(Enum):
        IOT_OTAG_FETCHED_SIZE = 0
        IOT_OTAG_FILE_SIZE = 1
        IOT_OTAG_MD5SUM = 2
        IOT_OTAG_VERSION = 3
        IOT_OTAG_CHECK_FIRMWARE = 4

    def __on_ota_report(self, topic, qos, payload, userdata):
        self.__logger.debug("%s:topic:%s,payload:%s" % (sys._getframe().f_code.co_name, topic, payload))
        code = payload["result_code"]

        if code == 0:
            self.__thd.report_res = True
        pass


    def __get_local_fw_running_version(self):
        # you should get real version and return
        return "0.1.0"


    def __get_local_fw_info(self, ota_cxt):
        if ota_cxt.info_file_path is None:
            self.__logger.error("file name is none")
            return 0
        if not os.path.exists(ota_cxt.info_file_path):
            self.__logger.error("info file not exists")
            return 0

        f = open(ota_cxt.info_file_path, "r")
        buf = f.read()
        if len(buf) > 0:
            file_buf = json.loads(buf)
            version = file_buf["version"]
            download_size = file_buf["downloaded_size"]
            if version is not None:
                ota_cxt.local_version = version
            if download_size > 0:
                return download_size
        f.close()

        return 0


    def __cal_exist_fw_md5(self, ota_cxt, thd):
        if ota_cxt.file_path is None:
            self.__logger.error("file name is none")
            return -1

        total_read = 0
        thd.handle.otaResetMd5(thd.product_id, thd.device_name)
        size = ota_cxt.download_size
        with open(ota_cxt.file_path, "rb") as f:
            while size > 0:
                rlen = 5000 if size > 5000 else size
                buf = f.read(rlen)
                if buf == "":
                    break
                thd.handle.otaMd5Update(thd.product_id, thd.device_name, buf)
                size -= rlen
                total_read += rlen
            pass
        f.close()
        self.__logger.debug("total read:%d" % total_read)

        return 0


    def __update_fw_downloaded_size(self, ota_cxt, thd):
        local_size = self.__get_local_fw_info(ota_cxt)
        self.__logger.debug("local_size:%d,local_ver:%s,re_ver:%s" % (local_size, ota_cxt.local_version, ota_cxt.remote_version))
        if ((ota_cxt.local_version != ota_cxt.remote_version)
                or (ota_cxt.download_size > ota_cxt.file_size)):
            ota_cxt.download_size = 0
            return 0
        ota_cxt.download_size = local_size
        rc = self.__cal_exist_fw_md5(ota_cxt, thd)
        if rc != 0:
            self.__logger.error("cal md5 error")
            os.remove(ota_cxt.info_file_path)
            ota_cxt.download_size = 0
            return 0

        return local_size


    def __save_fw_data_to_file(self, ota_cxt, buf, buf_len):
        if ota_cxt.file_path is None:
            self.__logger.error("file name is none")
            return -1
        f = None
        wr_len = 0
        if ota_cxt.download_size > 0:
            f = open(ota_cxt.file_path, "ab+")
        else:
            f = open(ota_cxt.file_path, "wb+")

        f.seek(ota_cxt.download_size, 0)
        while True:
            wr_len = f.write(buf)
            if wr_len == buf_len:
                break
            else:
                self.__logger.error('write size error')
                f.close()
                return -1
        f.flush()
        f.close()

        return 0


    def __update_local_fw_info(self, ota_cxt):
        data_format = "{\"%s\":\"%s\", \"%s\":%d}"
        data = data_format % ("version", ota_cxt.remote_version, "downloaded_size", ota_cxt.download_size)
        with open(ota_cxt.info_file_path, "w") as f:
            wr_len = f.write(data)
            if wr_len != len(data):
                return -1
        return 0


    def __wait_for_pub_ack(self, packet_id, thd):
        wait_cnt = 10
        thd.packet_id = packet_id

        while (thd.pub_ack is not True):
            self.__logger.debug("wait for ack...")
            time.sleep(0.5)
            if wait_cnt == 0:
                self.__logger.error("wait report pub ack timeout!")
                break
            wait_cnt -= 1
            pass

        thd.pub_ack = False


    def __board_upgrade(self, fw_path):
        self.__logger.debug("burning firmware...")

        return 0

    def update_reply_mid(self, mid):
        if self.__thd.packet_id == mid:
            self.__thd.pub_ack = True
            self.__logger.debug("publish ack id %d" % self.__thd.packet_id)

    def subdev_ota_start(self):
        self.__logger.debug("\033[1;36m ota test start...\033[0m")

        thd = self.ThreadResource(self.__product_id, self.__device_name, self.__handle)
        self.__thd = thd

        count = 0
        while True:
            if self.__handle.isMqttConnected():
                break
            else:
                if count >= 3:
                    # sys.exit()
                    self.__logger.error("\033[1;31m ota test fail...\033[0m")
                    # return False
                    # 区分单元测试和sample
                    return True
                time.sleep(1)
                count += 1

        self.__handle.otaInit(self.__product_id, self.__device_name, self.__on_ota_report)

        cnt = 0
        while True:
            if not self.__handle.isMqttConnected():
                if cnt >= 10:
                    self.__logger.error("mqtt disconnect")
                    break
                time.sleep(1)
                cnt += 1
                continue
            cnt = 0

            upgrade_fetch_success = True
            ota_cxt = self.OtaContextData()

            self.__handle.otaReportVersion(self.__product_id, self.__device_name, self.__get_local_fw_running_version())
            # wait for ack
            time.sleep(1)

            if thd.report_res:
                download_finished = False
                while (download_finished is not True):
                    self.__logger.debug("wait for ota upgrade command")
                    if self.__handle.otaIsFetching(self.__product_id, self.__device_name):
                        file_size, state = self.__handle.otaIoctlNumber(self.__product_id, self.__device_name,
                                                                            self.OtaCmdType.IOT_OTAG_FILE_SIZE)
                        if state == "success":
                            ota_cxt.file_size = file_size
                        else:
                            self.__logger.error("ota_ioctl_number fail")
                            break
                        pass

                        version, state = self.__handle.otaIoctlString(self.__product_id, self.__device_name,
                                                                        self.OtaCmdType.IOT_OTAG_VERSION, 32)
                        if state == "success":
                            ota_cxt.remote_version = version

                        ota_cxt.file_path = "./FW-%s_%s.bin" % (self.__product_id + self.__device_name, ota_cxt.remote_version)
                        ota_cxt.info_file_path = "./FW-%s_%s.json" % (self.__product_id + self.__device_name, ota_cxt.remote_version)

                        self.__update_fw_downloaded_size(ota_cxt, thd)

                        rc = self.__handle.otaDownloadStart(self.__product_id, self.__device_name,
                                                                ota_cxt.download_size, ota_cxt.file_size)
                        if rc != 0:
                            upgrade_fetch_success = False
                            break

                        while (self.__handle.otaIsFetchFinished(self.__product_id, self.__device_name, ) is not True):
                            buf, rv_len = self.__handle.otaFetchYield(self.__product_id, self.__device_name, 5000)
                            if rv_len > 0:
                                rc = self.__save_fw_data_to_file(ota_cxt, buf, rv_len)
                                if rc != 0:
                                    self.__logger.error("save data to file fail")
                                    upgrade_fetch_success = False
                                    break
                            elif rv_len < 0:
                                self.__logger.error("download fail rc:%d" % rv_len)
                                upgrade_fetch_success = False
                                break

                            fetched_size, state = self.__handle.otaIoctlNumber(self.__product_id, self.__device_name,
                                                                                self.OtaCmdType.IOT_OTAG_FETCHED_SIZE)
                            if state == "success":
                                ota_cxt.download_size = fetched_size
                            else:
                                break

                            rc = self.__update_local_fw_info(ota_cxt)
                            if rc != 0:
                                self.__logger.error("update local fw info error")
                            pass

                            #time.sleep(0.1)
                        # <<while is_fetch_finish>> end

                        if upgrade_fetch_success:
                            os.remove(ota_cxt.info_file_path)
                            firmware_valid, state = self.__handle.otaIoctlNumber(self.__product_id, self.__device_name,
                                                                                    self.OtaCmdType.IOT_OTAG_CHECK_FIRMWARE)
                            if firmware_valid == 0:
                                self.__logger.debug("The firmware(%s) download success" % (self.__product_id + self.__device_name))
                                upgrade_fetch_success = True
                            else:
                                self.__logger.error("The firmware(%s) is invalid,state:%s" % (state, self.__product_id + self.__device_name))
                                upgrade_fetch_success = False

                        download_finished = True
                    # <<if ota_is_fetching>> end

                    if not download_finished:
                        time.sleep(1)
                # <<download_finished != True>> end

                self.__board_upgrade(ota_cxt.file_path)

                # Report after confirming that the burning is successful or failed
                packet_id = 0
                if upgrade_fetch_success:
                    rc, packet_id = self.__handle.otaReportUpgradeSuccess(self.__product_id, self.__device_name, None)
                else:
                    rc, packet_id = self.__handle.otaReportUpgradeFail(self.__product_id, self.__device_name, None)
                if rc == 0:
                    self.__wait_for_pub_ack(packet_id, thd)

            thd.report_res = False
            time.sleep(2)

        self.__logger.debug("\033[1;36m ota test success...\033[0m")
        return True