## 接入三方CA证书流程

**1.生成测试CA证书、验证证书、设备证书以及设备私钥**

-  [官网证书管理文档](https://cloud.tencent.com/document/product/634/59363)，参考此链接文档将生成好的CA证书和设备证书上传至控制台，创建基于三房CA的产品和设备，此过程需注意生成证书的 Common Name 需正确填写，请按照文档顺序生成证书。测试CA证书可替换为厂商提供的CA证书。**注意**如需支持证书其他算法，如支持SM2算法，需同产品对接人沟通方案

-  需注意生成过程中，如上传证书不支持格式，可将 openssl 命令中 crt 改为 cer

-  mac 环境 openssl.cnf 文件在目录中可找到 /System/Library/OpenSSL/openssl.cnf



**2.配置Python SDK**

-  在 demo [配置文件](https://github.com/tencentyun/iot-device-python/blob/master/hub/sample/device_info.json) 中配置公有云CA证书+设备证书+设备密钥（设备证书+设备密钥使用的是第三方ca签名过的, 需注意此处使用的CA证书非三方CA，而是官网腾讯云CA证书）

	```
	举例配置文件如下配置证书认证方式：
	{
		"auth_mode":"CERT",
		"productId":"填写产品ID",
		"productSecret":"",
		"deviceName":"填写设备名称",

		"key_deviceinfo":{
			"deviceSecret":""
		},

		"cert_deviceinfo":{
			"devCaFile":"/Users/xxx/Desktop/tencent/iot-device-python/hub/sample/ca.crt",
			"devCertFile":"/Users/xxx/Desktop/tencent/iot-device-python/hub/sample/dev_01.crt",
			"devPrivateKeyFile":"/Users/xxx/Desktop/tencent/iot-device-python/hub/sample/dev_01.key"
	    },
	    "region":"china"
}
	```


-  运行 sample 事例 ``python3 hub/sample/test.py``

	```
	(test_env) eagleychen@EAGLEYCHEN-MB0 iot-device-python % python3 hub/sample/test.py         

	init sdk
	2022-05-20 15:22:51,821.821 [log.py:46] - DEBUG -  mqtt test start...
	2022-05-20 15:22:51,822.822 [log.py:46] - DEBUG - LoopThread thread enter
	2022-05-20 15:22:51,822.822 [log.py:54] - INFO - connect with certificate...
	2022-05-20 15:22:51,824.824 [log.py:46] - DEBUG - connect_async (productid.iotcloud.tencentdevices.com:8883)
	2022-05-20 15:22:52,085.085 [client.py:2404] - DEBUG - Sending CONNECT (u1, p1, wr0, wq0, wf0, c1, k60) client_id=b'productiddev_01'
	2022-05-20 15:22:52,154.154 [client.py:2404] - DEBUG - Received CONNACK (0, 0)
	2022-05-20 15:22:52,154.154 [log.py:46] - DEBUG - on_connect:flags:0,rc:0,userdata:None
	2022-05-20 15:22:52,825.825 [client.py:2404] - DEBUG - Sending SUBSCRIBE (d0, m1) [(b'$sys/operation/result/productid/dev_01', 0)]
	2022-05-20 15:22:52,826.826 [log.py:46] - DEBUG - subscribe success topic:$sys/operation/result/productid/dev_01
	2022-05-20 15:22:52,826.826 [client.py:2404] - DEBUG - Sending PUBLISH (d0, q0, r0, m2), 'b'$sys/operation/productid/dev_01'', ... (37 bytes)
	2022-05-20 15:22:52,827.827 [log.py:46] - DEBUG - publish success
	2022-05-20 15:22:52,827.827 [log.py:46] - DEBUG - on_publish:mid:2,userdata:None
	2022-05-20 15:22:52,885.885 [client.py:2404] - DEBUG - Received SUBACK
	2022-05-20 15:22:52,885.885 [log.py:46] - DEBUG - on_subscribe:mid:0,granted_qos:1,userdata:None
	2022-05-20 15:22:52,922.922 [client.py:2404] - DEBUG - Received PUBLISH (d0, q0, r0, m0), '$sys/operation/result/productid/dev_01', ...  (82 bytes)
	2022-05-20 15:22:53,028.028 [client.py:2404] - DEBUG - Sending UNSUBSCRIBE (d0, m3) [b'$sys/operation/result/productid/dev_01']
	2022-05-20 15:22:53,029.029 [log.py:46] - DEBUG - current time:2022-05-20 15:22:53
	2022-05-20 15:22:53,029.029 [log.py:46] - DEBUG -  mqtt test success...
	deinit sdk
	```


