import sys
import logging
import time
import json
from hub.hub import QcloudHub

prduct_id = None
device_name = None
resource_reply = False
logger = None


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

    global prduct_id
    global device_name

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
        rc, mid = qcloud.resourceCreateUploadTask(prduct_id, device_name)
        # wait for ack
        time.sleep(1)

        if rc == 0:
            logger.debug("\033[1;36m resourceCreateUploadTask test success...\033[0m")
            break

    # qcloud.disconnect()
    logger.debug("\033[1;36m resourceManage test success...\033[0m")

    return True