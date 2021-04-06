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


def example_mqtt():
    __log_format = '%(asctime)s.%(msecs)03d [%(filename)s:%(lineno)d] - %(levelname)s - %(message)s'
    logging.basicConfig(format=__log_format)

    te = explorer.QcloudExplorer(device_file="sample/device_info.json", tls=True)
    te.enable_logger(logging.DEBUG)

    te.user_on_connect = on_connect
    te.user_on_disconnect = on_disconnect
    te.user_on_message = on_message
    te.user_on_publish = on_publish
    te.user_on_subscribe = on_subscribe
    te.user_on_unsubscribe = on_unsubscribe


    te.mqtt_init(mqtt_domain="", useWebsocket=False)
    te.connect_async()

    return True
    '''
    count = 0
    while True:
        if te.is_mqtt_connected():
            break
        else:
            if count >= 3:
                # sys.exit()
                return True
            time.sleep(1)
            count += 1


    te.shadow_init()

    while True:
        try:
            msg = input()
        except KeyboardInterrupt:
            sys.exit()
        else:
            if msg == "1":
                te.disconnect()
            elif msg == "2":
                te.shadow_getdata()
            else:
                sys.exit()
    # '''
# if __name__ == '__main__':
#     example_mqtt()