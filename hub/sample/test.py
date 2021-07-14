import unittest

# from mqtt.example_mqtt import example_mqtt
from dynreg import example_dynreg as dynregtest
from gateway import example_gateway as gatewaytest
from mqtt import example_mqtt as mqtttest
from ota import example_ota as otatest
from broadcast import example_broadcast as broadcasttest
from rrpc import example_rrpc as rrpctest
from shadow import example_shadow as shadowtest

class MyTestCase(unittest.TestCase):

    def setUp(self):
        print ("\ninit sdk")
        pass

    def tearDown(self):
        print ("deinit sdk")
        pass

    def test_mqtt(self):
        ret = mqtttest.example_mqtt("hub/sample/device_info.json")
        self.assertEqual(ret, True)

    def test_dynreg(self):
        ret = dynregtest.example_dynreg()
        self.assertEqual(ret, True)
        pass

    def test_gateway(self):
        ret = gatewaytest.example_gateway("hub/sample/device_info.json")
        self.assertEqual(ret, True)
        pass

    def test_ota(self):
        ret = otatest.example_ota("hub/sample/device_info.json")
        self.assertEqual(ret, True)
        pass

    def test_broadcast(self):
        ret = broadcasttest.example_broadcast("hub/sample/device_info.json")
        self.assertEqual(ret, True)
        pass

    def test_rrpc(self):
        ret = rrpctest.example_rrpc("hub/sample/device_info.json")
        self.assertEqual(ret, True)
        pass

    def test_shadow(self):
        ret = shadowtest.example_shadow("hub/sample/device_info.json")
        self.assertEqual(ret, True)
        pass


if __name__ == '__main__':
    unittest.main()
