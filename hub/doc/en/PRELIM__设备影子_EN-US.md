* [Device Shadow](#Device-Shadow)
  * [Overview](#Overview)
  * [Running demo](#Running-demo)
    * [Entering parameters for authenticating device for connection](#Entering-parameters-for-authenticating-device-for-connection)
    * [Getting status cached in cloud](#Getting-status-cached-in-cloud)
    * [Modifying device shadow status](#Modifying-device-shadow-status)
    * [Regularly updating device shadow](#Regularly-updating-device-shadow)

# Device Shadow
## Overview
Device shadow is essentially a copy of device status and configuration data in JSON format cached by the server for the device. For more information, please see [Device Shadow Details](https://cloud.tencent.com/document/product/634/11918) and [Device Shadow Data Flow](https://cloud.tencent.com/document/product/634/14072).

As an intermediary, device shadow can effectively implement two-way data sync between device and user application:

* For device configuration, the user application does not need to directly modify the device; instead, it can modify the device shadow on the server, which will sync modifications to the device. In this way, if the device is offline at the time of modification, it will receive the latest configuration from the shadow once coming back online.
* For device status, the device reports the status to the device shadow, and when users initiate queries, they can simply query the shadow. This can effectively reduce the network interactions between the device and the server, especially for low-power devices.

## Running demo
You can run the [ShadowSample.py](../../hub/sample/shadow/example_shadow.py) demo to try out operations related to device shadow.

#### Entering parameters for authenticating device for connection
Enter the information of the device created in the console in [device_info.json](../../hub/sample/device_info.json), such as the `auth_mode`, `productId`, `deviceName`, and `deviceSecret` fields of a key-authenticated device, as shown below:
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

#### Getting status cached in cloud
After running the demo, subscribe to the `$shadow/operation/result/{productID}/{deviceName}` topic and get the cloud cache.
```
2021-07-20 16:44:56,611.611 [log.py:35] - DEBUG - LoopThread thread enter
2021-07-20 16:44:56,612.612 [log.py:35] - DEBUG - connect_async (xxx.iotcloud.tencentdevices.com:8883)
2021-07-20 16:44:57,010.010 [client.py:2165] - DEBUG - Sending CONNECT (u1, p1, wr0, wq0, wf0, c1, k60) client_id=b'xxxx'
2021-07-20 16:44:57,069.069 [client.py:2165] - DEBUG - Received CONNACK (0, 0)
2021-07-20 16:44:57,069.069 [log.py:35] - DEBUG - on_connect:flags:0,rc:0,userdata:None
2021-07-20 16:44:57,613.613 [client.py:2165] - DEBUG - Sending SUBSCRIBE (d0, m1) [(b'$shadow/operation/result/xxx/test01', 0)]
2021-07-20 16:44:57,614.614 [log.py:35] - DEBUG - subscribe success topic:$shadow/operation/result/xxx/test01
2021-07-20 16:44:57,661.661 [client.py:2165] - DEBUG - Received SUBACK
2021-07-20 16:44:57,662.662 [log.py:35] - DEBUG - on_subscribe:mid:0,granted_qos:1,userdata:None
2021-07-20 16:44:57,670.670 [client.py:2165] - DEBUG - Received PUBLISH (d0, q0, r0, m0), '$shadow/operation/result/xxx/test01', ...  (192 bytes)
2021-07-20 16:44:57,670.670 [log.py:35] - DEBUG - on_shadow_cb:payload:{'clientToken': 'xxx-0', 'payload': {'state': {'reported': {'updateCount': 0, 'updateCount11': 'shadow'}}, 'timestamp': 1626770626087, 'version': 8}, 'result': 0, 'timestamp': 1626770697, 'type': 'get'},userdata:None
```
As can be seen from the log, the values of the `updateCount` and `updateCount11` fields are `0` and `shadow` respectively.

#### Modifying device shadow status
Send the `shadow GET` command to the `$shadow/operation/{productID}/{deviceName}` topic to get the device status cached in the cloud.
```
2021-07-20 16:44:57,615.615 [log.py:35] - DEBUG - [shadow update] {'type': 'update', 'state': {'reported': {'updateCount': 12, 'updateCount12': 'shadow'}}, 'clientToken': 'xxx-1'}
2021-07-20 16:44:57,615.615 [client.py:2165] - DEBUG - Sending PUBLISH (d0, q0, r0, m3), 'b'$shadow/operation/xxx/test01'', ... (120 bytes)
2021-07-20 16:44:57,615.615 [log.py:35] - DEBUG - on_publish:mid:2,userdata:None
2021-07-20 16:44:57,615.615 [log.py:35] - DEBUG - publish success
2021-07-20 16:44:57,616.616 [log.py:35] - DEBUG - on_publish:mid:3,userdata:None
```
Observe the log, update the value of the `updateCount` field to `12`, add the new `updateCount12` field with the value `shadow` in the cloud, and get the cloud cache again. The log is as follows:
```
2021-07-20 16:44:58,688.688 [client.py:2165] - DEBUG - Received PUBLISH (d0, q0, r0, m0), '$shadow/operation/result/xxx/test01', ...  (219 bytes)
2021-07-20 16:44:58,688.688 [log.py:35] - DEBUG - on_shadow_cb:payload:{'clientToken': 'xxx-3', 'payload': {'state': {'reported': {'updateCount': 12, 'updateCount11': 'shadow', 'updateCount12': 'shadow'}}, 'timestamp': 1626770698640, 'version': 10}, 'result': 0, 'timestamp': 1626770698, 'type': 'get'},userdata:None
```
As can be seen from the log, the value of the `updateCount` field is updated to `12`, the value of the `updateCount11` field is `shadow`, and the value of the new `updateCount12` field is also `shadow`.

#### Regularly updating device shadow
In the demo, the device shadow is updated once every 3 seconds by increasing the value of the `updateCount` field by 1, and the cloud cache is reset once every three updates. The log is as follows:
```
2021-07-20 16:58:40,724.724 [log.py:35] - DEBUG - LoopThread thread enter
2021-07-20 16:58:40,724.724 [log.py:35] - DEBUG - connect_async (xxx.iotcloud.tencentdevices.com:8883)
2021-07-20 16:58:41,185.185 [client.py:2165] - DEBUG - Sending CONNECT (u1, p1, wr0, wq0, wf0, c1, k60) client_id=b'xxxx'
2021-07-20 16:58:41,245.245 [client.py:2165] - DEBUG - Received CONNACK (0, 0)
2021-07-20 16:58:41,245.245 [log.py:35] - DEBUG - on_connect:flags:0,rc:0,userdata:None
2021-07-20 16:58:41,726.726 [client.py:2165] - DEBUG - Sending SUBSCRIBE (d0, m1) [(b'$shadow/operation/result/xxx/test01', 0)]
2021-07-20 16:58:41,726.726 [log.py:35] - DEBUG - subscribe success topic:$shadow/operation/result/xxx/test01
2021-07-20 16:58:41,726.726 [log.py:35] - DEBUG - [shadow update] {'type': 'update', 'state': {'reported': {'updateCount': 1, 'updateCount12': 'shadow'}}, 'clientToken': 'xxx-0'}
2021-07-20 16:58:41,727.727 [client.py:2165] - DEBUG - Sending PUBLISH (d0, q0, r0, m2), 'b'$shadow/operation/xxx/test01'', ... (119 bytes)
2021-07-20 16:58:41,727.727 [log.py:35] - DEBUG - publish success
2021-07-20 16:58:41,727.727 [client.py:2165] - DEBUG - Sending PUBLISH (d0, q0, r0, m3), 'b'$shadow/operation/xxx/test01'', ... (46 bytes)
2021-07-20 16:58:41,728.728 [log.py:35] - DEBUG - on_publish:mid:2,userdata:None
2021-07-20 16:58:41,728.728 [log.py:35] - DEBUG - publish success
2021-07-20 16:58:41,728.728 [log.py:35] - DEBUG - on_publish:mid:3,userdata:None
2021-07-20 16:58:41,778.778 [client.py:2165] - DEBUG - Received SUBACK
2021-07-20 16:58:41,779.779 [log.py:35] - DEBUG - on_subscribe:mid:0,granted_qos:1,userdata:None
2021-07-20 16:58:41,795.795 [client.py:2165] - DEBUG - Received PUBLISH (d0, q0, r0, m0), '$shadow/operation/result/xxx/test01', ...  (174 bytes)
2021-07-20 16:58:41,795.795 [log.py:35] - DEBUG - on_shadow_cb:payload:{'clientToken': 'xxx-0', 'payload': {'state': {'reported': {'updateCount': 1}}, 'timestamp': 1626771521739, 'version': 21}, 'result': 0, 'timestamp': 1626771521739, 'type': 'update'},userdata:None
2021-07-20 16:58:41,802.802 [client.py:2165] - DEBUG - Received PUBLISH (d0, q0, r0, m0), '$shadow/operation/result/xxx/test01', ...  (218 bytes)
2021-07-20 16:58:41,802.802 [log.py:35] - DEBUG - on_shadow_cb:payload:{'clientToken': 'xxx-1', 'payload': {'state': {'reported': {'updateCount': 1, 'updateCount11': 'shadow', 'updateCount12': 'shadow'}}, 'timestamp': 1626771521739, 'version': 21}, 'result': 0, 'timestamp': 1626771521, 'type': 'get'},userdata:None
2021-07-20 16:58:44,729.729 [log.py:35] - DEBUG - [shadow update] {'type': 'update', 'state': {'reported': {'updateCount': 2, 'updateCount12': 'shadow'}}, 'clientToken': 'xxx-2'}
2021-07-20 16:58:44,729.729 [client.py:2165] - DEBUG - Sending PUBLISH (d0, q0, r0, m4), 'b'$shadow/operation/xxx/test01'', ... (119 bytes)
2021-07-20 16:58:44,729.729 [log.py:35] - DEBUG - publish success
2021-07-20 16:58:44,730.730 [client.py:2165] - DEBUG - Sending PUBLISH (d0, q0, r0, m5), 'b'$shadow/operation/xxx/test01'', ... (46 bytes)
2021-07-20 16:58:44,730.730 [log.py:35] - DEBUG - on_publish:mid:4,userdata:None
2021-07-20 16:58:44,730.730 [log.py:35] - DEBUG - publish success
2021-07-20 16:58:44,730.730 [log.py:35] - DEBUG - on_publish:mid:5,userdata:None
2021-07-20 16:58:44,804.804 [client.py:2165] - DEBUG - Received PUBLISH (d0, q0, r0, m0), '$shadow/operation/result/xxx/test01', ...  (174 bytes)
2021-07-20 16:58:44,805.805 [log.py:35] - DEBUG - on_shadow_cb:payload:{'clientToken': 'xxx-2', 'payload': {'state': {'reported': {'updateCount': 2}}, 'timestamp': 1626771524751, 'version': 22}, 'result': 0, 'timestamp': 1626771524751, 'type': 'update'},userdata:None
2021-07-20 16:58:44,810.810 [client.py:2165] - DEBUG - Received PUBLISH (d0, q0, r0, m0), '$shadow/operation/result/xxx/test01', ...  (218 bytes)
2021-07-20 16:58:44,811.811 [log.py:35] - DEBUG - on_shadow_cb:payload:{'clientToken': 'xxx-3', 'payload': {'state': {'reported': {'updateCount': 2, 'updateCount11': 'shadow', 'updateCount12': 'shadow'}}, 'timestamp': 1626771524751, 'version': 22}, 'result': 0, 'timestamp': 1626771524, 'type': 'get'},userdata:None
2021-07-20 16:58:47,734.734 [log.py:35] - DEBUG - [shadow update] {'type': 'update', 'state': {'reported': {'updateCount': 3, 'updateCount12': 'shadow'}}, 'clientToken': 'xxx-4'}
2021-07-20 16:58:47,734.734 [client.py:2165] - DEBUG - Sending PUBLISH (d0, q0, r0, m6), 'b'$shadow/operation/xxx/test01'', ... (119 bytes)
2021-07-20 16:58:47,734.734 [log.py:35] - DEBUG - publish success
2021-07-20 16:58:47,735.735 [client.py:2165] - DEBUG - Sending PUBLISH (d0, q0, r0, m7), 'b'$shadow/operation/xxx/test01'', ... (46 bytes)
2021-07-20 16:58:47,735.735 [log.py:35] - DEBUG - on_publish:mid:6,userdata:None
2021-07-20 16:58:47,735.735 [log.py:35] - DEBUG - publish success
2021-07-20 16:58:47,736.736 [log.py:35] - DEBUG - on_publish:mid:7,userdata:None
2021-07-20 16:58:47,808.808 [client.py:2165] - DEBUG - Received PUBLISH (d0, q0, r0, m0), '$shadow/operation/result/xxx/test01', ...  (174 bytes)
2021-07-20 16:58:47,809.809 [log.py:35] - DEBUG - on_shadow_cb:payload:{'clientToken': 'xxx-4', 'payload': {'state': {'reported': {'updateCount': 3}}, 'timestamp': 1626771527749, 'version': 23}, 'result': 0, 'timestamp': 1626771527749, 'type': 'update'},userdata:None
2021-07-20 16:58:47,816.816 [client.py:2165] - DEBUG - Received PUBLISH (d0, q0, r0, m0), '$shadow/operation/result/xxx/test01', ...  (218 bytes)
2021-07-20 16:58:47,817.817 [log.py:35] - DEBUG - on_shadow_cb:payload:{'clientToken': 'xxx-5', 'payload': {'state': {'reported': {'updateCount': 3, 'updateCount11': 'shadow', 'updateCount12': 'shadow'}}, 'timestamp': 1626771527749, 'version': 23}, 'result': 0, 'timestamp': 1626771527, 'type': 'get'},userdata:None
2021-07-20 16:58:50,739.739 [log.py:35] - DEBUG - [shadow update] {'type': 'update', 'state': {'reported': {'updateCount': 4, 'updateCount12': 'shadow'}}, 'clientToken': 'xxx-6'}
2021-07-20 16:58:50,739.739 [client.py:2165] - DEBUG - Sending PUBLISH (d0, q0, r0, m8), 'b'$shadow/operation/xxx/test01'', ... (119 bytes)
2021-07-20 16:58:50,740.740 [log.py:35] - DEBUG - publish success
2021-07-20 16:58:50,740.740 [client.py:2165] - DEBUG - Sending PUBLISH (d0, q0, r0, m9), 'b'$shadow/operation/xxx/test01'', ... (46 bytes)
2021-07-20 16:58:50,740.740 [log.py:35] - DEBUG - on_publish:mid:8,userdata:None
2021-07-20 16:58:50,741.741 [log.py:35] - DEBUG - on_publish:mid:9,userdata:None
2021-07-20 16:58:50,741.741 [log.py:35] - DEBUG - publish success
2021-07-20 16:58:50,801.801 [client.py:2165] - DEBUG - Received PUBLISH (d0, q0, r0, m0), '$shadow/operation/result/xxx/test01', ...  (174 bytes)
2021-07-20 16:58:50,801.801 [log.py:35] - DEBUG - on_shadow_cb:payload:{'clientToken': 'xxx-6', 'payload': {'state': {'reported': {'updateCount': 4}}, 'timestamp': 1626771530765, 'version': 24}, 'result': 0, 'timestamp': 1626771530765, 'type': 'update'},userdata:None
2021-07-20 16:58:50,808.808 [client.py:2165] - DEBUG - Received PUBLISH (d0, q0, r0, m0), '$shadow/operation/result/xxx/test01', ...  (218 bytes)
2021-07-20 16:58:50,808.808 [log.py:35] - DEBUG - on_shadow_cb:payload:{'clientToken': 'xxx-7', 'payload': {'state': {'reported': {'updateCount': 4, 'updateCount11': 'shadow', 'updateCount12': 'shadow'}}, 'timestamp': 1626771530765, 'version': 24}, 'result': 0, 'timestamp': 1626771530, 'type': 'get'},userdata:None
2021-07-20 16:58:53,745.745 [log.py:35] - DEBUG - [shadow update] {'type': 'update', 'state': {'reported': {'updateCount': 5, 'updateCount12': 'shadow'}}, 'clientToken': 'xxx-8'}
2021-07-20 16:58:53,745.745 [client.py:2165] - DEBUG - Sending PUBLISH (d0, q0, r0, m10), 'b'$shadow/operation/xxx/test01'', ... (119 bytes)
2021-07-20 16:58:53,745.745 [log.py:35] - DEBUG - publish success
2021-07-20 16:58:53,745.745 [client.py:2165] - DEBUG - Sending PUBLISH (d0, q0, r0, m11), 'b'$shadow/operation/xxx/test01'', ... (46 bytes)
2021-07-20 16:58:53,746.746 [log.py:35] - DEBUG - on_publish:mid:10,userdata:None
2021-07-20 16:58:53,746.746 [log.py:35] - DEBUG - publish success
2021-07-20 16:58:53,746.746 [log.py:35] - DEBUG - on_publish:mid:11,userdata:None
2021-07-20 16:58:53,821.821 [client.py:2165] - DEBUG - Received PUBLISH (d0, q0, r0, m0), '$shadow/operation/result/xxx/test01', ...  (174 bytes)
2021-07-20 16:58:53,821.821 [log.py:35] - DEBUG - on_shadow_cb:payload:{'clientToken': 'xxx-8', 'payload': {'state': {'reported': {'updateCount': 5}}, 'timestamp': 1626771533769, 'version': 25}, 'result': 0, 'timestamp': 1626771533769, 'type': 'update'},userdata:None
2021-07-20 16:58:53,827.827 [client.py:2165] - DEBUG - Received PUBLISH (d0, q0, r0, m0), '$shadow/operation/result/xxx/test01', ...  (218 bytes)
2021-07-20 16:58:53,827.827 [log.py:35] - DEBUG - on_shadow_cb:payload:{'clientToken': 'xxx-9', 'payload': {'state': {'reported': {'updateCount': 5, 'updateCount11': 'shadow', 'updateCount12': 'shadow'}}, 'timestamp': 1626771533769, 'version': 25}, 'result': 0, 'timestamp': 1626771533, 'type': 'get'},userdata:None
```
As can be seen from the log, the value of the `updateCount` field is increased by 1 after each time of reporting from 1 to 3 after three times of reporting. Then, after the cloud cache is reset, it restores to its initial status (with the `updateCount11` and `updateCount12` fields cleared). After the `updateCount` field with a value of 4 and the `updateCount11` and `updateCount12` fields are reported again, the cloud cache is updated from the initial status again.