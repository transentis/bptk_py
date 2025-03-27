import unittest
from BPTK_Py.server.bptkServer import InstanceManager

class TestBptkServer(unittest.TestCase):
    def setUp(self):
        pass

    def test_get_instance_invalid(self):
        instanceManager = InstanceManager(bptk_factory="test")

        self.assertIsNone(instanceManager.get_instance(instance_uuid=1))

        instanceManager._instances = {1: {"time": 0}}
        self.assertIsNone(instanceManager.get_instance(instance_uuid=1))

        ##timestamp is displayed as e.g. "datetime.datetime(2025, 3, 7, 16, 32, 10, 66503)" in json.
        ##KeyError for _update_instance_timestamp can probably not be triggered

if __name__ == '__main__':
    unittest.main()        