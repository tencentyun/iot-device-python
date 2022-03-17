import sys
import logging
import time
import json
from hub.hub import QcloudHub

prduct_id = None
device_name = None
resource_progress_reply = False
logger = None
uploadTaskUrl = None

def on_connect(flags, rc, userdata):
    logger.debug("%s:flags:%d,rc:%d,userdata:%s" % (sys._getframe().f_code.co_name, flags, rc, userdata))
    pass


def on_disconnect(rc, userdata):
    logger.debug("%s:rc:%d,userdata:%s" % (sys._getframe().f_code.co_name, rc, userdata))
    pass


def on_message(topic, qos, payload, userdata):
    logger.debug(
        "%s:topic:%s,payload:%s,qos:%s,userdata:%s" % (sys._getframe().f_code.co_name, topic, payload, qos, userdata))
    pass


def on_publish(mid, userdata):
    logger.debug("%s:mid:%d,userdata:%s" % (sys._getframe().f_code.co_name, mid, userdata))
    pass


def on_subscribe(mid, granted_qos, userdata):
    logger.debug("%s:mid:%d,granted_qos:%s,userdata:%s" % (sys._getframe().f_code.co_name, mid, granted_qos, userdata))
    pass


def on_unsubscribe(mid, userdata):
    logger.debug("%s:mid:%d,userdata:%s" % (sys._getframe().f_code.co_name, mid, userdata))
    pass


def on_resourceManage_cb(topic, qos, payload, userdata):
    logger.debug("%s:payload:%s,userdata:%s" % (sys._getframe().f_code.co_name, payload, userdata))

    global uploadTaskUrl
    global resource_progress_reply
    payloadDic = payload
    uploadType = payloadDic["type"]

    if 'url' in payloadDic:
        uploadTaskUrl = payloadDic["url"]
        if uploadTaskUrl is None or len(uploadTaskUrl) == 0:
            raise ValueError('create_upload_task_rsp url Invalid param')
    else:
        if uploadType == "report_upload_progress_rsp":
            if payloadDic["result_code"] == 0 and payloadDic["result_msg"] == "ok":
                resource_progress_reply = True

    pass


def example_resourceManage(isTest=True):
    global logger
    provider = QcloudHub(device_file="hub/sample/device_info.json", tls=True)
    qcloud = provider.hub
    logger = qcloud.logInit(qcloud.LoggerLevel.DEBUG, "logs/log", 1024 * 1024 * 10, 5, enable=True)

    logger.debug("\033[1;36m resourceManage test start...\033[0m")

    global prduct_id
    global device_name
    prduct_id = qcloud.getProductID()
    device_name = qcloud.getDeviceName()

    qcloud.registerMqttCallback(on_connect, on_disconnect,
                                on_message, on_publish,
                                on_subscribe, on_unsubscribe)
    qcloud.connect()

    count = 0
    while True:
        if qcloud.isMqttConnected():
            break
        else:
            if count >= 3:
                logger.error("\033[1;31m mqtt test fail...\033[0m")
                return False
            time.sleep(1)
            count += 1

    rc, mid = qcloud.resourceInit(prduct_id, device_name, on_resourceManage_cb)
    if rc != 0:
        logger.error("resourceInit error")
        return False

    cnt = 0
    while True:
        if not qcloud.isMqttConnected():
            if cnt >= 10:
                logger.debug("mqtt disconnect")
                break
            time.sleep(1)
            cnt += 1
            continue
        cnt = 0

        """*********需要传资源文件绝对路径*******"""
        rc, mid = qcloud.resourceCreateUploadTask(prduct_id, device_name,"")
        # wait for ack
        time.sleep(1)

        if rc != 0:
            logger.error("\033[1;31m resource create upload task fail ...\033[0m")
            return False

        logger.debug("\033[1;36m resource create upload task test success...\033[0m")

        #判断URL
        if uploadTaskUrl is None or len(uploadTaskUrl) == 0:
            logger.error("\033[1;31m create_upload_task_rsp url is empty\033[0m")
            return False

        #上传资源文件
        rc, mid = qcloud.resourceReportUploadProgress(prduct_id, device_name)
        if rc != 0:
            logger.error("\033[1;31m resource upload file progress fail ...\033[0m")
            return False

        logger.debug("\033[1;36m resource upload file progress success ...\033[0m")

        qcloud.resourceUploadfile(uploadTaskUrl)

        if resource_progress_reply:

            rc, mid = qcloud.resourceFinished()
            if rc != 0:
                logger.error("\033[1;31m resource http put upload file progress error ...\033[0m")
                return False

            logger.debug("\033[1;36m resource http put upload file progress finish ...\033[0m")
            break

        else:

            logger.error("\033[1;31m resource http put upload file progress fail ...\033[0m")
            return False

    # qcloud.disconnect()
    logger.debug("\033[1;36m resourceManage test success...\033[0m")

    return True