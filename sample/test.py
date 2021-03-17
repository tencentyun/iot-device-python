import unittest
import test_mqtt

class MyTestCase(unittest.TestCase):

    def setUp(self):
        print ("init sdk")
        pass

    def tearDown(self):
        print ("deinit sdk")
        pass

    def test_mqtt(self):
        ret = test_mqtt.example()
        self.assertEqual(ret, True)


if __name__ == '__main__':
    unittest.main()
