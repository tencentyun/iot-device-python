import sys
import time
import logging
from explorer import explorer


__log_format = '%(asctime)s.%(msecs)03d [%(filename)s:%(lineno)d] - %(levelname)s - %(message)s'
logging.basicConfig(format=__log_format)

te = explorer.QcloudExplorer(device_file="sample/device_info.json")
te.enableLogger(logging.DEBUG)

g_property_params = None
g_control_msg_arrived = False


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

def on_template_service_post(payload, userdata):
    print("payload:%s,userdata:%s",payload,userdata)
    pass

def on_template_prop_changed(params, userdata):
    print("%s:params:%s,userdata:%s" % (sys._getframe().f_code.co_name, params, userdata))

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

    te.templateControlReply(reply_param)

    pass


def on_template_event_post(payload, userdata):
    print("%s:payload:%s,userdata:%s" % (sys._getframe().f_code.co_name, payload, userdata))
    pass


# def on_template_action(clientToken, actionId, timestamp, payload, userdata):
def on_template_action(payload, userdata):
    print("%s:payload:%s,userdata:%s" % (sys._getframe().f_code.co_name, payload, userdata))

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

    te.templateActionReply(clientToken, res, reply_param)
    pass


def example_template():

    print("\033[1;36m template test start...\033[0m")

    te.user_on_connect = on_connect
    te.user_on_disconnect = on_disconnect
    te.user_on_message = on_message
    te.user_on_publish = on_publish
    te.user_on_subscribe = on_subscribe
    te.user_on_unsubscribe = on_unsubscribe
    te.on_template_prop_changed = on_template_prop_changed
    te.on_template_event_post = on_template_event_post
    te.on_template_action = on_template_action
    te.on_template_service_post = on_template_service_post


    te.templateSetup("sample/template/template_config.json")
    te.mqttInit(mqtt_domain="")
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


    te.templateInit()

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
                te.templateReportSysInfo(sys_info)
            elif msg == "2":
                te.templateGetStatus()
            elif msg == "3":
                if g_control_msg_arrived:
                    params_in = te.templateJsonConstructReportArray(g_property_params)
                    te.templateReport(params_in)
                else:
                    prop_list = te.template_property_list
                    reports = {
                        prop_list[0].key: prop_list[0].data,
                        prop_list[1].key: prop_list[1].data,
                        prop_list[2].key: prop_list[2].data,
                        prop_list[3].key: prop_list[3].data
                    }

                    params_in = te.templateJsonConstructReportArray(reports)
                    te.templateReport(params_in)

            elif msg == "4":
                event_list = te.template_events_list

                '''
                for event in event_list:
                    print("event_name:%s" % (event.event_name))
                    for prop in event.events_prop:
                        print("key:%s" % (prop.key))
                '''

                # deal events and add your real value
                status = 1
                message = "message"
                voltage = 20.0
                name = "memory"
                error_code = 0
                timestamp = int(round(time.time() * 1000))

                events = {
                    "events": [
                        {
                            "eventId": event_list[0].event_name,
                            "type": event_list[0].type,
                            "timestamp": timestamp,
                            "params": {
                                event_list[0].events_prop[0].key:status,
                                event_list[0].events_prop[1].key:message
                            }
                        },
                        {
                            "eventId": event_list[1].event_name,
                            "type": event_list[1].type,
                            "timestamp": timestamp,
                            "params": {
                                event_list[1].events_prop[0].key:voltage
                            }
                        },
                        {
                            "eventId": event_list[2].event_name,
                            "type": event_list[2].type,
                            "timestamp": timestamp,
                            "params": {
                                event_list[2].events_prop[0].key:name,
                                event_list[2].events_prop[1].key:error_code
                            }
                        }
                    ]
                }
                te.templateEventPost(events)

            elif msg == "5":
                te.templateDeinit()

            elif msg == "6":
                te.disconnect()

            elif msg == "7":
                te.clearControl()

            else:
                sys.exit()

    print("\033[1;36m template test success...\033[0m")
    return True

# if __name__ == '__main__':
#     example_template()