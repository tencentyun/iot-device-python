* [RRPC Sync Communication](#RRPC-Sync-Communication)
  * [Overview](#Overview)
  * [Running demo](#Running-demo)
    * [Entering parameters for authenticating device for connection](#Entering-parameters-for-authenticating-device-for-connection)
    * [Initializing RRPC](#Initializing-RRPC)
    * [Receiving RRPC request](#Receiving-RRPC-request)
    * [Responding to request](#Responding-to-request)

# RRPC Sync Communication
## Overview
Because of the async communication mode of the MQTT protocol based on the publish/subscribe pattern, the server cannot control the device to synchronously return the result. To solve this problem, IoT Hub implements a sync communication mechanism called Revert RPC (RRPC).
That is, the server initiates a request to the client, and the client responds immediately and replies synchronously.
* Subscription message topic: `$rrpc/rxd/{productID}/{deviceName}/+`
* Request message topic: `$rrpc/rxd/{productID}/{deviceName}/{processID}`
* Response message topic: `$rrpc/txd/{productID}/{deviceName}/{processID}`
* processID: unique message ID generated by the server to identify different RRPC messages. The corresponding RRPC request message can be found through the `processID` carried in the RRPC response message.

The process is as shown below:
![image.png](https://main.qcloudimg.com/raw/1e83a60cb7b6438ebb5927b7237b77ba.png)
* **RRPC requests time out in 4s**, that is, if the device doesn't respond within 4s, the request will be considered to have timed out.

## Running demo
You can run the [RrpcSample.py](../../hub/sample/rrpc/example_rrpc.py) demo to try out the sync communication process.

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

#### Initializing RRPC
After running the demo, call the RRPC initialization API to subscribe to the relevant topic and then wait for the RRPC message.
```
2021-07-20 17:43:30,612.612 [log.py:35] - DEBUG - LoopThread thread enter
2021-07-20 17:43:30,622.622 [log.py:35] - DEBUG - connect_async (xxx.iotcloud.tencentdevices.com:8883)
2021-07-20 17:43:31,111.111 [client.py:2165] - DEBUG - Sending CONNECT (u1, p1, wr0, wq0, wf0, c1, k60) client_id=b'xxxx'
2021-07-20 17:43:31,164.164 [client.py:2165] - DEBUG - Received CONNACK (0, 0)
2021-07-20 17:43:31,164.164 [log.py:35] - DEBUG - on_connect:flags:0,rc:0,userdata:None
2021-07-20 17:43:31,613.613 [client.py:2165] - DEBUG - Sending SUBSCRIBE (d0, m1) [(b'$rrpc/rxd/xxx/test01/+', 0)]
2021-07-20 17:43:31,614.614 [log.py:35] - DEBUG - subscribe success topic:$rrpc/rxd/xxx/test01/+
2021-07-20 17:43:31,614.614 [log.py:35] - DEBUG - rrpc while...
2021-07-20 17:43:31,677.677 [client.py:2165] - DEBUG - Received SUBACK
2021-07-20 17:43:31,678.678 [log.py:35] - DEBUG - on_subscribe:mid:0,granted_qos:1,userdata:None
2021-07-20 17:43:32,616.616 [log.py:35] - DEBUG - rrpc while...
2021-07-20 17:43:33,618.618 [log.py:35] - DEBUG - rrpc while...
2021-07-20 17:43:34,620.620 [log.py:35] - DEBUG - rrpc while...
```

#### Receiving RRPC request
Call TencentCloud API `PublishRRPCMessage` to send an RRPC request message.
Go to [API Explorer](https://console.cloud.tencent.com/api/explorer?Product=iotcloud&Version=2018-06-14&Action=PublishRRPCMessage&SignVersion=), enter the personal key and device parameter information, select **Online Call**, and send the request.

The device successfully receives the RRPC request message with the `process id` of `41440`.
```
2021-07-20 19:07:31,220.220 [log.py:35] - DEBUG - rrpc while...
2021-07-20 19:07:31,330.330 [client.py:2165] - DEBUG - Received PUBLISH (d0, q0, r0, m0), '$rrpc/rxd/xxx/test01/41440', ...  (23 bytes)
2021-07-20 19:07:31,330.330 [log.py:35] - DEBUG - on_rrpc_cb:payload:{'payload': 'rrpc test'},userdata:None
```

#### Responding to request
The device needs to respond promptly after receiving the RRPC request.
```
2021-07-20 19:07:31,330.330 [log.py:43] - INFO - [rrpc reply] ok
2021-07-20 19:07:31,331.331 [client.py:2165] - DEBUG - Sending PUBLISH (d0, q0, r0, m2), 'b'$rrpc/txd/xxx/test01/41440'', ... (4 bytes)
2021-07-20 19:07:31,331.331 [log.py:35] - DEBUG - publish success
2021-07-20 19:07:31,331.331 [log.py:35] - DEBUG - on_publish:mid:2,userdata:None
```
The demo responds with the `ok` string in the cloud. At this point, as can be seen from the TencentCloud API, the cloud successfully receives the response message from the device.