* [快速开始](#快速开始)
  *  [控制台创建设备](#控制台创建设备)
  *  [运行示例程序](#运行示例程序)
     *  [填写认证连接设备的参数](#填写认证连接设备的参数)
     *  [运行示例程序进行 MQTT 认证连接](#运行示例程序进行-MQTT-认证连接)
     *  [订阅 Topic 主题](#订阅-Topic-主题)
     *  [发布 Topic 主题](#发布-Topic-主题)
     *  [取消订阅 Topic 主题](#取消订阅-Topic-主题)
     *  [运行示例程序进行断开MQTT连接](#运行示例程序进行断开-MQTT-连接)


# 快速开始
本文将介绍如何在腾讯云物联网通信IoT Hub控制台创建设备, 并结合 SDK Demo 快速体验设备端通过 MQTT 协议连接腾讯云IoT Hub, 发送和接收消息。

## 控制台创建设备

设备接入SDK前需要在控制台中创建产品设备，获取产品ID、设备名称、设备证书（证书认证）、设备私钥（证书认证）、设备密钥（密钥认证），设备与云端认证连接时需要用到以上信息。详情请参考官网 [控制台使用手册-设备接入准备](https://cloud.tencent.com/document/product/634/14442)。

当在控制台中成功创建产品后，该产品默认有三条权限：

```
${productId}/${deviceName}/control  // 订阅
${productId}/${deviceName}/data     // 订阅和发布
${productId}/${deviceName}/event    // 发布
```
详情请参考官网 [控制台使用手册-权限列表](https://cloud.tencent.com/document/product/634/14444) 操作Topic权限。

## 运行示例程序

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

#### 运行示例程序进行MQTT认证连接
运行 [MqttSample.py](../../hub/sample/mqtt/example_mqtt.py) 示例程序,会进行mqtt连接、topic订阅、消息发送、消息接收以及断开连接过程。运行sample日志如下如下：
```
2021-07-16 10:38:45,940.940 [log.py:35] - DEBUG - LoopThread thread enter
2021-07-16 10:38:45,940.940 [log.py:35] - DEBUG - connect_async...8883
2021-07-16 10:38:46,366.366 [client.py:2165] - DEBUG - Sending CONNECT (u1, p1, wr0, wq0, wf0, c1, k60) client_id=b'xxxx'
2021-07-16 10:38:46,451.451 [client.py:2165] - DEBUG - Received CONNACK (0, 0)
2021-07-16 10:38:46,452.452 [log.py:35] - DEBUG - on_connect:flags:0,rc:0,userdata:None
2021-07-16 10:38:46,942.942 [client.py:2165] - DEBUG - Sending SUBSCRIBE (d0, m1) [(b'$sys/operation/result/xxx/xxx', 0)]
2021-07-16 10:38:46,943.943 [log.py:35] - DEBUG - subscribe success topic:$sys/operation/result/xxx/xxx
2021-07-16 10:38:46,944.944 [log.py:35] - DEBUG - pub topic:$sys/operation/xxx/xxx,payload:{'type': 'get', 'resource': ['time']},qos:0
2021-07-16 10:38:46,945.945 [client.py:2165] - DEBUG - Sending PUBLISH (d0, q0, r0, m2), 'b'$sys/operation/xxx/xxx'', ... (37 bytes)
2021-07-16 10:38:46,947.947 [log.py:35] - DEBUG - publish success
2021-07-16 10:38:46,947.947 [log.py:35] - DEBUG - on_publish:mid:2,userdata:None
2021-07-16 10:38:47,026.026 [client.py:2165] - DEBUG - Received SUBACK
2021-07-16 10:38:47,027.027 [log.py:35] - DEBUG - on_subscribe:mid:0,granted_qos:1,userdata:None
2021-07-16 10:38:47,159.159 [client.py:2165] - DEBUG - Received PUBLISH (d0, q0, r0, m0), '$sys/operation/result/xxx/xxx', ...  (82 bytes)
2021-07-16 10:38:47,349.349 [client.py:2165] - DEBUG - Sending UNSUBSCRIBE (d0, m3) [b'$sys/operation/result/xxx/xxx']
2021-07-16 10:38:47,350.350 [log.py:35] - DEBUG - current time:2021-07-16 10:38:47
2021-07-16 10:38:47,433.433 [client.py:2165] - DEBUG - Received UNSUBACK (Mid: 3)
2021-07-16 10:38:47,434.434 [log.py:35] - DEBUG - on_unsubscribe:mid:3,userdata:None
2021-07-16 10:38:48,352.352 [log.py:35] - DEBUG - disconnect
2021-07-16 10:38:48,352.352 [client.py:2165] - DEBUG - Sending DISCONNECT
2021-07-16 10:38:48,354.354 [log.py:35] - DEBUG - LoopThread thread exit
2021-07-16 10:38:48,355.355 [log.py:35] - DEBUG - on_disconnect:rc:0,userdata:None
```
观察日志输出,可以看到程序通过 MQTT 连接成功
```
2021-07-16 10:38:45,940.940 [log.py:35] - DEBUG - connect_async...8883
2021-07-16 10:38:46,366.366 [client.py:2165] - DEBUG - Sending CONNECT (u1, p1, wr0, wq0, wf0, c1, k60) client_id=b'xxxx'
2021-07-16 10:38:46,451.451 [client.py:2165] - DEBUG - Received CONNACK (0, 0)
2021-07-16 10:38:46,452.452 [log.py:35] - DEBUG - on_connect:flags:0,rc:0,userdata:None
```

#### 订阅 Topic 主题
观察日志输出,可以看出程序通过 MQTT 成功订阅了系统 Topic: `$sys/operation/result/${productID}/${deviceName}`
```
2021-07-16 10:38:46,942.942 [client.py:2165] - DEBUG - Sending SUBSCRIBE (d0, m1) [(b'$sys/operation/result/xxx/xxx', 0)]
2021-07-16 10:38:46,943.943 [log.py:35] - DEBUG - subscribe success topic:$sys/operation/result/xxx/xxx
2021-07-16 10:38:47,027.027 [log.py:35] - DEBUG - on_subscribe:mid:0,granted_qos:1,userdata:None
```

#### 发布 Topic 主题
观察日志输出,可以看出程序通过 MQTT 的 Publish 成功发布了消息到 Topic: `$sys/operation/${productID}/${deviceName}`,服务器收到了该消息并在处理后作出了响应
```
2021-07-16 10:38:46,944.944 [log.py:35] - DEBUG - pub topic:$sys/operation/xxx/xxx,payload:{'type': 'get', 'resource': ['time']},qos:0
2021-07-16 10:38:46,945.945 [client.py:2165] - DEBUG - Sending PUBLISH (d0, q0, r0, m2), 'b'$sys/operation/xxx/xxx'', ... (37 bytes)
2021-07-16 10:38:46,947.947 [log.py:35] - DEBUG - publish success
2021-07-16 10:38:46,947.947 [log.py:35] - DEBUG - on_publish:mid:2,userdata:None
2021-07-16 10:38:47,350.350 [log.py:35] - DEBUG - current time:2021-07-16 10:38:47
```

#### 取消订阅 Topic 主题
观察日志输出,可以看出程序在完成消息的发布和接收后取消了对 Topic 的订阅
```
2021-07-16 10:38:47,349.349 [client.py:2165] - DEBUG - Sending UNSUBSCRIBE (d0, m3) [b'$sys/operation/result/xxx/xxx']
2021-07-16 10:38:47,433.433 [client.py:2165] - DEBUG - Received UNSUBACK (Mid: 3)
2021-07-16 10:38:47,434.434 [log.py:35] - DEBUG - on_unsubscribe:mid:3,userdata:None
```

#### 运行示例程序进行断开MQTT连接
观察日志输出,可以看到程序在完成所有任务后断开了 MQTT 的连接
```
2021-07-16 10:38:48,352.352 [log.py:35] - DEBUG - disconnect
2021-07-16 10:38:48,352.352 [client.py:2165] - DEBUG - Sending DISCONNECT
2021-07-16 10:38:48,354.354 [log.py:35] - DEBUG - LoopThread thread exit
2021-07-16 10:38:48,355.355 [log.py:35] - DEBUG - on_disconnect:rc:0,userdata:None
```