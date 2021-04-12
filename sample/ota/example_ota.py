import sys
import time
import logging
import json
import os
from explorer import explorer

__log_format = '%(asctime)s.%(msecs)03d [%(filename)s:%(lineno)d] - %(levelname)s - %(message)s'
logging.basicConfig(format=__log_format)

te = explorer.QcloudExplorer(device_file="sample/device_info.json")
te.enableLogger(logging.DEBUG)

g_report_res = False
g_packet_id = 0
g_pub_ack = False


class OtaContextData(object):
    def __init__(self):
        self.file_size = 0
        self.version = None
        self.file_path = None
        self.info_file_path = None
        self.remote_version = None
        self.local_version = None
        self.download_size = 0


def on_connect(flags, rc, userdata):
    print("%s:flags:%d,rc:%d,userdata:%s" % (sys._getframe().f_code.co_name, flags, rc, userdata))
    pass


def on_disconnect(rc, userdata):
    print("%s:rc:%d,userdata:%s" % (sys._getframe().f_code.co_name, rc, userdata))
    pass


def on_message(topic, payload, qos, userdata):
    print("%s:topic:%s,payload:%s,qos:%s,userdata:%s" % (sys._getframe().f_code.co_name, topic, payload, qos, userdata))
    pass


def on_publish(mid, userdata):
    # print("%s:mid:%d,userdata:%s" % (sys._getframe().f_code.co_name, mid, userdata))

    global g_packet_id
    if g_packet_id == mid:
        global g_pub_ack
        g_pub_ack = True
        print("pub ack......")

    pass


def on_subscribe(granted_qos, mid, userdata):
    print("%s:mid:%d,granted_qos:%s,userdata:%s" % (sys._getframe().f_code.co_name, mid, granted_qos, userdata))
    pass


def on_unsubscribe(mid, userdata):
    print("%s:mid:%d,userdata:%s" % (sys._getframe().f_code.co_name, mid, userdata))
    pass


def on_ota_report(payload, userdata):
    print("%s:payload:%s,userdata:%s" % (sys._getframe().f_code.co_name, payload, userdata))
    code = payload["result_code"]
    if code == 0:
        global g_report_res
        g_report_res = True

    pass


def _get_local_fw_running_version():
    # you should get real version and return
    return "0.1.0"


def _get_local_fw_info(ota_cxt):
    if ota_cxt.info_file_path is None:
        print("file name is none")
        return 0
    if not os.path.exists(ota_cxt.info_file_path):
        print("info file not exists")
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


def _cal_exist_fw_md5(ota_cxt):
    if ota_cxt.file_path is None:
        print("file name is none")
        return -1

    total_read = 0
    te.otaResetMd5()
    size = ota_cxt.download_size
    with open(ota_cxt.file_path, "rb") as f:
        while size > 0:
            rlen = 5000 if size > 5000 else size
            buf = f.read(rlen)
            if buf == "":
                break
            te.otaMd5Update(buf)
            size -= rlen
            total_read += rlen
        pass
    f.close()
    print("total read:%d" % total_read)

    return 0


def _update_fw_downloaded_size(ota_cxt):
    local_size = _get_local_fw_info(ota_cxt)
    print("local_size:%d,local_ver:%s,re_ver:%s" % (local_size, ota_cxt.local_version, ota_cxt.remote_version))
    if ((ota_cxt.local_version != ota_cxt.remote_version)
            or (ota_cxt.download_size > ota_cxt.file_size)):
        ota_cxt.download_size = 0
        return 0
    ota_cxt.download_size = local_size
    rc = _cal_exist_fw_md5(ota_cxt)
    if rc != 0:
        print("cal md5 error")
        os.remove(ota_cxt.info_file_path)
        ota_cxt.download_size = 0
        return 0

    return local_size


def _save_fw_data_to_file(ota_cxt, buf, buf_len):
    if ota_cxt.file_path is None:
        print("file name is none")
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
            print('write size error')
            f.close()
            return -1
        """
        wr_buf = buf[wr_len:buf_len]
        wr_len = f.write(wr_buf)
        if wr_len > buf_len:
            raise ValueError('write size error')
        elif wr_len < buf_len:
            f.seek(ota_cxt.__download_size + wr_len, 0)
            continue
        else:
            break
        pass
        """
    f.flush()
    f.close()

    return 0


def _update_local_fw_info(ota_cxt):
    data_format = "{\"%s\":\"%s\", \"%s\":%d}"
    data = data_format % ("version", ota_cxt.remote_version, "downloaded_size", ota_cxt.download_size)
    with open(ota_cxt.info_file_path, "w") as f:
        wr_len = f.write(data)
        if wr_len != len(data):
            return -1
    return 0


