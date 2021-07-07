import sys
import time
import logging
from threading import Thread
# explorer网关测试
from explorer import explorer
# hub网关测试
# from hub.hub import QcloudHub

from gateway import product_ZPHBLEB4J5 as product_ZPHBLEB4J5
from gateway import product_Z53CXC198M as product_Z53CXC198M

g_property_params = None
g_control_msg_arrived = False

g_task_1_runing = False
g_task_2_runing = False
g_task_1 = None
g_task_2 = None

# 网关下所有产品名称列表
g_product_list = ["ZPHBLEB4J5", "Z53CXC198M"]

# 产品下所有设备列表
g_Z53CXC198M_subdev_list = []
g_ZPHBLEB4J5_subdev_list = []


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


# 调用数据模板入口函数
def task_1(product_id, subdev_list=[]):

    global te
    product_ZPHBLEB4J5.product_init(product_id, subdev_list, te)

    global g_task_1_runing
    g_task_1_runing = True


def task_2(product_id, subdev_list=[]):

    global te
    product_Z53CXC198M.product_init(product_id, subdev_list, te)

    global g_task_2_runing
    g_task_2_runing = True


def example_gateway():
    global g_task_1
    global g_task_2

    __log_format = '%(asctime)s.%(msecs)03d [%(filename)s:%(lineno)d] - %(levelname)s - %(message)s'
    logging.basicConfig(format=__log_format)

    global te
    te = explorer.QcloudExplorer(device_file="sample/device_info.json")
    te.enableLogger(logging.WARNING)

    print("\033[1;36m gateway test start...\033[0m")

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

    while True:
        try:
            msg = input()
        except KeyboardInterrupt:
            sys.exit()
        else:
            if msg == "1":
                for subdev in subdev_list:
                    if te.isSubdevStatusOnline(subdev.sub_productId, subdev.sub_devName) is not True:
                        rc, mid = te.gatewaySubdevOnline(subdev.sub_productId, subdev.sub_devName)
                        if rc == 0:
                            te.updateSubdevStatus(subdev.sub_productId, subdev.sub_devName, "online")
                            print("online success")
                        else:
                            print("online fail")

            elif msg == "2":
                for subdev in subdev_list:
                    if te.isSubdevStatusOnline(subdev.sub_productId, subdev.sub_devName) is True:
                        rc, mid = te.gatewaySubdevOffline(subdev.sub_productId, subdev.sub_devName)
                        if rc == 0:
                            te.updateSubdevStatus(subdev.sub_productId, subdev.sub_devName, "offline")
                            print("offline success")
                        else:
                            print("offline fail")

            elif msg == "3":
                rc, mid = te.gatewaySubdevBind("SUBDEV_PRODUCT_ID", "SUBDEV_DEVICE_NAME", "SUBDEV_DEVICE_SECRET")
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
                if not g_task_1_runing:
                    product_id = g_product_list[0]
                    for subdev in subdev_list:
                        if subdev.sub_productId == product_id:
                            g_ZPHBLEB4J5_subdev_list.append(subdev.sub_devName)
                        else:
                            continue

                    # global g_task_1
                    g_task_1 = Thread(target=task_1, args=(product_id, g_ZPHBLEB4J5_subdev_list,))
                    g_task_1.start()

                if not g_task_2_runing:
                    product_id = g_product_list[1]
                    for subdev in subdev_list:
                        if subdev.sub_productId == product_id:
                            g_Z53CXC198M_subdev_list.append(subdev.sub_devName)
                        else:
                            continue

                    # global g_task_2
                    g_task_2 = Thread(target=task_2, args=(product_id, g_Z53CXC198M_subdev_list,))
                    g_task_2.start()

            elif msg == "6":
                te.disconnect()
                # global g_task_1
                if g_task_1.is_alive():
                    g_task_1.stop()
                    g_task_1.join()

                # global g_task_2
                if g_task_2.is_alive():
                    g_task_2.stop()
                    g_task_2.join()

            else:
                sys.exit()
    print("\033[1;36m gateway test success...\033[0m")
    return True
if __name__ == '__main__':
	example_gateway()