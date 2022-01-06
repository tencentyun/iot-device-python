* [Subscribing and Unsubscribing](#Subscribing-and-Unsubscribing)
  * [Subscribing to topic associated with data template](#Subscribing-to-topic-associated-with-data-template)
  * [Receiving device binding/unbinding notification messages](#Receiving-device-binding/unbinding-notification-messages)
  * [Unsubscribing from topic](#Unsubscribing-from-topic)

# Subscribing and Unsubscribing

When you create a product in the IoT Explorer console, a data template and some standard features will be generated for it by default. You can also customize the features. Such features are divided into three categories: attribute, event, and action. For more information on how to use a data template in the console, please see [Data Template](https://cloud.tencent.com/document/product/1081/44921).

After a data template is defined for a product, the device can report attributes and events according to the definitions in the data template, and you can also deliver remote control instructions to the device to modify its writable attributes. For more information on how to manage a data template, please see Product Definition. The data template protocol includes device attribute reporting, remote device control, device-reported latest information acquisition, device event reporting, and device action triggering. For more information on the corresponding definitions and the topics used by the cloud to deliver control instructions, please see [Thing Model Protocol](https://cloud.tencent.com/document/product/1081/34916).

This document describes how to subscribe to/unsubscribe from a topic associated with a data template.

## Subscribing to topic associated with data template

Run [TemplateSample.py](../../explorer/sample/template/example_template.py), and the initialized data template will automatically subscribe to the attribute, event, and action topics associated with it:
```
$thing/down/property/{ProductID}/{DeviceName}
$thing/down/event/{ProductID}/{DeviceName}
$thing/down/action/{ProductID}/{DeviceName}
$thing/down/service/{ProductID}/{DeviceName}
```
After topic subscription, the corresponding downstream messages will be provided by the callback function registered during the initialization of the data template, which is defined as follows:
```python
def on_template_property(topic, qos, payload, userdata):
  """Attribute callback
  Receive the downstream message from `$thing/down/property/{ProductID}/{DeviceName}`
  Args:
    topic: downstream topic
    qos: qos
    payload: downstream message content
    userdata: any structure registered by user
  """
  pass

def on_template_service(topic, qos, payload, userdata):
  """Service callback
  Receive the downstream message from `$thing/down/service/{ProductID}/{DeviceName}`
  Args:
    topic: downstream topic
    qos: qos
    payload: downstream message content
    userdata: any structure registered by user
  """
  pass

def on_template_event(topic, qos, payload, userdata):
  """Event callback
  Receive the downstream message from `$thing/down/event/{ProductID}/{DeviceName}`
  Args:
    topic: downstream topic
    qos: qos
    payload: downstream message content
    userdata: any structure registered by user
  """
  pass

def on_template_action(topic, qos, payload, userdata):
  """Action callback
  Receive the downstream message from `$thing/down/action/{ProductID}/{DeviceName}`
  Args:
    topic: downstream topic
    qos: qos
    payload: downstream message content
    userdata: any structure registered by user
  """
  pass
```

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

# Initialize the data template and automatically subscribe to the relevant topics
qcloud.templateInit(product_id, device_name, on_template_property,
                        on_template_action, on_template_event, on_template_service)
qcloud.templateSetup(product_id, device_name, "sample/template/template_config.json")
```

Observe the log.
```
2021-07-21 16:59:34,956.956 [log.py:35] - DEBUG - LoopThread thread enter
2021-07-21 16:59:34,956.956 [log.py:35] - DEBUG - connect_async (xxx.iotcloud.tencentdevices.com:8883)
2021-07-21 16:59:35,432.432 [client.py:2165] - DEBUG - Sending CONNECT (u1, p1, wr0, wq0, wf0, c1, k60) client_id=b'xxxx'
2021-07-21 16:59:35,491.491 [client.py:2165] - DEBUG - Received CONNACK (0, 0)
2021-07-21 16:59:35,491.491 [log.py:35] - DEBUG - on_connect:flags:0,rc:0,userdata:None
2021-07-21 16:59:35,958.958 [client.py:2165] - DEBUG - Sending SUBSCRIBE (d0, m1) [(b'$thing/down/property/xxx/dev1', 0)]
2021-07-21 16:59:35,958.958 [log.py:35] - DEBUG - subscribe success topic:$thing/down/property/xxx/dev1
2021-07-21 16:59:35,959.959 [client.py:2165] - DEBUG - Sending SUBSCRIBE (d0, m2) [(b'$thing/down/action/xxx/dev1', 0)]
2021-07-21 16:59:35,959.959 [log.py:35] - DEBUG - subscribe success topic:$thing/down/action/xxx/dev1
2021-07-21 16:59:35,960.960 [client.py:2165] - DEBUG - Sending SUBSCRIBE (d0, m3) [(b'$thing/down/event/xxx/dev1', 0)]
2021-07-21 16:59:35,960.960 [log.py:35] - DEBUG - subscribe success topic:$thing/down/event/xxx/dev1
2021-07-21 16:59:35,960.960 [client.py:2165] - DEBUG - Sending SUBSCRIBE (d0, m4) [(b'$thing/down/service/xxx/dev1', 0)]
2021-07-21 16:59:35,960.960 [log.py:35] - DEBUG - subscribe success topic:$thing/down/service/xxx/dev1
2021-07-21 16:59:36,006.006 [client.py:2165] - DEBUG - Received SUBACK
2021-07-21 16:59:36,006.006 [log.py:35] - DEBUG - on_subscribe:mid:0,granted_qos:1,userdata:None
2021-07-21 16:59:36,009.009 [client.py:2165] - DEBUG - Received SUBACK
2021-07-21 16:59:36,010.010 [client.py:2165] - DEBUG - Received SUBACK
2021-07-21 16:59:36,010.010 [log.py:35] - DEBUG - on_subscribe:mid:0,granted_qos:2,userdata:None
2021-07-21 16:59:36,010.010 [log.py:35] - DEBUG - on_subscribe:mid:0,granted_qos:4,userdata:None
2021-07-21 16:59:36,016.016 [client.py:2165] - DEBUG - Received SUBACK
2021-07-21 16:59:36,016.016 [log.py:35] - DEBUG - on_subscribe:mid:0,granted_qos:3,userdata:None
```
As can be seen from the log, the device subscribes to the topics successfully.

## Receiving device binding/unbinding notification messages
After the data template is initialized, you can run the demo and use Tencent IoT Link to try out the downstream message receiving feature.
* Receive device binding notification
Display the device QR code in the console, scan it with Tencent IoT Link to bind the device, and the device will receive the `bind_device` message. The log is as follows:
```
2021-07-29 15:09:09,407.407 [client.py:2165] - DEBUG - Received PUBLISH (d0, q0, r0, m0), '$thing/down/service/xxx/xxx', ...  (86 bytes)
2021-07-29 15:09:09,407.407 [log.py:35] - DEBUG - on_template_service:payload:{'method': 'bind_device', 'clientToken': 'clientToken-8l1b8SX3cw', 'timestamp': 1627542549},userdata:None
```

* Receive device unbinding notification
After you choose to delete the device on Tencent IoT Link, it will receive the `unbind_device` message. The log is as follows:
```
2021-07-29 15:09:28,343.343 [client.py:2165] - DEBUG - Received PUBLISH (d0, q0, r0, m0), '$thing/down/service/xxx/xxx', ...  (118 bytes)
2021-07-29 15:09:28,345.345 [log.py:35] - DEBUG - on_template_service:payload:{'method': 'unbind_device', 'DeviceId': 'xxx/xxx', 'clientToken': 'clientToken-Bcjwl8Io0', 'timestamp': 1627542568},userdata:None
```

## Unsubscribing from topic

Run [TemplateSample.py](../../explorer/sample/template/example_template.py) and call the `templateDeinit()` API to unsubscribe from the topic when exiting the demo.

Below is the sample code:
```python
# Delete the data template
qcloud.templateDeinit(product_id, device_name)

# Disconnect from MQTT
qcloud.disconnect()
```

Observe the output log.
```
2021-07-21 17:21:33,833.833 [client.py:2165] - DEBUG - Sending UNSUBSCRIBE (d0, m5) [b'$thing/down/property/xxx/dev1', b'$thing/down/event/xxx/dev1', b'$thing/down/action/xxx/dev1', b'$thing/down/service/xxx/dev1']
2021-07-21 17:21:33,913.913 [client.py:2165] - DEBUG - Received UNSUBACK (Mid: 5)
2021-07-21 17:21:33,914.914 [log.py:35] - DEBUG - on_unsubscribe:mid:5,userdata:None
2021-07-21 17:21:35,218.218 [log.py:35] - DEBUG - disconnect
2021-07-21 17:21:35,218.218 [client.py:2165] - DEBUG - Sending DISCONNECT
2021-07-21 17:21:35,219.219 [log.py:35] - DEBUG - LoopThread thread exit
2021-07-21 17:21:35,219.219 [log.py:35] - DEBUG - on_disconnect:rc:0,userdata:None
```
As can be seen from the log, the device unsubscribes from the topic successfully.
