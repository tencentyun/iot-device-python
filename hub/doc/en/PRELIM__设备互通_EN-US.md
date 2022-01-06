* [Device Interconnection](#Device-Interconnection)
  * [Overview](#Overview)
  * [Running demo](#Running-demo)
    * [Entering parameters for authenticating device for connection](#Entering-parameters-for-authenticating-device-for-connection)
    * [Trying out homecoming for door device](#Trying-out-homecoming-for-door-device)
    * [Trying out homeleaving for door device](#Trying-out-homeleaving-for-door-device)

# Device Interconnection
## Overview
This document describes how to try out device interconnection based on cross-device messaging and the rule engine in a smart home scenario with the aid of the IoT Hub device SDK for Python. For more information, please see [Scenario 1: Device Interconnection](https://cloud.tencent.com/document/product/634/11913).

To try out device interconnection, you need to create two types of smart devices (`Door` and `AirConditioner`) as instructed in the documentation. You also need to configure the rule engine as instructed in [Overview](https://cloud.tencent.com/document/product/634/14446) and [forward the data to another topic](https://cloud.tencent.com/document/product/634/14449).

## Running demo
You can run [DoorSample.py](../../hub/sample/scenarized/example_door.py) to send a message to the air conditioner device upon homecoming and run [AircondSample.py](../../hub/sample/scenarized/example_aircond.py) to turn on/off the air conditioner device when messages are received from the door device.

#### Entering parameters for authenticating device for connection
To try out device interconnection, you need to create two devices. In the demo, an air conditioner device (AirConditioner) and a door device (door) are created, and the air conditioner will be turned on/off upon homecoming/homeleaving.
Enter the information of the air conditioner device created in the console in ***aircond_device_info.json*** as shown below:
```
{
  "auth_mode":"KEY",
  "productId":"xxx",
  "deviceName":"AirConditioner1",
  "key_deviceinfo":{
    "deviceSecret":"xxxx"
  }
}
```
Enter the information of the door device created in the console in ***door_device_info.json*** as shown below:
```
{
  "auth_mode":"KEY",
  "productId":"xxx",
  "deviceName":"door1",
  "key_deviceinfo":{
    "deviceSecret":"xxxx"
  }
}
```

#### Trying out homecoming for door device
The demo simulates the room temperature. The initial value is 25°C, the maximum value is 40°C, and the minimum value is -10°C. The temperature goes up by 1°C per second after the air conditioner is turned off and goes down by 1°C per second after it is turned on.
The homecoming log of the `door1` device is as follows:
```
2021-07-21 14:59:53,618.618 [log.py:35] - DEBUG - LoopThread thread enter
2021-07-21 14:59:53,618.618 [log.py:35] - DEBUG - connect_async (xxx.iotcloud.tencentdevices.com:8883)
2021-07-21 14:59:54,000.000 [client.py:2165] - DEBUG - Sending CONNECT (u1, p1, wr0, wq0, wf0, c1, k60) client_id=b'xxxx'
2021-07-21 14:59:54,061.061 [client.py:2165] - DEBUG - Received CONNACK (0, 0)
2021-07-21 14:59:54,061.061 [log.py:35] - DEBUG - on_connect:flags:0,rc:0,userdata:None
2021-07-21 14:59:54,619.619 [log.py:35] - DEBUG - publish {"action": "come_home", "targetDevice": "AirConditioner1"}
2021-07-21 14:59:54,619.619 [client.py:2165] - DEBUG - Sending PUBLISH (d0, q1, r0, m1), 'b'xxx/door1/event'', ... (68 bytes)
2021-07-21 14:59:54,620.620 [log.py:35] - DEBUG - publish success
2021-07-21 14:59:54,620.620 [log.py:35] - DEBUG - wait reply...
2021-07-21 14:59:54,670.670 [client.py:2165] - DEBUG - Received PUBACK (Mid: 1)
2021-07-21 14:59:54,670.670 [log.py:35] - DEBUG - on_publish:mid:1,userdata:None
2021-07-21 14:59:55,621.621 [log.py:35] - DEBUG - disconnect
2021-07-21 14:59:55,621.621 [client.py:2165] - DEBUG - Sending DISCONNECT
2021-07-21 14:59:55,622.622 [log.py:35] - DEBUG - LoopThread thread exit
```
As can be seen, the device simulates homecoming and sends a `come_home` message to the air conditioner device.
The log of the `AirConditioner1` device is as follows:
```
2021-07-21 14:59:48,270.270 [log.py:35] - DEBUG - LoopThread thread enter
2021-07-21 14:59:48,270.270 [log.py:35] - DEBUG - connect_async (xxx.iotcloud.tencentdevices.com:8883)
2021-07-21 14:59:48,650.650 [client.py:2165] - DEBUG - Sending CONNECT (u1, p1, wr0, wq0, wf0, c1, k60) client_id=b'xxxx'
2021-07-21 14:59:48,715.715 [client.py:2165] - DEBUG - Received CONNACK (0, 0)
2021-07-21 14:59:48,715.715 [log.py:35] - DEBUG - on_connect:flags:0,rc:0,userdata:None
2021-07-21 14:59:49,272.272 [client.py:2165] - DEBUG - Sending SUBSCRIBE (d0, m1) [(b'xxx/AirConditioner1/control', 1)]
2021-07-21 14:59:49,272.272 [log.py:35] - DEBUG - subscribe success topic:xxx/AirConditioner1/control
2021-07-21 14:59:49,273.273 [log.py:35] - DEBUG - [air is close] temperature 25
2021-07-21 14:59:49,320.320 [client.py:2165] - DEBUG - Received SUBACK
2021-07-21 14:59:49,320.320 [log.py:35] - DEBUG - on_subscribe:mid:1,granted_qos:1,userdata:None
2021-07-21 14:59:50,274.274 [log.py:35] - DEBUG - [air is close] temperature 25
2021-07-21 14:59:51,276.276 [log.py:35] - DEBUG - [air is close] temperature 26
2021-07-21 14:59:52,278.278 [log.py:35] - DEBUG - [air is close] temperature 26
2021-07-21 14:59:53,280.280 [log.py:35] - DEBUG - [air is close] temperature 27
2021-07-21 14:59:54,283.283 [log.py:35] - DEBUG - [air is close] temperature 27
2021-07-21 14:59:54,687.687 [client.py:2165] - DEBUG - Received PUBLISH (d0, q1, r0, m24), 'xxx/AirConditioner1/control', ...  (68 bytes)
2021-07-21 14:59:54,687.687 [client.py:2165] - DEBUG - Sending PUBACK (Mid: 24)
2021-07-21 14:59:54,687.687 [log.py:35] - DEBUG - on_aircond_cb:payload:{"action": "come_home", "targetDevice": "AirConditioner1"},userdata:None
2021-07-21 14:59:55,285.285 [log.py:35] - DEBUG - [air is open] temperature 28
2021-07-21 14:59:56,288.288 [log.py:35] - DEBUG - [air is open] temperature 27
2021-07-21 14:59:57,289.289 [log.py:35] - DEBUG - [air is open] temperature 27
2021-07-21 14:59:58,291.291 [log.py:35] - DEBUG - [air is open] temperature 26
2021-07-21 14:59:59,293.293 [log.py:35] - DEBUG - [air is open] temperature 26
2021-07-21 15:00:00,299.299 [log.py:35] - DEBUG - [air is open] temperature 25
2021-07-21 15:00:01,301.301 [log.py:35] - DEBUG - [air is open] temperature 25
2021-07-21 15:00:02,311.311 [log.py:35] - DEBUG - [air is open] temperature 24
2021-07-21 15:00:03,312.312 [log.py:35] - DEBUG - [air is open] temperature 24
2021-07-21 15:00:04,314.314 [log.py:35] - DEBUG - [air is open] temperature 23
2021-07-21 15:00:05,315.315 [log.py:35] - DEBUG - [air is open] temperature 23
```
As can be seen, the air conditioner is off and the air temperature goes up before it receives the homecoming message, and it is turned on and the air temperature gradually goes down after it receives the message.

#### Trying out homeleaving for door device
The homeleaving log of the `door1` device is as follows:
```
2021-07-21 15:00:04,962.962 [log.py:35] - DEBUG - LoopThread thread enter
2021-07-21 15:00:04,963.963 [log.py:35] - DEBUG - connect_async (xxx.iotcloud.tencentdevices.com:8883)
2021-07-21 15:00:05,288.288 [client.py:2165] - DEBUG - Sending CONNECT (u1, p1, wr0, wq0, wf0, c1, k60) client_id=b'xxxx'
2021-07-21 15:00:05,355.355 [client.py:2165] - DEBUG - Received CONNACK (0, 0)
2021-07-21 15:00:05,356.356 [log.py:35] - DEBUG - on_connect:flags:0,rc:0,userdata:None
2021-07-21 15:00:05,964.964 [log.py:35] - DEBUG - publish {"action": "leave_home", "targetDevice": "AirConditioner1"}
2021-07-21 15:00:05,964.964 [client.py:2165] - DEBUG - Sending PUBLISH (d0, q1, r0, m1), 'b'xxx/door1/event'', ... (69 bytes)
2021-07-21 15:00:05,964.964 [log.py:35] - DEBUG - publish success
2021-07-21 15:00:05,965.965 [log.py:35] - DEBUG - wait reply...
2021-07-21 15:00:06,011.011 [client.py:2165] - DEBUG - Received PUBACK (Mid: 1)
2021-07-21 15:00:06,012.012 [log.py:35] - DEBUG - on_publish:mid:1,userdata:None
2021-07-21 15:00:06,966.966 [log.py:35] - DEBUG - disconnect
2021-07-21 15:00:06,966.966 [client.py:2165] - DEBUG - Sending DISCONNECT
2021-07-21 15:00:06,967.967 [log.py:35] - DEBUG - LoopThread thread exit
2021-07-21 15:00:06,967.967 [log.py:35] - DEBUG - on_disconnect:rc:0,userdata:None
```
As can be seen, the device simulates homeleaving and sends a `leave_home` message to the air conditioner device.
The log of the `AirConditioner1` device is as follows:
```
2021-07-21 15:00:06,030.030 [client.py:2165] - DEBUG - Received PUBLISH (d0, q1, r0, m25), 'xxx/AirConditioner1/control', ...  (69 bytes)
2021-07-21 15:00:06,031.031 [client.py:2165] - DEBUG - Sending PUBACK (Mid: 25)
2021-07-21 15:00:06,031.031 [log.py:35] - DEBUG - on_aircond_cb:payload:{"action": "leave_home", "targetDevice": "AirConditioner1"},userdata:None
2021-07-21 15:00:06,318.318 [log.py:35] - DEBUG - [air is close] temperature 22
2021-07-21 15:00:07,319.319 [log.py:35] - DEBUG - [air is close] temperature 23
2021-07-21 15:00:08,321.321 [log.py:35] - DEBUG - [air is close] temperature 23
2021-07-21 15:00:09,323.323 [log.py:35] - DEBUG - [air is close] temperature 24
2021-07-21 15:00:10,325.325 [log.py:35] - DEBUG - [air is close] temperature 24
2021-07-21 15:00:11,327.327 [log.py:35] - DEBUG - [air is close] temperature 25
2021-07-21 15:00:12,329.329 [log.py:35] - DEBUG - [air is close] temperature 25
```
As can be seen, the air conditioner is turned off and the temperature gradually goes up again after it receives the homeleaving message.
