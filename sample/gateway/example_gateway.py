import sys
import time
import logging
from threading import Thread
from explorer import explorer
import product_ZPHBLEB4J5
import product_Z53CXC198M


__log_format = '%(asctime)s.%(msecs)03d [%(filename)s:%(lineno)d] - %(levelname)s - %(message)s'
logging.basicConfig(format=__log_format)

te = explorer.QcloudExplorer(device_file="./device_info.json")
te.enable_logger(logging.DEBUG)

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


te.user_on_connect = on_connect
te.user_on_disconnect = on_disconnect
te.user_on_message = on_message
te.user_on_publish = on_publish
te.user_on_subscribe = on_subscribe
te.user_on_unsubscribe = on_unsubscribe


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


te.mqtt_init(mqtt_domain="")
te.connect_async()

count = 0
while True:
    if te.is_mqtt_connected():
        break
    else:
        if count >= 3:
            sys.exit()
        time.sleep(1)
        count += 1


te.gateway_init()

# 获取到子设备信息后,在此维护设备状态,sdk中不处理设备状态
subdev_list = te.gateway_subdev_list

while True:
    try:
        msg = input()
    except KeyboardInterrupt:
        sys.exit()
    else:
        if msg == "1":
            for subdev in subdev_list:
                if subdev.session_status is not te.SessionState.SUBDEV_SEESION_STATUS_ONLINE:
                    rc = te.gateway_subdev_online_offline("online", subdev.sub_productId, subdev.sub_devName)
                    if rc == 0:
                        subdev.session_status = te.SessionState.SUBDEV_SEESION_STATUS_ONLINE
                        print("online success")
                    else:
                        print("online fail")

        elif msg == "2":
            for subdev in subdev_list:
                if subdev.session_status == te.SessionState.SUBDEV_SEESION_STATUS_ONLINE:
                    rc = te.gateway_subdev_online_offline("offline", subdev.sub_productId, subdev.sub_devName)
                    if rc == 0:
                        subdev.session_status = te.SessionState.SUBDEV_SEESION_STATUS_OFFLINE
                        print("offline success")
                    else:
                        print("offline fail")

        elif msg == "3":
            rc = te.gateway_subdev_bind_unbind("bind", "Z53CXC198M", "dev2", "McP73GqPW0cDmZ5q+O3jdg==")
            if rc == 0:
                print("bind success")
            else:
                print("bind fail")

        elif msg == "4":
            rc = te.gateway_subdev_bind_unbind("unbind", "Z53CXC198M", "dev2", None)
            if rc == 0:
                print("unbind success")
            else:
                print("unbind fail")

        elif msg == "5":
            """
            # 废弃
            report = {
                "method": "report",
                "clientToken": "123",
                "params": {}
            }
            topic_format = "$thing/up/property/%s/%s"
            for subdev in subdev_list:
                if subdev.session_status == te.SessionState.SUBDEV_SEESION_STATUS_ONLINE:
                    topic = topic_format % (subdev.sub_productId, subdev.sub_devName)
                    rc = te.gateway_publish(topic, report)
                    if rc == 0:
                        print("gateway_publish success")
                    else:
                        print("gateway_publish fail")
            """
        elif msg == "6":
            if not g_task_1_runing:
                product_id = g_product_list[0]
                for subdev in subdev_list:
                    if subdev.sub_productId == product_id:
                        g_ZPHBLEB4J5_subdev_list.append(subdev.sub_devName)
                    else:
                        continue

                global g_task_1
                g_task_1 = Thread(target=task_1, args=(product_id, g_ZPHBLEB4J5_subdev_list,))
                g_task_1.start()

            if not g_task_2_runing:
                product_id = g_product_list[1]
                for subdev in subdev_list:
                    if subdev.sub_productId == product_id:
                        g_Z53CXC198M_subdev_list.append(subdev.sub_devName)
                    else:
                        continue

                global g_task_2
                g_task_2 = Thread(target=task_2, args=(product_id, g_Z53CXC198M_subdev_list,))
                g_task_2.start()

        elif msg == "7":
            te.disconnect()
            global g_task_1
            if g_task_1.is_alive():
                g_task_1.stop()
                g_task_1.join()

            global g_task_2
            if g_task_2.is_alive():
                g_task_2.stop()
                g_task_2.join()

        else:
            sys.exit()
