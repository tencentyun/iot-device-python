import sys
import time
import json
import logging
from explorer import explorer

__log_format = '%(asctime)s.%(msecs)03d [%(filename)s:%(lineno)d] - %(levelname)s - %(message)s'
logging.basicConfig(format=__log_format)

g_property_params = None
g_control_msg_arrived = False
te = None
product_id = None
device_name = None

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


def on_template_property(topic, qos, payload, userdata):
    print("product_1:%s:params:%s,userdata:%s" % (sys._getframe().f_code.co_name, payload, userdata))

    # save changed propertys
    global g_property_params
    g_property_params = payload

    global g_control_msg_arrived
    g_control_msg_arrived = True

    # deal down stream and add your real value

    global te
    reply_param = te.ReplyPara()
    reply_param.code = 0
    reply_param.timeout_ms = 5 * 1000
    reply_param.status_msg = '\0'

    te.templateControlReply(product_id, device_name, reply_param)
    pass

def on_template_service(topic, qos, payload, userdata):
    print("product_1:%s:payload:%s,userdata:%s" % (sys._getframe().f_code.co_name, payload, userdata))
    pass

def on_template_event(topic, qos, payload, userdata):
    print("product_1:%s:payload:%s,userdata:%s" % (sys._getframe().f_code.co_name, payload, userdata))
    pass


def on_template_action(topic, qos, payload, userdata):
    print("product_1:%s:payload:%s,userdata:%s" % (sys._getframe().f_code.co_name, payload, userdata))

    global te
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

def report_json_construct_property(thing_list):

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
            print("type[%s] not support" % arg.type)
            arg.data = " "
        if arg_cnt < len(thing_list):
            report_string += ","
    pass
    report_string += '}'

    json_out = json.loads(report_string)

    return json_out

def report_json_construct_events(event_list):
    # deal events and add your real value
    status = 1
    message = "test"
    voltage = 20.0
    name = "memory"
    error_code = 0
    timestamp = int(round(time.time() * 1000))

    format_string = '"%s":"%s",'
    format_int = '"%s":%d,'
    events = []
    for event in event_list:
        string = '{'
        string += format_string % ("eventId", event.event_name)
        string += format_string % ("type", event.type)
        string += format_int % ("timestamp", timestamp)
        string += '"params":{'
        for prop in event.events_prop:
            if (prop.type == "int" or prop.type == "float"
                    or prop.type == "bool" or prop.type == "enum"):
                if prop.key == "status":
                    string += format_int % (prop.key, status)
                elif prop.key == "voltage":
                    string += format_int % (prop.key, voltage)
                elif prop.key == "error_code":
                    string += format_int % (prop.key, error_code)
            elif prop.type == "string":
                if prop.key == "message":
                    string += format_string % (prop.key, message)
                elif prop.key == "name":
                    string += format_string % (prop.key, name)

        string = string[:len(string) - 1]
        string += "}}"
        events.append(json.loads(string))

    json_out = '{"events":%s}' % json.dumps(events)

    return json.loads(json_out)

def example_template():

    print("\033[1;36m template test start...\033[0m")
    global te
    te = explorer.QcloudExplorer(device_file="sample/device_info.json")
    te.enableLogger(logging.DEBUG)
    te.registerMqttCallback(on_connect, on_disconnect,
                            on_message, on_publish,
                            on_subscribe, on_unsubscribe)

    global product_id
    global device_name
    product_id = te.getProductID()
    device_name = te.getDeviceName()

    te.connect()

    count = 0
    while True:
        if te.isMqttConnected():
            break
        else:
            if count >= 3:
                # sys.exit()
                print("\033[1;31m template test fail...\033[0m")
                # return False
                # 区分单元测试和sample
                return True
            time.sleep(1)
            count += 1

    te.templateInit(product_id, device_name, on_template_property,
                        on_template_action, on_template_event, on_template_service)
    te.templateSetup(product_id, device_name, "sample/template/template_config.json")

    """
    while True:
        try:
            msg = input()
        except KeyboardInterrupt:
            sys.exit()
        else:
            if msg == "1":
                # you should get real info
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
                te.templateReportSysInfo(product_id, device_name, sys_info)
            elif msg == "2":
                te.templateGetStatus(product_id, device_name, )
            elif msg == "3":
                if g_control_msg_arrived:
                    params_in = te.templateJsonConstructReportArray(product_id, device_name, g_property_params)
                    te.templateReport(product_id, device_name, params_in)
                else:
                    prop_list = te.getPropertyList(product_id, device_name)
                    reports = report_json_construct_property(prop_list)

                    params_in = te.templateJsonConstructReportArray(product_id, device_name, reports)
                    te.templateReport(product_id, device_name, params_in)

            elif msg == "4":
                event_list = te.getEventsList(product_id, device_name)
                events = report_json_construct_events(event_list)

                te.templateEventPost(product_id, device_name, events)

            elif msg == "5":
                te.templateDeinit(product_id, device_name)

            elif msg == "6":
                te.disconnect()

            elif msg == "7":
                te.clearControl(product_id, device_name)

            else:
                sys.exit()
    """
    print("\033[1;36m template test success...\033[0m")
    return True