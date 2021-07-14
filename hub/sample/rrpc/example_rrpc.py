import sys
import logging
import time
import json
from hub.hub import QcloudHub

prduct_id = None
device_name = None
rrpc_reply = False

qcloud = QcloudHub(device_file="hub/sample/device_info.json", tls=True)
logger = qcloud.logInit(qcloud.LoggerLevel.DEBUG, enable=True)

def on_connect(flags, rc, userdata):
    logger.debug("%s:flags:%d,rc:%d,userdata:%s" % (sys._getframe().f_code.co_name, flags, rc, userdata))
    pass

def on_disconnect(rc, userdata):
    logger.debug("%s:rc:%d,userdata:%s" % (sys._getframe().f_code.co_name, rc, userdata))
    pass

def on_message(topic, qos, payload, userdata):
    logger.debug("%s:topic:%s,payload:%s,qos:%s,userdata:%s" % (sys._getframe().f_code.co_name, topic, payload, qos, userdata))
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

def on_rrpc_cb(topic, qos, payload, userdata):
    logger.debug("%s:payload:%s,userdata:%s" % (sys._getframe().f_code.co_name, payload, userdata))

    global prduct_id
    global device_name
    qcloud.rrpcReply(prduct_id, device_name, "ok", 2)
    global rrpc_reply
    rrpc_reply = True
    pass

def example_rrpc():
    logger.debug("\033[1;36m shadow test start...\033[0m")

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
                # return False
                # 区分单元测试和sample
                return True
            time.sleep(1)
            count += 1

    qcloud.rrpcInit(prduct_id, device_name, on_rrpc_cb)

    # while rrpc_reply is False:
    #     logger.debug("rrpc while...")
    #     time.sleep(1)

    qcloud.disconnect()
    logger.debug("\033[1;36m shadow test success...\033[0m")
    return True