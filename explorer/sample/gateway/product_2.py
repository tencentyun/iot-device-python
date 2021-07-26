import sys
import time
import json
import logging

qcloud = None
g_property_params = None
g_control_msg_arrived = False
reply = False

def on_subdev_cb(topic, qos, payload, userdata):
    global reply
    reply = True
    pass

def on_template_property(topic, qos, payload, userdata):
    logger.debug("product_2:%s:params:%s,userdata:%s" % (sys._getframe().f_code.co_name, payload, userdata))
    global reply
    reply = True

    global qcloud
    # save changed propertys
    global g_property_params
    g_property_params = payload

    global g_control_msg_arrived
    g_control_msg_arrived = True

    # deal down stream

    # 测试,实际应发送用户属性数据
    reply_param = qcloud.ReplyPara()
    reply_param.code = 0
    reply_param.timeout_ms = 5 * 1000
    reply_param.status_msg = '\0'

    qcloud.templateControlReply(product_id, device_name, reply_param)

    pass

def on_template_service(topic, qos, payload, userdata):
    logger.debug("product_2:%s:payload:%s,userdata:%s" % (sys._getframe().f_code.co_name, payload, userdata))
    global reply
    reply = True
    pass

def on_template_event(topic, qos, payload, userdata):
    logger.debug("product_2:%s:payload:%s,userdata:%s" % (sys._getframe().f_code.co_name, payload, userdata))
    global reply
    reply = True
    pass


def on_template_action(topic, qos, payload, userdata):
    logger.debug("product_2:%s:payload:%s,userdata:%s" % (sys._getframe().f_code.co_name, payload, userdata))
    global reply
    reply = True

    global qcloud
    clientToken = payload["clientToken"]
    reply_param = qcloud.ReplyPara()
    reply_param.code = 0
    reply_param.timeout_ms = 5 * 1000
    reply_param.status_msg = "action execute success!"
    res = {
        "err_code": 0
    }

    qcloud.templateActionReply(product_id, device_name, clientToken, res, reply_param)
    pass

def report_json_construct(thing_list):

    format_string = '"%s":"%s"'
    format_int = '"%s":%d'
    report_string = '{'
    arg_cnt = 0

    for arg in thing_list:
        arg_cnt += 1
        if arg.type == "int" or arg.type == "float" or arg.type == "bool" or arg.type == "enum":
            report_string += format_int % (arg.key, arg.data)
        elif arg.type == "string":
            report_string += format_string % (arg.key, arg.data)
        else:
            logger.error("type[%s] not support" % arg.type)
            arg.data = " "
        if arg_cnt < len(thing_list):
            report_string += ","
    pass
    report_string += '}'

    json_out = json.loads(report_string)

    return json_out

def wait_for_reply():
    cnt = 0
    global reply
    while cnt < 3:
        if reply is True:
            reply = False
            return 0
        time.sleep(0.2)
        cnt += 1
    return -1

def product_init(pid, subdev_list, handle, log):
    global qcloud
    global logger
    qcloud = handle
    logger = log

    subdev = subdev_list
    global product_id
    global device_name
    product_id = pid
    device_name = subdev

    """
    订阅网关子设备topic
    """
    topic_list = []
    topic_format = "%s/%s/%s"
    topic_data = topic_format % (product_id, device_name, "data")
    topic_list.append((topic_data, 0))
    """ 注册topic对应回调 """
    qcloud.registerUserCallback(topic_data, on_subdev_cb)

    """ 订阅子设备topic,在此必须传入元组列表[(topic1,qos2),(topic2,qos2)] """
    rc, mid = qcloud.gatewaySubdevSubscribe(topic_list)
    if rc == 0:
        logger.debug("gateway subdev subscribe success")
    else:
        logger.error("gateway subdev subscribe fail")
        return -1

    qcloud.templateInit(product_id, device_name, on_template_property,
                        on_template_action, on_template_event, on_template_service)
    qcloud.templateSetup(product_id, device_name, "explorer/sample/gateway/prdouct2_config.json")

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
    rc, mid = qcloud.templateReportSysInfo(product_id, device_name, sys_info)
    if rc != 0:
        logger.error("sysinfo report fail")
        return -1
    rc = wait_for_reply()
    if rc != 0:
        logger.error("wait for report event reply timeout")
        return -1

    rc, mid = qcloud.templateGetStatus(product_id, device_name)
    if rc != 0:
        logger.error("get status fail")
        return -1
    rc = wait_for_reply()
    if rc != 0:
        logger.error("wait for report event reply timeout")
        return -1

    prop_list = qcloud.getPropertyList(product_id, device_name)
    reports = report_json_construct(prop_list)
    params_in = qcloud.templateJsonConstructReportArray(product_id, device_name, reports)
    rc, mid = qcloud.templateReport(product_id, device_name, params_in)
    if rc != 0:
        logger.error("property report fail")
        return -1
    rc = wait_for_reply()
    if rc != 0:
        logger.error("wait for report event reply timeout")
        return -1

    return 0
