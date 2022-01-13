import unittest

from dynreg import example_dynreg as dynregtest
from gateway import example_gateway as gatewaytest
from mqtt import example_mqtt as mqtttest
from ota import example_ota as otatest
from template import example_template as templatetest
from httpAccess import example_http as httptest

class MyTestCase(unittest.TestCase):

    def setUp(self):
        print ("\ninit sdk")
        pass

    def tearDown(self):
        print ("deinit sdk")
        pass

    def test_mqtt(self):
        ret = mqtttest.example_mqtt()
        self.assertEqual(ret, True)

    def test_dynreg(self):
        ret = dynregtest.example_dynreg()
        self.assertEqual(ret, True)
        pass

    def test_gateway(self):
        ret = gatewaytest.example_gateway()
        self.assertEqual(ret, True)
        pass

    def test_http(self):
        ret = httptest.example_http()
        self.assertEqual(ret, True)
        pass

    @unittest.skip("skipping")
    def test_ota(self):
        ret = otatest.example_ota()
        self.assertEqual(ret, True)
        pass

    def test_template(self):
        ret = templatetest.example_template()
        self.assertEqual(ret, True)
        pass


if __name__ == '__main__':
    unittest.main()
