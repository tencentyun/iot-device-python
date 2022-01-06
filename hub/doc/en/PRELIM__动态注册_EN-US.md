* [Dynamic Registration Authentication](#Dynamic-Registration-Authentication)
  * [Overview](#Overview)
  * [Enabling dynamic registration in console](#Enabling-dynamic-registration-in-console)
  * [Running demo for dynamic registration](#Running-demo-for-dynamic-registration)

# Dynamic Registration Authentication
## Overview
This feature assigns a unified key to all devices under the same product, and a device gets a device certificate/key through a registration request for authentication. You can burn the same configuration information for the same batch of devices. For more information on the dynamic registration request, please see [Dynamic Registration API Description](https://cloud.tencent.com/document/product/1081/47612).

If you enable automatic device creation in the console, you don't need to create devices in advance, but you must guarantee that device names are unique under the same product ID, which are generally unique device identifiers (such as MAC address). This method is more flexible. If you disable it in the console, you must create devices in advance and enter the same device names during dynamic registration, which is more secure but less convenient.

## Enabling dynamic registration in console
To use the dynamic registration feature, you need to enable it when creating a product in the console and save the `productSecret` information of the product. The settings in the console are as shown below:
![](https://main.qcloudimg.com/raw/a02f57cbe40f26ead94170396d78253c.jpg)

## Running demo for dynamic registration
Before running the demo, you need to enter the product information obtained in the console in the [device_info.json](../../hub/sample/device_info.json) file, with the device name to be generated in the `deviceName` field, `YOUR_DEVICE_SECRET` in the `deviceSecret` field, and the `productSecret` information generated during product creation in the console in the `productSecret` field.

You can run [DynregSample.py](../../hub/sample/dynreg/example_dynreg.py) to call the `dynregDevice()` API for dynamic registration authentication. After the dynamic registration callback gets the key or certificate information of the corresponding device, it will be returned through the returned value of the API. Below is the sample code:

```
from hub.hub import QcloudHub

qcloud = QcloudHub(device_file="hub/sample/device_info.json", tls=True)
logger = qcloud.logInit(qcloud.LoggerLevel.DEBUG, enable=True)

ret, msg = qcloud.dynregDevice()
if ret == 0:
    logger.debug('dynamic register success, psk: {}'.format(msg))
else:
    logger.error('dynamic register fail, msg: {}'.format(msg))
```

The following is the log of successful authentication for dynamic device registration.
```
dynamic register test success, psk: xxxxxxx
2021-07-15 15:00:17,500.500 [log.py:35] - DEBUG - LoopThread thread enter
2021-07-15 15:00:17,500.500 [log.py:35] - DEBUG - connect_async...8883
2021-07-15 15:00:18,185.185 [client.py:2165] - DEBUG - Sending CONNECT (u1, p1, wr0, wq0, wf0, c1, k60) client_id=b'xxxxxxx'
2021-07-15 15:00:18,284.284 [client.py:2165] - DEBUG - Received CONNACK (0, 0)
2021-07-15 15:00:18,285.285 [log.py:35] - DEBUG - on_connect:flags:0,rc:0,userdata:None
2021-07-15 15:00:18,502.502 [client.py:2165] - DEBUG - Sending SUBSCRIBE (d0, m1) [(b'$sys/operation/result/xxx/xxx', 0)]
2021-07-15 15:00:18,503.503 [log.py:35] - DEBUG - subscribe success topic:$sys/operation/result/xxx/xxx
2021-07-15 15:00:18,503.503 [log.py:35] - DEBUG - pub topic:$sys/operation/xxx/xxx,payload:{'type': 'get', 'resource': ['time']},qos:0
2021-07-15 15:00:18,504.504 [client.py:2165] - DEBUG - Sending PUBLISH (d0, q0, r0, m2), 'b'$sys/operation/xxx/xxx'', ... (37 bytes)
2021-07-15 15:00:18,505.505 [log.py:35] - DEBUG - publish success
2021-07-15 15:00:18,505.505 [log.py:35] - DEBUG - on_publish:mid:2,userdata:None
2021-07-15 15:00:18,584.584 [client.py:2165] - DEBUG - Received SUBACK
2021-07-15 15:00:18,585.585 [log.py:35] - DEBUG - on_subscribe:mid:0,granted_qos:1,userdata:None
2021-07-15 15:00:18,588.588 [client.py:2165] - DEBUG - Received PUBLISH (d0, q0, r0, m0), '$sys/operation/result/xxx/xxx', ...  (82 bytes)
2021-07-15 15:00:18,706.706 [log.py:35] - DEBUG - current time:2021-07-15 15:00:18
2021-07-15 15:00:18,707.707 [log.py:35] - DEBUG - disconnect
2021-07-15 15:00:18,707.707 [client.py:2165] - DEBUG - Sending DISCONNECT
2021-07-15 15:00:18,709.709 [log.py:35] - DEBUG - LoopThread thread exit
2021-07-15 15:00:18,710.710 [log.py:35] - DEBUG - on_disconnect:rc:0,userdata:None
```
As can be seen, the dynamic registration is successful, the device key is obtained, the MQTT is connected successfully, the NTP time is synced, and the `deviceSecret` field is updated in the [device_info.json](../../hub/sample/device_info.json) configuration file.
