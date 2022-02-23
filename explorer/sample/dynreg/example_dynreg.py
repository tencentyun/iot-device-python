import sys
import time
import logging
from explorer.explorer import QcloudExplorer


logger = None

def on_connect(flags, rc, userdata):
    global logger
    logger.debug("%s:flags:%d,rc:%d,userdata:%s" % (sys._getframe().f_code.co_name, flags, rc, userdata))
    pass


def on_disconnect(rc, userdata):
    global logger
    logger.debug("%s:rc:%d,userdata:%s" % (sys._getframe().f_code.co_name, rc, userdata))
    pass


def on_message(topic, payload, qos, userdata):
    global logger
    logger.debug("%s:topic:%s,payload:%s,qos:%s,userdata:%s" % (sys._getframe().f_code.co_name, topic, payload, qos, userdata))
    pass


def on_publish(mid, userdata):
    global logger
    logger.debug("%s:mid:%d,userdata:%s" % (sys._getframe().f_code.co_name, mid, userdata))
    pass


def on_subscribe(mid, granted_qos, userdata):
    global logger
    logger.debug("%s:mid:%d,granted_qos:%s,userdata:%s" % (sys._getframe().f_code.co_name, mid, granted_qos, userdata))
    pass


def on_unsubscribe(mid, userdata):
    global logger
    logger.debug("%s:mid:%d,userdata:%s" % (sys._getframe().f_code.co_name, mid, userdata))
    pass

def example_dynreg():
    qcloud = QcloudExplorer(device_file="explorer/sample/device_info.json", tls=True)
    print("\033[1;36m dynreg test start...\033[0m")

    """
    start dynamic register
    """
    ret, msg = qcloud.dynregDevice()
    if ret == 0:
        # print("\033[1;36m dynamic register test success, psk: {}\033[0m".format(msg))
        print("\033[1;36m dynamic register test success, psk = msg 内容 \033[0m")
    else:
        print("\033[1;31m dynamic register test fail, msg: {}\033[0m".format(msg))
        return False

    """
    start mqtt connect
    """
    global logger
    logger = qcloud.logInit(qcloud.LoggerLevel.DEBUG, "logs/log", 1024*1024*10, 5, enable=True)
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

    timestamp = qcloud.getNtpAccurateTime()
    dt = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp/1000))
    logger.debug("current time:%s" % dt)

    # qcloud.disconnect()
    logger.debug("\033[1;36m dynamic register test success...\033[0m")

    return True