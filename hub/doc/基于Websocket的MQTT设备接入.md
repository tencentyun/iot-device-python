* [基于Websocket的MQTT设备接入](#基于Websocket的MQTT设备接入)
  * [基于Websocket的MQTT设备接入简介](#基于Websocket的MQTT设备接入简介)
  * [填写认证连接设备的参数](#填写认证连接设备的参数)
  * [运行示例](#运行示例)
    * [基于Websocket连接MQTT功能](#基于Websocket连接MQTT功能)
    * [基于Websocket的MQTT发布订阅功能](#基于Websocket的MQTT发布订阅功能)
    * [基于Websocket断开MQTT连接功能](#基于Websocket断开MQTT连接功能)

# 基于Websocket的MQTT设备接入
### 基于Websocket的MQTT设备接入简介
物联网平台支持基于 WebSocket 的 MQTT 通信，设备可以在 WebSocket 协议的基础之上使用 MQTT 协议进行消息的传输。请参考官网 [设备基于 WebSocket 的 MQTT 接入](https://cloud.tencent.com/document/product/634/46347)

### 填写认证连接设备的参数
将在控制台创建设备时生成的设备信息填写到 [device_info.json](../../hub/sample/device_info.json)中,以密钥认证方式为例,主要关注`auth_mode`,`productId`,`deviceName`和`deviceSecret`字段,示例如下:
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

### 运行示例程序
修改 [MqttSample.py](../../hub/sample/mqtt/example_mqtt.py) 示例代码接入方式为websocket方式
```
qcloud = QcloudHub(device_file="hub/sample/device_info.json", tls=True, useWebsocket=True)
logger = qcloud.logInit(qcloud.LoggerLevel.DEBUG, enable=True)
```

#### 运行示例程序进行MQTT认证连接
运行 [MqttSample.py](../../hub/sample/mqtt/example_mqtt.py) 示例程序,会进行mqtt连接、topic订阅、消息发送、消息接收以及断开连接过程。运行sample日志如下如下：
```
2021-07-16 15:13:41,394.394 [log.py:35] - DEBUG - LoopThread thread enter
2021-07-16 15:13:41,394.394 [log.py:35] - DEBUG - connect_async (UJDZES2SR2.ap-guangzhou.iothub.tencentdevices.com:443)
2021-07-16 15:13:41,875.875 [client.py:2165] - DEBUG - Sending CONNECT (u1, p1, wr0, wq0, wf0, c1, k60) client_id=b'UJDZES2SR2test1'
2021-07-16 15:13:41,952.952 [client.py:2165] - DEBUG - Received CONNACK (0, 0)
2021-07-16 15:13:41,952.952 [log.py:35] - DEBUG - on_connect:flags:0,rc:0,userdata:None
2021-07-16 15:13:42,396.396 [client.py:2165] - DEBUG - Sending SUBSCRIBE (d0, m1) [(b'$sys/operation/result/UJDZES2SR2/test1', 0)]
2021-07-16 15:13:42,396.396 [log.py:35] - DEBUG - subscribe success topic:$sys/operation/result/UJDZES2SR2/test1
2021-07-16 15:13:42,397.397 [log.py:35] - DEBUG - pub topic:$sys/operation/UJDZES2SR2/test1,payload:{'type': 'get', 'resource': ['time']},qos:0
2021-07-16 15:13:42,397.397 [client.py:2165] - DEBUG - Sending PUBLISH (d0, q0, r0, m2), 'b'$sys/operation/UJDZES2SR2/test1'', ... (37 bytes)
2021-07-16 15:13:42,397.397 [log.py:35] - DEBUG - publish success
2021-07-16 15:13:42,398.398 [log.py:35] - DEBUG - on_publish:mid:2,userdata:None
2021-07-16 15:13:42,498.498 [client.py:2165] - DEBUG - Received SUBACK
2021-07-16 15:13:42,499.499 [log.py:35] - DEBUG - on_subscribe:mid:0,granted_qos:1,userdata:None
2021-07-16 15:13:42,627.627 [client.py:2165] - DEBUG - Received PUBLISH (d0, q0, r0, m0), '$sys/operation/result/UJDZES2SR2/test1', ...  (82 bytes)
2021-07-16 15:13:42,799.799 [client.py:2165] - DEBUG - Sending UNSUBSCRIBE (d0, m3) [b'$sys/operation/result/UJDZES2SR2/test1']
2021-07-16 15:13:42,800.800 [log.py:35] - DEBUG - current time:2021-07-16 15:13:42
2021-07-16 15:13:42,872.872 [client.py:2165] - DEBUG - Received UNSUBACK (Mid: 3)
2021-07-16 15:13:42,872.872 [log.py:35] - DEBUG - on_unsubscribe:mid:3,userdata:None
2021-07-16 15:13:43,802.802 [log.py:35] - DEBUG - disconnect
2021-07-16 15:13:43,802.802 [client.py:2165] - DEBUG - Sending DISCONNECT
2021-07-16 15:13:43,803.803 [log.py:35] - DEBUG - LoopThread thread exit
```
观察日志输出,可以看到程序通过 MQTT 连接成功,连接域名和端口都是websocket域名和端口
```
2021-07-16 15:13:41,394.394 [log.py:35] - DEBUG - LoopThread thread enter
2021-07-16 15:13:41,394.394 [log.py:35] - DEBUG - connect_async (UJDZES2SR2.ap-guangzhou.iothub.tencentdevices.com:443)
2021-07-16 15:13:41,875.875 [client.py:2165] - DEBUG - Sending CONNECT (u1, p1, wr0, wq0, wf0, c1, k60) client_id=b'UJDZES2SR2test1'
2021-07-16 15:13:41,952.952 [client.py:2165] - DEBUG - Received CONNACK (0, 0)
2021-07-16 15:13:41,952.952 [log.py:35] - DEBUG - on_connect:flags:0,rc:0,userdata:None
```

#### 基于Websocket的MQTT订阅功能
观察日志输出,可以看出程序通过 MQTT 成功订阅了系统 Topic: `$sys/operation/result/${productID}/${deviceName}`
```
2021-07-16 15:13:42,396.396 [client.py:2165] - DEBUG - Sending SUBSCRIBE (d0, m1) [(b'$sys/operation/result/UJDZES2SR2/test1', 0)]
2021-07-16 15:13:42,396.396 [log.py:35] - DEBUG - subscribe success topic:$sys/operation/result/UJDZES2SR2/test1
2021-07-16 15:13:42,498.498 [client.py:2165] - DEBUG - Received SUBACK
2021-07-16 15:13:42,499.499 [log.py:35] - DEBUG - on_subscribe:mid:0,granted_qos:1,userdata:None
```

#### 基于Websocket的MQTT发布功能
观察日志输出,可以看出程序通过 MQTT 的 Publish 成功发布了消息到 Topic: `$sys/operation/${productID}/${deviceName}`,服务器收到了该消息并在处理后作出了响应
```
2021-07-16 15:13:42,397.397 [log.py:35] - DEBUG - pub topic:$sys/operation/UJDZES2SR2/test1,payload:{'type': 'get', 'resource': ['time']},qos:0
2021-07-16 15:13:42,397.397 [client.py:2165] - DEBUG - Sending PUBLISH (d0, q0, r0, m2), 'b'$sys/operation/UJDZES2SR2/test1'', ... (37 bytes)
2021-07-16 15:13:42,397.397 [log.py:35] - DEBUG - publish success
2021-07-16 15:13:42,398.398 [log.py:35] - DEBUG - on_publish:mid:2,userdata:None
2021-07-16 15:13:42,627.627 [client.py:2165] - DEBUG - Received PUBLISH (d0, q0, r0, m0), '$sys/operation/result/UJDZES2SR2/test1', ...  (82 bytes)
2021-07-16 15:13:42,800.800 [log.py:35] - DEBUG - current time:2021-07-16 15:13:42
```

#### 基于Websocket断开MQTT连接功能
观察日志输出,可以看到程序在完成所有任务后断开了 MQTT 的连接
```
2021-07-16 15:13:43,802.802 [log.py:35] - DEBUG - disconnect
2021-07-16 15:13:43,802.802 [client.py:2165] - DEBUG - Sending DISCONNECT
```