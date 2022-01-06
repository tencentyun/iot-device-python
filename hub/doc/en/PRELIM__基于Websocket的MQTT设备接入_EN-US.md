* [Device Connection Through MQTT over WebSocket](#Device-Connection-Through-MQTT-over-WebSocket)
  * [Overview](#Overview)
  * [Entering parameters for authenticating device for connection](#Entering-parameters-for-authenticating-device-for-connection)
  * [Running demo](#Running-demo)
    * [Connecting to MQTT over WebSocket](#Connecting-to-MQTT-over-WebSocket)
    * [Publishing and subscribing through MQTT over WebSocket](#Publishing-and-subscribing-through-MQTT-over-WebSocket)
    * [Disconnecting from MQTT over WebSocket](#Disconnecting-from-MQTT-over-WebSocket)

# Device Connection Through MQTT over WebSocket
### Overview
The IoT Hub platform supports MQTT communication over WebSocket, so that devices can use the MQTT protocol for message transfer on the basis of the WebSocket protocol. For more information, please see [Device Connection Through MQTT over WebSocket](https://cloud.tencent.com/document/product/634/46347).

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

### Running demo
Change the connection method in the [MqttSample.py](../../hub/sample/mqtt/example_mqtt.py) demo to WebSocket.
```
qcloud = QcloudHub(device_file="hub/sample/device_info.json", tls=True, useWebsocket=True)
logger = qcloud.logInit(qcloud.LoggerLevel.DEBUG, enable=True)
```

#### Running demo for authenticated MQTT connection
You can run the [MqttSample.py](../../hub/sample/mqtt/example_mqtt.py) demo to try out processes such as establishing an MQTT connection, subscribing to a topic, sending/receiving a message, and closing the connection. The log of running the demo is as follows:
```
2021-07-16 15:13:41,394.394 [log.py:35] - DEBUG - LoopThread thread enter
2021-07-16 15:13:41,394.394 [log.py:35] - DEBUG - connect_async (UJDZES2SR2.ap-guangzhou.iothub.tencentdevices.com:443)
2021-07-16 15:13:41,875.875 [client.py:2165] - DEBUG - Sending CONNECT (u1, p1, wr0, wq0, wf0, c1, k60) client_id=b'UJDZES2SR2test1'
2021-07-16 15:13:41,952.952 [client.py:2165] - DEBUG - Received CONNACK (0, 0)
2021-07-16 15:13:41,952.952 [log.py:35] - DEBUG - on_connect:flags:0,rc:0,userdata:None
2021-07-16 15:13:42,396.396 [client.py:2165] - DEBUG - Sending SUBSCRIBE (d0, m1) [(b'$sys/operation/result/UJDZES2SR2/test1', 0)]
2021-07-16 15:13:42,396.396 [log.py:35] - DEBUG - subscribe success topic:$sys/operation/result/UJDZES2SR2/test1
2021-07-16 15:13:42,397.397 [log.py:35] - DEBUG - pub topic:$sys/operation/UJDZES2SR2/test1,payload:{'type': 'get', 'resource': ['time']},qos:0
2021-07-16 15:13:42,397.397 [client.py:2165] - DEBUG - Sending PUBLISH (d0, q0, r0, m2), 'b'$sys/operation/UJDZES2SR2/test1'', ... (37 bytes)
2021-07-16 15:13:42,397.397 [log.py:35] - DEBUG - publish success
2021-07-16 15:13:42,398.398 [log.py:35] - DEBUG - on_publish:mid:2,userdata:None
2021-07-16 15:13:42,498.498 [client.py:2165] - DEBUG - Received SUBACK
2021-07-16 15:13:42,499.499 [log.py:35] - DEBUG - on_subscribe:mid:0,granted_qos:1,userdata:None
2021-07-16 15:13:42,627.627 [client.py:2165] - DEBUG - Received PUBLISH (d0, q0, r0, m0), '$sys/operation/result/UJDZES2SR2/test1', ...  (82 bytes)
2021-07-16 15:13:42,799.799 [client.py:2165] - DEBUG - Sending UNSUBSCRIBE (d0, m3) [b'$sys/operation/result/UJDZES2SR2/test1']
2021-07-16 15:13:42,800.800 [log.py:35] - DEBUG - current time:2021-07-16 15:13:42
2021-07-16 15:13:42,872.872 [client.py:2165] - DEBUG - Received UNSUBACK (Mid: 3)
2021-07-16 15:13:42,872.872 [log.py:35] - DEBUG - on_unsubscribe:mid:3,userdata:None
2021-07-16 15:13:43,802.802 [log.py:35] - DEBUG - disconnect
2021-07-16 15:13:43,802.802 [client.py:2165] - DEBUG - Sending DISCONNECT
2021-07-16 15:13:43,803.803 [log.py:35] - DEBUG - LoopThread thread exit
```
As can be seen from the output log, the demo is connected over MQTT successfully, and the connection domain name and port are the domain name and port of WebSocket.
```
2021-07-16 15:13:41,394.394 [log.py:35] - DEBUG - LoopThread thread enter
2021-07-16 15:13:41,394.394 [log.py:35] - DEBUG - connect_async (UJDZES2SR2.ap-guangzhou.iothub.tencentdevices.com:443)
2021-07-16 15:13:41,875.875 [client.py:2165] - DEBUG - Sending CONNECT (u1, p1, wr0, wq0, wf0, c1, k60) client_id=b'UJDZES2SR2test1'
2021-07-16 15:13:41,952.952 [client.py:2165] - DEBUG - Received CONNACK (0, 0)
2021-07-16 15:13:41,952.952 [log.py:35] - DEBUG - on_connect:flags:0,rc:0,userdata:None
```

#### Subscribing through MQTT over WebSocket
As can be seen from the output log, the demo successfully subscribes to the system topic `$sys/operation/result/${productID}/${deviceName}` over MQTT.
```
2021-07-16 15:13:42,396.396 [client.py:2165] - DEBUG - Sending SUBSCRIBE (d0, m1) [(b'$sys/operation/result/UJDZES2SR2/test1', 0)]
2021-07-16 15:13:42,396.396 [log.py:35] - DEBUG - subscribe success topic:$sys/operation/result/UJDZES2SR2/test1
2021-07-16 15:13:42,498.498 [client.py:2165] - DEBUG - Received SUBACK
2021-07-16 15:13:42,499.499 [log.py:35] - DEBUG - on_subscribe:mid:0,granted_qos:1,userdata:None
```

#### Publishing through MQTT over WebSocket
As can be seen from the output log, the demo publishes a message over MQTT successfully to the `$sys/operation/${productID}/${deviceName}` topic, and the server responds after receiving and processing the message.
```
2021-07-16 15:13:42,397.397 [log.py:35] - DEBUG - pub topic:$sys/operation/UJDZES2SR2/test1,payload:{'type': 'get', 'resource': ['time']},qos:0
2021-07-16 15:13:42,397.397 [client.py:2165] - DEBUG - Sending PUBLISH (d0, q0, r0, m2), 'b'$sys/operation/UJDZES2SR2/test1'', ... (37 bytes)
2021-07-16 15:13:42,397.397 [log.py:35] - DEBUG - publish success
2021-07-16 15:13:42,398.398 [log.py:35] - DEBUG - on_publish:mid:2,userdata:None
2021-07-16 15:13:42,627.627 [client.py:2165] - DEBUG - Received PUBLISH (d0, q0, r0, m0), '$sys/operation/result/UJDZES2SR2/test1', ...  (82 bytes)
2021-07-16 15:13:42,800.800 [log.py:35] - DEBUG - current time:2021-07-16 15:13:42
```

#### Disconnecting from MQTT over WebSocket
As can be seen from the output log, the demo disconnects from MQTT after completing all the tasks.
```
2021-07-16 15:13:43,802.802 [log.py:35] - DEBUG - disconnect
2021-07-16 15:13:43,802.802 [client.py:2165] - DEBUG - Sending DISCONNECT
```