* [Getting Latest Information Reported by Device](#Getting-Latest-Information-Reported-by-Device)
  * [Publishing to topic for getting latest information reported by device](#Publishing-to-topic-for-getting-latest-information-reported-by-device)

# Getting Latest Information Reported by Device

When you create a product in the IoT Explorer console, a data template and some standard features will be generated for it by default. You can also customize the features. Such features are divided into three categories: attribute, event, and action. For more information on how to use a data template in the console, please see [Data Template](https://cloud.tencent.com/document/product/1081/44921).

After a data template is defined for a product, the device can report attributes and events according to the definitions in the data template, and you can also deliver remote control instructions to the device to modify its writable attributes. For more information on how to manage a data template, please see Product Definition. The data template protocol includes device attribute reporting, remote device control, device-reported latest information acquisition, device event reporting, and device action triggering. For more information on the corresponding definitions and the topics used by the cloud to deliver control instructions, please see [Thing Model Protocol](https://cloud.tencent.com/document/product/1081/34916).

This document describes how to get the latest information reported by a device in a data template.

## Publishing to topic for getting latest information reported by device 

Run [TemplateSample.py](../../explorer/sample/template/example_template.py). After the device is connected successfully, it will initialize the data template and then call the async `templatGetStatus()` API to get the latest information. The obtained information will be notified to the registered callback function.

Below is the sample code:
```python
# Call back message receipt
def on_template_property(topic, qos, payload, userdata):
    logger.debug("%s:params:%s,userdata:%s" % (sys._getframe().f_code.co_name, payload, userdata))

    # save changed propertys
    global g_property_params
    g_property_params = payload

    global g_control_msg_arrived
    g_control_msg_arrived = True

    # deal down stream and add your real value

    reply_param = qcloud.ReplyPara()
    reply_param.code = 0
    reply_param.timeout_ms = 5 * 1000
    reply_param.status_msg = '\0'

    qcloud.templateControlReply(product_id, device_name, reply_param)
    pass

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

# Get the latest information
qcloud.templateGetStatus(product_id, device_name)

# Disconnect from MQTT
qcloud.disconnect()
```

Observe the output log.
```
2021-07-21 16:16:46,271.271 [log.py:35] - DEBUG - [template report] {'method': 'report', 'clientToken': 'xxx-0', 'params': {'power_switch': 1, 'color': 1, 'brightness': 1, 'name': 'test'}}
2021-07-21 16:16:46,272.272 [client.py:2165] - DEBUG - Sending PUBLISH (d0, q0, r0, m5), 'b'$thing/up/property/xxx/dev1'', ... (127 bytes)
2021-07-21 16:16:46,272.272 [log.py:35] - DEBUG - publish success
2021-07-21 16:16:46,272.272 [log.py:35] - DEBUG - on_publish:mid:5,userdata:None
2021-07-21 16:16:46,373.373 [client.py:2165] - DEBUG - Received PUBLISH (d0, q0, r0, m0), '$thing/down/property/xxx/dev1', ...  (82 bytes)
2021-07-21 16:16:46,373.373 [log.py:35] - DEBUG - on_template_property:params:{'method': 'report_reply', 'clientToken': 'xxx-0', 'code': 0, 'status': 'success'},userdata:None
2021-07-21 16:16:46,373.373 [client.py:2165] - DEBUG - Sending PUBLISH (d0, q0, r0, m6), 'b'$thing/up/property/xxx/dev1'', ... (52 bytes)
2021-07-21 16:16:46,374.374 [log.py:35] - DEBUG - publish success
2021-07-21 16:16:46,374.374 [log.py:35] - DEBUG - on_publish:mid:6,userdata:None
2021-07-21 16:16:48,930.930 [client.py:2165] - DEBUG - Sending PUBLISH (d0, q0, r0, m7), 'b'$thing/up/property/xxx/dev1'', ... (55 bytes)
2021-07-21 16:16:48,931.931 [log.py:35] - DEBUG - publish success
2021-07-21 16:16:48,931.931 [log.py:35] - DEBUG - on_publish:mid:7,userdata:None
2021-07-21 16:16:49,023.023 [client.py:2165] - DEBUG - Received PUBLISH (d0, q0, r0, m0), '$thing/down/property/xxx/dev1', ...  (164 bytes)
2021-07-21 16:16:49,023.023 [log.py:35] - DEBUG - on_template_property:params:{'method': 'get_status_reply', 'clientToken': 'xxx-1', 'code': 0, 'status': 'success', 'data': {'reported': {'name': 'test', 'power_switch': 1, 'color': 1, 'brightness': 1}}},userdata:None
2021-07-21 16:16:49,023.023 [client.py:2165] - DEBUG - Sending PUBLISH (d0, q0, r0, m8), 'b'$thing/up/property/xxx/dev1'', ... (62 bytes)
2021-07-21 16:16:49,024.024 [log.py:35] - DEBUG - publish success
2021-07-21 16:16:49,024.024 [log.py:35] - DEBUG - on_publish:mid:8,userdata:None
```
As can be seen from the log, after the demo is started, it first reports an attribute message, where the value of the `name` field is `test` and the values of the `power_switch` and other fields are all `1`. The field values obtained by getting the latest information reported by the device are exactly the same as those reported. In addition, you can also view the corresponding latest values of the device attributes in the console, which you will find the same as the attribute values in the `data` parameter of the received subscription message. For more information on how to view the device attributes and debug devices online, please see [Device Debugging](https://cloud.tencent.com/document/product/1081/34741).

