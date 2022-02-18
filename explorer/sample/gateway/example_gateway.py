import sys
import time
import logging
import threading
from explorer.explorer import QcloudExplorer
from gateway import product_1 as product_1
from gateway import product_2 as product_2

g_property_params = None
g_control_msg_arrived = False

product_list = []
thread_list = []

logger = None

def on_connect(flags, rc, userdata):
    logger.debug("%s:flags:%d,rc:%d,userdata:%s" % (sys._getframe().f_code.co_name, flags, rc, userdata))
    pass


def on_disconnect(rc, userdata):
    logger.debug("%s:rc:%d,userdata:%s" % (sys._getframe().f_code.co_name, rc, userdata))
    pass


def on_message(topic, payload, qos, userdata):
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

def example_gateway():
    global logger
    qcloud = QcloudExplorer(device_file="explorer/sample/device_info.json", tls=True)
    logger = qcloud.logInit(qcloud.LoggerLevel.DEBUG, "logs/log", 1024 * 1024 * 10, 5, enable=True)

    logger.debug("\033[1;36m gateway test start...\033[0m")

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
                logger.error("\033[1;31m gateway test fail...\033[0m")
                return False
            time.sleep(1)
            count += 1

    qcloud.gatewayInit()

    """sub-device online"""
    subdev_list = qcloud.gatewaySubdevGetConfigList()
    for subdev in subdev_list:
        if qcloud.isSubdevStatusOnline(subdev.product_id, subdev.device_name) is not True:
            rc, mid = qcloud.gatewaySubdevOnline(subdev.product_id, subdev.device_name)
            if rc == 0:
                qcloud.updateSubdevStatus(subdev.product_id, subdev.device_name, "online")
                logger.debug("online success")
            else:
                logger.error("online fail")
                return False

    """sub-device offline"""
    for subdev in subdev_list:
        if qcloud.isSubdevStatusOnline(subdev.product_id, subdev.device_name) is True:
            rc, mid = qcloud.gatewaySubdevOffline(subdev.product_id, subdev.device_name)
            if rc == 0:
                qcloud.updateSubdevStatus(subdev.product_id, subdev.device_name, "offline")
                logger.debug("offline success")
            else:
                logger.error("offline fail")
                return False

    # """sub-device bind"""
    # rc, mid = qcloud.gatewaySubdevBind("SUBDEV_PRODUCT_ID", "SUBDEV_DEVICE_NAME", "SUBDEV_DEVICE_SECRET")
    # if rc == 0:
    #     logger.debug("bind success")
    # else:
    #     logger.error("bind fail")
    #     return False

    # """sub-device unbind"""
    # rc, mid = qcloud.gatewaySubdevUnbind("SUBDEV_PRODUCT_ID", "SUBDEV_DEVICE_NAME")
    # if rc == 0:
    #     logger.debug("unbind success")
    # else:
    #     logger.error("unbind fail")
    #     return False

    product_list.append(product_1)
    product_list.append(product_2)
    index = 0
    """sub-device affairs"""
    for subdev in subdev_list:
        if index >= len(product_list):
            break
        try:
            thread = threading.Thread(target=product_list[index].product_init, args=(subdev.product_id, subdev.device_name, qcloud, logger))
            global thread_list
            thread_list.append(thread)
            thread.start()
        except:
            logger.error("Error: unable to start thread")
            return False
        index += 1

    for thread in thread_list:
        thread.join()

    # qcloud.disconnect()
    logger.debug("\033[1;36m gateway test success...\033[0m")

    return True