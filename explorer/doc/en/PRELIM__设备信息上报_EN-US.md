* [Device Information Reporting](#Device-Information-Reporting)
  * [Publishing to topic for reporting device information](#Publishing-to-topic-for-reporting-device-information)

# Device Information Reporting

This document describes how to report device information to the cloud.

## Publishing to topic for reporting device information 

Run [TemplateSample.py](../../explorer/sample/template/example_template.py). After the device is connected successfully, it will initialize the data template and then call the `templateReportSysInfo()` API to report the device information. The topic for device information reporting is:
`$thing/up/property/{ProductID}/{DeviceName}`

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

# Simulate the device information
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
# Report the device information
qcloud.templateReportSysInfo(product_id, device_name, sys_info)

# Disconnect from MQTT
qcloud.disconnect()
```

Observe the output log.
```
2021-07-21 16:39:33,894.894 [client.py:2165] - DEBUG - Sending PUBLISH (d0, q0, r0, m5), 'b'$thing/up/property/xxx/dev1'', ... (266 bytes)
2021-07-21 16:39:33,895.895 [log.py:35] - DEBUG - publish success
2021-07-21 16:39:33,896.896 [log.py:35] - DEBUG - on_publish:mid:5,userdata:None
2021-07-21 16:39:33,965.965 [client.py:2165] - DEBUG - Received PUBLISH (d0, q0, r0, m0), '$thing/down/property/xxx/dev1', ...  (87 bytes)
2021-07-21 16:39:33,966.966 [log.py:35] - DEBUG - on_template_property:params:{'method': 'report_info_reply', 'clientToken': 'xxx-0', 'code': 0, 'status': 'success'},userdata:None
2021-07-21 16:39:33,966.966 [client.py:2165] - DEBUG - Sending PUBLISH (d0, q0, r0, m6), 'b'$thing/up/property/xxx/dev1'', ... (52 bytes)
2021-07-21 16:39:33,966.966 [log.py:35] - DEBUG - publish success
2021-07-21 16:39:33,966.966 [log.py:35] - DEBUG - on_publish:mid:6,userdata:None
```
As can be seen from the log, the device reports the information successfully and receives a reply from the cloud.

