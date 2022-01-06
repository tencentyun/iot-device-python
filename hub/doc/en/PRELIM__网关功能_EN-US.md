* [Gateway Feature](#Gateway-Feature)
  * [Overview](#Overview)
  * [Running demo](#Running-demo)
    * [Entering parameters for authenticating device for connection](#Entering-parameters-for-authenticating-device-for-connection)
    * [Proxying subdevice connection and disconnection](#Proxying-subdevice-connection-and-disconnection)
    * [Binding and unbinding subdevice](#Binding-and-unbinding-subdevice)
    * [Querying the list of bound subdevices](#Querying-the-list-of-bound-subdevices)
    * [Updating subdevice firmware](#Updating-subdevice-firmware)

# Gateway Feature
## Overview
In addition to the basic features of general products, a gateway product can also be bound to products that cannot directly access the internet and used to exchange data with IoT Hub on behalf of such products (i.e., subdevices). This document describes how to connect a gateway product to IoT Hub over the MQTT protocol for proxied subdevice connection/disconnection and message sending/receiving.

To try out the gateway feature, you need to create a gateway product in the console and bind a subproduct and a subdevice. For more information, please see [Device Connection Preparations](https://cloud.tencent.com/document/product/634/14442) and [Gateway Product Connection](https://cloud.tencent.com/document/product/634/32740).

## Running demo
You can run the [GatewaySample.py](../../hub/sample/gateway/example_gateway.py) demo to try out processes such as proxied subdevice connection/disconnection through the gateway, subdevice binding/unbinding, and subdevice firmware update.

#### Entering parameters for authenticating device for connection
Enter the information of the device created in the console in [device_info.json](../../hub/sample/device_info.json), such as the `auth_mode`, `productId`, `deviceName`, and `deviceSecret` fields of a key-authenticated device as well as certain fields of a subdevice (`subDev`), as shown below:
```
{
  "auth_mode":"KEY",
  "productId":"xxx",
  "deviceName":"test01",
  "key_deviceinfo":{
    "deviceSecret":"xxxx"
  }
}
"subDev":{
  "subdev_num":2,
  "subdev_list":
  [
    {"sub_productId": "xxxx", "sub_devName": "test1"},
    {"sub_productId": "xxxx", "sub_devName": "dev1"}
  ]
}
```

#### Proxying subdevice connection and disconnection
In the configuration file of the demo, two subdevices are bound to the gateway device, with their `device_name` being `test1` and `dev1` respectively.
* Proxied subdevice connection through a gateway
Offline subdevices can be connected through the gateway:
```
2021-07-19 14:58:18,394.394 [log.py:35] - DEBUG - LoopThread thread enter
2021-07-19 14:58:18,403.403 [log.py:35] - DEBUG - connect_async (xxx.iotcloud.tencentdevices.com:8883)
2021-07-19 14:58:19,585.585 [client.py:2165] - DEBUG - Sending CONNECT (u1, p1, wr0, wq0, wf0, c1, k60) client_id=b'xxxtest01'
2021-07-19 14:58:19,678.678 [client.py:2165] - DEBUG - Received CONNACK (0, 0)
2021-07-19 14:58:19,678.678 [log.py:35] - DEBUG - on_connect:flags:0,rc:0,userdata:None
2021-07-19 14:58:20,398.398 [client.py:2165] - DEBUG - Sending SUBSCRIBE (d0, m1) [(b'$gateway/operation/result/xxx/test01', 0)]
2021-07-19 14:58:20,399.399 [log.py:35] - DEBUG - subscribe success topic:$gateway/operation/result/xxx/test01
2021-07-19 14:58:20,459.459 [client.py:2165] - DEBUG - Received SUBACK
2021-07-19 14:58:20,460.460 [log.py:35] - DEBUG - on_subscribe:mid:0,granted_qos:1,userdata:None
1
2021-07-19 14:58:24,178.178 [client.py:2165] - DEBUG - Sending PUBLISH (d0, q0, r0, m2), 'b'$gateway/operation/xxx/test01'', ... (98 bytes)
2021-07-19 14:58:24,178.178 [log.py:35] - DEBUG - publish success
2021-07-19 14:58:24,178.178 [log.py:35] - DEBUG - on_publish:mid:2,userdata:None
2021-07-19 14:58:24,291.291 [client.py:2165] - DEBUG - Received PUBLISH (d0, q0, r0, m0), '$gateway/operation/result/xxx/test01', ...  (102 bytes)
2021-07-19 14:58:24,379.379 [log.py:35] - DEBUG - client:xxx/test1 online success
2021-07-19 14:58:24,379.379 [client.py:2165] - DEBUG - Sending SUBSCRIBE (d0, m3) [(b'xxx/test1/data', 0)]
2021-07-19 14:58:24,379.379 [log.py:35] - DEBUG - subscribe success topic:xxx/test1/data
2021-07-19 14:58:24,380.380 [log.py:35] - DEBUG - gateway subdev subscribe success
2021-07-19 14:58:24,380.380 [client.py:2165] - DEBUG - Sending PUBLISH (d0, q1, r0, m4), 'b'xxx/test1/data'', ... (36 bytes)
2021-07-19 14:58:24,388.388 [log.py:35] - DEBUG - publish success
2021-07-19 14:58:24,388.388 [log.py:35] - DEBUG - online success
2021-07-19 14:58:24,389.389 [client.py:2165] - DEBUG - Sending PUBLISH (d0, q0, r0, m5), 'b'$gateway/operation/xxx/test01'', ... (97 bytes)
2021-07-19 14:58:24,389.389 [log.py:35] - DEBUG - on_publish:mid:5,userdata:None
2021-07-19 14:58:24,389.389 [log.py:35] - DEBUG - publish success
2021-07-19 14:58:24,464.464 [client.py:2165] - DEBUG - Received PUBACK (Mid: 4)
2021-07-19 14:58:24,465.465 [log.py:35] - DEBUG - on_publish:mid:4,userdata:None
2021-07-19 14:58:24,467.467 [client.py:2165] - DEBUG - Received SUBACK
2021-07-19 14:58:24,467.467 [log.py:35] - DEBUG - on_subscribe:mid:0,granted_qos:3,userdata:None
2021-07-19 14:58:24,499.499 [client.py:2165] - DEBUG - Received PUBLISH (d0, q0, r0, m0), '$gateway/operation/result/xxx/test01', ...  (101 bytes)
2021-07-19 14:58:24,590.590 [log.py:35] - DEBUG - client:xxx/dev1 online success
2021-07-19 14:58:24,590.590 [client.py:2165] - DEBUG - Sending SUBSCRIBE (d0, m6) [(b'xxx/dev1/data', 0)]
2021-07-19 14:58:24,591.591 [log.py:35] - DEBUG - subscribe success topic:xxx/dev1/data
2021-07-19 14:58:24,591.591 [log.py:35] - DEBUG - gateway subdev subscribe success
2021-07-19 14:58:24,591.591 [client.py:2165] - DEBUG - Sending PUBLISH (d0, q1, r0, m7), 'b'xxx/dev1/data'', ... (36 bytes)
2021-07-19 14:58:24,591.591 [log.py:35] - DEBUG - publish success
2021-07-19 14:58:24,591.591 [log.py:35] - DEBUG - online success
2021-07-19 14:58:24,675.675 [client.py:2165] - DEBUG - Received PUBACK (Mid: 7)
2021-07-19 14:58:24,676.676 [log.py:35] - DEBUG - on_publish:mid:7,userdata:None
2021-07-19 14:58:24,686.686 [client.py:2165] - DEBUG - Received SUBACK
2021-07-19 14:58:24,686.686 [log.py:35] - DEBUG - on_subscribe:mid:0,granted_qos:6,userdata:None
```
As can be seen from the log, the two subdevices `test1` and `dev1` are connected successfully (`online success`). At this point, you can see in the console that the subdevices are online.

* Proxied subdevice disconnection through a gateway
Online subdevices can be disconnected through the gateway:
```
2021-07-19 15:12:31,923.923 [client.py:2165] - DEBUG - Sending PUBLISH (d0, q0, r0, m8), 'b'$gateway/operation/xxx/test01'', ... (99 bytes)
2021-07-19 15:12:31,925.925 [log.py:35] - DEBUG - publish success
2021-07-19 15:12:31,926.926 [log.py:35] - DEBUG - on_publish:mid:8,userdata:None
2021-07-19 15:12:31,995.995 [client.py:2165] - DEBUG - Received PUBLISH (d0, q0, r0, m0), '$gateway/operation/result/xxx/test01', ...  (103 bytes)
2021-07-19 15:12:32,126.126 [log.py:35] - DEBUG - client:xxx/test1 offline success
2021-07-19 15:12:32,126.126 [log.py:35] - DEBUG - offline success
2021-07-19 15:12:32,126.126 [client.py:2165] - DEBUG - Sending PUBLISH (d0, q0, r0, m9), 'b'$gateway/operation/xxx/test01'', ... (98 bytes)
2021-07-19 15:12:32,127.127 [log.py:35] - DEBUG - publish success
2021-07-19 15:12:32,127.127 [log.py:35] - DEBUG - on_publish:mid:9,userdata:None
2021-07-19 15:12:32,219.219 [client.py:2165] - DEBUG - Received PUBLISH (d0, q0, r0, m0), '$gateway/operation/result/xxx/test01', ...  (102 bytes)
2021-07-19 15:12:32,327.327 [log.py:35] - DEBUG - client:xxx/dev1 offline success
2021-07-19 15:12:32,328.328 [log.py:35] - DEBUG - offline success
```
As can be seen from the log, the two subdevices just connected are disconnected successfully (`offline success`) through the gateway.

#### Binding and unbinding subdevice
* Bind a subdevice
Subdevices not bound to a gateway can be bound on the device side.
```
2021-07-19 15:26:35,524.524 [log.py:35] - DEBUG - sign base64 *****************
2021-07-19 15:26:35,524.524 [client.py:2165] - DEBUG - Sending PUBLISH (d0, q0, r0, m6), 'b'$gateway/operation/xxx/test01'', ... (231 bytes)
2021-07-19 15:26:35,525.525 [log.py:35] - DEBUG - publish success
2021-07-19 15:26:35,525.525 [log.py:35] - DEBUG - client:xxx/test1 bind success
2021-07-19 15:26:35,525.525 [log.py:35] - DEBUG - bind success
2021-07-19 15:26:35,525.525 [log.py:35] - DEBUG - on_publish:mid:6,userdata:None
2021-07-19 15:26:35,597.597 [client.py:2165] - DEBUG - Received PUBLISH (d0, q0, r0, m0), '$gateway/operation/result/xxx/test01', ...  (100 bytes)
```
As can be seen from the log, the `test1` subdevice is bound to the gateway successfully. At this point, you can see in the console that `test1` is already in the subdevice list.

* Unbind a subdevice
Subdevices bound to a gateway can be unbound on the device side.
```
2021-07-19 15:21:05,701.701 [client.py:2165] - DEBUG - Sending PUBLISH (d0, q0, r0, m3), 'b'$gateway/operation/xxx/test01'', ... (98 bytes)
2021-07-19 15:21:05,701.701 [log.py:35] - DEBUG - publish success
2021-07-19 15:21:05,701.701 [log.py:35] - DEBUG - on_publish:mid:3,userdata:None
2021-07-19 15:21:05,786.786 [client.py:2165] - DEBUG - Received PUBLISH (d0, q0, r0, m0), '$gateway/operation/result/xxx/test01', ...  (102 bytes)
2021-07-19 15:21:05,902.902 [log.py:35] - DEBUG - client:xxx/test1 unbind success
2021-07-19 15:21:05,902.902 [log.py:35] - DEBUG - unbind success
```
As can be seen from the log, the `test1` subdevice is unbound from the gateway successfully. At this point, you can see in the console that `test1` is not in the subdevice list.

#### Querying the list of bound subdevices
You can query the list of subdevices bound to the current gateway on the device side.
```
2021-07-19 15:28:01,941.941 [client.py:2165] - DEBUG - Sending PUBLISH (d0, q0, r0, m7), 'b'$gateway/operation/xxx/test01'', ... (32 bytes)
2021-07-19 15:28:01,941.941 [log.py:35] - DEBUG - publish success
2021-07-19 15:28:01,942.942 [log.py:35] - DEBUG - on_publish:mid:7,userdata:None
2021-07-19 15:28:02,016.016 [client.py:2165] - DEBUG - Received PUBLISH (d0, q0, r0, m0), '$gateway/operation/result/xxx/test01', ...  (154 bytes)
2021-07-19 15:28:02,142.142 [log.py:35] - DEBUG - client:xxx/test01 get bind list success
2021-07-19 15:28:02,142.142 [log.py:35] - DEBUG - subdev id:xxx, name:dev1
2021-07-19 15:28:02,142.142 [log.py:35] - DEBUG - subdev id:xxx, name:test1
```
As can be seen from the log, two subdevices are bound to the current gateway, with their `device_name` being `test1` and `dev1` respectively.

#### Updating subdevice firmware
Subdevice firmware update requires the gateway to download the firmware and then deliver it to the subdevice for update.
```
2021-07-20 10:14:15,311.311 [log.py:35] - DEBUG - LoopThread thread enter
2021-07-20 10:14:15,312.312 [log.py:35] - DEBUG - connect_async (xxx.iotcloud.tencentdevices.com:8883)
2021-07-20 10:14:16,976.976 [client.py:2165] - DEBUG - Sending CONNECT (u1, p1, wr0, wq0, wf0, c1, k60) client_id=b'xxxx'
2021-07-20 10:14:17,057.057 [client.py:2165] - DEBUG - Received CONNACK (0, 0)
2021-07-20 10:14:17,057.057 [log.py:35] - DEBUG - on_connect:flags:0,rc:0,userdata:None
2021-07-20 10:14:17,315.315 [client.py:2165] - DEBUG - Sending SUBSCRIBE (d0, m1) [(b'$gateway/operation/result/xxx/test01', 0)]
2021-07-20 10:14:17,317.317 [log.py:35] - DEBUG - subscribe success topic:$gateway/operation/result/xxx/test01
2021-07-20 10:14:17,401.401 [client.py:2165] - DEBUG - Received SUBACK
2021-07-20 10:14:17,401.401 [log.py:35] - DEBUG - on_subscribe:mid:0,granted_qos:1,userdata:None
6
2021-07-20 10:14:18,791.791 [log.py:35] - DEBUG -  ota test start...
2021-07-20 10:14:18,791.791 [client.py:2165] - DEBUG - Sending SUBSCRIBE (d0, m2) [(b'$ota/update/xxx/test1', 1)]
2021-07-20 10:14:18,791.791 [log.py:35] - DEBUG - subscribe success topic:$ota/update/xxx/test1
2021-07-20 10:14:18,792.792 [log.py:35] - DEBUG -  ota test start...
2021-07-20 10:14:18,792.792 [client.py:2165] - DEBUG - Sending SUBSCRIBE (d0, m3) [(b'$ota/update/xxx/dev1', 1)]
2021-07-20 10:14:18,793.793 [log.py:35] - DEBUG - subscribe success topic:$ota/update/xxx/dev1
2021-07-20 10:14:18,868.868 [client.py:2165] - DEBUG - Received SUBACK
2021-07-20 10:14:18,868.868 [log.py:35] - DEBUG - on_subscribe:mid:1,granted_qos:2,userdata:None
2021-07-20 10:14:18,993.993 [client.py:2165] - DEBUG - Sending PUBLISH (d0, q1, r0, m4), 'b'$ota/report/xxx/test1'', ... (58 bytes)
2021-07-20 10:14:18,993.993 [log.py:35] - DEBUG - publish success
2021-07-20 10:14:19,718.718 [client.py:2165] - DEBUG - Received SUBACK
2021-07-20 10:14:19,718.718 [client.py:2165] - DEBUG - Received PUBACK (Mid: 4)
2021-07-20 10:14:19,718.718 [client.py:2165] - DEBUG - Received PUBLISH (d0, q0, r0, m0), '$ota/update/xxx/test1', ...  (86 bytes)
2021-07-20 10:14:19,718.718 [log.py:35] - DEBUG - on_subscribe:mid:1,granted_qos:3,userdata:None
2021-07-20 10:14:19,719.719 [log.py:35] - DEBUG - on_publish:mid:4,userdata:None
2021-07-20 10:14:19,719.719 [client.py:2165] - DEBUG - Received PUBLISH (d0, q0, r0, m0), '$ota/update/xxx/test1', ...  (472 bytes)
2021-07-20 10:14:19,719.719 [log.py:35] - DEBUG - __on_ota_report:topic:$ota/update/xxx/test1,payload:{'result_code': 0, 'result_msg': 'success', 'type': 'report_version_rsp', 'version': '0.1.0'}
2021-07-20 10:14:19,796.796 [client.py:2165] - DEBUG - Sending PUBLISH (d0, q1, r0, m5), 'b'$ota/report/xxx/dev1'', ... (58 bytes)
2021-07-20 10:14:19,796.796 [log.py:35] - DEBUG - publish success
2021-07-20 10:14:19,870.870 [client.py:2165] - DEBUG - Received PUBACK (Mid: 5)
2021-07-20 10:14:19,870.870 [log.py:35] - DEBUG - on_publish:mid:5,userdata:None
2021-07-20 10:14:19,887.887 [client.py:2165] - DEBUG - Received PUBLISH (d0, q0, r0, m0), '$ota/update/xxx/dev1', ...  (86 bytes)
2021-07-20 10:14:19,888.888 [log.py:35] - DEBUG - __on_ota_report:topic:$ota/update/xxx/dev1,payload:{'result_code': 0, 'result_msg': 'success', 'type': 'report_version_rsp', 'version': '0.1.0'}
2021-07-20 10:14:19,994.994 [log.py:35] - DEBUG - wait for ota upgrade command
2021-07-20 10:14:19,994.994 [log.py:47] - ERROR - info file not exists
2021-07-20 10:14:19,994.994 [log.py:35] - DEBUG - local_size:0,local_ver:None,re_ver:1.0.0
__ota_http_deinit do nothing
2021-07-20 10:14:20,799.799 [log.py:35] - DEBUG - wait for ota upgrade command
2021-07-20 10:14:20,991.991 [log.py:35] - DEBUG - [ota report] {'type': 'report_progress', 'report': {'progress': {'state': 'downloading', 'percent': '0', 'result_code': '0', 'result_msg': ''}, 'version': '1.0.0'}}
2021-07-20 10:14:20,991.991 [client.py:2165] - DEBUG - Sending PUBLISH (d0, q0, r0, m6), 'b'$ota/report/xxx/test1'', ... (151 bytes)
2021-07-20 10:14:20,991.991 [log.py:35] - DEBUG - publish success
2021-07-20 10:14:20,991.991 [log.py:35] - DEBUG - on_publish:mid:6,userdata:None
2021-07-20 10:14:21,160.160 [log.py:35] - DEBUG - [ota report] {'type': 'report_progress', 'report': {'progress': {'state': 'downloading', 'percent': '0', 'result_code': '0', 'result_msg': ''}, 'version': '1.0.0'}}
2021-07-20 10:14:21,161.161 [client.py:2165] - DEBUG - Sending PUBLISH (d0, q0, r0, m7), 'b'$ota/report/xxx/test1'', ... (151 bytes)
2021-07-20 10:14:21,161.161 [log.py:35] - DEBUG - publish success
2021-07-20 10:14:21,162.162 [log.py:35] - DEBUG - on_publish:mid:7,userdata:None
2021-07-20 10:14:21,800.800 [log.py:35] - DEBUG - wait for ota upgrade command
2021-07-20 10:14:22,038.038 [log.py:35] - DEBUG - [ota report] {'type': 'report_progress', 'report': {'progress': {'state': 'downloading', 'percent': '0', 'result_code': '0', 'result_msg': ''}, 'version': '1.0.0'}}
2021-07-20 10:14:22,038.038 [client.py:2165] - DEBUG - Sending PUBLISH (d0, q0, r0, m8), 'b'$ota/report/xxx/test1'', ... (151 bytes)
2021-07-20 10:14:22,039.039 [log.py:35] - DEBUG - publish success
2021-07-20 10:14:22,039.039 [log.py:35] - DEBUG - on_publish:mid:8,userdata:None
2021-07-20 10:14:22,801.801 [log.py:35] - DEBUG - wait for ota upgrade command
2021-07-20 10:14:23,105.105 [log.py:35] - DEBUG - [ota report] {'type': 'report_progress', 'report': {'progress': {'state': 'downloading', 'percent': '1', 'result_code': '0', 'result_msg': ''}, 'version': '1.0.0'}}
2021-07-20 10:14:23,106.106 [client.py:2165] - DEBUG - Sending PUBLISH (d0, q0, r0, m9), 'b'$ota/report/xxx/test1'', ... (151 bytes)
2021-07-20 10:14:23,107.107 [log.py:35] - DEBUG - publish success
2021-07-20 10:14:23,108.108 [log.py:35] - DEBUG - on_publish:mid:9,userdata:None
2021-07-20 10:14:23,803.803 [log.py:35] - DEBUG - wait for ota upgrade command
2021-07-20 10:14:24,107.107 [log.py:35] - DEBUG - [ota report] {'type': 'report_progress', 'report': {'progress': {'state': 'downloading', 'percent': '2', 'result_code': '0', 'result_msg': ''}, 'version': '1.0.0'}}
2021-07-20 10:14:24,107.107 [client.py:2165] - DEBUG - Sending PUBLISH (d0, q0, r0, m10), 'b'$ota/report/xxx/test1'', ... (151 bytes)
2021-07-20 10:14:24,107.107 [log.py:35] - DEBUG - publish success
2021-07-20 10:14:24,108.108 [log.py:35] - DEBUG - on_publish:mid:10,userdata:None
2021-07-20 10:14:24,804.804 [log.py:35] - DEBUG - wait for ota upgrade command
2021-07-20 10:14:25,684.684 [log.py:35] - DEBUG - [ota report] {'type': 'report_progress', 'report': {'progress': {'state': 'downloading', 'percent': '2', 'result_code': '0', 'result_msg': ''}, 'version': '1.0.0'}}
2021-07-20 10:14:25,684.684 [client.py:2165] - DEBUG - Sending PUBLISH (d0, q0, r0, m11), 'b'$ota/report/xxx/test1'', ... (151 bytes)
2021-07-20 10:14:25,685.685 [log.py:35] - DEBUG - publish success
2021-07-20 10:14:25,685.685 [log.py:35] - DEBUG - on_publish:mid:11,userdata:None
2021-07-20 10:14:25,806.806 [log.py:35] - DEBUG - wait for ota upgrade command
2021-07-20 10:14:26,062.062 [log.py:35] - DEBUG - [ota report] {'type': 'report_progress', 'report': {'progress': {'state': 'downloading', 'percent': '3', 'result_code': '0', 'result_msg': ''}, 'version': '1.0.0'}}
2021-07-20 10:14:26,062.062 [client.py:2165] - DEBUG - Sending PUBLISH (d0, q0, r0, m12), 'b'$ota/report/xxx/test1'', ... (151 bytes)
2021-07-20 10:14:26,063.063 [log.py:35] - DEBUG - publish success
2021-07-20 10:14:26,063.063 [log.py:35] - DEBUG - on_publish:mid:12,userdata:None
2021-07-20 10:14:26,808.808 [log.py:35] - DEBUG - wait for ota upgrade command
```
The above log represents the process of subdevice firmware update through the gateway. The gateway is `xxx/test01`, and two subdevices are bound to it: `xxx/test1` and `xxx/dev1`. The console delivers a firmware update command to the `xxx/test1` subdevice for update, while the `xxx/dev1` device is in the waiting status. After downloading the firmware on behalf of the subdevice, the gateway needs to deliver the firmware to the subdevice and ask it to update. After the subdevice update is completed, the subdevice needs to notify the gateway of the update result, so that the gateway can report the update result on its behalf.
