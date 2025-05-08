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

import hashlib
import hmac
import ssl
import base64
from Crypto.Cipher import AES

import Crypto.Signature.PKCS1_v1_5 as sign_PKCS1_v1_5 #用于签名/验签
from Crypto.Cipher import PKCS1_v1_5 as Cipher_pkcs1_v1_5 #用于加密
from Crypto import Hash
from Crypto.PublicKey import RSA

class Codec(object):
    def __init__(self):
        self.__init = None

    class _AESUtil:
        __BLOCK_SIZE_16 = BLOCK_SIZE_16 = AES.block_size

        '''
        @staticmethod
        def encryt(str, key, iv):
            cipher = AES.new(key, AES.MODE_CBC, iv)
            x = AESUtil.__BLOCK_SIZE_16 - (len(str) % AESUtil.__BLOCK_SIZE_16)
            if x != 0:
                str = str + chr(x) * x
            msg = cipher.encrypt(str)
            msg = base64.b64encode(msg)
            return msg
        '''

        @staticmethod
        def decrypt(encrypt_str, key, init_vector):
            cipher = AES.new(key, AES.MODE_CBC, init_vector)
            decrypt_bytes = base64.b64decode(encrypt_str)
            return cipher.decrypt(decrypt_bytes)

    class Hmac:
        @staticmethod
        def sha1_encode(key, content):
            return hmac.new(key, content, hashlib.sha1).digest()

        @staticmethod
        def sha256_encode(key, content):
            return hmac.new(key, content, hashlib.sha256).digest()
    class RSA:
        @staticmethod
        def sha256_encode(key, content):
            signer_pri_obj = sign_PKCS1_v1_5.new(RSA.importKey(key))
            rand_hash = Hash.SHA256.new()
            rand_hash.update(content)
            signature = signer_pri_obj.sign(rand_hash)
            sign_result = base64.b64encode(signature).decode('utf-8')
            return sign_result

    class Hash:
        @staticmethod
        def sha256_encode(content):
            return hashlib.sha256(content).hexdigest()

    class Base64:
        @staticmethod
        def encode(content):
            return base64.b64encode(content).decode('utf-8')

        @staticmethod
        def encodeHex(contentHex):

            byte_array = bytes.fromhex(contentHex)
            byte_array.hex()
            base64_byte_array = base64.b64encode(byte_array)
            result = base64_byte_array.decode('utf-8')
            return result


    class Ssl():
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

        def __init__(self):
            self.__iot_ca_crt = self.__IOT_CA_CRT

        def create_content(self, cadata=None):
            if cadata is None:
                cadata = self.__iot_ca_crt

            # 创建SSL上下文
            context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)

            # 设置TLS协议版本
            context.minimum_version = ssl.TLSVersion.TLSv1_2

            # 配置证书验证
            context.verify_mode = ssl.CERT_REQUIRED
            context.check_hostname = False  # 禁用主机名验证

            # 加载CA证书
            try:
                if cadata:
                    # 清理证书字符串，确保格式正确
                    cleaned_cadata = "\n".join(
                        line.strip() for line in cadata.splitlines()
                        if line.strip() and not line.strip().startswith("--")
                    )
                    context.load_verify_locations(cadata=cleaned_cadata.encode())

                    # 同时加载系统默认证书
                    context.load_default_certs()
            except Exception as e:
                # 如果证书加载失败，回退到不验证证书(仅用于测试)
                context.verify_mode = ssl.CERT_NONE

            return context