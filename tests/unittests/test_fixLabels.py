import io
import unittest
from contextlib import redirect_stdout

from BPTK_Py.sdcompiler.plugins.fixLabels import resolve


class TestFixLabels(unittest.TestCase):
    def test_recursion_error_is_caught(self):
        """A self-referential expression drives resolve into a RecursionError, which the
        plugin catches (logging a message) rather than letting it propagate."""
        circular = {"name": "x", "type": "identifier"}
        circular["args"] = [circular]

        entity = {"labels": ["a"], "dimensions": ["d"], "name": "e"}
        with redirect_stdout(io.StringIO()):
            result = resolve(circular, entity)

        self.assertIsInstance(result, dict)


if __name__ == '__main__':
    unittest.main()
