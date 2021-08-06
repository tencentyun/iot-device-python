import sys
import time
import logging
import threading
from hub.hub import QcloudHub
from gateway import subdev_ota as SubdevOta

provider = QcloudHub(device_file="hub/sample/device_info.json", tls=True)
qcloud = provider.hub
logger = qcloud.logInit(qcloud.LoggerLevel.DEBUG, "logs/log", 1024*1024*10, 5, enable=True)

subdev_map = {}
thread_list = []

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
    global subdev_map
    for subdev_ota in subdev_map.values():
        if subdev_ota is not None:
            subdev_ota.update_reply_mid(mid)
    pass

def on_subscribe(mid, granted_qos, userdata):
    logger.debug("%s:mid:%d,granted_qos:%s,userdata:%s" % (sys._getframe().f_code.co_name, mid, granted_qos, userdata))
    pass


def on_unsubscribe(mid, userdata):
    logger.debug("%s:mid:%d,userdata:%s" % (sys._getframe().f_code.co_name, mid, userdata))
    pass

def on_subdev_cb(topic, qos, payload, userdata):
    logger.debug("%s:topic:%s,payload:%s" % (sys._getframe().f_code.co_name, topic, payload))
    pass

def subdev_ota_thread(isTest, subdev_list=[]):
    for subdev in subdev_list:
        try:
            subdev_ota = SubdevOta(subdev.product_id, subdev.device_name, qcloud, logger)
            client = subdev.product_id + subdev.device_name
            global subdev_map
            subdev_map[client] = subdev_ota
            thread = threading.Thread(target=subdev_ota.subdev_ota_start, args=(isTest))
            global thread_list
            thread_list.append(thread)
            thread.start()
        except:
            logger.error("Error: unable to start thread")

def subscribe_subdev_topic(product_id, device_name, topic_suffix):
    """
    订阅网关子设备topic
    eg:${productId}/${deviceName}/data
    """
    topic_list = []
    topic_format = "%s/%s/%s"
    topic_data = topic_format % (product_id, device_name, topic_suffix)
    topic_list.append((topic_data, 0))
    """ 注册topic对应回调 """
    qcloud.registerUserCallback(topic_data, on_subdev_cb)

    """ 订阅子设备topic,在此必须传入元组列表[(topic1,qos2),(topic2,qos2)] """
    rc, mid = qcloud.gatewaySubdevSubscribe(topic_list)
    if rc == 0:
        logger.debug("gateway subdev subscribe success")
    else:
        logger.error("gateway subdev subscribe fail")
    pass

def publish_subdev_message(product_id, device_name, topic_suffix):
    topic_format = "%s/%s/%s"
    topic_data = topic_format % (product_id, device_name, topic_suffix)
    message = {
        "action":"gateway subdev publish"
    }
    qcloud.publish(topic_data, message, 1)

def example_gateway(isTest=True):
    logger.debug("\033[1;36m gateway test start...\033[0m")

    product_id = qcloud.getProductID()
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
                logger.error("\033[1;31m gateway test fail...\033[0m")
                return False
            time.sleep(1)
            count += 1

    qcloud.gatewayInit()

    subdev_list = qcloud.gatewaySubdevGetConfigList()

    """sub-device online"""
    for subdev in subdev_list:
        if qcloud.isSubdevStatusOnline(subdev.product_id, subdev.device_name) is not True:
            rc, mid = qcloud.gatewaySubdevOnline(subdev.product_id, subdev.device_name)
            if rc == 0:
                qcloud.updateSubdevStatus(subdev.product_id, subdev.device_name, "online")
                subscribe_subdev_topic(subdev.product_id, subdev.device_name, "data")
                publish_subdev_message(subdev.product_id, subdev.device_name, "data")
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

    """
    rc, mid = qcloud.gatewaySubdevBind("YOUR_SUBDEV_PRODUCT_ID",
                                        "YOUR_SUBDEV_DEVICE_NAME",
                                        "YOUR_SUBDEV_SECRET")
    if rc == 0:
        logger.debug("bind success")
    else:
        logger.error("bind fail")
        return False

    rc, mid = qcloud.gatewaySubdevUnbind("SUBDEV_PRODUCT_ID", "SUBDEV_DEVICE_NAME")
    if rc == 0:
        logger.debug("unbind success")
    else:
        logger.error("unbind fail")
        return False
    """

    bind_list = []
    rc, bind_list = qcloud.gatewaySubdevGetBindList(product_id, device_name)
    if rc != 0:
        logger.error("get bind list error")
        return False
    
    """子设备固件升级"""
    subdev_ota_thread(isTest, subdev_list)
    for thread in thread_list:
        thread.join()

    # qcloud.disconnect()
    logger.debug("\033[1;36m gateway test success...\033[0m")
    return True
