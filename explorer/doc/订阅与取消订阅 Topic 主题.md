* [订阅与取消订阅](#订阅与取消订阅)
  * [订阅 数据模板相关联 Topic 主题](#订阅-数据模板相关联-Topic-主题)
  * [取消订阅 Topic 主题](#取消订阅-Topic-主题)

# 订阅与取消订阅

在腾讯云物联网开发平台控制台（以下简称控制台）创建产品时，会默认生成一套产品的数据模板和一些标准功能，用户也可以自定义功能。数据模板对应的功能包含三大类：属性，事件和行为。控制台数据模板的使用，可参考官网 [数据模板](https://cloud.tencent.com/document/product/1081/44921) 章节。

产品定义数据模板后，设备可以按照数据模板中的定义上报属性、事件，并可对设备下发远程控制指令，即对可写的设备属性进行修改。数据模板的管理详见 产品定义。数据模板协议包括设备属性上报、设备远程控制、获取设备最新上报信息、设备事件上报、设备行为。对应的定义和云端下发控制指令使用的 Topic 请参考官网 [数据模板协议](https://cloud.tencent.com/document/product/1081/34916) 章节。

本文主要描述 如何对数据模板相关联 Topic 的订阅与取消订阅。

## 订阅 数据模板相关联 Topic 主题

运行 [MqttSample.py](../sample/MqttSample.py) 的main函数，设备成功上线后，调用subscribeTopic()，订阅数据模板相关联的属性、事件和行为类型的 Topic:

```
$thing/down/property/{ProductID}/{DeviceName}
$thing/down/event/{ProductID}/{DeviceName}
$thing/down/action/{ProductID}/{DeviceName}
```
示例代码如下：

```
def on_message(topic, payload, qos, userdata):
    print("%s:topic:%s,payload:%s,qos:%s,userdata:%s" % (sys._getframe().f_code.co_name, topic, payload, qos, userdata))
    pass


def on_publish(mid, userdata):
    print("%s:mid:%d,userdata:%s" % (sys._getframe().f_code.co_name, mid, userdata))
    pass


def on_subscribe(mid, granted_qos, userdata):
    print("%s:mid:%d,granted_qos:%s,userdata:%s" % (sys._getframe().f_code.co_name, mid, granted_qos, userdata))
    pass


def on_unsubscribe(mid, userdata):
    print("%s:mid:%d,userdata:%s" % (sys._getframe().f_code.co_name, mid, userdata))
    pass

te = explorer.QcloudExplorer(device_file="./device_info.json")
te.user_on_connect = on_connect
te.user_on_disconnect = on_disconnect
te.user_on_message = on_message
te.user_on_publish = on_publish
te.user_on_subscribe = on_subscribe
te.user_on_unsubscribe = on_unsubscribe

te.template_setup("./example_config.json")
te.mqtt_init(mqtt_domain="")
te.connect_async()

te.template_init(None)
```

观察日志。

```
on_subscribe to ssl://LWVUL5SZ2L.iotcloud.tencentdevices.com:8883]
23/02/2021 19:39:52,686 [MQTT Call: LWVUL5SZ2Llight1] DEBUG MqttSample onSubscribeCompleted 330  - onSubscribeCompleted, status[OK], topics[[$thing/down/property/LWVUL5SZ2L/light1]], 
```
以上日志为 订阅 Topic 主题 成功。

## 取消订阅 Topic 主题

运行 [MqttSample.py](../sample/MqttSample.py) ，设备成功上线后，订阅过Topic后，调用unSubscribeTopic()，取消订阅属性、事件和行为类型的 Topic:

```
$thing/down/property/{ProductID}/{DeviceName}
$thing/down/event/{ProductID}/{DeviceName}
$thing/down/action/{ProductID}/{DeviceName}
```
示例代码如下：

```
te.topic_subscribe()
```

观察输出日志。

```
[unsubscribe success]
```
以上日志为 取消订阅 Topic 主题 成功。
