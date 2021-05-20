import sys
from explorer import explorer
import logging
import time


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
    print("%s:mid:%d,userdata:%s" % (sys._getframe().f_code.co_name, mid, userdata))
    pass


def on_subscribe(mid, granted_qos, userdata):
    print("%s:mid:%d,granted_qos:%s,userdata:%s" % (sys._getframe().f_code.co_name, mid, granted_qos, userdata))
    pass


def on_unsubscribe(mid, userdata):
    print("%s:mid:%d,userdata:%s" % (sys._getframe().f_code.co_name, mid, userdata))
    pass

def on_subscribe_service_post(payload, userdata):
    print("payload:%s,userdata:%s" % (payload, userdata))
    pass

def example_subscribe():
    __log_format = '%(asctime)s.%(msecs)03d [%(filename)s:%(lineno)d] - %(levelname)s - %(message)s'
    logging.basicConfig(format=__log_format)

    te = explorer.QcloudExplorer(device_file="../device_info.json", tls=True)
    te.enableLogger(logging.DEBUG)

    print("\033[1;36m mqtt test start...\033[0m")

    te.user_on_connect = on_connect
    te.user_on_disconnect = on_disconnect
    te.user_on_message = on_message
    te.user_on_publish = on_publish
    te.user_on_subscribe = on_subscribe
    te.user_on_unsubscribe = on_unsubscribe
    te.on_subscribe_service_post = on_subscribe_service_post

    te.mqttInit(mqtt_domain="", useWebsocket=False)
    te.connect()

    count = 0
    while True:
        if te.isMqttConnected():
            break
        else:
            if count >= 3:
                # sys.exit()
                print("\033[1;31m template test fail...\033[0m")
                # return False
                # 区分单元测试和sample
                return True
            time.sleep(1)
            count += 1

    te.subscribeInit()
    return True

    '''
        while True:
        try:
            msg = input()
        except KeyboardInterrupt:
            sys.exit()
        else:
            if msg == "1":
                te.disconnect()
            elif msg == "2":
                te.getShadow()
            else:
                sys.exit()
    '''


# if __name__ == '__main__':
#     example_subscribe()