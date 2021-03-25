* [快速开始](#快速开始)
  *  [控制台创建设备](#控制台创建设备)
  *  [编译运行示例程序](#编译运行示例程序)
     *  [填写认证连接设备的参数](#填写认证连接设备的参数)
     *  [运行示例程序进行 MQTT 认证连接](#运行示例程序进行-MQTT-认证连接)
     *  [运行示例程序进行断开 MQTT 连接](#运行示例程序进行断开-MQTT-连接)
     *  [订阅 Topic 主题](#订阅-Topic-主题)
     *  [取消订阅 Topic 主题](#取消订阅-Topic-主题)
     *  [发布 Topic 主题](#发布-Topic-主题)

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

## 编译运行示例程序

[下载IoT Hub Python-SDK Demo示例代码](../README.md#下载IoT-Hub-Python-SDK-Demo示例代码)