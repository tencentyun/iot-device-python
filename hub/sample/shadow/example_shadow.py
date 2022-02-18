import sys
import logging
import time
import json
from hub.hub import QcloudHub

g_connected = False
g_delta_arrived = False
reply = False

logger = None

def on_connect(flags, rc, userdata):
    logger.debug("%s:flags:%d,rc:%d,userdata:%s" % (sys._getframe().f_code.co_name, flags, rc, userdata))
    global g_connected
    g_connected = True

    pass

def on_disconnect(rc, userdata):
    logger.debug("%s:rc:%d,userdata:%s" % (sys._getframe().f_code.co_name, rc, userdata))
    pass

def on_message(topic, qos, payload, userdata):
    logger.debug("%s:topic:%s,payload:%s,qos:%s,userdata:%s" % (sys._getframe().f_code.co_name, topic, payload, qos, userdata))

    message_type = payload["type"]
    if message_type == "delta":
        global g_delta_arrived
        g_delta_arrived = True

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

def on_shadow_cb(topic, qos, payload, userdata):
    logger.debug("%s:payload:%s,userdata:%s" % (sys._getframe().f_code.co_name, payload, userdata))
    global reply
    reply = True
    pass

def wait_for_reply():
    cnt = 0
    global reply
    while cnt < 3:
        if reply is True:
            reply = False
            return 0
        time.sleep(0.5)
        cnt += 1
    return -1

def example_shadow(isTest=True):
    global logger
    provider = QcloudHub(device_file="hub/sample/device_info.json", tls=True)
    qcloud = provider.hub
    logger = qcloud.logInit(qcloud.LoggerLevel.DEBUG, "logs/log", 1024 * 1024 * 10, 5, enable=True)

    logger.debug("\033[1;36m shadow test start...\033[0m")

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

    rc, mid = qcloud.shadowInit(prduct_id, device_name, on_shadow_cb)
    if rc != 0:
        logger.error("shadowInit error")
        return False

    cnt = 0
    while True:
        cnt += 1
        p_prop = qcloud.device_property()
        p_prop.key = "updateCount"
        p_prop.data = cnt
        p_prop.type = "int"

        p_prop1 = qcloud.device_property()
        p_prop1.key = "updateCount12"
        p_prop1.data = "shadow"
        p_prop1.type = "string"

        rc, mid = qcloud.getShadow(prduct_id, device_name)
        if rc != 0:
            logger.error("getShadow error")
            return False
        rc = wait_for_reply()
        if rc != 0:
            logger.error("wait for reply timeout")
            return False

        global g_delta_arrived
        if g_delta_arrived is True and cnt%3 == 0:
            payload = qcloud.shadowJsonConstructDesireAllNull(prduct_id, device_name)
            rc, mid = qcloud.shadowUpdate(prduct_id, device_name, payload, len(payload))
            if rc != 0:
                logger.error("shadowUpdate error")
                return False
            rc = wait_for_reply()
            if rc != 0:
                logger.error("wait for reply timeout")
                return False
            g_delta_arrived= False

        payload = qcloud.shadowJsonConstructReport(prduct_id, device_name, p_prop, p_prop1)
        rc, mid = qcloud.shadowUpdate(prduct_id, device_name, payload, len(payload))
        if rc != 0:
            logger.error("shadowUpdate error")
            return False
        rc = wait_for_reply()
        if rc != 0:
            logger.error("wait for reply timeout")
            return False

        rc, mid = qcloud.getShadow(prduct_id, device_name)
        if rc != 0:
            logger.error("getShadow error")
            return False
        rc = wait_for_reply()
        if rc != 0:
            logger.error("wait for reply timeout")
            return False

        if isTest:
            break

        time.sleep(3)
    # qcloud.disconnect()
    logger.debug("\033[1;36m shadow test success...\033[0m")

    return True

