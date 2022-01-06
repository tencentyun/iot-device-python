* [Clearing Control](#Clearing-Control)
  * [Publishing to topic for clearing control](#Publishing-to-topic-for-clearing-control)

# Clearing Control

This document describes how a device delivers an instruction to clear control.

## Publishing to topic for clearing control 

Run [TemplateSample.py](../../explorer/sample/template/example_template.py). After the device is connected successfully, it will initialize the data template and call `clearControl()` to clear control when needed. The topic for control clearing is:
`$thing/up/property/{ProductID}/{DeviceName}`

Below is the sample code:
```python
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

# Clear control
qcloud.clearControl(product_id, device_name)

# Disconnect from MQTT
qcloud.disconnect()
```

Observe the output log.
```
2021-07-21 15:57:20,128.128 [client.py:2165] - DEBUG - Sending PUBLISH (d0, q0, r0, m5), 'b'$thing/up/property/xxx/dev1'', ... (55 bytes)
2021-07-21 15:57:20,129.129 [log.py:35] - DEBUG - publish success
2021-07-21 15:57:20,129.129 [log.py:35] - DEBUG - on_publish:mid:5,userdata:None
2021-07-21 15:57:20,204.204 [client.py:2165] - DEBUG - Received PUBLISH (d0, q0, r0, m0), '$thing/down/property/xxx/dev1', ...  (160 bytes)
2021-07-21 15:57:20,205.205 [log.py:35] - DEBUG - on_template_property:params:{'method': 'get_status_reply', 'clientToken': 'xxx-0', 'code': 0, 'status': 'success', 'data': {'reported': {'name': '', 'power_switch': 0, 'color': 0, 'brightness': 0}}},userdata:None
2021-07-21 15:57:20,205.205 [client.py:2165] - DEBUG - Sending PUBLISH (d0, q0, r0, m6), 'b'$thing/up/property/xxx/dev1'', ... (62 bytes)
2021-07-21 15:57:20,205.205 [log.py:35] - DEBUG - publish success
2021-07-21 15:57:20,205.205 [log.py:35] - DEBUG - on_publish:mid:6,userdata:None
7
2021-07-21 15:57:21,965.965 [client.py:2165] - DEBUG - Sending PUBLISH (d0, q0, r0, m7), 'b'$thing/up/property/xxx/dev1'', ... (58 bytes)
2021-07-21 15:57:21,966.966 [log.py:35] - DEBUG - publish success
2021-07-21 15:57:21,966.966 [log.py:35] - DEBUG - on_publish:mid:7,userdata:None
2021-07-21 15:57:22,038.038 [client.py:2165] - DEBUG - Received PUBLISH (d0, q0, r0, m0), '$thing/down/property/xxx/dev1', ...  (89 bytes)
2021-07-21 15:57:22,038.038 [log.py:35] - DEBUG - on_template_property:params:{'method': 'clear_control_reply', 'clientToken': 'xxx-0', 'code': 0, 'status': 'success'},userdata:None
2021-07-21 15:57:22,038.038 [client.py:2165] - DEBUG - Sending PUBLISH (d0, q0, r0, m8), 'b'$thing/up/property/xxx/dev1'', ... (62 bytes)
2021-07-21 15:57:22,038.038 [log.py:35] - DEBUG - publish success
2021-07-21 15:57:22,039.039 [log.py:35] - DEBUG - on_publish:mid:8,userdata:None
```
As can been seen from the log, the demo publishes a control clearing message successfully and receives the `clear_control_reply` reply from the cloud.

