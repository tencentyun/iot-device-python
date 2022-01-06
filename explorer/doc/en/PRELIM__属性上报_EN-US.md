* [Attribute Reporting](#Attribute-Reporting)
  * [Publishing to topic for reporting attribute](#Publishing-to-topic-for-reporting-attribute)

# Attribute Reporting

When you create a product in the IoT Explorer console, a data template and some standard features will be generated for it by default. You can also customize the features. Such features are divided into three categories: attribute, event, and action. For more information on how to use a data template in the console, please see [Data Template](https://cloud.tencent.com/document/product/1081/44921).

After a data template is defined for a product, the device can report attributes and events according to the definitions in the data template, and you can also deliver remote control instructions to the device to modify its writable attributes. For more information on how to manage a data template, please see Product Definition. The data template protocol includes device attribute reporting, remote device control, device-reported latest information acquisition, device event reporting, and device action triggering. For more information on the corresponding definitions and the topics used by the cloud to deliver control instructions, please see [Thing Model Protocol](https://cloud.tencent.com/document/product/1081/34916).

This document describes how to report the values of the associated attributes in the data template.

## Publishing to topic for reporting attribute 

Run [TemplateSample.py](../../explorer/sample/template/example_template.py). After the device is connected successfully, it will initialize the data template, call the `templateReport()` API to report attributes, and publish to the attribute topic:
`$thing/up/property/{ProductID}/{DeviceName}`

Below is the sample code:
```python
# Construct a JSON message
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
            logger.err_code("type[%s] not support" % arg.type)
            arg.data = " "
        if arg_cnt < len(thing_list):
            report_string += ","
    pass
    report_string += '}'

    json_out = json.loads(report_string)

    return json_out

# Construct QcloudExplorer
qcloud = QcloudExplorer(device_file="explorer/sample/device_info.json", tls=True)
# Initialize the log
logger = qcloud.logInit(qcloud.LoggerLevel.DEBUG, enable=True)

# Register the MQTT callback
qcloud.registerMqttCallback(on_connect, on_disconnect,
                            on_message, on_publish,
                            on_subscribe, on_unsubscribe)
# Get the product ID and device name
product_id = qcloud.getProductID()
device_name = qcloud.getDeviceName()

# Connect to MQTT
qcloud.connect()

# Initialize the data template
qcloud.templateInit(product_id, device_name, on_template_property,
                        on_template_action, on_template_event, on_template_service)
qcloud.templateSetup(product_id, device_name, "sample/template/template_config.json")

# Get the attribute list from the configuration file
prop_list = qcloud.getPropertyList(product_id, device_name)
# Construct a JSON attribute structure based on the attribute list
reports = report_json_construct_property(prop_list)
# Construct an attribute message
params_in = qcloud.templateJsonConstructReportArray(product_id, device_name, reports)
# Report the attributes
qcloud.templateReport(product_id, device_name, params_in)

# Disconnect from MQTT
qcloud.disconnect()
```

Observe the output log.
```
2021-07-21 15:41:23,702.702 [log.py:35] - DEBUG - LoopThread thread enter
2021-07-21 15:41:23,703.703 [log.py:35] - DEBUG - connect_async (xxx.iotcloud.tencentdevices.com:8883)
2021-07-21 15:41:24,117.117 [client.py:2165] - DEBUG - Sending CONNECT (u1, p1, wr0, wq0, wf0, c1, k60) client_id=b'xxxx'
2021-07-21 15:41:24,176.176 [client.py:2165] - DEBUG - Received CONNACK (0, 0)
2021-07-21 15:41:24,176.176 [log.py:35] - DEBUG - on_connect:flags:0,rc:0,userdata:None
2021-07-21 15:41:24,704.704 [client.py:2165] - DEBUG - Sending SUBSCRIBE (d0, m1) [(b'$thing/down/property/xxx/dev1', 0)]
2021-07-21 15:41:24,705.705 [log.py:35] - DEBUG - subscribe success topic:$thing/down/property/xxx/dev1
2021-07-21 15:41:24,705.705 [client.py:2165] - DEBUG - Sending SUBSCRIBE (d0, m2) [(b'$thing/down/action/xxx/dev1', 0)]
2021-07-21 15:41:24,705.705 [log.py:35] - DEBUG - subscribe success topic:$thing/down/action/xxx/dev1
2021-07-21 15:41:24,705.705 [client.py:2165] - DEBUG - Sending SUBSCRIBE (d0, m3) [(b'$thing/down/event/xxx/dev1', 0)]
2021-07-21 15:41:24,706.706 [log.py:35] - DEBUG - subscribe success topic:$thing/down/event/xxx/dev1
2021-07-21 15:41:24,706.706 [client.py:2165] - DEBUG - Sending SUBSCRIBE (d0, m4) [(b'$thing/down/service/xxx/dev1', 0)]
2021-07-21 15:41:24,706.706 [log.py:35] - DEBUG - subscribe success topic:$thing/down/service/xxx/dev1
2021-07-21 15:41:24,754.754 [client.py:2165] - DEBUG - Received SUBACK
2021-07-21 15:41:24,755.755 [client.py:2165] - DEBUG - Received SUBACK
2021-07-21 15:41:24,755.755 [log.py:35] - DEBUG - on_subscribe:mid:0,granted_qos:1,userdata:None
2021-07-21 15:41:24,755.755 [log.py:35] - DEBUG - on_subscribe:mid:0,granted_qos:4,userdata:None
2021-07-21 15:41:24,755.755 [client.py:2165] - DEBUG - Received SUBACK
2021-07-21 15:41:24,756.756 [log.py:35] - DEBUG - on_subscribe:mid:0,granted_qos:2,userdata:None
2021-07-21 15:41:24,756.756 [client.py:2165] - DEBUG - Received SUBACK
2021-07-21 15:41:24,756.756 [log.py:35] - DEBUG - on_subscribe:mid:0,granted_qos:3,userdata:None
2021-07-21 15:41:26,068.068 [log.py:35] - DEBUG - [template report] {'method': 'report', 'clientToken': 'xxx-0', 'params': {'power_switch': 0, 'color': 0, 'brightness': 0, 'name': ''}}
2021-07-21 15:41:26,068.068 [client.py:2165] - DEBUG - Sending PUBLISH (d0, q0, r0, m5), 'b'$thing/up/property/xxx/dev1'', ... (123 bytes)
2021-07-21 15:41:26,068.068 [log.py:35] - DEBUG - publish success
2021-07-21 15:41:26,069.069 [log.py:35] - DEBUG - on_publish:mid:5,userdata:None
2021-07-21 15:41:26,149.149 [client.py:2165] - DEBUG - Received PUBLISH (d0, q0, r0, m0), '$thing/down/property/xxx/dev1', ...  (82 bytes)
2021-07-21 15:41:26,149.149 [log.py:35] - DEBUG - product_1:on_template_property:params:{'method': 'report_reply', 'clientToken': 'xxx-0', 'code': 0, 'status': 'success'},userdata:None
2021-07-21 15:41:26,151.151 [client.py:2165] - DEBUG - Sending PUBLISH (d0, q0, r0, m6), 'b'$thing/up/property/xxx/dev1'', ... (52 bytes)
2021-07-21 15:41:26,151.151 [log.py:35] - DEBUG - publish success
2021-07-21 15:41:26,151.151 [log.py:35] - DEBUG - on_publish:mid:6,userdata:None
```
As can be seen from the log, after the demo is started, it subscribes to the topics related to the data template, reports the attribute message through the `$thing/up/property/{ProductID}/{DeviceName}` topic, and receives the `report_reply` message from the cloud. You can view the log of the device created in the console. In the online debugging section, you can see that the attribute values of the device have changed to the reported ones. For more information on how to view the device logs and debug devices online, please see [Device Debugging](https://cloud.tencent.com/document/product/1081/34741).

