import sys
import time
import json
import logging

__log_format = '%(asctime)s.%(msecs)03d [%(filename)s:%(lineno)d] - %(levelname)s - %(message)s'
logging.basicConfig(format=__log_format)

g_te = None
g_property_params = None
g_control_msg_arrived = False

topic_property = None
topic_action = None
topic_event = None
topic_list = []

def _template_prop(params, userdata):
    print("product_002:%s:params:%s,userdata:%s" % (sys._getframe().f_code.co_name, params, userdata))

    global g_te
    te = g_te
    # save changed propertys
    global g_property_params
    g_property_params = params

    global g_control_msg_arrived
    g_control_msg_arrived = True

    # deal down stream

    # 测试,实际应发送用户属性数据
    reply_param = te.ReplyPara()
    reply_param.code = 0
    reply_param.timeout_ms = 5 * 1000
    reply_param.status_msg = '\0'

    te.templateControlReply(product_id, device_name, reply_param)

    pass


def _template_event_post(payload, userdata):
    print("product_002:%s:payload:%s,userdata:%s" % (sys._getframe().f_code.co_name, payload, userdata))
    pass


def _template_action(payload, userdata):
    print("product_002:%s:payload:%s,userdata:%s" % (sys._getframe().f_code.co_name, payload, userdata))

    global g_te
    te = g_te

    clientToken = payload["clientToken"]

    reply_param = te.ReplyPara()
    reply_param.code = 0
    reply_param.timeout_ms = 5 * 1000
    reply_param.status_msg = "action execute success!"
    res = {
        "err_code": 0
    }

    te.templateActionReply(product_id, device_name, clientToken, res, reply_param)
    pass

def on_template_changed(topic, qos, payload, userdata):
    print("product_002:%s:payload:%s,userdata:%s" % (sys._getframe().f_code.co_name, payload, userdata))
    global topic_property
    global topic_action
    global topic_event

    if topic == topic_property:
        _template_prop(payload, userdata)
    elif topic == topic_action:
        _template_action(payload, userdata)
    elif topic == topic_event:
        _template_event_post(payload, userdata)
    else:
        print("unkonw topic %s" % topic)

def product_init(pid, subdev_list, te):

    print("product_002:=========%s==========" % pid)
    global g_te
    g_te = te

    subdev = subdev_list[0]
    global product_id
    global device_name
    product_id = pid
    device_name = subdev

    global topic_property
    global topic_action
    global topic_event
    topic_property = "$thing/down/property/%s/%s" % (product_id, device_name)
    topic_action = "$thing/down/action/%s/%s" % (product_id, device_name)
    topic_event = "$thing/down/event/%s/%s" % (product_id, device_name)
    te.registerUserCallback(topic_property, on_template_changed)
    te.registerUserCallback(topic_action, on_template_changed)
    te.registerUserCallback(topic_event, on_template_changed)

    """
    订阅网关子设备topic
    """
    topic_format = "%s/%s/%s"
    topic_data = topic_format % (product_id, device_name, "data")
    topic_list.append((topic_data, 0))
    """ 注册topic对应回调 """
    te.registerUserCallback(topic_data, on_template_changed)

    topic_control = topic_format % (product_id, device_name, "control")
    topic_list.append((topic_control, 0))
    """ 注册topic对应回调 """
    te.registerUserCallback(topic_control, on_template_changed)

    """ 订阅子设备topic,在此必须传入元组列表[(topic1,qos2),(topic2,qos2)] """
    rc, mid = te.gatewaySubdevSubscribe(topic_list)
    if rc == 0:
        print("gateway subdev subscribe success")
    else:
        print("gateway subdev subscribe fail")


    te.templateInit(product_id, device_name)
    te.templateSetup(product_id, device_name, "sample/gateway/Z53CXC198M_config.json")
    # sysinfo report
    sys_info = {
        "module_hardinfo": "ESP8266",
        "module_softinfo": "V1.0",
        "fw_ver": "3.1.4",
        "imei": "11-22-33-44",
        "lat": "22.546015",
        "lon": "113.941125",
        "device_label": {
            "append_info": "your self define info"
        }
    }
    rc, mid = te.templateReportSysInfo(product_id, device_name, sys_info)
    if rc != 0:
        print("sysinfo report fail")
        return 1

    rc, mid = te.templateGetStatus(product_id, device_name)
    if rc != 0:
        print("get status fail")
        return 1

    while te.isMqttConnected():
        prop_list = te.getPropertyList(product_id, device_name)
        reports = {
            prop_list[0].key: prop_list[0].data,
            prop_list[1].key: prop_list[1].data,
            prop_list[2].key: prop_list[2].data,
            prop_list[3].key: prop_list[3].data
        }
        params_in = te.templateJsonConstructReportArray(product_id, device_name, reports)
        te.templateReport(product_id, device_name, params_in)

        time.sleep(3)
