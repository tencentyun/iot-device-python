* [Getting Started](#Getting-Started)
  *  [Creating device in console](#Creating-device-in-console)
  *  [Running demo](#Running-demo)
     *  [Key authentication for connection](#Key-authentication-for-connection)
     *  [Certificate authentication for connection](#Certificate-authentication-for-connection)
     *  [Device connection](#Device-connection)
     *  [Device disconnection](#Device-disconnection)

# Getting Started
This document describes how to create a device in the IoT Explorer console and quickly try out how it connects to Tencent Cloud over MQTT and disconnects from MQTT with the aid of the demo.

## Creating device in console

Before connecting devices to the SDK, you need to create project products and devices in the console and get the product ID, device name, device certificate (for certificate authentication), device private key (for certificate authentication), and device key (for key authentication), which are required for authentication of the devices when you connect them to the cloud. For more information, please see [Project Management](https://cloud.tencent.com/document/product/1081/40290), [Product Definition](https://cloud.tencent.com/document/product/1081/34739), and [Device Debugging](https://cloud.tencent.com/document/product/1081/34741).

## Running demo

You can run the [MqttSample.py](../../explorer/sample/mqtt/example_mqtt.py) demo to try out how a device connects and disconnects through key authentication and certificate authentication.

#### Key authentication for connection
Edit the parameter configuration information in the [device_info.json](../../explorer/sample/device_info.json) file in the demo.
```
{
    "auth_mode":"KEY",

    "productId":"xxx",
    "productSecret":"YOUR_PRODUCT_SECRET",
    "deviceName":"xxx",

    "key_deviceinfo":{    
        "deviceSecret":"xxx"
    },

    "cert_deviceinfo":{
        "devCaFile":"YOUR_DEVICE_CA_FILE_NAME",
        "devCertFile":"YOUR_DEVICE_CERT_FILE_NAME",
        "devPrivateKeyFile":"YOUR_DEVICE_PRIVATE_KEY_FILE_NAME"
    },

    "subDev":{
        "subdev_num":4,
        "subdev_list":
        [
                {"sub_productId": "", "sub_devName": ""},
                {"sub_productId": "", "sub_devName": ""},
                {"sub_productId": "", "sub_devName": ""},
                {"sub_productId": "", "sub_devName": ""}
        ]     
    },
	
    "region":"china"
}
```
To use key authentication, you need to enter `productId` (product ID), `deviceName`(device name), and `deviceSecret` (device key) in `device_info.json` and specify the value of the `auth_mode` field as `KEY`. Key authentication is used in the demo.

#### Certificate authentication for connection

To use certificate authentication, you need to download the device certificate from the console, save it on the device, enter the `devCaFile` (`ca` certificate), `devCertFile` (`cert` certificate), and `devPrivateKeyFile` (`private` certificate) fields in the `device_info.json` configuration file to specify the absolute path of the certificate, and specify the value of the `auth_mode` field as `CERT`.
```
{
    "auth_mode":"CERT",

    "productId":"xxx",
    "productSecret":"YOUR_PRODUCT_SECRET",
    "deviceName":"xxx",

    "key_deviceinfo":{    
        "deviceSecret":"YOUR_DEVICE_SECRET"
    },

    "cert_deviceinfo":{
        "devCaFile":"CA_FILE_PATH",
        "devCertFile":"CERT_FILE_PATH",
        "devPrivateKeyFile":"PRIVATEKEY_FILE_PATH"
    },

    "subDev":{
        "subdev_num":4,
        "subdev_list":
        [
                {"sub_productId": "", "sub_devName": ""},
                {"sub_productId": "", "sub_devName": ""},
                {"sub_productId": "", "sub_devName": ""},
                {"sub_productId": "", "sub_devName": ""}
        ]     
    },
	
    "region":"china"
}
```

#### Device connection

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
# Connect to MQTT
qcloud.connect()
```

Observe the log.
```
2021-07-22 10:49:52,302.302 [log.py:35] - DEBUG - LoopThread thread enter
2021-07-22 10:49:52,302.302 [log.py:43] - INFO - connect with key...
2021-07-22 10:49:52,302.302 [log.py:35] - DEBUG - connect_async (xxx.iotcloud.tencentdevices.com:8883)
2021-07-22 10:49:53,068.068 [client.py:2165] - DEBUG - Sending CONNECT (u1, p1, wr0, wq0, wf0, c1, k60) client_id=b'xxxx'
2021-07-22 10:49:53,179.179 [client.py:2165] - DEBUG - Received CONNACK (0, 0)
2021-07-22 10:49:53,179.179 [log.py:35] - DEBUG - on_connect:flags:0,rc:0,userdata:None
2021-07-22 10:49:53,304.304 [client.py:2165] - DEBUG - Sending SUBSCRIBE (d0, m1) [(b'$sys/operation/result/xxx/dev1', 0)]
2021-07-22 10:49:53,306.306 [log.py:35] - DEBUG - subscribe success topic:$sys/operation/result/xxx/dev1
2021-07-22 10:49:53,307.307 [client.py:2165] - DEBUG - Sending PUBLISH (d0, q0, r0, m2), 'b'$sys/operation/xxx/dev1'', ... (37 bytes)
2021-07-22 10:49:53,308.308 [log.py:35] - DEBUG - publish success
2021-07-22 10:49:53,310.310 [log.py:35] - DEBUG - on_publish:mid:2,userdata:None
2021-07-22 10:49:53,416.416 [client.py:2165] - DEBUG - Received SUBACK
2021-07-22 10:49:53,416.416 [log.py:35] - DEBUG - on_subscribe:mid:0,granted_qos:1,userdata:None
2021-07-22 10:49:53,424.424 [client.py:2165] - DEBUG - Received PUBLISH (d0, q0, r0, m0), '$sys/operation/result/xxx/dev1', ...  (82 bytes)
2021-07-22 10:49:53,511.511 [client.py:2165] - DEBUG - Sending UNSUBSCRIBE (d0, m3) [b'$sys/operation/result/xxx/dev1']
2021-07-22 10:49:53,512.512 [log.py:35] - DEBUG - current time:2021-07-22 10:49:53
```
The above log represents the process in which the device connects to the cloud over MQTT through key authentication successfully and requests the NTP time. In the console, you can see that the status of the device has been updated to `online`.

```
2021-07-22 10:47:33,080.080 [log.py:35] - DEBUG - LoopThread thread enter
2021-07-22 10:47:33,080.080 [log.py:43] - INFO - connect with certificate...
2021-07-22 10:47:33,081.081 [log.py:35] - DEBUG - connect_async (xxx.iotcloud.tencentdevices.com:8883)
2021-07-22 10:47:33,609.609 [client.py:2165] - DEBUG - Sending CONNECT (u1, p1, wr0, wq0, wf0, c1, k60) client_id=b'xxxx'
2021-07-22 10:47:33,693.693 [client.py:2165] - DEBUG - Received CONNACK (0, 0)
2021-07-22 10:47:33,694.694 [log.py:35] - DEBUG - on_connect:flags:0,rc:0,userdata:None
2021-07-22 10:47:34,081.081 [client.py:2165] - DEBUG - Sending SUBSCRIBE (d0, m1) [(b'$sys/operation/result/xxx/dev001', 0)]
2021-07-22 10:47:34,082.082 [log.py:35] - DEBUG - subscribe success topic:$sys/operation/result/xxx/dev001
2021-07-22 10:47:34,082.082 [client.py:2165] - DEBUG - Sending PUBLISH (d0, q0, r0, m2), 'b'$sys/operation/xxx/dev001'', ... (37 bytes)
2021-07-22 10:47:34,082.082 [log.py:35] - DEBUG - publish success
2021-07-22 10:47:34,083.083 [log.py:35] - DEBUG - on_publish:mid:2,userdata:None
2021-07-22 10:47:34,170.170 [client.py:2165] - DEBUG - Received SUBACK
2021-07-22 10:47:34,170.170 [log.py:35] - DEBUG - on_subscribe:mid:0,granted_qos:1,userdata:None
2021-07-22 10:47:34,181.181 [client.py:2165] - DEBUG - Received PUBLISH (d0, q0, r0, m0), '$sys/operation/result/xxx/dev001', ...  (82 bytes)
2021-07-22 10:47:34,283.283 [client.py:2165] - DEBUG - Sending UNSUBSCRIBE (d0, m3) [b'$sys/operation/result/xxx/dev001']
2021-07-22 10:47:34,284.284 [log.py:35] - DEBUG - current time:2021-07-22 10:47:34
```
The above log represents the process in which the device connects to the cloud over MQTT through certificate authentication successfully and requests the NTP time. In the console, you can see that the status of the device has been updated to `online`.

#### Device disconnection

Below is the sample code:
```python
# Disconnect from MQTT
qcloud.disconnect()
```

Observe the output log.
```
2021-07-21 17:40:42,080.080 [log.py:35] - DEBUG - disconnect
2021-07-21 17:40:42,081.081 [client.py:2165] - DEBUG - Sending DISCONNECT
2021-07-21 17:40:42,081.081 [log.py:35] - DEBUG - LoopThread thread exit
```
The above log represents the process in which the device disconnects from MQTT through key authentication successfully. In the console, you can see that the status of the device has been updated to `offline`.

```
2021-07-22 10:47:34,285.285 [log.py:35] - DEBUG - disconnect
2021-07-22 10:47:34,285.285 [client.py:2165] - DEBUG - Sending DISCONNECT
2021-07-22 10:47:34,286.286 [log.py:35] - DEBUG - LoopThread thread exit
```
The above log represents the process in which the device disconnects from MQTT through certificate authentication successfully. In the console, you can see that the status of the device has been updated to `offline`.