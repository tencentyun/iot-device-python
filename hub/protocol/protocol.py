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
import paho.mqtt.client as mqtt
from hub.utils.codec import Codec

class AsyncConnClient(object):

    def __init__(self, host, product_id, device_name, device_secret,
                    websocket=False, tls=True, logger=None):
        self.__logger = logger
        self.__tls = tls
        self.__useWebsocket = websocket
        self.__key_mode = True
        # self.__iot_ca_crt = self.__IOT_CA_CRT
        self.__mqtt_client = None
        self.__product_id = product_id
        self.__device_name = device_name
        self.__device_secret = device_secret
        self.__host = host
        self.__psk = None
        self.__certificate = self.Certificate()
        self.__codec = Codec()
        self.__set_mqtt_default_param()

        self.__init(host, product_id, device_name, device_secret)

    class Certificate:
        def __init__(self):
            self.ca_file = None
            self.cert_file = None
            self.key_file = None

    def __set_mqtt_default_param(self):
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

    def _generate_pwss(self, client_id, device_secret):
        self.__psk = base64.b64decode(device_secret.encode("utf-8"))

        timestamp = str(int(round(time.time() * 1000)))
        conn_id = ''.join(random.sample(string.ascii_letters + string.digits, 5))
        username = client_id + ";21010406;" + conn_id + ";" + timestamp
        sign = hmac.new(self.__psk, username.encode("utf-8"), hashlib.sha1).hexdigest()
        password = "%s;hmacsha1" % (sign)

        return username, password

    def _ssl_init(self, key_mode):
        # 密钥认证
        if key_mode is True:
            # context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH, cadata=self.__iot_ca_crt)
            self.__logger.info("connect with key...")
            context = self.__codec.Ssl().create_content()
            self.__mqtt_client.tls_set_context(context)
        else:
            self.__logger.info("connect with certificate...")
            ca = self.__certificate.ca_file
            cert = self.__certificate.cert_file
            key = self.__certificate.key_file
            self.__mqtt_client.tls_set(ca_certs=ca, certfile=cert, keyfile=key,
                                        cert_reqs=ssl.CERT_REQUIRED, tls_version=ssl.PROTOCOL_SSLv23)
        pass

    def __init(self, host, product_id, device_name, device_secret):
        client_id = product_id + device_name
        username, password = self._generate_pwss(client_id, device_secret)

        if self.__mqtt_protocol == "MQTTv311":
            mqtt_protocol_version = mqtt.MQTTv311
        elif self.__mqtt_protocol == "MQTTv31":
            mqtt_protocol_version = mqtt.MQTTv31
        if self.__useWebsocket:
            self.__mqtt_client = mqtt.Client(client_id=client_id,
                                             clean_session=self.__mqtt_clean_session,
                                             protocol=mqtt_protocol_version,
                                             transport="websockets")
        else:
            self.__mqtt_client = mqtt.Client(client_id=client_id,
                                             clean_session=self.__mqtt_clean_session,
                                             protocol=mqtt_protocol_version)

        # self._configuration_init(username, password)
        self.__mqtt_client.username_pw_set(username, password)

    def set_connect_state(self, state):
        self.__connect_state = state

    def get_connect_state(self):
        return self.__connect_state
    
    def enable_logger(self, pahoLog):
        if self.__mqtt_client is not None:
            self.__mqtt_client.enable_logger(pahoLog)

    # 设置重连时间,config_connect之前调用
    def set_reconnect_interval(self, max_sec, min_sec):
        self.__mqtt_auto_reconnect_min_sec = min_sec
        self.__mqtt_auto_reconnect_max_sec = max_sec

    # 设置消息发送超时时间,connect之前调用
    def set_message_timout(self, timeout):
        self.__mqtt_command_timeout = timeout

    # 设置保活时间,connect之前调用
    def set_keepalive_interval(self, interval):
        self.__mqtt_keep_alive = interval

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

    def register_event_callbacks(self, on_connect, on_disconnect, on_message, on_publish, on_subscribe, on_unsubscribe):
        self.__mqtt_client.on_connect = on_connect
        self.__mqtt_client.on_disconnect = on_disconnect
        self.__mqtt_client.on_message = on_message
        self.__mqtt_client.on_publish = on_publish
        self.__mqtt_client.on_subscribe = on_subscribe
        self.__mqtt_client.on_unsubscribe = on_unsubscribe

    # 配置mqtt,connect之前调用
    def config_connect(self):
        self.__mqtt_client.reconnect_delay_set(self.__mqtt_auto_reconnect_min_sec, self.__mqtt_auto_reconnect_max_sec)
        self.__mqtt_client.max_queued_messages_set(self.__mqtt_max_queued_message)
        self.__mqtt_client.max_inflight_messages_set(self.__mqtt_max_inflight_message)

    # 设置证书路径,connect之前调用
    def set_cert_file(self, ca, cert, key):
        # 认证模式置为证书方式
        self.__key_mode = False
        self.__certificate.ca_file = ca
        self.__certificate.cert_file = cert
        self.__certificate.key_file = key

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
                self._ssl_init(self.__key_mode)
            except ssl.SSLError as e:
                self.__logger.error("ssl init error:" + str(e))
                return False
        else:
            mqtt_port = self.__mqtt_tcp_port
            if self.__useWebsocket:
                mqtt_port = self.__mqtt_socket_tcp_port
            pass
        try:
            self.__logger.debug("connect_async (%s:%d)" % (self.__host, mqtt_port))
            self.__mqtt_client.connect_async(host=self.__host, port=mqtt_port, keepalive=self.__mqtt_keep_alive)
        except Exception as e:
            self.__logger.error("mqtt connect with async error:" + str(e))
            return False
        return True

    def disconnect(self):
        if self.__mqtt_client is not None:
            self.__mqtt_client.disconnect()

    def subscribe(self, topic, qos=-1):
        rc, mid = -1, -1
        if self.__mqtt_client is None:
            return rc, mid
        
        if isinstance(topic, tuple):
            topic, qos = topic
        if isinstance(topic, str):
            if qos < 0 or qos > 1:
                raise ValueError('Invalid QoS level.')
            if topic is None or len(topic) == 0:
                raise ValueError('Invalid topic.')
            pass
            rc, mid = self.__mqtt_client.subscribe(topic, qos)
            if rc == mqtt.MQTT_ERR_SUCCESS:
                self.__logger.debug("subscribe success topic:%s" % topic)
                return 0, mid
            elif rc == mqtt.MQTT_ERR_NO_CONN:
                return 2, mid
            else:
                self.__logger.debug("subscribe error topic:%s" % topic)
                return -1, mid
        # topic format [(topic1, qos),(topic2,qos)]
        if isinstance(topic, list):
            topic_list = []
            for t, qos in topic:
                if qos < 0 or qos > 1:
                    raise ValueError('Invalid QoS level.')
                if t is None or len(t) == 0 or not isinstance(t, str):
                    raise ValueError('Invalid topic.')
                topic_list.append((t, qos))

            rc, mid = self.__mqtt_client.subscribe(topic_list)
            if rc == mqtt.MQTT_ERR_SUCCESS:
                self.__logger.debug("subscribe success topic:%s" % topic)
                return 0, mid
            elif rc == mqtt.MQTT_ERR_NO_CONN:
                return 2, mid
            else:
                self.__logger.debug("subscribe error topic:%s" % topic)
                return -1, mid

    def unsubscribe(self, topic):
        rc, mid = -1, -1
        if self.__mqtt_client is None:
            return rc, mid

        rc, mid = self.__mqtt_client.unsubscribe(topic)
        if rc == mqtt.MQTT_ERR_SUCCESS:
            return 0, mid
        else:
            return rc, mid

    def publish(self, topic, payload, qos):
        rc, mid = -1, -1
        if self.__mqtt_client is None:
            return rc, mid

        # rc, mid = self.__mqtt_client.publish(topic, json.dumps(payload), qos)
        rc, mid = self.__mqtt_client.publish(topic, payload, qos)
        if rc == mqtt.MQTT_ERR_SUCCESS:
            self.__logger.debug("publish success")
            return 0, mid
        else:
            self.__logger.debug("publish failed")
            return rc, mid
