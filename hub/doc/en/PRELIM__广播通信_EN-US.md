* [Broadcast Communication](#Broadcast-Communication)
  * [Overview](#Overview)
  * [Broadcast topic](#Broadcast-topic)
  * [Running demo](#Running-demo)
    * [Entering parameters for authenticating device for connection](#Entering-parameters-for-authenticating-device-for-connection)
    * [Initializing broadcast](#Initializing-broadcast)
    * [Receiving broadcast message](#Receiving-broadcast-message)

# Broadcast Communication
## Overview
The IoT Hub platform provides a broadcast communication topic. The server can publish a broadcast message by calling the broadcast communication API, which can be received by online devices that have subscribed to the broadcast topic under the same product. For more information, please see [Broadcast Communication](https://cloud.tencent.com/document/product/634/47333).

## Broadcast topic
* The broadcast communication topic is `$broadcast/rxd/${ProductId}/${DeviceName}`, where `ProductId` and `DeviceName` represent the product ID and device name respectively.


## Running demo
You can run [BroadcastSample.py](../../hub/sample/broadcast/example_broadcast.py) to try out broadcast message receiving by a device.

#### Entering parameters for authenticating device for connection
To try out broadcast message receiving, you need to create two devices and enter the information of the device created in the console in [device_info.json](../../hub/sample/device_info.json), such as the `auth_mode`, `productId`, `deviceName`, and `deviceSecret` fields of a key-authenticated device, as shown below:
```
{
  "auth_mode":"KEY",
  "productId":"xxx",
  "deviceName":"test01",
  "key_deviceinfo":{
    "deviceSecret":"xxxx"
  }
}
```
You can create two configuration files, enter the information of the two created devices respectively, and modify the demo by importing their corresponding configuration files. Below is the sample code:
```
# Replace "hub/sample/device_info.json" with the configuration files of the created devices
qcloud = QcloudHub(device_file="hub/sample/device_info.json", tls=True)
logger = qcloud.logInit(qcloud.LoggerLevel.DEBUG, enable=True)
```

#### Initializing broadcast
After running the demo, call the broadcast initialization API to subscribe to the relevant topic and then wait for the broadcast message.
The `test01` device is initialized and waits for the broadcast message.
```
2021-07-20 19:43:09,109.109 [log.py:35] - DEBUG - LoopThread thread enter
2021-07-20 19:43:09,119.119 [log.py:35] - DEBUG - connect_async (xxx.iotcloud.tencentdevices.com:8883)
2021-07-20 19:43:09,516.516 [client.py:2165] - DEBUG - Sending CONNECT (u1, p1, wr0, wq0, wf0, c1, k60) client_id=b'xxxx'
2021-07-20 19:43:09,573.573 [client.py:2165] - DEBUG - Received CONNACK (0, 0)
2021-07-20 19:43:09,573.573 [log.py:35] - DEBUG - on_connect:flags:0,rc:0,userdata:None
2021-07-20 19:43:10,112.112 [client.py:2165] - DEBUG - Sending SUBSCRIBE (d0, m1) [(b'$broadcast/rxd/xxx/test01', 0)]
2021-07-20 19:43:10,113.113 [log.py:35] - DEBUG - subscribe success topic:$broadcast/rxd/xxx/test01
2021-07-20 19:43:10,113.113 [log.py:35] - DEBUG - broadcast wait
2021-07-20 19:43:10,156.156 [client.py:2165] - DEBUG - Received SUBACK
2021-07-20 19:43:10,157.157 [log.py:35] - DEBUG - on_subscribe:mid:0,granted_qos:1,userdata:None
2021-07-20 19:43:11,115.115 [log.py:35] - DEBUG - broadcast wait
2021-07-20 19:43:12,118.118 [log.py:35] - DEBUG - broadcast wait
2021-07-20 19:43:13,119.119 [log.py:35] - DEBUG - broadcast wait
```
The `dev01` device is initialized and waits for the broadcast message.
```
2021-07-20 19:47:14,510.510 [log.py:35] - DEBUG - LoopThread thread enter
2021-07-20 19:47:14,511.511 [log.py:35] - DEBUG - connect_async (xxx.iotcloud.tencentdevices.com:8883)
2021-07-20 19:47:15,099.099 [client.py:2165] - DEBUG - Sending CONNECT (u1, p1, wr0, wq0, wf0, c1, k60) client_id=b'xxxx'
2021-07-20 19:47:15,160.160 [client.py:2165] - DEBUG - Received CONNACK (0, 0)
2021-07-20 19:47:15,161.161 [log.py:35] - DEBUG - on_connect:flags:0,rc:0,userdata:None
2021-07-20 19:47:15,512.512 [client.py:2165] - DEBUG - Sending SUBSCRIBE (d0, m1) [(b'$broadcast/rxd/xxx/dev01', 0)]
2021-07-20 19:47:15,514.514 [log.py:35] - DEBUG - subscribe success topic:$broadcast/rxd/xxx/dev01
2021-07-20 19:47:15,514.514 [log.py:35] - DEBUG - broadcast wait
2021-07-20 19:47:15,561.561 [client.py:2165] - DEBUG - Received SUBACK
2021-07-20 19:47:15,561.561 [log.py:35] - DEBUG - on_subscribe:mid:0,granted_qos:1,userdata:None
2021-07-20 19:47:16,516.516 [log.py:35] - DEBUG - broadcast wait
2021-07-20 19:47:17,518.518 [log.py:35] - DEBUG - broadcast wait
```

#### Receiving broadcast message
Call TencentCloud API `PublishBroadcastMessage` to send a broadcast message
Go to [API Explorer](https://console.cloud.tencent.com/api/explorer?Product=iotcloud&Version=2018-06-14&Action=PublishBroadcastMessage&SignVersion=), enter the personal key and device parameter information, select **Online Call**, and send the request.

The `test01` device successfully receives the broadcast message.
```
2021-07-20 19:48:32,693.693 [log.py:35] - DEBUG - broadcast wait
2021-07-20 19:48:33,003.003 [client.py:2165] - DEBUG - Received PUBLISH (d0, q0, r0, m0), '$broadcast/rxd/xxx/test01', ...  (28 bytes)
2021-07-20 19:48:33,013.013 [log.py:35] - DEBUG - on_broadcast_cb:payload:{'payload': 'broadcast test'},userdata:None
```

The `dev01` device successfully receives the broadcast message.
```
2021-07-20 19:48:32,657.657 [log.py:35] - DEBUG - broadcast wait
2021-07-20 19:48:33,002.002 [client.py:2165] - DEBUG - Received PUBLISH (d0, q0, r0, m0), '$broadcast/rxd/xxx/dev01', ...  (28 bytes)
2021-07-20 19:48:33,013.013 [log.py:35] - DEBUG - on_broadcast_cb:payload:{'payload': 'broadcast test'},userdata:None
```