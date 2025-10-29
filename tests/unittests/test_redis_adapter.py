import unittest, jsonpickle, redis
import numpy as np

from unittest.mock import MagicMock

import BPTK_Py.logger.logger as logmod
from BPTK_Py.externalstateadapter.externalStateAdapter import InstanceState
from BPTK_Py.externalstateadapter.redis_adapter import RedisAdapter

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

    def test_init(self):
        adapter1 = RedisAdapter(redis_client=self.mock_redis)
        adapter2 = RedisAdapter(redis_client=self.mock_redis, key_prefix="custom:prefix", compress=False)

        self.assertIs(adapter1._redis_client, self.mock_redis)
        self.assertIs(adapter2._redis_client, self.mock_redis)
        self.assertEqual(adapter1._key_prefix, "bptk:state")
        self.assertEqual(adapter2._key_prefix, "custom:prefix")
        self.assertTrue(getattr(adapter1, "_compress", True))
        self.assertTrue(getattr(adapter2, "_compress", True))

if __name__ == '__main__':
    unittest.main()         