def _wait_for_pub_ack(packet_id):
    wait_cnt = 10

    global g_packet_id
    g_packet_id = packet_id

    global g_pub_ack
    while (g_pub_ack is not True):
        print("wait for ack...")
        time.sleep(0.5)
        if wait_cnt == 0:
            print("wait report pub ack timeout!")
            break
        wait_cnt -= 1
        pass

    g_pub_ack = False


def _board_upgrade(fw_path):
    print("burning firmware...")

    return 0


def example_ota():

    print("\033[1;36m ota test start...\033[0m")

    te.user_on_connect = on_connect
    te.user_on_disconnect = on_disconnect
    te.user_on_message = on_message
    te.user_on_publish = on_publish
    te.user_on_subscribe = on_subscribe
    te.user_on_unsubscribe = on_unsubscribe
    te.user_on_ota_report = on_ota_report

    te.mqttInit(mqtt_domain="")
    te.connect()

    count = 0
    while True:
        if te.is_mqtt_connected():
            break
        else:
            if count >= 3:
                # sys.exit()
                print("\033[1;31m ota test fail...\033[0m")
                return False
            time.sleep(1)
            count += 1

    te.otaInit()

    cnt = 0
    while True:
        if not te.isMqttConnected():
            if cnt >= 10:
                print("mqtt disconnect")
                break
            time.sleep(1)
            cnt += 1
            continue
        cnt = 0

        upgrade_fetch_success = True
        ota_cxt = OtaContextData()

        te.otaReportVersion(_get_local_fw_running_version())
        # wait for ack
        time.sleep(1)

        if g_report_res:
            download_finished = False
            while (download_finished is not True):
                print("wait for ota upgrade command...")
                if te.otaIsFetching():
                    file_size, state = te.otaIoctlNumber(te.OtaCmdType.IOT_OTAG_FILE_SIZE)
                    if state == "success":
                        ota_cxt.file_size = file_size
                    else:
                        print("ota_ioctl_number fail..............")
                        break
                    pass

                    version, state = te.otaIoctlString(te.OtaCmdType.IOT_OTAG_VERSION, 32)
                    if state == "success":
                        ota_cxt.remote_version = version

                    ota_cxt.file_path = "./FW_%s.bin" % (ota_cxt.remote_version)
                    ota_cxt.info_file_path = "./FW_%s.json" % (ota_cxt.remote_version)

                    _update_fw_downloaded_size(ota_cxt)

                    rc = te.otaDownloadStart(ota_cxt.download_size, ota_cxt.file_size)
                    if rc != 0:
                        upgrade_fetch_success = False
                        break

                    while (te.otaIsFetchFinished() is not True):
                        buf, rv_len = te.otaFetchYield(5000)
                        if rv_len > 0:
                            rc = _save_fw_data_to_file(ota_cxt, buf, rv_len)
                            if rc != 0:
                                print("save data to file fail")
                                upgrade_fetch_success = False
                                break
                        elif rv_len < 0:
                            print("download fail rc:%d" % rv_len)
                            upgrade_fetch_success = False
                            break

                        fetched_size, state = te.otaIoctlNumber(te.OtaCmdType.IOT_OTAG_FETCHED_SIZE)
                        if state == "success":
                            ota_cxt.download_size = fetched_size
                        else:
                            break

                        rc = _update_local_fw_info(ota_cxt)
                        if rc != 0:
                            print("update local fw info error")
                        pass

                        time.sleep(0.1)
                    # <<while is_fetch_finish>> end

                    if upgrade_fetch_success:
                        os.remove(ota_cxt.info_file_path)
                        firmware_valid, state = te.otaIoctlNumber(te.OtaCmdType.IOT_OTAG_CHECK_FIRMWARE)
                        if firmware_valid == 0:
                            print("The firmware is valid")
                            upgrade_fetch_success = True
                        else:
                            print("The firmware is invalid,state:%s" % state)
                            upgrade_fetch_success = False

                    download_finished = True
                # <<if ota_is_fetching>> end

                if not download_finished:
                    time.sleep(1)
            # <<download_finished != True>> end

            _board_upgrade(ota_cxt.file_path)

            # Report after confirming that the burning is successful or failed
            packet_id = 0
            if upgrade_fetch_success:
                packet_id = te.otaReportUpgradeSuccess(None)
            else:
                packet_id = te.otaReportUpgradeFail(None)
            if packet_id >= 0:
                _wait_for_pub_ack(packet_id)

        g_report_res = False
        time.sleep(2)

    te.disconnect()
    print("\033[1;36m ota test success...\033[0m")
    return True
