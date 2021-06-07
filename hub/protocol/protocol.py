#
# Tencent is pleased to support the open source community by making IoT Hub available.
# Copyright (C) 2016 THL A29 Limited, a Tencent company. All rights reserved.

# Licensed under the MIT License (the "License"); you may not use this file except in
# compliance with the License. You may obtain a copy of the License at
# http://opensource.org/licenses/MIT

# Unless required by applicable law or agreed to in writing, software distributed under the License is
# distributed on an "AS IS" basis, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
# either express or implied. See the License for the specific language governing permissions and
# limitations under the License.


import sys
import socket
import string
import time
import hmac
import hashlib
import base64
import random
import ssl
# from enum import Enum
# from enum import IntEnum
import paho.mqtt.client as mqtt
# from hub.manager.manager import TaskManager

class IotProtocol(object):
    __IOT_CA_CRT = "\
-----BEGIN CERTIFICATE-----\n\
MIIDxTCCAq2gAwIBAgIJALM1winYO2xzMA0GCSqGSIb3DQEBCwUAMHkxCzAJBgNV\n\
BAYTAkNOMRIwEAYDVQQIDAlHdWFuZ0RvbmcxETAPBgNVBAcMCFNoZW5aaGVuMRAw\n\
DgYDVQQKDAdUZW5jZW50MRcwFQYDVQQLDA5UZW5jZW50IElvdGh1YjEYMBYGA1UE\n\
AwwPd3d3LnRlbmNlbnQuY29tMB4XDTE3MTEyNzA0MjA1OVoXDTMyMTEyMzA0MjA1\n\
OVoweTELMAkGA1UEBhMCQ04xEjAQBgNVBAgMCUd1YW5nRG9uZzERMA8GA1UEBwwI\n\
U2hlblpoZW4xEDAOBgNVBAoMB1RlbmNlbnQxFzAVBgNVBAsMDlRlbmNlbnQgSW90\n\
aHViMRgwFgYDVQQDDA93d3cudGVuY2VudC5jb20wggEiMA0GCSqGSIb3DQEBAQUA\n\
A4IBDwAwggEKAoIBAQDVxwDZRVkU5WexneBEkdaKs4ehgQbzpbufrWo5Lb5gJ3i0\n\
eukbOB81yAaavb23oiNta4gmMTq2F6/hAFsRv4J2bdTs5SxwEYbiYU1teGHuUQHO\n\
iQsZCdNTJgcikga9JYKWcBjFEnAxKycNsmqsq4AJ0CEyZbo//IYX3czEQtYWHjp7\n\
FJOlPPd1idKtFMVNG6LGXEwS/TPElE+grYOxwB7Anx3iC5ZpE5lo5tTioFTHzqbT\n\
qTN7rbFZRytAPk/JXMTLgO55fldm4JZTP3GQsPzwIh4wNNKhi4yWG1o2u3hAnZDv\n\
UVFV7al2zFdOfuu0KMzuLzrWrK16SPadRDd9eT17AgMBAAGjUDBOMB0GA1UdDgQW\n\
BBQrr48jv4FxdKs3r0BkmJO7zH4ALzAfBgNVHSMEGDAWgBQrr48jv4FxdKs3r0Bk\n\
mJO7zH4ALzAMBgNVHRMEBTADAQH/MA0GCSqGSIb3DQEBCwUAA4IBAQDRSjXnBc3T\n\
d9VmtTCuALXrQELY8KtM+cXYYNgtodHsxmrRMpJofsPGiqPfb82klvswpXxPK8Xx\n\
SuUUo74Fo+AEyJxMrRKlbJvlEtnpSilKmG6rO9+bFq3nbeOAfat4lPl0DIscWUx3\n\
ajXtvMCcSwTlF8rPgXbOaSXZidRYNqSyUjC2Q4m93Cv+KlyB+FgOke8x4aKAkf5p\n\
XR8i1BN1OiMTIRYhGSfeZbVRq5kTdvtahiWFZu9DGO+hxDZObYGIxGHWPftrhBKz\n\
RT16Amn780rQLWojr70q7o7QP5tO0wDPfCdFSc6CQFq/ngOzYag0kJ2F+O5U6+kS\n\
QVrcRBDxzx/G\n\
-----END CERTIFICATE-----"

    def __init__(self, tls=True, logger=None):
        self.__logger = logger
        self.__tls = tls
        self.__useWebsocket = False
        self.__key_mode = True
        self.__iot_ca_crt = self.__IOT_CA_CRT
        self.__mqtt_client = None
        self.__product_id = None
        self.__device_name = None
        self.__host = None
        self.__psk = None
        self.__certificate = self.Certificate()
        self.__set_mqtt_param()

    class Certificate:
        def __init__(self):
            self.ca_file = None
            self.cert_file = None
            self.key_file = None

    def __set_mqtt_param(self):
        self.__mqtt_tls_port = 8883
        self.__mqtt_tcp_port = 1883
        self.__mqtt_socket_tls_port = 443
        self.__mqtt_socket_tcp_port = 80
        self.__mqtt_protocol = "MQTTv31"
        self.__mqtt_transport = "TCP"
        self.__mqtt_secure = "TLS"
        self.__mqtt_clean_session = True
        self.__mqtt_keep_alive = 60

        self.__mqtt_auto_reconnect_min_sec = 1
        self.__mqtt_auto_reconnect_max_sec = 60
        self.__mqtt_max_queued_message = 40
        self.__mqtt_max_inflight_message = 20
        self.__mqtt_auto_reconnect_sec = 0
        self.__mqtt_request_timeout = 10

        # default MQTT/CoAP timeout value when connect/pub/sub
        self.__mqtt_command_timeout = 5
        pass
    
    def __set_mqtt_callback(self):
        self.__mqtt_client.on_connect = self.__on_connect
        self.__mqtt_client.on_disconnect = self.__on_disconnect
        self.__mqtt_client.on_message = self.__on_message
        self.__mqtt_client.on_publish = self.__on_publish
        self.__mqtt_client.on_subscribe = self.__on_subscribe
        self.__mqtt_client.on_unsubscribe = self.__on_unsubscribe

    def __on_connect(self, client, user_data, session_flag, rc):
        self.__logger.info("__on_connect,rc:%d" % (rc))
    
    def __on_disconnect(self, client, user_data, rc):
        self.__logger.info("__on_disconnect,rc:%d" % (rc))
    
    def __on_message(self, client, user_data, message):
        self.__logger.info("__on_message")
    
    def __on_publish(self, client, user_data, mid):
        self.__logger.info("__on_publish")
    
    def __on_subscribe(self, client, user_data, mid, granted_qos):
        self.__logger.info("__on_subscribe")
    
    def __on_unsubscribe(self, client, user_data, mid):
        self.__logger.info("__on_unsubscribe")

    def _generate_pwss(self, client_id, device_secret):
        self.__psk = base64.b64decode(device_secret.encode("utf-8"))
        sha1_key = client_id

        timestamp = str(int(round(time.time() * 1000)))
        conn_id = ''.join(random.sample(string.ascii_letters + string.digits, 5))
        username = client_id + ";21010406;" + conn_id + ";" + timestamp
        sign = hmac.new(sha1_key, username.encode("utf-8"), hashlib.sha1).hexdigest()
        password = "%s;hmacsha1" % (sign)

        return username, password

    def _configuration_init(self, username, password):
        # set username,password for connect()
        self.__mqtt_client.username_pw_set(username, password)

        # mqtt callback set
        self.__set_mqtt_callback()

        self.__mqtt_client.reconnect_delay_set(self.__mqtt_auto_reconnect_min_sec, self.__mqtt_auto_reconnect_max_sec)
        self.__mqtt_client.max_queued_messages_set(self.__mqtt_max_queued_message)
        self.__mqtt_client.max_inflight_messages_set(self.__mqtt_max_inflight_message)

    def _ssl_init(self, key_mode):
        # 密钥认证
        if key_mode is True:
            context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH, cadata=self.__iot_ca_crt)
            self.__mqtt_client.tls_set_context(context)
        else:
            ca = self.__certificate.ca_file
            cert = self.__certificate.cert_file
            key = self.__certificate.key_file
            self.__mqtt_client.tls_set(ca_certs=ca, certfile=cert, keyfile=key,
                                        cert_reqs=ssl.CERT_REQUIRED, tls_version=ssl.PROTOCOL_SSLv23)
        pass

    def _init(self, host, product_id, device_name, device_secret, websocket=False):
        self.__useWebsocket = websocket
        self.__host = host
        self.__product_id = product_id
        self.__device_name = device_name
        self.__device_secret = device_secret
        client_id = self.__product_id + self.__device_name

        username, password = self._generate_pwss(client_id, device_secret)

        if self.__mqtt_protocol == "MQTTv311":
            mqtt_protocol_version = mqtt.MQTTv311
        elif self.__mqtt_protocol == "MQTTv31":
            mqtt_protocol_version = mqtt.MQTTv31
        if websocket:
            self.__mqtt_client = mqtt.Client(client_id=client_id,
                                             clean_session=self.__mqtt_clean_session,
                                             protocol=mqtt_protocol_version,
                                             transport="websockets")
        else:
            self.__mqtt_client = mqtt.Client(client_id=client_id,
                                             clean_session=self.__mqtt_clean_session,
                                             protocol=mqtt_protocol_version)

        self._configuration_init(username, password)

    def setConnectState(self, state):
        self.__connect_state = state
    
    def getConnectState(self):
        return self.__connect_state

    def reset_reconnect_wait(self):
        self.__mqtt_auto_reconnect_sec = 0

    def reconnect_wait(self):
        if self.__mqtt_auto_reconnect_sec == 0:
            self.__mqtt_auto_reconnect_sec = self.__mqtt_auto_reconnect_min_sec
        else:
            self.__mqtt_auto_reconnect_sec = min(self.__mqtt_auto_reconnect_sec * 2, self.__mqtt_auto_reconnect_max_sec)
            self.__mqtt_auto_reconnect_sec += random.randint(1, self.__mqtt_auto_reconnect_sec)
        time.sleep(self.__mqtt_auto_reconnect_sec)
        pass

    # 设置证书路径
    def setCertFile(self, ca, cert, key):
        # 认证模式置为证书方式
        self.__key_mode = False
        self.__certificate.ca_file = ca
        self.__certificate.cert_file = cert
        self.__certificate.key_file = key

    def mqttInit(self, host, product_id, device_name, device_secret):
        self._init(host, product_id, device_name, device_secret)

    def websocketInit(self, host, product_id, device_name, device_secret):
        self._init(host, product_id, device_name, device_secret, True)

    def loop(self):
        rc = mqtt.MQTT_ERR_SUCCESS
        while rc == mqtt.MQTT_ERR_SUCCESS and self.__mqtt_client is not None:
            rc = self.__mqtt_client.loop(self.__mqtt_command_timeout, 1)

    def reconnect(self):
        if self.__mqtt_client is not None:
            self.__mqtt_client.reconnect()

    def connect(self):
        mqtt_port = self.__mqtt_tls_port
        if self.__tls:
            try:
                if self.__useWebsocket:
                    mqtt_port = self.__mqtt_socket_tls_port
                    pass

                self._ssl_init(self.__key_mode)
            except ssl.SSLError as e:
                self.__logger.error("ssl init error:" + str(e))
                # self.__connect_state = self.ConnectState.INITIALIZED
                # connect again 待添加

                return False
        else:
            mqtt_port = self.__mqtt_tcp_port
            if self.__useWebsocket:
                mqtt_port = self.__mqtt_socket_tcp_port
                pass

        try:
            self.__logger.debug("connect_async...%s", mqtt_port)
            self.__mqtt_client.connect_async(host=self.__host, port=mqtt_port, keepalive=self.__mqtt_keep_alive)
        except Exception as e:
            self.__logger.error("mqtt connect with async error:" + str(e))
            # self.__connect_state = self.ConnectState.INITIALIZED
            # connect again 待添加

            return False

            rc = mqtt.MQTT_ERR_SUCCESS
            while rc == mqtt.MQTT_ERR_SUCCESS:
                rc = self.__mqtt_client.loop(self.__mqtt_command_timeout, 1)
        

