import sys
import logging
import time
import json
from hub.hub import QcloudHub

qcloud = QcloudHub(device_file="hub/sample/scenarized/aircond_device_info.json", tls=True)
logger = qcloud.logInit(qcloud.LoggerLevel.DEBUG, "logs/log", 1024*1024*10, 5, enable=True)
reply = False
air_open = False

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

def on_aircond_cb(topic, qos, payload, userdata):
    logger.debug("%s:payload:%s,userdata:%s" % (sys._getframe().f_code.co_name, payload, userdata))
    global reply
    reply = True

    cmd = json.loads(payload)
    action = cmd["action"]
    global air_open
    if action == "come_home":
        air_open = True
    elif action == "leave_home":
        air_open = False

    pass

def example_aircond():

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
    topic_control = topic_format % (product_id, device_name, "control")
    topic_list.append((topic_control, 1))
    qcloud.registerUserCallback(topic_control, on_aircond_cb)
    qcloud.subscribe(topic_control, 1)

    temperature = 25
    while True:
        global air_open
        if temperature >= 40:
            temperature = 40
        if temperature <= -10:
            temperature = -10

        if air_open is True:
            logger.debug("[air is open] temperature %d" % temperature)
            temperature -= 0.5
        else:
            logger.debug("[air is close] temperature %d" % temperature)
            temperature += 0.5
        time.sleep(1)

    qcloud.disconnect()
    return True
example_aircond()