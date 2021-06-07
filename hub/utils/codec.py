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

import ssl
import base64
from Crypto.Cipher import AES

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

    class Ssl(object):
        def __init__(self):
            self.__init = None
            

    