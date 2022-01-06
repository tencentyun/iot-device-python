* [OTA Device Firmware Update](#OTA-Device-Firmware-Update)
  * [Overview](#Overview)
  * [Running demo](#Running-demo)
    * [Entering parameters for authenticating device for connection](#Entering-parameters-for-authenticating-device-for-connection)
    * [Uploading firmware](#Uploading-firmware)
    * [Reporting version](#Reporting-version)
    * [Starting download](#Starting-download)
    * [Reporting progress](#Reporting-progress)
    * [Using checkpoint restart](#Using-checkpoint-restart)
    * [Reporting result](#Reporting-result)


# OTA Device Firmware Update
## Overview
Device firmware update (aka OTA) is an important part of the IoT Hub service. When a device has new features available or vulnerabilities that need to be fixed, firmware update can be quickly performed for it through the OTA service. For more information, please see [Firmware Update](https://cloud.tencent.com/document/product/634/14673).

To try out firmware update, you need to add a new firmware file in the console. For more information, please see [Device Firmware Update](https://cloud.tencent.com/document/product/634/14674).


## Running demo
You can run the [OtaSample.py](../../hub/sample/ota/example_ota.py) demo to try out processes such as reporting the current version, downloading the firmware, and reporting the OTA progress.

#### Entering parameters for authenticating device for connection
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

#### Uploading firmware
To update the firmware, you first need to upload it to the IoT Hub backend in the console as shown below:
![](https://main.qcloudimg.com/raw/2ccbc69f812c91884941060b17db86e8.png)

#### Reporting version
As can be seen from the output log, the demo reports the current firmware version (0.1.0) and starts waiting for the update command from the cloud.
```
2021-07-19 10:54:26,800.800 [log.py:35] - DEBUG - LoopThread thread enter
2021-07-19 10:54:26,800.800 [log.py:35] - DEBUG - connect_async (xxx.iotcloud.tencentdevices.com:8883)
2021-07-19 10:54:28,159.159 [client.py:2165] - DEBUG - Sending CONNECT (u1, p1, wr0, wq0, wf0, c1, k60) client_id=b'xxxx'
2021-07-19 10:54:28,384.384 [client.py:2165] - DEBUG - Received CONNACK (0, 0)
2021-07-19 10:54:28,385.385 [log.py:35] - DEBUG - on_connect:flags:0,rc:0,userdata:None
2021-07-19 10:54:28,803.803 [client.py:2165] - DEBUG - Sending SUBSCRIBE (d0, m1) [(b'$ota/update/xxx/xxx', 1)]
2021-07-19 10:54:28,803.803 [log.py:35] - DEBUG - subscribe success topic:$ota/update/xxx/txest1
2021-07-19 10:54:28,932.932 [client.py:2165] - DEBUG - Received SUBACK
2021-07-19 10:54:28,932.932 [log.py:35] - DEBUG - on_subscribe:mid:1,granted_qos:1,userdata:None
2021-07-19 10:54:29,004.004 [client.py:2165] - DEBUG - Sending PUBLISH (d0, q1, r0, m2), 'b'$ota/report/xxx/xxx'', ... (58 bytes)
2021-07-19 10:54:29,005.005 [log.py:35] - DEBUG - publish success
2021-07-19 10:54:29,144.144 [client.py:2165] - DEBUG - Received PUBACK (Mid: 2)
2021-07-19 10:54:29,145.145 [client.py:2165] - DEBUG - Received PUBLISH (d0, q0, r0, m0), '$ota/update/xxx/xxx', ...  (86 bytes)
2021-07-19 10:54:29,147.147 [log.py:35] - DEBUG - on_ota_report:payload:{'result_code': 0, 'result_msg': 'success', 'type': 'report_version_rsp', 'version': '0.1.0'},userdata:None
2021-07-19 10:54:30,006.006 [log.py:35] - DEBUG - wait for ota upgrade command
2021-07-19 10:54:31,008.008 [log.py:35] - DEBUG - wait for ota upgrade command
2021-07-19 10:54:32,010.010 [log.py:35] - DEBUG - wait for ota upgrade command
```

#### Starting download
After receiving the firmware version reported by the device, select the target new firmware and run the update command. You can update the firmware in the console in the following three methods:

1. Update all devices by firmware version number. The selected version number is the version number for update, and you can select multiple version numbers for update.
![](https://main.qcloudimg.com/raw/dcc27c9875ee4f94b9016e6ee094895e.png)
2. Batch update specified devices by firmware version number. You can select multiple version numbers and devices for update.
![](https://main.qcloudimg.com/raw/aea220c450a1d32fadf3f3b693840f4c.png)
3. Batch update the devices in the template file by device name. You can ignore the version number for update and directly update the devices in the template file to the selected firmware.
![](https://main.qcloudimg.com/raw/86c1c899ce0723162cd851b18ffdc973.png)

***For methods 1 and 2, if the currently running firmware of the devices to be updated is not uploaded to the console, you cannot select their version number for update. In this case, you can upload this firmware to the console or select method 3 for update.***

As can be seen from the output log, after the cloud delivers the update command, the demo starts downloading the firmware over HTTPS.
```
2021-07-19 10:54:44,032.032 [log.py:35] - DEBUG - wait for ota upgrade command
2021-07-19 10:54:45,034.034 [log.py:35] - DEBUG - wait for ota upgrade command
2021-07-19 10:54:45,409.409 [client.py:2165] - DEBUG - Received PUBLISH (d0, q0, r0, m0), '$ota/update/xxx/xxx', ...  (468 bytes)
2021-07-19 10:54:46,036.036 [log.py:35] - DEBUG - wait for ota upgrade command
2021-07-19 10:54:46,036.036 [log.py:47] - ERROR - info file not exists
2021-07-19 10:54:46,036.036 [log.py:47] - ERROR - local_size:0,local_ver:None,re_ver:1.0.0
2021-07-19 10:54:47,052.052 [log.py:35] - DEBUG - [ota report] {'type': 'report_progress', 'report': {'progress': {'state': 'downloading', 'percent': '0', 'result_code': '0', 'result_msg': ''}, 'version': '1.0.0'}}
2021-07-19 10:54:47,052.052 [client.py:2165] - DEBUG - Sending PUBLISH (d0, q0, r0, m3), 'b'$ota/report/xxx/xxx'', ... (151 bytes)
2021-07-19 10:54:47,053.053 [log.py:35] - DEBUG - publish success
```

#### Reporting progress
After the firmware download starts, the download progress (in percentages) will be continuously reported until the download is completed as shown in the following log:
```
2021-07-19 10:55:08,066.066 [log.py:35] - DEBUG - [ota report] {'type': 'report_progress', 'report': {'progress': {'state': 'downloading', 'percent': '13', 'result_code': '0', 'result_msg': ''}, 'version': '1.0.0'}}
2021-07-19 10:55:08,066.066 [client.py:2165] - DEBUG - Sending PUBLISH (d0, q0, r0, m24), 'b'$ota/report/xxx/xxx'', ... (152 bytes)
2021-07-19 10:55:08,066.066 [log.py:35] - DEBUG - publish success
2021-07-19 10:55:09,083.083 [log.py:35] - DEBUG - [ota report] {'type': 'report_progress', 'report': {'progress': {'state': 'downloading', 'percent': '14', 'result_code': '0', 'result_msg': ''}, 'version': '1.0.0'}}
2021-07-19 10:55:09,084.084 [client.py:2165] - DEBUG - Sending PUBLISH (d0, q0, r0, m25), 'b'$ota/report/xxx/xxx'', ... (152 bytes)
2021-07-19 10:55:09,084.084 [log.py:35] - DEBUG - publish success
2021-07-19 10:55:10,002.002 [log.py:35] - DEBUG - [ota report] {'type': 'report_progress', 'report': {'progress': {'state': 'downloading', 'percent': '15', 'result_code': '0', 'result_msg': ''}, 'version': '1.0.0'}}
2021-07-19 10:55:10,002.002 [client.py:2165] - DEBUG - Sending PUBLISH (d0, q0, r0, m26), 'b'$ota/report/xxx/xxx'', ... (152 bytes)
2021-07-19 10:55:10,002.002 [log.py:35] - DEBUG - publish success
2021-07-19 10:55:11,216.216 [log.py:35] - DEBUG - [ota report] {'type': 'report_progress', 'report': {'progress': {'state': 'downloading', 'percent': '16', 'result_code': '0', 'result_msg': ''}, 'version': '1.0.0'}}
2021-07-19 10:55:11,216.216 [client.py:2165] - DEBUG - Sending PUBLISH (d0, q0, r0, m27), 'b'$ota/report/xxx/xxx'', ... (152 bytes)
2021-07-19 10:55:11,217.217 [log.py:35] - DEBUG - publish success
```

#### Using checkpoint restart
Firmware update supports checkpoint restart; that is, if the firmware download process is interrupted due to any issues, it will resume from where interrupted. The log is as shown below:
```
2021-07-19 10:55:26,142.142 [log.py:35] - DEBUG - [ota report] {'type': 'report_progress', 'report': {'progress': {'state': 'downloading', 'percent': '28', 'result_code': '0', 'result_msg': ''}, 'version': '1.0.0'}}
2021-07-19 10:55:26,142.142 [client.py:2165] - DEBUG - Sending PUBLISH (d0, q0, r0, m42), 'b'$ota/report/xxx/xxx'', ... (152 bytes)
2021-07-19 10:55:26,143.143 [log.py:35] - DEBUG - publish success
```
The download is interrupted when the firmware download progress reaches 28%, and then the demo is restarted for update.
```
2021-07-19 10:55:27,797.797 [log.py:35] - DEBUG - LoopThread thread enter
2021-07-19 10:55:27,797.797 [log.py:35] - DEBUG - connect_async (xxx.iotcloud.tencentdevices.com:8883)
2021-07-19 10:55:28,581.581 [client.py:2165] - DEBUG - Sending CONNECT (u1, p1, wr0, wq0, wf0, c1, k60) client_id=b'xxxx'
2021-07-19 10:55:28,680.680 [client.py:2165] - DEBUG - Received CONNACK (0, 0)
2021-07-19 10:55:28,681.681 [log.py:35] - DEBUG - on_connect:flags:0,rc:0,userdata:None
2021-07-19 10:55:28,799.799 [client.py:2165] - DEBUG - Sending SUBSCRIBE (d0, m1) [(b'$ota/update/xxx/xxx', 1)]
2021-07-19 10:55:28,800.800 [log.py:35] - DEBUG - subscribe success topic:$ota/update/xxx/xxx
2021-07-19 10:55:28,892.892 [client.py:2165] - DEBUG - Received SUBACK
2021-07-19 10:55:28,892.892 [log.py:35] - DEBUG - on_subscribe:mid:1,granted_qos:1,userdata:None
2021-07-19 10:55:29,002.002 [client.py:2165] - DEBUG - Sending PUBLISH (d0, q1, r0, m2), 'b'$ota/report/xxx/xxx'', ... (58 bytes)
2021-07-19 10:55:29,003.003 [log.py:35] - DEBUG - publish success
2021-07-19 10:55:29,079.079 [client.py:2165] - DEBUG - Received PUBACK (Mid: 2)
2021-07-19 10:55:29,096.096 [client.py:2165] - DEBUG - Received PUBLISH (d0, q0, r0, m0), '$ota/update/xxx/xxx', ...  (86 bytes)
2021-07-19 10:55:29,096.096 [log.py:35] - DEBUG - on_ota_report:payload:{'result_code': 0, 'result_msg': 'success', 'type': 'report_version_rsp', 'version': '0.1.0'},userdata:None
2021-07-19 10:55:29,118.118 [client.py:2165] - DEBUG - Received PUBLISH (d0, q0, r0, m0), '$ota/update/xxx/xxx', ...  (472 bytes)
2021-07-19 10:55:30,005.005 [log.py:35] - DEBUG - wait for ota upgrade command
2021-07-19 10:55:30,006.006 [log.py:47] - ERROR - local_size:5620000,local_ver:1.0.0,re_ver:1.0.0
2021-07-19 10:55:30,029.029 [log.py:47] - ERROR - total read:5620000
__ota_http_deinit do nothing
2021-07-19 10:55:31,221.221 [log.py:35] - DEBUG - [ota report] {'type': 'report_progress', 'report': {'progress': {'state': 'downloading', 'percent': '28', 'result_code': '0', 'result_msg': ''}, 'version': '1.0.0'}}
2021-07-19 10:55:31,222.222 [client.py:2165] - DEBUG - Sending PUBLISH (d0, q0, r0, m3), 'b'$ota/report/xxx/xxx'', ... (152 bytes)
2021-07-19 10:55:31,223.223 [log.py:35] - DEBUG - publish success
2021-07-19 10:55:32,358.358 [log.py:35] - DEBUG - [ota report] {'type': 'report_progress', 'report': {'progress': {'state': 'downloading', 'percent': '29', 'result_code': '0', 'result_msg': ''}, 'version': '1.0.0'}}
2021-07-19 10:55:32,359.359 [client.py:2165] - DEBUG - Sending PUBLISH (d0, q0, r0, m4), 'b'$ota/report/xxx/xxx'', ... (152 bytes)
2021-07-19 10:55:32,359.359 [log.py:35] - DEBUG - publish success
```
As can be seen from the log, after the demo is restarted, the firmware download process resumes from where interrupted until it is completed.

#### Reporting result
After the firmware is downloaded, it is burnt and the result is reported to the cloud.
```
2021-07-19 10:57:25,228.228 [log.py:35] - DEBUG - [ota report] {'type': 'report_progress', 'report': {'progress': {'state': 'downloading', 'percent': '99', 'result_code': '0', 'result_msg': ''}, 'version': '1.0.0'}}
2021-07-19 10:57:25,228.228 [client.py:2165] - DEBUG - Sending PUBLISH (d0, q0, r0, m116), 'b'$ota/report/xxx/xxx'', ... (152 bytes)
2021-07-19 10:57:25,229.229 [log.py:35] - DEBUG - publish success
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
2021-07-19 10:57:28,175.175 [client.py:2165] - DEBUG - Received PUBLISH (d0, q0, r0, m0), '$ota/update/xxx/xxx', ...  (86 bytes)
2021-07-19 10:57:28,175.175 [log.py:35] - DEBUG - on_ota_report:payload:{'result_code': 0, 'result_msg': 'success', 'type': 'report_version_rsp', 'version': '0.1.0'},userdata:None
2021-07-19 10:57:29,045.045 [log.py:35] - DEBUG - wait for ota upgrade command
2021-07-19 10:57:30,048.048 [log.py:35] - DEBUG - wait for ota upgrade command
```
As can be seen from the log, after the firmware is downloaded, the demo verifies the firmware first and then simulates firmware burning. After that, the demo reports the update success to the cloud and waits for it to respond to ensure that it receives the reported result. Then, the demo starts waiting for the next update.