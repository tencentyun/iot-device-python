import sys
import logging
import time
from hub.hub import QcloudHub

qcloud = QcloudHub(device_file="hub/sample/scenarized/door_device_info.json", tls=True)
logger = qcloud.logInit(qcloud.LoggerLevel.DEBUG, enable=True)
reply = False

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
    global reply
    reply = True
    pass


def on_subscribe(mid, granted_qos, userdata):
    logger.debug("%s:mid:%d,granted_qos:%s,userdata:%s" % (sys._getframe().f_code.co_name, mid, granted_qos, userdata))
    pass


def on_unsubscribe(mid, userdata):
    logger.debug("%s:mid:%d,userdata:%s" % (sys._getframe().f_code.co_name, mid, userdata))
    pass

def on_door_cb(topic, qos, payload, userdata):
    logger.debug("%s:payload:%s,userdata:%s" % (sys._getframe().f_code.co_name, payload, userdata))
    
    pass

def door_publish(topic, qos, message, device):
    context = ""
    if message == "come_home" or message == "leave_home":
        context = '{"action": "%s", "targetDevice": "%s"}' % (message, device)

    logger.debug("publish %s" % context)
    qcloud.publish(topic, context, qos)
    pass


def example_door():
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
                logger.error("\033[1;31m mqtt connect fail...\033[0m")
                return False
            time.sleep(1)
            count += 1

    product_id = qcloud.getProductID()
    device_name = qcloud.getDeviceName()

    topic_list = []
    topic_format = "%s/%s/%s"
    topic_event = topic_format % (product_id, device_name, "event")
    topic_list.append((topic_event, 1))
    qcloud.registerUserCallback(topic_event, on_door_cb)

    door_publish(topic_event, 1, sys.argv[1], "AirConditioner1")

    while reply is False:
        logger.debug("wait reply...")
        time.sleep(1)

    qcloud.disconnect()

    return True
example_door()