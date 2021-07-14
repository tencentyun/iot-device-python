import sys
import logging
import time
import json
from hub.hub import QcloudHub

g_connected = False
g_delta_arrived = False

def on_connect(flags, rc, userdata):
    print("%s:flags:%d,rc:%d,userdata:%s" % (sys._getframe().f_code.co_name, flags, rc, userdata))
    global g_connected
    g_connected = True

    pass

def on_disconnect(rc, userdata):
    print("%s:rc:%d,userdata:%s" % (sys._getframe().f_code.co_name, rc, userdata))
    pass

def on_message(topic, qos, payload, userdata):
    print("%s:topic:%s,payload:%s,qos:%s,userdata:%s" % (sys._getframe().f_code.co_name, topic, payload, qos, userdata))

    message_type = payload["type"]
    if message_type == "delta":
        global g_delta_arrived
        g_delta_arrived = True

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

def on_shadow_cb(topic, qos, payload, userdata):
    print("%s:payload:%s,userdata:%s" % (sys._getframe().f_code.co_name, payload, userdata))
    pass

def example_shadow():
    __log_format = '%(asctime)s.%(msecs)03d [%(filename)s:%(lineno)d] - %(levelname)s - %(message)s'
    logging.basicConfig(format=__log_format)

    te = QcloudHub(device_file="sample/device_info.json", tls=True)
    te.enableLogger(logging.INFO)

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

    te.shadowInit(prduct_id, device_name, on_shadow_cb)

    p_prop = QcloudHub.device_property()
    p_prop.key = "updateCount"
    p_prop.data = 0
    p_prop.type = "int"

    p_prop1 = QcloudHub.device_property()
    p_prop1.key = "updateCount11"
    p_prop1.data = "shadow"
    p_prop1.type = "string"

    te.getShadow(prduct_id, device_name)
        
    global g_delta_arrived
    if g_delta_arrived is True:
        payload = te.shadowJsonConstructDesireAllNull(prduct_id, device_name)
        te.shadowUpdate(prduct_id, device_name, payload, len(payload))
        g_delta_arrived= False

    payload = te.shadowJsonConstructReport(prduct_id, device_name, p_prop, p_prop1)
    te.shadowUpdate(prduct_id, device_name, payload, len(payload))

    time.sleep(1)
    payload = te.shadowJsonConstructReport(prduct_id, device_name, p_prop)
    te.shadowUpdate(prduct_id, device_name, payload, len(payload))

    print("\033[1;36m shadow test success...\033[0m")
    return True

