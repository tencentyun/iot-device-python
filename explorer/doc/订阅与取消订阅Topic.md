* [订阅与取消订阅](#订阅与取消订阅)
  * [订阅数据模板相关联 Topic 主题](#订阅数据模板相关联-Topic-主题)
  * [接收设备绑定解绑通知消息](#接收设备绑定解绑通知消息)
  * [取消订阅 Topic 主题](#取消订阅-Topic-主题)

# 订阅与取消订阅

在腾讯云物联网开发平台控制台（以下简称控制台）创建产品时，会默认生成一套产品的数据模板和一些标准功能，用户也可以自定义功能。数据模板对应的功能包含三大类：属性，事件和行为。控制台数据模板的使用，可参考官网 [数据模板](https://cloud.tencent.com/document/product/1081/44921) 章节。

产品定义数据模板后，设备可以按照数据模板中的定义上报属性、事件，并可对设备下发远程控制指令，即对可写的设备属性进行修改。数据模板的管理详见 产品定义。数据模板协议包括设备属性上报、设备远程控制、获取设备最新上报信息、设备事件上报、设备行为。对应的定义和云端下发控制指令使用的 Topic 请参考官网 [数据模板协议](https://cloud.tencent.com/document/product/1081/34916) 章节。

本文主要描述 如何对数据模板相关联 Topic 的订阅与取消订阅。

## 订阅数据模板相关联 Topic 主题

运行 [TemplateSample.py](../../explorer/sample/template/example_template.py)，初始化数据模板会自动订阅数据模板相关联的属性、事件和行为类型的 Topic:
```
$thing/down/property/{ProductID}/{DeviceName}
$thing/down/event/{ProductID}/{DeviceName}
$thing/down/action/{ProductID}/{DeviceName}
$thing/down/service/{ProductID}/{DeviceName}
```
订阅Topic后对应的下行消息由初始化数据模板时注册的回调函数给出，回调函数定义如下:
```python
def on_template_property(topic, qos, payload, userdata):
  """属性回调
  接受$thing/down/property/{ProductID}/{DeviceName}的下行消息
  Args:
    topic: 下行主题
    qos: qos
    payload: 下行消息内容
    userdata: 用户注册的任意结构
  """
  pass

def on_template_service(topic, qos, payload, userdata):
  """服务回调
  接受$thing/down/service/{ProductID}/{DeviceName}的下行消息
  Args:
    topic: 下行主题
    qos: qos
    payload: 下行消息内容
    userdata: 用户注册的任意结构
  """
  pass

def on_template_event(topic, qos, payload, userdata):
  """事件回调
  接受$thing/down/event/{ProductID}/{DeviceName}的下行消息
  Args:
    topic: 下行主题
    qos: qos
    payload: 下行消息内容
    userdata: 用户注册的任意结构
  """
  pass

def on_template_action(topic, qos, payload, userdata):
  """行为回调
  接受$thing/down/action/{ProductID}/{DeviceName}的下行消息
  Args:
    topic: 下行主题
    qos: qos
    payload: 下行消息内容
    userdata: 用户注册的任意结构
  """
  pass
```

示例代码如下：
```python
# 构造QcloudExplorer
qcloud = QcloudExplorer(device_file="explorer/sample/device_info.json", tls=True)
# 初始化日志
logger = qcloud.logInit(qcloud.LoggerLevel.DEBUG, enable=True)

# 注册mqtt回调
qcloud.registerMqttCallback(on_connect, on_disconnect,
                            on_message, on_publish,
                            on_subscribe, on_unsubscribe)
# 获取设备product id和device name
product_id = qcloud.getProductID()
device_name = qcloud.getDeviceName()

# mqtt连接
qcloud.connect()

# 数据模板初始化,自动订阅相关Topic
qcloud.templateInit(product_id, device_name, on_template_property,
                        on_template_action, on_template_event, on_template_service)
qcloud.templateSetup(product_id, device_name, "sample/template/template_config.json")
```

观察日志。
```
2021-07-21 16:59:34,956.956 [log.py:35] - DEBUG - LoopThread thread enter
2021-07-21 16:59:34,956.956 [log.py:35] - DEBUG - connect_async (xxx.iotcloud.tencentdevices.com:8883)
2021-07-21 16:59:35,432.432 [client.py:2165] - DEBUG - Sending CONNECT (u1, p1, wr0, wq0, wf0, c1, k60) client_id=b'xxxx'
2021-07-21 16:59:35,491.491 [client.py:2165] - DEBUG - Received CONNACK (0, 0)
2021-07-21 16:59:35,491.491 [log.py:35] - DEBUG - on_connect:flags:0,rc:0,userdata:None
2021-07-21 16:59:35,958.958 [client.py:2165] - DEBUG - Sending SUBSCRIBE (d0, m1) [(b'$thing/down/property/xxx/dev1', 0)]
2021-07-21 16:59:35,958.958 [log.py:35] - DEBUG - subscribe success topic:$thing/down/property/xxx/dev1
2021-07-21 16:59:35,959.959 [client.py:2165] - DEBUG - Sending SUBSCRIBE (d0, m2) [(b'$thing/down/action/xxx/dev1', 0)]
2021-07-21 16:59:35,959.959 [log.py:35] - DEBUG - subscribe success topic:$thing/down/action/xxx/dev1
2021-07-21 16:59:35,960.960 [client.py:2165] - DEBUG - Sending SUBSCRIBE (d0, m3) [(b'$thing/down/event/xxx/dev1', 0)]
2021-07-21 16:59:35,960.960 [log.py:35] - DEBUG - subscribe success topic:$thing/down/event/xxx/dev1
2021-07-21 16:59:35,960.960 [client.py:2165] - DEBUG - Sending SUBSCRIBE (d0, m4) [(b'$thing/down/service/xxx/dev1', 0)]
2021-07-21 16:59:35,960.960 [log.py:35] - DEBUG - subscribe success topic:$thing/down/service/xxx/dev1
2021-07-21 16:59:36,006.006 [client.py:2165] - DEBUG - Received SUBACK
2021-07-21 16:59:36,006.006 [log.py:35] - DEBUG - on_subscribe:mid:0,granted_qos:1,userdata:None
2021-07-21 16:59:36,009.009 [client.py:2165] - DEBUG - Received SUBACK
2021-07-21 16:59:36,010.010 [client.py:2165] - DEBUG - Received SUBACK
2021-07-21 16:59:36,010.010 [log.py:35] - DEBUG - on_subscribe:mid:0,granted_qos:2,userdata:None
2021-07-21 16:59:36,010.010 [log.py:35] - DEBUG - on_subscribe:mid:0,granted_qos:4,userdata:None
2021-07-21 16:59:36,016.016 [client.py:2165] - DEBUG - Received SUBACK
2021-07-21 16:59:36,016.016 [log.py:35] - DEBUG - on_subscribe:mid:0,granted_qos:3,userdata:None
```
观察日志可以看到成功设备订阅了Topic．

## 接收设备绑定解绑通知消息
数据模板初始化后程序配合腾讯连连可以体验接收下行消息功能．
* 接收绑定设备通知
在控制台打开设备二维码，使用腾讯连连小程序扫描绑定设备后设备端会收到`bind_device`消息，日志如下:
```
2021-07-29 15:09:09,407.407 [client.py:2165] - DEBUG - Received PUBLISH (d0, q0, r0, m0), '$thing/down/service/xxx/xxx', ...  (86 bytes)
2021-07-29 15:09:09,407.407 [log.py:35] - DEBUG - on_template_service:payload:{'method': 'bind_device', 'clientToken': 'clientToken-8l1b8SX3cw', 'timestamp': 1627542549},userdata:None
```

* 接收解绑设备通知
在腾讯连连中选择删除设备后设备端会收到`unbind_device`消息，日志如下:
```
2021-07-29 15:09:28,343.343 [client.py:2165] - DEBUG - Received PUBLISH (d0, q0, r0, m0), '$thing/down/service/xxx/xxx', ...  (118 bytes)
2021-07-29 15:09:28,345.345 [log.py:35] - DEBUG - on_template_service:payload:{'method': 'unbind_device', 'DeviceId': 'xxx/xxx', 'clientToken': 'clientToken-Bcjwl8Io0', 'timestamp': 1627542568},userdata:None
```

## 取消订阅 Topic 主题

运行 [TemplateSample.py](../../explorer/sample/template/example_template.py)，退出时调用`templateDeinit()`接口取消订阅 Topic．

示例代码如下：
```python
# 注销数据模板
qcloud.templateDeinit(product_id, device_name)

# 断开mqtt连接
qcloud.disconnect()
```

观察输出日志。
```
2021-07-21 17:21:33,833.833 [client.py:2165] - DEBUG - Sending UNSUBSCRIBE (d0, m5) [b'$thing/down/property/xxx/dev1', b'$thing/down/event/xxx/dev1', b'$thing/down/action/xxx/dev1', b'$thing/down/service/xxx/dev1']
2021-07-21 17:21:33,913.913 [client.py:2165] - DEBUG - Received UNSUBACK (Mid: 5)
2021-07-21 17:21:33,914.914 [log.py:35] - DEBUG - on_unsubscribe:mid:5,userdata:None
2021-07-21 17:21:35,218.218 [log.py:35] - DEBUG - disconnect
2021-07-21 17:21:35,218.218 [client.py:2165] - DEBUG - Sending DISCONNECT
2021-07-21 17:21:35,219.219 [log.py:35] - DEBUG - LoopThread thread exit
2021-07-21 17:21:35,219.219 [log.py:35] - DEBUG - on_disconnect:rc:0,userdata:None
```
观察日志可以看到成功设备取消订阅了Topic．
