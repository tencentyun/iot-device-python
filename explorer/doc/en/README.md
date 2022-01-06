[简体中文](../../../explorer) | English

* [IoT Explorer Device SDK for Python](#IoT-Explorer-Device-SDK-for-Python)
  * [Prerequisites](#Prerequisites)
  * [Project configuration](#Project-configuration)
  * [Downloading the sample code of IoT Explorer SDK for Python demo](#Downloading-the-sample-code-of-IoT-Explorer-SDK-for-Python-demo)
  * [Feature documentation](#Feature-documentation)
  * [SDK API description](#SDK-API-description)

# IoT Explorer Device SDK for Python
Welcome to the IoT Explorer device SDK for Python.

The IoT Explorer device SDK for Python works with the device data template defined by the platform to implement a framework for data interaction between devices and the cloud based on the data template protocol. You can quickly implement data interaction between devices and the platform as well as between devices and applications based on the framework. This document describes how to get and call the IoT Explorer SDK for Python. If you encounter any issues when using it, please [feel free to submit them at GitHub](https://github.com/tencentyun/iot-device-python/issues/new).

## Prerequisites
* Create a Tencent Cloud account and activate IoT Explorer in the Tencent Cloud console.
* Create project products and devices in the console and get the product ID, device name, device certificate (for certificate authentication), device private key (for certificate authentication), and device key (for key authentication), which are required for authentication of the devices when you connect them to the cloud. For detailed directions, please see [Project Management](https://cloud.tencent.com/document/product/1081/40290), [Product Definition](https://cloud.tencent.com/document/product/1081/34739), and [Device Debugging](https://cloud.tencent.com/document/product/1081/34741).

## Project configuration
The SDK can be installed through pip or through source code locally. For more information on how to connect, please see [SDK Connection Description](doc/SDK-Connection-Description.md).

## Downloading the code of IoT Explorer SDK for Python demo
Download the complete code in the [repository](../../../). The sample code of the IoT Explorer SDK for Python demo is in the [iot-device-python/sample](../../../tree/master/sample) directory.

## Feature documentation
For more information on how to call the APIs, please see the demos of the following corresponding features.

* [Controlling Device Connection and Disconnection](doc/Controlling-Device-Connection-and-Disconnection.md)
* [Dynamic Registration](doc/Dynamic-Registration.md)
* [Subscribing to and Unsubscribing from Topic](doc/Subscribing-to-and-Unsubscribing-from-Topic.md)
* [Attribute Reporting](doc/Attribute-Reporting.md)
* [Getting Latest Information Reported by Device](doc/Getting-Latest-Information-Reported-by-Device.md)
* [Device Information Reporting](doc/Device-Information-Reporting.md)
* [Clearing Control](doc/Clearing-Control.md)
* [Event Reporting and Multi-Event Reporting](doc/Event-Reporting-and-Multi-Event-Reporting.md)
* [Checking for Firmware Update](doc/Checking-for-Firmware-Update.md)
* [Gateway Use Cases](doc/Gateway-Use-Cases.md)
