import sys
import time
import logging


__log_format = '%(asctime)s.%(msecs)03d [%(filename)s:%(lineno)d] - %(levelname)s - %(message)s'
logging.basicConfig(format=__log_format)

g_te = None
g_property_params = None
g_control_msg_arrived = False


def on_template_prop_changed(params, userdata):
    print("product_001:%s:params:%s,userdata:%s" % (sys._getframe().f_code.co_name, params, userdata))

    global g_te
    te = g_te
    # save changed propertys
    global g_property_params
    g_property_params = params

    global g_control_msg_arrived
    g_control_msg_arrived = True

    # deal down stream

    # 测试,实际应发送用户属性数据
    reply_param = te.sReplyPara()
    reply_param.code = 0
    reply_param.timeout_ms = 5 * 1000
    reply_param.status_msg = '\0'

    te.template_control_reply(reply_param)

    pass


def on_template_event_post(payload, userdata):
    print("product_001:%s:payload:%s,userdata:%s" % (sys._getframe().f_code.co_name, payload, userdata))
    pass


def on_template_action(payload, userdata):
    print("product_001:%s:payload:%s,userdata:%s" % (sys._getframe().f_code.co_name, payload, userdata))

    global g_te
    te = g_te

    clientToken = payload["clientToken"]

    """
    actionId = payload["actionId"]
    timestamp = payload["timestamp"]
    params = payload["params"]
    """

    reply_param = te.sReplyPara()
    reply_param.code = 0
    reply_param.timeout_ms = 5 * 1000
    reply_param.status_msg = "action execute success!"
    res = {
        "err_code": 0
    }

    te.template_action_reply(clientToken, res, reply_param)
    pass


def product_init(product_id, subdev_list, te):

    print("product_001:=========%s==========" % product_id)
    global g_te
    g_te = te

    # 注册数据模板回调函数
    te.register_user_property_callback(product_id, on_template_prop_changed)
    te.register_user_action_callback(product_id, on_template_action)
    te.register_user_event_callback(product_id, on_template_event_post)

    te.template_setup("./ZPHBLEB4J5_config.json")

    """
    # 保存自身property list
    prop_list = te.template_property_list
    event_list = te.template_events_list
    action_list = te.template_action_list
    """

    topic_property_format = "$thing/down/property/%s/%s"
    topic_action_format = "$thing/down/action/%s/%s"
    topic_event_format = "$thing/down/event/%s/%s"

    topic_property_list = []
    topic_action_list = []
    topic_event_list = []
    for subdev in subdev_list:

        topic_property = topic_property_format % (product_id, subdev)
        topic_property_list.append((topic_property, 0))

        topic_action = topic_action_format % (product_id, subdev)
        topic_action_list.append((topic_action, 0))

        topic_event = topic_event_format % (product_id, subdev)
        topic_event_list.append((topic_event, 0))

    # 订阅子设备topic,在此必须传入元组列表[(topic1,qos2),(topic2,qos2)]
    rc = te.gateway_subdev_template_subscribe(product_id, topic_property_list, topic_action_list, topic_event_list)
    if rc == 0:
        print("gateway_subdev_template_subscribe success")
    else:
        print("gateway_subdev_template_subscribe fail")

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
    rc = te.template_report_sys_info(sys_info)
    if rc != 0:
        print("sysinfo report fail")
        return 1

    rc = te.template_get_status()
    if rc != 0:
        print("get status fail")
        return 1

    while te.is_mqtt_connected():

        # add user logic
        """
        if g_control_msg_arrived:
            params_in = te.template_json_construct_report_array(g_property_params)
            te.template_report(params_in)
        else:
            reports = {
                prop_list[0].key: prop_list[0].data,
                prop_list[1].key: prop_list[1].data,
                prop_list[2].key: prop_list[2].data,
                prop_list[3].key: prop_list[3].data
            }

            params_in = te.template_json_construct_report_array(reports)
            te.template_report(params_in)
        """

        time.sleep(1)
