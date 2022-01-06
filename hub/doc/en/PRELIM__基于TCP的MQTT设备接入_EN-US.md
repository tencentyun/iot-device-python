* [Getting Started](#Getting-Started)
  *  [Creating device in console](#Creating-device-in-console)
  *  [Running demo](#Running-demo)
     *  [Entering parameters for authenticating device for connection](#Entering-parameters-for-authenticating-device-for-connection)
     *  [Running demo for authenticated MQTT connection](#Running-demo-for-authenticated-MQTT-connection)
     *  [Subscribing to topic](#Subscribing-to-topic)
     *  [Publishing to topic](#Publishing-to-topic)
     *  [Unsubscribing from topic](#Unsubscribing-from-topic)
     *  [Running demo to close MQTT connection](#Running-demo-to-close-MQTT-connection)


# Getting Started
This document describes how to create devices in the IoT Hub console and quickly try out device connection to IoT Hub over the MQTT protocol for message sending/receiving on the SDK demo.

## Creating device in console

Before connecting devices to the SDK, you need to create products and devices in the console and get the product ID, device name, device certificate (for certificate authentication), device private key (for certificate authentication), and device key (for key authentication), which are required for authentication of the devices when you connect them to the cloud. For more information, please see [Device Connection Preparations](https://cloud.tencent.com/document/product/634/14442).

After a product is created successfully in the console, it has three permissions by default:

```
${productId}/${deviceName}/control  // Subscribe
${productId}/${deviceName}/data     // Subscribe and publish
${productId}/${deviceName}/event    // Publish
```
For more information on how to manipulate the topic permissions, please see [Permission List](https://cloud.tencent.com/document/product/634/14444).

## Running demo

### Entering parameters for authenticating device for connection
Enter the information of the device created in the console in [device_info.json](../../hub/sample/device_info.json), such as the `auth_mode`, `productId`, `deviceName`, and `deviceSecret` fields of a key-authenticated device, as shown below:
```
{
  "auth_mode":"KEY",
  "productId":"xxx",
  "deviceName":"xxx",
  "key_deviceinfo":{
      "deviceSecret":"xxxx"
  }
}
```

#### Running demo for authenticated MQTT connection
You can run the [MqttSample.py](../../hub/sample/mqtt/example_mqtt.py) demo to try out processes such as establishing an MQTT connection, subscribing to a topic, sending/receiving a message, and closing the connection. The log of running the demo is as follows:
```
2021-07-16 10:38:45,940.940 [log.py:35] - DEBUG - LoopThread thread enter
2021-07-16 10:38:45,940.940 [log.py:35] - DEBUG - connect_async...8883
2021-07-16 10:38:46,366.366 [client.py:2165] - DEBUG - Sending CONNECT (u1, p1, wr0, wq0, wf0, c1, k60) client_id=b'xxxx'
2021-07-16 10:38:46,451.451 [client.py:2165] - DEBUG - Received CONNACK (0, 0)
2021-07-16 10:38:46,452.452 [log.py:35] - DEBUG - on_connect:flags:0,rc:0,userdata:None
2021-07-16 10:38:46,942.942 [client.py:2165] - DEBUG - Sending SUBSCRIBE (d0, m1) [(b'$sys/operation/result/xxx/xxx', 0)]
2021-07-16 10:38:46,943.943 [log.py:35] - DEBUG - subscribe success topic:$sys/operation/result/xxx/xxx
2021-07-16 10:38:46,944.944 [log.py:35] - DEBUG - pub topic:$sys/operation/xxx/xxx,payload:{'type': 'get', 'resource': ['time']},qos:0
2021-07-16 10:38:46,945.945 [client.py:2165] - DEBUG - Sending PUBLISH (d0, q0, r0, m2), 'b'$sys/operation/xxx/xxx'', ... (37 bytes)
2021-07-16 10:38:46,947.947 [log.py:35] - DEBUG - publish success
2021-07-16 10:38:46,947.947 [log.py:35] - DEBUG - on_publish:mid:2,userdata:None
2021-07-16 10:38:47,026.026 [client.py:2165] - DEBUG - Received SUBACK
2021-07-16 10:38:47,027.027 [log.py:35] - DEBUG - on_subscribe:mid:0,granted_qos:1,userdata:None
2021-07-16 10:38:47,159.159 [client.py:2165] - DEBUG - Received PUBLISH (d0, q0, r0, m0), '$sys/operation/result/xxx/xxx', ...  (82 bytes)
2021-07-16 10:38:47,349.349 [client.py:2165] - DEBUG - Sending UNSUBSCRIBE (d0, m3) [b'$sys/operation/result/xxx/xxx']
2021-07-16 10:38:47,350.350 [log.py:35] - DEBUG - current time:2021-07-16 10:38:47
2021-07-16 10:38:47,433.433 [client.py:2165] - DEBUG - Received UNSUBACK (Mid: 3)
2021-07-16 10:38:47,434.434 [log.py:35] - DEBUG - on_unsubscribe:mid:3,userdata:None
2021-07-16 10:38:48,352.352 [log.py:35] - DEBUG - disconnect
2021-07-16 10:38:48,352.352 [client.py:2165] - DEBUG - Sending DISCONNECT
2021-07-16 10:38:48,354.354 [log.py:35] - DEBUG - LoopThread thread exit
2021-07-16 10:38:48,355.355 [log.py:35] - DEBUG - on_disconnect:rc:0,userdata:None
```
As can be seen from the output log, the demo is connected over MQTT successfully.
```
2021-07-16 10:38:45,940.940 [log.py:35] - DEBUG - connect_async...8883
2021-07-16 10:38:46,366.366 [client.py:2165] - DEBUG - Sending CONNECT (u1, p1, wr0, wq0, wf0, c1, k60) client_id=b'xxxx'
2021-07-16 10:38:46,451.451 [client.py:2165] - DEBUG - Received CONNACK (0, 0)
2021-07-16 10:38:46,452.452 [log.py:35] - DEBUG - on_connect:flags:0,rc:0,userdata:None
```

#### Subscribing to topic
As can be seen from the output log, the demo successfully subscribes to the system topic `$sys/operation/result/${productID}/${deviceName}` over MQTT.
```
2021-07-16 10:38:46,942.942 [client.py:2165] - DEBUG - Sending SUBSCRIBE (d0, m1) [(b'$sys/operation/result/xxx/xxx', 0)]
2021-07-16 10:38:46,943.943 [log.py:35] - DEBUG - subscribe success topic:$sys/operation/result/xxx/xxx
2021-07-16 10:38:47,027.027 [log.py:35] - DEBUG - on_subscribe:mid:0,granted_qos:1,userdata:None
```

#### Publishing to topic
As can be seen from the output log, the demo publishes a message over MQTT successfully to the `$sys/operation/${productID}/${deviceName}` topic, and the server responds after receiving and processing the message.
```
2021-07-16 10:38:46,944.944 [log.py:35] - DEBUG - pub topic:$sys/operation/xxx/xxx,payload:{'type': 'get', 'resource': ['time']},qos:0
2021-07-16 10:38:46,945.945 [client.py:2165] - DEBUG - Sending PUBLISH (d0, q0, r0, m2), 'b'$sys/operation/xxx/xxx'', ... (37 bytes)
2021-07-16 10:38:46,947.947 [log.py:35] - DEBUG - publish success
2021-07-16 10:38:46,947.947 [log.py:35] - DEBUG - on_publish:mid:2,userdata:None
2021-07-16 10:38:47,350.350 [log.py:35] - DEBUG - current time:2021-07-16 10:38:47
```

#### Unsubscribing from topic
As can be seen from the output log, the demo unsubscribes from the topic after completing message publishing and receiving.
```
2021-07-16 10:38:47,349.349 [client.py:2165] - DEBUG - Sending UNSUBSCRIBE (d0, m3) [b'$sys/operation/result/xxx/xxx']
2021-07-16 10:38:47,433.433 [client.py:2165] - DEBUG - Received UNSUBACK (Mid: 3)
2021-07-16 10:38:47,434.434 [log.py:35] - DEBUG - on_unsubscribe:mid:3,userdata:None
```

#### Running demo to close MQTT connection
As can be seen from the output log, the demo disconnects from MQTT after completing all the tasks.
```
2021-07-16 10:38:48,352.352 [log.py:35] - DEBUG - disconnect
2021-07-16 10:38:48,352.352 [client.py:2165] - DEBUG - Sending DISCONNECT
2021-07-16 10:38:48,354.354 [log.py:35] - DEBUG - LoopThread thread exit
2021-07-16 10:38:48,355.355 [log.py:35] - DEBUG - on_disconnect:rc:0,userdata:None
```