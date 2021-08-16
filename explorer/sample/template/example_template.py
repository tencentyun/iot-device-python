import sys
import time
import json
import logging
from explorer.explorer import QcloudExplorer

product_id = None
device_name = None
reply = False

qcloud = QcloudExplorer(device_file="explorer/sample/device_info.json", tls=True)
logger = qcloud.logInit(qcloud.LoggerLevel.DEBUG, "logs/log", 1024*1024*10, 5, enable=True)

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


def on_subscribe(qos, mid, userdata):
    logger.debug("%s:mid:%d,qos:%s,userdata:%s" % (sys._getframe().f_code.co_name, mid, qos, userdata))
    pass


def on_unsubscribe(mid, userdata):
    logger.debug("%s:mid:%d,userdata:%s" % (sys._getframe().f_code.co_name, mid, userdata))
    pass


def on_template_property(topic, qos, payload, userdata):
    logger.debug("%s:params:%s,userdata:%s" % (sys._getframe().f_code.co_name, payload, userdata))

    # save changed property
    global reply
    reply = True

    # deal down stream and add your real value

    reply_param = qcloud.ReplyPara()
    reply_param.code = 0
    reply_param.timeout_ms = 5 * 1000
    reply_param.status_msg = '\0'

    qcloud.templateControlReply(product_id, device_name, reply_param)
    pass

def on_template_service(topic, qos, payload, userdata):
    logger.debug("%s:payload:%s,userdata:%s" % (sys._getframe().f_code.co_name, payload, userdata))
    pass

def on_template_event(topic, qos, payload, userdata):
    logger.debug("%s:payload:%s,userdata:%s" % (sys._getframe().f_code.co_name, payload, userdata))
    global reply
    reply = True
    pass


def on_template_action(topic, qos, payload, userdata):
    logger.debug("%s:payload:%s,userdata:%s" % (sys._getframe().f_code.co_name, payload, userdata))
    global reply
    reply = True

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

def report_json_construct_property(thing_list):

    format_string = '"%s":"%s"'
    format_int = '"%s":%d'
    report_string = '{'
    arg_cnt = 0

    for arg in thing_list:
        arg_cnt += 1
        if arg.type == "int" or arg.type == "float" or arg.type == "bool" or arg.type == "enum":
            report_string += format_int % (arg.key, arg.data + 1)
        elif arg.type == "string":
            report_string += format_string % (arg.key, arg.data + "test")
        else:
            logger.err_code("type[%s] not support" % arg.type)
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

def wait_for_reply():
    cnt = 0
    global reply
    while cnt < 3:
        if reply is True:
            reply = False
            return 0
        time.sleep(0.5)
        cnt += 1
    return -1

def example_template():
    logger.debug("\033[1;36m template test start...\033[0m")

    qcloud.registerMqttCallback(on_connect, on_disconnect,
                            on_message, on_publish,
                            on_subscribe, on_unsubscribe)

    global product_id
    global device_name
    product_id = qcloud.getProductID()
    device_name = qcloud.getDeviceName()

    qcloud.connect()

    count = 0
    while True:
        if qcloud.isMqttConnected():
            break
        else:
            if count >= 3:
                logger.error("\033[1;31m template test fail...\033[0m")
                return False
            time.sleep(1)
            count += 1

    """template init"""
    rc, mid = qcloud.templateInit(product_id, device_name, on_template_property,
                        on_template_action, on_template_event, on_template_service)
    if rc != 0:
        return False

    qcloud.templateSetup(product_id, device_name, "explorer/sample/template/template_config.json")

    """report sysinfo """
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
        logger.error("report sysinfo error")
        return False

    rc = wait_for_reply()
    if rc != 0:
        logger.error("wait for report sysinfo reply timeout")
        return False

    """get status"""
    rc, mid = qcloud.templateGetStatus(product_id, device_name)
    if rc != 0:
        logger.error("get status error")
        return False
    rc = wait_for_reply()
    if rc != 0:
        logger.error("wait for get status reply timeout")
        return False

    """report property"""
    prop_list = qcloud.getPropertyList(product_id, device_name)
    reports = report_json_construct_property(prop_list)
    params_in = qcloud.templateJsonConstructReportArray(product_id, device_name, reports)
    rc, mid = qcloud.templateReport(product_id, device_name, params_in)
    if rc != 0:
        logger.error("report property error")
        return False

    rc = wait_for_reply()
    if rc != 0:
        logger.error("wait for report property reply timeout")
        return False

    """events post"""
    event_list = qcloud.getEventsList(product_id, device_name)
    events = report_json_construct_events(event_list)
    rc, mid = qcloud.templateEventPost(product_id, device_name, events)
    if rc != 0:
        logger.error("events post error")
        return False

    rc = wait_for_reply()
    if rc != 0:
        logger.error("wait for report events reply timeout")
        return False

    """report event"""
    timestamp = int(round(time.time() * 1000))
    event = {
        "events": [
            {
                "eventId": "status_report",
                "type": "info",
                "timestamp": timestamp,
                "params": {
                    "status":0,
                    "message":""
                }
            }
        ]
    }
    rc, mid = qcloud.templateEventPost(product_id, device_name, event)
    if rc != 0:
        logger.error("report event error")
        return False

    rc = wait_for_reply()
    if rc != 0:
        logger.error("wait for report event reply timeout")
        return False

    while True:
        time.sleep(3)
    """clear control"""
    qcloud.clearControl(product_id, device_name)

    """template exit"""
    qcloud.templateDeinit(product_id, device_name)
    qcloud.disconnect()

    logger.debug("\033[1;36m template test success...\033[0m")
    return True
example_template()