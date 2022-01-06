[简体中文](../../../hub) | English   

* [IoT Hub Device SDK for Python](#IoT-Hub-Device-SDK-for-Python)
  * [Prerequisites](#Prerequisites)
  * [Project configuration](#Project-configuration)
  * [Downloading the sample code of IoT Hub SDK for Python demo](#Downloading-the-sample-code-of-IoT-Hub-SDK-for-Python-demo)
  * [Feature documentation](#Feature-documentation)
  * [SDK API and parameter descriptions](#SDK-API-and-parameter-descriptions)
  * [FAQs](#FAQs)

# IoT Hub Device SDK for Python
Welcome to the IoT Hub device SDK for Python.

The IoT Hub device SDK for Python relies on a secure and powerful data channel to enable IoT developers to connect devices (such as sensors, actuators, embedded devices, and smart home appliances) to the cloud for two-way communication. This document describes how to get and call the IoT Hub SDK for Python. If you encounter any issues when using it, please [feel free to submit them at GitHub](https://github.com/tencentyun/iot-device-python/issues/new).

## Prerequisites
* Create a Tencent Cloud account and activate IoT Hub in the Tencent Cloud console.
* Create IoT products and devices in the console and get the product ID, device name, device certificate (for certificate authentication), device private key (for certificate authentication), and device key (for key authentication), which are required for authentication of the devices when you connect them to the cloud. For more information, please see [Device Connection Preparations](https://cloud.tencent.com/document/product/634/14442).
* Understand the topic permissions. After a product is created successfully in the console, it has three permissions by default: subscribing to `${productId}/${deviceName}/control`, subscribing and publishing to `${productId}/${deviceName}/data`, and publishing to `${productId}/${deviceName}/event`. For more information on how to manipulate the topic permissions, please see [Permission List](https://cloud.tencent.com/document/product/634/14444).

## Project configuration

The SDK supports remote pip dependencies and local source code dependencies. For more information on how to connect, please see [SDK Connection Description](doc/SDK-Connection-Description.md).

## Downloading the sample code of IoT Hub SDK for Python demo
Download the complete code in the [repository](../../../). The sample code of the IoT Hub SDK for Python demo is in the [iot-device-python/sample](../../../tree/master/sample) module.


## Feature documentation
For more information on how to call the APIs, please see the demos of the following corresponding features.

* [Device Connection Through MQTT over TCP](doc/Device-Connection-Through-MQTT-over-TCP.md)
* [Device Connection Through MQTT over WebSocket](doc/Device-Connection-Through-MQTT-over-WebSocket.md)
* [Dynamic Registration](doc/Dynamic-Registration.md)
* ~~[Broadcast Communication](doc/Broadcast-Communication.md) (to be updated)~~
* [Gateway Feature](doc/Gateway-Feature.md)
* [Firmware Update](doc/Firmware-Update.md)
* ~~[Gateway Subdevice Firmware Update](doc/Gateway-Subdevice-Firmware-Update.md) (to be updated)~~
* ~~[Device Log Reporting](doc/Device-Log-Reporting.md) (to be updated)~~
* ~~[Gateway Device Topological Relationship](doc/Gateway-Device-Topological-Relationship.md) (to be updated)~~
* ~~[Device Interconnection](doc/Device-Interconnection.md) (to be updated)~~
* [Device Shadow](doc/Device-Shadow.md)
* ~~[Device Status Reporting and Setting](doc/Device-Status-Reporting-and-Setting.md) (to be updated)~~