import unittest, jsonpickle, redis, datetime, importlib
import numpy as np

import BPTK_Py.logger.logger as logmod
from unittest.mock import MagicMock
from BPTK_Py.externalstateadapter.redis_adapter import RedisAdapter, InstanceState

encode = lambda obj: jsonpickle.encode(obj, make_refs=False)
decode = jsonpickle.decode

class TestNumpyJsonpickleHandlers(unittest.TestCase):
    def test_numpy_scalars_and_array_serialization(self):
        vals = {
            "f32": np.float32(1.5),
            "i64": np.int64(42),
            "b": np.bool_(True),
            "arr": np.array([np.float32(1.0), np.int64(2), np.bool_(False)]),
        }
        s = encode(vals)
        self.assertNotIn("py/object", s)
        self.assertNotIn("!!python", s)

        d = decode(s)
        self.assertEqual(d, {"f32": 1.5, "i64": 42, "b": True, "arr": [1.0, 2, False]})

    def test_nested_numpy_structures(self):
        data = {"nested": [np.float64(3.14), {"x": np.array([1, 2])}]}
        s = encode(data)
        self.assertNotIn("!!python", s)
        self.assertEqual(decode(s), {"nested": [3.14, {"x": [1, 2]}]})

class TestRedisAdapter(unittest.TestCase):
    def setUp(self):
        self.mock_redis = MagicMock(spec=redis.Redis)
        importlib.reload(logmod)
        logmod.loglevel = "INFO"

    def test_init(self):
        adapter1 = RedisAdapter(redis_client=self.mock_redis)
        adapter2 = RedisAdapter(redis_client=self.mock_redis, key_prefix="custom:prefix", compress=False)

        self.assertIs(adapter1._redis_client, self.mock_redis)
        self.assertIs(adapter2._redis_client, self.mock_redis)
        self.assertEqual(adapter1._key_prefix, "bptk:state")
        self.assertEqual(adapter2._key_prefix, "custom:prefix")
        self.assertTrue(adapter1.compress)
        self.assertFalse(adapter2.compress)

        with open(logmod.logfile, "r", encoding="UTF-8") as f:
            content = f.read()
        self.assertIn("RedisAdapter initialized with key_prefix: bptk:state, compression: True", content)     
        self.assertIn("RedisAdapter initialized with key_prefix: custom:prefix, compression: False", content)     

    def test_get_instance_key(self):
        adapter = RedisAdapter(redis_client=self.mock_redis, key_prefix="testprefix")
        key = adapter._get_instance_key("instance123")
        self.assertEqual(key, "testprefix:instance123")

    def test_load_instance(self):
        #load existing instance
        instance_id = "abc123"
        fake_state = {"a": 1, "b": 2}
        fake_time = datetime.datetime(2024, 1, 1, 12, 0, 0)
        fake_timeout = {"weeks": 0, "days": 0, "hours": 1, "minutes": 0, "seconds": 0,
                        "milliseconds": 0, "microseconds": 0}
        fake_step = 5

        # Prepare mocked Redis response
        redis_value = jsonpickle.encode({
            "state": jsonpickle.encode(fake_state),
            "instance_id": instance_id,
            "time": fake_time.isoformat(),
            "timeout": fake_timeout,
            "step": fake_step
        }, make_refs=False)

        self.mock_redis.get.return_value = redis_value        

        self.adapter = RedisAdapter(redis_client=self.mock_redis, key_prefix="testprefix")
        result = self.adapter.load_instance(instance_id)

        self.assertIsInstance(result, InstanceState)
        self.assertEqual(result.instance_id, instance_id)
        self.assertEqual(result.state, fake_state)
        self.assertEqual(result.step, fake_step)
        self.assertEqual(result.timeout, fake_timeout)
        self.assertEqual(result.time, fake_time)
        expected_key = f"testprefix:{instance_id}"
        self.mock_redis.get.assert_called_once_with(expected_key)

        with open(logmod.logfile, "r", encoding="UTF-8") as f:
            content = f.read()
        self.assertIn("Loading instance abc123 from Redis key: testprefix:abc123", content)     
        self.assertIn("Data retrieved from Redis for instance abc123", content)  
        self.assertIn("Decoding instance data for abc123", content)  
        self.assertIn("Instance abc123 loaded successfully from Redis", content)

        #load not existing instance
        instance_id2 = "missing"
        self.mock_redis.get.return_value = None

        result = self.adapter._load_instance(instance_id2)
        self.assertIsNone(result)

        with open(logmod.logfile, "r", encoding="UTF-8") as f:
            content = f.read()
        self.assertIn("Loading instance missing from Redis key: testprefix:missing", content)     
        self.assertIn("No data found in Redis for instance missing", content)  

        # KeyError (missing value)
        instance_id3 = "test_error"
        invalid_redis_value = jsonpickle.encode({"unexpected": "structure"}, make_refs=False)
        self.mock_redis.get.return_value = invalid_redis_value

        res = self.adapter._load_instance(instance_id3)
        self.assertIsNone(res)

        with open(logmod.logfile, "r", encoding="UTF-8") as f:
            content = f.read()
        self.assertIn("Loading instance test_error from Redis key: testprefix:test_error", content)     
        self.assertIn("Failed to load instance test_error from Redis", content)

        #Exception (simulated client failure)
        instance_id4 = "test_exception"
        self.mock_redis.get.side_effect = RuntimeError("simulated client failure")

        res = self.adapter._load_instance(instance_id4)
        self.assertIsNone(res)

        with open(logmod.logfile, "r", encoding="UTF-8") as f:
            content = f.read()
        self.assertIn("Loading instance test_exception from Redis key: testprefix:test_exception", content)     
        self.assertIn("Unexpected error loading instance test_exception from Redis", content)

if __name__ == '__main__':
    unittest.main()         