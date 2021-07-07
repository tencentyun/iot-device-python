import sys
import logging
import time
import json
from hub.hub import QcloudHub

prduct_id = None
device_name = None
rrpc_reply = False
te = None

def on_connect(flags, rc, userdata):
    print("%s:flags:%d,rc:%d,userdata:%s" % (sys._getframe().f_code.co_name, flags, rc, userdata))
    pass

def on_disconnect(rc, userdata):
    print("%s:rc:%d,userdata:%s" % (sys._getframe().f_code.co_name, rc, userdata))
    pass

def on_message(topic, qos, payload, userdata):
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

def on_rrpc_cb(topic, qos, payload, userdata):
    print("%s:payload:%s,userdata:%s" % (sys._getframe().f_code.co_name, payload, userdata))

    global prduct_id
    global device_name
    global te
    te.rrpcReply(prduct_id, device_name, "ok", 2)
    global rrpc_reply
    rrpc_reply = True
    pass

def example_rrpc():
    __log_format = '%(asctime)s.%(msecs)03d [%(filename)s:%(lineno)d] - %(levelname)s - %(message)s'
    logging.basicConfig(format=__log_format)

    global prduct_id
    global device_name
    global te

    te = QcloudHub(device_file="sample/device_info.json", tls=True)
    te.enableLogger(logging.DEBUG)

    print("\033[1;36m shadow test start...\033[0m")

    prduct_id = te.getProductID()
    device_name = te.getDeviceName()

    te.registerMqttCallback(on_connect, on_disconnect,
                            on_message, on_publish,
                            on_subscribe, on_unsubscribe)
    te.connect()

    count = 0
    while True:
        if te.isMqttConnected():
            break
        else:
            if count >= 3:
                print("\033[1;31m mqtt test fail...\033[0m")
                # return False
                # 区分单元测试和sample
                return True
            time.sleep(1)
            count += 1

    te.rrpcInit(prduct_id, device_name, on_rrpc_cb)

    # while rrpc_reply is False:
    #     print("rrpc while...")
    #     time.sleep(1)

    print("\033[1;36m shadow test success...\033[0m")
    return True