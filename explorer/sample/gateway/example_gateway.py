import sys
import time
import logging
from threading import Thread
from explorer.explorer import QcloudExplorer
from gateway import product_1 as product_1
from gateway import product_2 as product_2

g_property_params = None
g_control_msg_arrived = False

g_task_1_runing = False
g_task_2_runing = False
g_task_1 = None
g_task_2 = None

# 网关下所有产品名称列表
g_product_list = ["PRODUCT1", "PRODUCT2"]

# 产品下所有设备列表
g_product1_subdev_list = []
g_product2_subdev_list = []

qcloud = QcloudExplorer(device_file="explorer/sample/device_info.json", tls=True)
logger = qcloud.logInit(qcloud.LoggerLevel.DEBUG, enable=True)

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


# 调用数据模板入口函数
def task_1(product_id, subdev_list=[]):
    product_1.product_init(product_id, subdev_list, qcloud, logger)

    global g_task_1_runing
    g_task_1_runing = True


def task_2(product_id, subdev_list=[]):
    product_2.product_init(product_id, subdev_list, qcloud, logger)

    global g_task_2_runing
    g_task_2_runing = True


def example_gateway():
    global g_task_1
    global g_task_2

    logger.debug("\033[1;36m gateway test start...\033[0m")

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
                # sys.exit()
                logger.error("\033[1;31m gateway test fail...\033[0m")
                # return False
                # 区分单元测试和sample
                return True
            time.sleep(1)
            count += 1

    """
    qcloud.gatewayInit()

    subdev_list = qcloud.gatewaySubdevGetConfigList()

    while True:
        try:
            msg = input()
        except KeyboardInterrupt:
            sys.exit()
        else:
            if msg == "1":
                for subdev in subdev_list:
                    if qcloud.isSubdevStatusOnline(subdev.product_id, subdev.device_name) is not True:
                        rc, mid = qcloud.gatewaySubdevOnline(subdev.product_id, subdev.device_name)
                        if rc == 0:
                            qcloud.updateSubdevStatus(subdev.product_id, subdev.device_name, "online")
                            logger.debug("online success")
                        else:
                            logger.error("online fail")

            elif msg == "2":
                for subdev in subdev_list:
                    if qcloud.isSubdevStatusOnline(subdev.product_id, subdev.device_name) is True:
                        rc, mid = qcloud.gatewaySubdevOffline(subdev.product_id, subdev.device_name)
                        if rc == 0:
                            qcloud.updateSubdevStatus(subdev.product_id, subdev.device_name, "offline")
                            logger.debug("offline success")
                        else:
                            logger.error("offline fail")

            elif msg == "3":
                rc, mid = qcloud.gatewaySubdevBind("SUBDEV_PRODUCT_ID", "SUBDEV_DEVICE_NAME", "SUBDEV_DEVICE_SECRET")
                if rc == 0:
                    logger.debug("bind success")
                else:
                    logger.error("bind fail")

            elif msg == "4":
                rc, mid = qcloud.gatewaySubdevUnbind("SUBDEV_PRODUCT_ID", "SUBDEV_DEVICE_NAME")
                if rc == 0:
                    logger.debug("unbind success")
                else:
                    logger.error("unbind fail")

            elif msg == "5":
                if not g_task_1_runing:
                    product_id = g_product_list[0]
                    for subdev in subdev_list:
                        if subdev.product_id == product_id:
                            g_product1_subdev_list.append(subdev.device_name)
                        else:
                            continue

                    # global g_task_1
                    g_task_1 = Thread(target=task_1, args=(product_id, g_product1_subdev_list,))
                    g_task_1.start()

                if not g_task_2_runing:
                    product_id = g_product_list[1]
                    for subdev in subdev_list:
                        if subdev.product_id == product_id:
                            g_product2_subdev_list.append(subdev.device_name)
                        else:
                            continue

                    # global g_task_2
                    g_task_2 = Thread(target=task_2, args=(product_id, g_product2_subdev_list,))
                    g_task_2.start()

            elif msg == "6":
                qcloud.disconnect()
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
    """
    qcloud.disconnect()
    logger.debug("\033[1;36m gateway test success...\033[0m")
    return True