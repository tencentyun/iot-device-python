import sys
import time
import logging
import threading
from hub.hub import QcloudHub
# from subdev_ota import SubdevOta
from gateway import subdev_ota as SubdevOta
# sys.path.append('.')

subdev_map = {}

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
    global subdev_map
    for subdev_ota in subdev_map.values():
        if subdev_ota is not None:
            subdev_ota.update_reply_mid(mid)
    pass

def on_subscribe(mid, granted_qos, userdata):
    print("%s:mid:%d,granted_qos:%s,userdata:%s" % (sys._getframe().f_code.co_name, mid, granted_qos, userdata))
    pass


def on_unsubscribe(mid, userdata):
    print("%s:mid:%d,userdata:%s" % (sys._getframe().f_code.co_name, mid, userdata))
    pass

def on_subdev_cb(topic, qos, payload, userdata):
    print("%s:topic:%s,payload:%s" % (sys._getframe().f_code.co_name, topic, payload))
    pass

def subdev_ota_thread(subdev_list=[]):
    for subdev in subdev_list:
        try:
            global te
            subdev_ota = SubdevOta(subdev.product_id, subdev.device_name, te)
            client = subdev.product_id + subdev.device_name
            global subdev_map
            subdev_map[client] = subdev_ota
            thread = threading.Thread(target=subdev_ota.subdev_ota_start, args=())
            thread.start()
        except:
            print("Error: unable to start thread")

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
    te.registerUserCallback(topic_data, on_subdev_cb)

    """ 订阅子设备topic,在此必须传入元组列表[(topic1,qos2),(topic2,qos2)] """
    rc, mid = te.gatewaySubdevSubscribe(topic_list)
    if rc == 0:
        print("gateway subdev subscribe success")
    else:
        print("gateway subdev subscribe fail")
    pass

def publish_subdev_message(product_id, device_name, topic_suffix):
    topic_format = "%s/%s/%s"
    topic_data = topic_format % (product_id, device_name, topic_suffix)
    message = {
        "action":"gateway subdev publish"
    }
    te.publish(topic_data, message, 1)

def example_gateway(device_file):
    __log_format = '%(asctime)s.%(msecs)03d [%(filename)s:%(lineno)d] - %(levelname)s - %(message)s'
    logging.basicConfig(format=__log_format)

    global te
    te = QcloudHub(device_file=device_file)
    te.enableLogger(logging.DEBUG)

    print("\033[1;36m gateway test start...\033[0m")

    product_id = te.getProductID()
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
                # sys.exit()
                print("\033[1;31m gateway test fail...\033[0m")
                # return False
                # 区分单元测试和sample
                return True
            time.sleep(1)
            count += 1

    te.gatewayInit()

    subdev_list = te.gatewaySubdevGetConfigList()
    """
    while True:
        try:
            msg = input()
        except KeyboardInterrupt:
            sys.exit()
        else:
            if msg == "1":
                for subdev in subdev_list:
                    print("name:%s" % subdev.device_name)
                    if te.isSubdevStatusOnline(subdev.product_id, subdev.device_name) is not True:
                        rc, mid = te.gatewaySubdevOnline(subdev.product_id, subdev.device_name)
                        if rc == 0:
                            te.updateSubdevStatus(subdev.product_id, subdev.device_name, "online")
                            subscribe_subdev_topic(subdev.product_id, subdev.device_name, "data")
                            publish_subdev_message(subdev.product_id, subdev.device_name, "data")
                            print("online success")
                        else:
                            print("online fail")

            elif msg == "2":
                for subdev in subdev_list:
                    if te.isSubdevStatusOnline(subdev.product_id, subdev.device_name) is True:
                        rc, mid = te.gatewaySubdevOffline(subdev.product_id, subdev.device_name)
                        if rc == 0:
                            te.updateSubdevStatus(subdev.product_id, subdev.device_name, "offline")
                            print("offline success")
                        else:
                            print("offline fail")

            elif msg == "3":
                rc, mid = te.gatewaySubdevBind("YOUR_SUBDEV_PRODUCT_ID",
                                                "YOUR_SUBDEV_DEVICE_NAME",
                                                "YOUR_SUBDEV_SECRET")
                if rc == 0:
                    print("bind success")
                else:
                    print("bind fail")

            elif msg == "4":
                rc, mid = te.gatewaySubdevUnbind("SUBDEV_PRODUCT_ID", "SUBDEV_DEVICE_NAME")
                if rc == 0:
                    print("unbind success")
                else:
                    print("unbind fail")

            elif msg == "5":
                bind_list = []
                bind_list = te.gatewaySubdevGetBindList(product_id, device_name)
                for subdev in bind_list:
                    print("subdev id:%s, name:%s" % (subdev.product_id, subdev.device_name))

            elif msg == "6":
                # 子设备固件升级
                subdev_ota_thread(subdev_list)
            elif msg == "7":
                te.disconnect()

            else:
                sys.exit()
    """
    te.disconnect()
    print("\033[1;36m gateway test success...\033[0m")
    return True
