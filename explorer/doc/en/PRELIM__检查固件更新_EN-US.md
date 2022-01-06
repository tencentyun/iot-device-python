* [Checking for Firmware Update](#Checking-for-Firmware-Update)
  * [Subscribing and publishing to topic for checking for firmware update](#Subscribing-and-publishing-to-topic-for-checking-for-firmware-update)
  * [Updating firmware](#Updating-firmware)

# Checking for Firmware Update
Device firmware update (aka OTA) is an important part of the IoT Hub service. When a device has new features available or vulnerabilities that need to be fixed, firmware update can be quickly performed for it through the OTA service. For more information, please see [Firmware Update](https://cloud.tencent.com/document/product/634/14673).

To try out firmware update, you need to add a new firmware file in the console. For more information, please see [Device Firmware Update](https://cloud.tencent.com/document/product/634/14674).

This document describes how to subscribe and publish to the topic for checking for firmware update.

## Subscribing and publishing to topic for checking for firmware update 

Run [OtaSample.py](../../explorer/sample/ota/example_ota.py). After the device is connected, it will subscribe to the relevant topic, check the current firmware version, and report it.

The relevant topics are as follows:
* Subscribe to the topic for checking for firmware update: `$ota/update/${productID}/${deviceName}`
* Publish to the topic for checking for firmware update: `$ota/report/${productID}/${deviceName}`

Observe the log:
```
2021-07-19 10:54:26,800.800 [log.py:35] - DEBUG - LoopThread thread enter
2021-07-19 10:54:26,800.800 [log.py:35] - DEBUG - connect_async (xxx.iotcloud.tencentdevices.com:8883)
2021-07-19 10:54:28,159.159 [client.py:2165] - DEBUG - Sending CONNECT (u1, p1, wr0, wq0, wf0, c1, k60) client_id=b'xxxx'
2021-07-19 10:54:28,384.384 [client.py:2165] - DEBUG - Received CONNACK (0, 0)
2021-07-19 10:54:28,385.385 [log.py:35] - DEBUG - on_connect:flags:0,rc:0,userdata:None
2021-07-19 10:54:28,803.803 [client.py:2165] - DEBUG - Sending SUBSCRIBE (d0, m1) [(b'$ota/update/xxx/xxx', 1)]
2021-07-19 10:54:28,803.803 [log.py:35] - DEBUG - subscribe success topic:$ota/update/xxx/xxx
2021-07-19 10:54:28,932.932 [client.py:2165] - DEBUG - Received SUBACK
2021-07-19 10:54:28,932.932 [log.py:35] - DEBUG - on_subscribe:mid:1,granted_qos:1,userdata:None
2021-07-19 10:54:29,004.004 [client.py:2165] - DEBUG - Sending PUBLISH (d0, q1, r0, m2), 'b'$ota/report/xxx/xxx'', ... (58 bytes)
2021-07-19 10:54:29,005.005 [log.py:35] - DEBUG - publish success
2021-07-19 10:54:29,144.144 [client.py:2165] - DEBUG - Received PUBACK (Mid: 2)
2021-07-19 10:54:29,145.145 [client.py:2165] - DEBUG - Received PUBLISH (d0, q0, r0, m0), '$ota/update/xxx/xxx', ...  (86 bytes)
2021-07-19 10:54:29,147.147 [log.py:35] - DEBUG - on_ota_report:payload:{'result_code': 0, 'result_msg': 'success', 'type': 'report_version_rsp', 'version': '0.1.0'},userdata:None
2021-07-19 10:54:30,006.006 [log.py:35] - DEBUG - wait for ota upgrade command
2021-07-19 10:54:31,008.008 [log.py:35] - DEBUG - wait for ota upgrade command
```
As can be seen from the above log, after the demo goes online, it subscribes to the `$ota/update/xxx/xxx` topic (`xxx/xxx` is the real `product_id` and `device_name`) to receive commands delivered by the cloud, checks the current local firmware version, reports the version number (`0.1.0` here) to the cloud through the `$ota/report/xxx/xxx` topic, receives a reply from the cloud, and waits for the update command.

## Updating firmware

In the firmware update module of the IoT Explorer console, you can upload a new version of the firmware for a product, update the firmware of a specified device, and update the firmware of devices in batches. For more information, please see [Firmware Update](https://cloud.tencent.com/document/product/1081/40296).

After the firmware update operation is triggered in the console, the device will receive a firmware update message through the subscribed `$ota/update/${productID}/${deviceName}` topic, start downloading the firmware, and regularly report the download progress.
```
2021-07-19 10:54:44,032.032 [log.py:35] - DEBUG - wait for ota upgrade command
2021-07-19 10:54:45,034.034 [log.py:35] - DEBUG - wait for ota upgrade command
2021-07-19 10:54:45,409.409 [client.py:2165] - DEBUG - Received PUBLISH (d0, q0, r0, m0), '$ota/update/xxx/xxx', ...  (468 bytes)
2021-07-19 10:54:46,036.036 [log.py:35] - DEBUG - wait for ota upgrade command
2021-07-19 10:54:46,036.036 [log.py:47] - ERROR - info file not exists
2021-07-19 10:54:46,036.036 [log.py:47] - ERROR - local_size:0,local_ver:None,re_ver:1.0.0
__ota_http_deinit do nothing
2021-07-19 10:54:47,052.052 [log.py:35] - DEBUG - [ota report] {'type': 'report_progress', 'report': {'progress': {'state': 'downloading', 'percent': '0', 'result_code': '0', 'result_msg': ''}, 'version': '1.0.0'}}
2021-07-19 10:54:47,052.052 [client.py:2165] - DEBUG - Sending PUBLISH (d0, q0, r0, m3), 'b'$ota/report/xxx/xxx'', ... (151 bytes)
2021-07-19 10:54:47,053.053 [log.py:35] - DEBUG - publish success
2021-07-19 10:54:48,032.032 [log.py:35] - DEBUG - [ota report] {'type': 'report_progress', 'report': {'progress': {'state': 'downloading', 'percent': '0', 'result_code': '0', 'result_msg': ''}, 'version': '1.0.0'}}
2021-07-19 10:54:48,032.032 [client.py:2165] - DEBUG - Sending PUBLISH (d0, q0, r0, m4), 'b'$ota/report/xxx/xxx'', ... (151 bytes)
2021-07-19 10:54:48,032.032 [log.py:35] - DEBUG - publish success
2021-07-19 10:54:49,118.118 [log.py:35] - DEBUG - [ota report] {'type': 'report_progress', 'report': {'progress': {'state': 'downloading', 'percent': '1', 'result_code': '0', 'result_msg': ''}, 'version': '1.0.0'}}
2021-07-19 10:54:49,119.119 [client.py:2165] - DEBUG - Sending PUBLISH (d0, q0, r0, m5), 'b'$ota/report/xxx/xxx'', ... (151 bytes)
2021-07-19 10:54:49,119.119 [log.py:35] - DEBUG - publish success
```
The above log represents the process in which the device receives the firmware version 1.0.0 update message successfully, and the SDK calls back the firmware download progress and reports it. At this point, you can see that the new firmware OTA update package is already at the download path passed in.

After the update is completed, the device will report the update result and wait for a reply from the cloud.
```
2021-07-19 10:57:25,537.537 [log.py:35] - DEBUG - [ota report] {'type': 'report_progress', 'report': {'progress': {'state': 'downloading', 'percent': '100', 'result_code': '0', 'result_msg': ''}, 'version': '1.0.0'}}
2021-07-19 10:57:25,537.537 [client.py:2165] - DEBUG - Sending PUBLISH (d0, q0, r0, m117), 'b'$ota/report/xxx/xxx'', ... (153 bytes)
2021-07-19 10:57:25,537.537 [log.py:35] - DEBUG - publish success
2021-07-19 10:57:25,538.538 [log.py:35] - DEBUG - The firmware download success
2021-07-19 10:57:25,538.538 [log.py:35] - DEBUG - burning firmware...
2021-07-19 10:57:25,538.538 [client.py:2165] - DEBUG - Sending PUBLISH (d0, q1, r0, m118), 'b'$ota/report/xxx/xxx'', ... (128 bytes)
2021-07-19 10:57:25,538.538 [log.py:35] - DEBUG - publish success
2021-07-19 10:57:25,539.539 [log.py:35] - DEBUG - wait for ack...
2021-07-19 10:57:25,641.641 [client.py:2165] - DEBUG - Received PUBACK (Mid: 118)
2021-07-19 10:57:25,642.642 [log.py:35] - DEBUG - publish ack id 118
2021-07-19 10:57:28,042.042 [client.py:2165] - DEBUG - Sending PUBLISH (d0, q1, r0, m119), 'b'$ota/report/xxx/xxx'', ... (58 bytes)
2021-07-19 10:57:28,043.043 [log.py:35] - DEBUG - publish success
2021-07-19 10:57:28,128.128 [client.py:2165] - DEBUG - Received PUBACK (Mid: 119)
```
