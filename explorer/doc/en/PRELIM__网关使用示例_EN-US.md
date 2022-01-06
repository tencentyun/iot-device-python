* [Gateway Use Cases](#Gateway-Use-Cases)
    * [Creating gateway device in console](#Creating-gateway-device-in-console)
        * [Creating gateway product and device](#Creating-gateway-product-and-device)
        * [Defining subdevice data template](#Defining-subdevice-data-template)
    * [Running demo](#Running-demo)
        * [Entering parameters for authenticating device for connection](#Entering-parameters-for-authenticating-device-for-connection)
        * [Proxying subdevice connection and disconnection](#Proxying-subdevice-connection-and-disconnection)
        * [Binding and unbinding subdevice](#Binding-and-unbinding-subdevice)
        * [Proxying subdevice communication based on data template](#Proxying-subdevice-communication-based-on-data-template)

# Gateway Use Cases

This document describes how to apply for a gateway device and bind a subdevice to it in the IoT Explorer console, and quickly try out proxying subdevice connection/disconnection for the subdevice to send/receive messages based on the data template protocol or custom data with the aid of the [GatewaySample.py](../../explorer/sample/gateway/example_gateway.py) demo of the SDK.

## Creating gateway device in console
#### Creating gateway product and device
To use the gateway demo, you need to create a gateway device and a general device in the IoT Explorer console and bind the latter to the former as a subdevice. For more information, please see [Gateway Device Connection](https://cloud.tencent.com/document/product/1081/43417).

#### Defining subdevice data template
After creating a subdevice, you need to define its data template. You can use the default data template when trying out the demo. For more information, please see [Guide to Connecting Smart Light](https://cloud.tencent.com/document/product/1081/41155).


## Running demo
You can run the [GatewaySample.py](../../explorer/sample/gateway/example_gateway.py) demo to try out how a gateway proxies subdevice connection/disconnection, binds/unbinds subdevices, and proxies subdevices' message communication based on their respective data templates.

#### Entering parameters for authenticating device for connection
Enter the information of the device created in the console in [device_info.json](../../explorer/sample/device_info.json), such as the `auth_mode`, `productId`, `deviceName`, and `deviceSecret` fields of a key-authenticated device as well as certain fields of a subdevice (`subDev`), as shown below:
```
{
    "auth_mode":"KEY",
    "productId":"xxx",
    "deviceName":"test02",
    "key_deviceinfo":{
        "deviceSecret":"xxxx"
    }
}
"subDev":{
    "subdev_num":2,
    "subdev_list":
    [
        {"sub_productId": "xxxx", "sub_devName": "dev1"},
        {"sub_productId": "xxxx", "sub_devName": "dev001"}
    ]
}
```

#### Proxying subdevice connection and disconnection
In the configuration file of the demo, two subdevices are bound to the gateway device `test02`, with their `device_name` being `dev1` and `dev001` respectively.
* Proxied subdevice disconnection through a gateway
Offline subdevices can be connected through the gateway:
```
2021-07-20 14:12:29,913.913 [client.py:2165] - DEBUG - Sending PUBLISH (d0, q0, r0, m2), 'b'$gateway/operation/xxx/test02'', ... (97 bytes)
2021-07-20 14:12:29,913.913 [log.py:35] - DEBUG - publish success
2021-07-20 14:12:29,913.913 [log.py:35] - DEBUG - on_publish:mid:2,userdata:None
2021-07-20 14:12:30,029.029 [client.py:2165] - DEBUG - Received PUBLISH (d0, q0, r0, m0), '$gateway/operation/result/NCUL2VSYG6/test02', ...  (101 bytes)
2021-07-20 14:12:30,114.114 [log.py:35] - DEBUG - client:xxx/dev1 online success
2021-07-20 14:12:30,114.114 [log.py:35] - DEBUG - online success
2021-07-20 14:12:30,114.114 [client.py:2165] - DEBUG - Sending PUBLISH (d0, q0, r0, m3), 'b'$gateway/operation/xxx/test02'', ... (99 bytes)
2021-07-20 14:12:30,115.115 [log.py:35] - DEBUG - publish success
2021-07-20 14:12:30,115.115 [log.py:35] - DEBUG - on_publish:mid:3,userdata:None
2021-07-20 14:12:30,249.249 [client.py:2165] - DEBUG - Received PUBLISH (d0, q0, r0, m0), '$gateway/operation/result/xxx/test02', ...  (103 bytes)
2021-07-20 14:12:30,315.315 [log.py:35] - DEBUG - client:xxx/dev001 online success
2021-07-20 14:12:30,315.315 [log.py:35] - DEBUG - online success
```
As can be seen from the log, the two subdevices `dev1` and `dev001` are connected successfully (`online success`). At this point, you can see in the console that the subdevices are online.

* Proxied subdevice disconnection through a gateway
Online subdevices can be disconnected through the gateway:
```
2021-07-20 14:14:50,962.962 [client.py:2165] - DEBUG - Sending PUBLISH (d0, q0, r0, m4), 'b'$gateway/operation/xxx/test02'', ... (98 bytes)
2021-07-20 14:14:50,963.963 [log.py:35] - DEBUG - publish success
2021-07-20 14:14:50,963.963 [log.py:35] - DEBUG - on_publish:mid:4,userdata:None
2021-07-20 14:14:51,037.037 [client.py:2165] - DEBUG - Received PUBLISH (d0, q0, r0, m0), '$gateway/operation/result/xxx/test02', ...  (102 bytes)
2021-07-20 14:14:51,163.163 [log.py:35] - DEBUG - client:xxx/dev1 offline success
2021-07-20 14:14:51,164.164 [log.py:35] - DEBUG - offline success
2021-07-20 14:14:51,165.165 [client.py:2165] - DEBUG - Sending PUBLISH (d0, q0, r0, m5), 'b'$gateway/operation/xxx/test02'', ... (100 bytes)
2021-07-20 14:14:51,166.166 [log.py:35] - DEBUG - publish success
2021-07-20 14:14:51,167.167 [log.py:35] - DEBUG - on_publish:mid:5,userdata:None
2021-07-20 14:14:51,247.247 [client.py:2165] - DEBUG - Received PUBLISH (d0, q0, r0, m0), '$gateway/operation/result/xxx/test02', ...  (104 bytes)
2021-07-20 14:14:51,368.368 [log.py:35] - DEBUG - client:xxx/dev001 offline success
2021-07-20 14:14:51,368.368 [log.py:35] - DEBUG - offline success
```
As can be seen from the log, the two subdevices just connected are disconnected successfully (`offline success`) through the gateway. At this point, you can see that they are offline in the console.


#### Binding and unbinding subdevice
* Bind a subdevice
Subdevices not bound to a gateway can be bound on the device side.
```
2021-07-20 14:18:28,801.801 [log.py:35] - DEBUG - sign base64 ********************
2021-07-20 14:18:28,801.801 [client.py:2165] - DEBUG - Sending PUBLISH (d0, q0, r0, m3), 'b'$gateway/operation/xxx/test02'', ... (233 bytes)
2021-07-20 14:18:28,802.802 [log.py:35] - DEBUG - publish success
2021-07-20 14:18:28,802.802 [log.py:35] - DEBUG - on_publish:mid:3,userdata:None
2021-07-20 14:18:28,873.873 [client.py:2165] - DEBUG - Received PUBLISH (d0, q0, r0, m0), '$gateway/operation/result/xxx/test02', ...  (101 bytes)
2021-07-20 14:18:29,003.003 [log.py:35] - DEBUG - client:xxx/dev001 bind success
2021-07-20 14:18:29,003.003 [log.py:35] - DEBUG - bind success
```
As can be seen from the log, the `dev001` subdevice is bound to the gateway successfully. At this point, you can see in the console that `dev001` is already in the subdevice list.

* Unbind a subdevice
Subdevices bound to a gateway can be unbound on the device side.
```
2021-07-20 14:17:04,807.807 [client.py:2165] - DEBUG - Sending PUBLISH (d0, q0, r0, m2), 'b'$gateway/operation/xxx/test02'', ... (99 bytes)
2021-07-20 14:17:04,807.807 [log.py:35] - DEBUG - publish success
2021-07-20 14:17:04,808.808 [log.py:35] - DEBUG - on_publish:mid:2,userdata:None
2021-07-20 14:17:04,914.914 [client.py:2165] - DEBUG - Received PUBLISH (d0, q0, r0, m0), '$gateway/operation/result/xxx/test02', ...  (103 bytes)
2021-07-20 14:17:05,009.009 [log.py:35] - DEBUG - client:xxx/dev001 unbind success
2021-07-20 14:17:05,009.009 [log.py:35] - DEBUG - unbind success
```
As can be seen from the log, the `dev001` subdevice is unbound from the gateway successfully. At this point, you can see in the console that `dev001` is not in the subdevice list.
。

#### Proxying subdevice communication based on data template
A data template defines a general method for describing and controlling devices in a unified manner and thus provides data flow and computing services to enable data interconnection, flow, and fusion between different devices and help with application implementation. For the specific protocol, please see [Thing Model Protocol](https://cloud.tencent.com/document/product/1081/34916).

A gateway device processes multiple subdevice transactions through multiple threads and initializes the subdevice data template in the subdevice transaction processing threads. This process will subscribe to the data template topics of the subdevices. The message communication between the subdevices and the cloud should be sent to the gateway device to proxy subdevices' message sending/receiving.

* Proxy the subdevice's topic subscription
```
2021-07-20 14:34:16,975.975 [client.py:2165] - DEBUG - Sending SUBSCRIBE (d0, m2) [(b'xxx/dev001/data', 0)]
2021-07-20 14:34:16,976.976 [client.py:2165] - DEBUG - Sending SUBSCRIBE (d0, m3) [(b'xxx/dev1/data', 0)]
2021-07-20 14:34:16,977.977 [log.py:35] - DEBUG - subscribe success topic:xxx/dev001/data
2021-07-20 14:34:16,977.977 [log.py:35] - DEBUG - gateway subdev subscribe success
2021-07-20 14:34:16,977.977 [log.py:35] - DEBUG - subscribe success topic:xxx/dev1/data
2021-07-20 14:34:16,977.977 [log.py:35] - DEBUG - gateway subdev subscribe success
2021-07-20 14:34:16,977.977 [client.py:2165] - DEBUG - Sending SUBSCRIBE (d0, m4) [(b'$thing/down/property/xxx/dev001', 0)]
2021-07-20 14:34:16,978.978 [log.py:35] - DEBUG - subscribe success topic:$thing/down/property/xxx/dev001
2021-07-20 14:34:16,978.978 [client.py:2165] - DEBUG - Sending SUBSCRIBE (d0, m5) [(b'$thing/down/action/xxx/dev001', 0)]
2021-07-20 14:34:16,978.978 [log.py:35] - DEBUG - subscribe success topic:$thing/down/action/xxx/dev001
2021-07-20 14:34:16,978.978 [client.py:2165] - DEBUG - Sending SUBSCRIBE (d0, m6) [(b'$thing/down/event/xxx/dev001', 0)]
2021-07-20 14:34:16,978.978 [log.py:35] - DEBUG - subscribe success topic:$thing/down/event/xxx/dev001
2021-07-20 14:34:16,979.979 [client.py:2165] - DEBUG - Sending SUBSCRIBE (d0, m7) [(b'$thing/down/service/xxx/dev001', 0)]
2021-07-20 14:34:16,979.979 [log.py:35] - DEBUG - subscribe success topic:$thing/down/service/xxx/dev001
2021-07-20 14:34:16,979.979 [client.py:2165] - DEBUG - Sending SUBSCRIBE (d0, m9) [(b'$thing/down/property/xxx/dev1', 0)]
2021-07-20 14:34:16,980.980 [log.py:35] - DEBUG - subscribe success topic:$thing/down/property/xxx/dev1
2021-07-20 14:34:16,981.981 [client.py:2165] - DEBUG - Sending SUBSCRIBE (d0, m11) [(b'$thing/down/action/xxx/dev1', 0)]
2021-07-20 14:34:16,981.981 [log.py:35] - DEBUG - subscribe success topic:$thing/down/action/xxx/dev1
2021-07-20 14:34:16,982.982 [client.py:2165] - DEBUG - Sending SUBSCRIBE (d0, m13) [(b'$thing/down/event/xxx/dev1', 0)]
2021-07-20 14:34:16,983.983 [log.py:35] - DEBUG - subscribe success topic:$thing/down/event/xxx/dev1
2021-07-20 14:34:16,983.983 [client.py:2165] - DEBUG - Sending SUBSCRIBE (d0, m14) [(b'$thing/down/service/xxx/dev1', 0)]
2021-07-20 14:34:16,983.983 [log.py:35] - DEBUG - subscribe success topic:$thing/down/service/xxx/dev1
2021-07-20 14:34:17,063.063 [client.py:2165] - DEBUG - Received SUBACK
2021-07-20 14:34:17,063.063 [log.py:35] - DEBUG - on_subscribe:mid:0,granted_qos:4,userdata:None
2021-07-20 14:34:17,065.065 [client.py:2165] - DEBUG - Received SUBACK
2021-07-20 14:34:17,065.065 [client.py:2165] - DEBUG - Received SUBACK
2021-07-20 14:34:17,065.065 [client.py:2165] - DEBUG - Received SUBACK
2021-07-20 14:34:17,065.065 [log.py:35] - DEBUG - on_subscribe:mid:0,granted_qos:6,userdata:None
2021-07-20 14:34:17,066.066 [log.py:35] - DEBUG - on_subscribe:mid:0,granted_qos:5,userdata:None
2021-07-20 14:34:17,066.066 [log.py:35] - DEBUG - on_subscribe:mid:0,granted_qos:3,userdata:None
2021-07-20 14:34:17,066.066 [client.py:2165] - DEBUG - Received SUBACK
2021-07-20 14:34:17,066.066 [log.py:35] - DEBUG - on_subscribe:mid:0,granted_qos:2,userdata:None
2021-07-20 14:34:17,070.070 [client.py:2165] - DEBUG - Received SUBACK
2021-07-20 14:34:17,070.070 [log.py:35] - DEBUG - on_subscribe:mid:0,granted_qos:13,userdata:None
2021-07-20 14:34:17,070.070 [client.py:2165] - DEBUG - Received SUBACK
2021-07-20 14:34:17,070.070 [log.py:35] - DEBUG - on_subscribe:mid:0,granted_qos:7,userdata:None
2021-07-20 14:34:17,070.070 [client.py:2165] - DEBUG - Received SUBACK
2021-07-20 14:34:17,071.071 [log.py:35] - DEBUG - on_subscribe:mid:0,granted_qos:14,userdata:None
2021-07-20 14:34:17,071.071 [client.py:2165] - DEBUG - Received SUBACK
2021-07-20 14:34:17,071.071 [log.py:35] - DEBUG - on_subscribe:mid:0,granted_qos:11,userdata:None
2021-07-20 14:34:17,071.071 [client.py:2165] - DEBUG - Received SUBACK
2021-07-20 14:34:17,071.071 [log.py:35] - DEBUG - on_subscribe:mid:0,granted_qos:9,userdata:None
```
As can be seen from the above log, the gateway device subscribes to the `${product_id}/${device_name}/data` topic of the two subdevices to receive the messages delivered by the cloud and then subscribes to the topics related to their data templates after initializing the data templates to receive event notifications and report attributes.

* Receive the control message from the subdevice
Debug the subdevice by modifying its attributes in **Device Debugging** > **Online Debugging** > **Attribute Debugging** in the console and deliver them to the device.
```
2021-07-20 14:34:22,861.861 [client.py:2165] - DEBUG - Received PUBLISH (d0, q0, r0, m0), '$thing/down/property/xxx/dev1', ...  (152 bytes)
2021-07-20 14:34:22,862.862 [log.py:35] - DEBUG - on_template_property:params:{'method': 'control', 'clientToken': 'clientToken-2842aa2d-a9c8-48e3-9160-e13aafa338b3', 'params': {'power_switch': 1, 'color': 2, 'brightness': 5, 'name': 'dev1'}},userdata:None
2021-07-20 14:34:20,194.194 [client.py:2165] - DEBUG - Received PUBLISH (d0, q0, r0, m0), '$thing/down/property/xxx/dev001', ...  (155 bytes)
2021-07-20 14:34:20,194.194 [log.py:35] - DEBUG - product_1:on_template_property:params:{'method': 'control', 'clientToken': 'clientToken-502eae4d-642f-47c0-b6a9-47b6e15c8f4f', 'params': {'power_switch': 1, 'color': 1, 'brightness': 10, 'name': 'dev001'}},userdata:None
```
As can be seen from the log, the gateway device receives the delivered control message successfully. At this point, it should deliver the message to the corresponding subdevice.

* Receive the action message from the subdevice
Debug the subdevice by selecting the action of turning light on in **Device Debugging** > **Online Debugging** > **Action Invocation** in the console and deliver the information to the subdevice.
```
2021-07-20 14:34:29,164.164 [client.py:2165] - DEBUG - Received PUBLISH (d0, q0, r0, m0), '$thing/down/action/xxx/dev1', ...  (143 bytes)
2021-07-20 14:34:29,164.164 [log.py:35] - DEBUG - on_template_action:payload:{'method': 'action', 'clientToken': '146761673::81d315f7-17d9-4d00-9ce0-1ff782c25666', 'actionId': 'c_sw', 'timestamp': 1626762869, 'params': {'sw': 1}},userdata:None
2021-07-20 14:34:35,394.394 [client.py:2165] - DEBUG - Received PUBLISH (d0, q0, r0, m0), '$thing/down/action/xxx/dev001', ...  (150 bytes)
2021-07-20 14:34:35,394.394 [log.py:35] - DEBUG - on_template_action:payload:{'method': 'action', 'clientToken': '146761676::a27e4649-d94e-4acb-b636-5bfe7f4a592d', 'actionId': 'light_on', 'timestamp': 1626762875, 'params': {'is_on': 1}},userdata:None
```
As can be seen from the log, the gateway receives the turn-light-on message successfully. At this point, it should deliver the message to the corresponding subdevice.