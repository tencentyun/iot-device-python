* [RRPC同步通信](#RRPC同步通信)
  * [RRPC功能简介](#RRPC功能简介)
  * [运行示例](#运行示例)
    * [填写认证连接设备的参数](#填写认证连接设备的参数)
    * [初始化RRPC](#初始化RRPC)
    * [接收RRPC请求](#接收RRPC请求)
    * [响应请求](#响应请求)

# RRPC同步通信
## RRPC功能简介
MQTT协议是基于发布/订阅的异步通信模式，服务器无法控制设备同步返回结果。为解决此问题，物联网通信平台实现了一套同步通信机制，称为RRPC(Revert RPC)。
即由服务器向客户端发起请求，客户端即时响应并同步给出答复。
* 订阅消息Topic: `$rrpc/rxd/{productID}/{deviceName}/+`
* 请求消息Topic: `$rrpc/rxd/{productID}/{deviceName}/{processID}`
* 应答消息Topic: `$rrpc/txd/{productID}/{deviceName}/{processID}`
* processID   : 服务器生成的唯一的消息ID，用来标识不同RRPC消息。可以通过RRPC应答消息中携带的`processID`找到对应的RRPC请求消息。

原理如下图:
![image.png](https://main.qcloudimg.com/raw/1e83a60cb7b6438ebb5927b7237b77ba.png)
* **RRPC请求4s超时**，即4s内设备端没有应答就认为请求超时。

## 运行示例
运行 [RrpcSample.py](../../hub/sample/rrpc/example_rrpc.py) 示例程序，可以体验同步通信过程。

#### 填写认证连接设备的参数
将在控制台创建设备时生成的设备信息填写到 [device_info.json](../../hub/sample/device_info.json)中,以密钥认证方式为例,主要关注`auth_mode`,`productId`,`deviceName`,`deviceSecret`字段,示例如下:
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

#### 初始化RRPC
示例程序运行后调用RRPC初始化接口进行相关Topic订阅，之后等待RRPC消息．
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

#### 接收RRPC请求
调用云API `PublishRRPCMessage` 发送RRPC请求消息．
打开腾讯云[API控制台](https://console.cloud.tencent.com/api/explorer?Product=iotcloud&Version=2018-06-14&Action=PublishRRPCMessage&SignVersion=)，填写个人密钥和设备参数信息，选择在线调用并发送请求．

设备端成功接收到RRPC请求消息，`process id`为41440。
```
2021-07-20 19:07:31,220.220 [log.py:35] - DEBUG - rrpc while...
2021-07-20 19:07:31,330.330 [client.py:2165] - DEBUG - Received PUBLISH (d0, q0, r0, m0), '$rrpc/rxd/xxx/test01/41440', ...  (23 bytes)
2021-07-20 19:07:31,330.330 [log.py:35] - DEBUG - on_rrpc_cb:payload:{'payload': 'rrpc test'},userdata:None
```

#### 响应请求
设备收到RRPC请求后需要及时作出响应．
```
2021-07-20 19:07:31,330.330 [log.py:43] - INFO - [rrpc reply] ok
2021-07-20 19:07:31,331.331 [client.py:2165] - DEBUG - Sending PUBLISH (d0, q0, r0, m2), 'b'$rrpc/txd/xxx/test01/41440'', ... (4 bytes)
2021-07-20 19:07:31,331.331 [log.py:35] - DEBUG - publish success
2021-07-20 19:07:31,331.331 [log.py:35] - DEBUG - on_publish:mid:2,userdata:None
```
示例响应云端`ok`字符串，此时观察云API可以看到云端已经成功收到设备端的响应消息．