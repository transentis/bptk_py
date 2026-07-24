import importlib
import unittest
from unittest import mock

import BPTK_Py
from BPTK_Py.bptk import bptk


class TestPackageInit(unittest.TestCase):
    def test_instantiate_returns_bptk(self):
        """The package-level instantiate() helper returns a bptk instance."""
        self.assertIsInstance(BPTK_Py.instantiate(), bptk)

    def test_version_falls_back_to_unavailable(self):
        """If the installed package version cannot be resolved, __version__ falls
        back to "UNAVAILABLE"."""
        try:
            with mock.patch("importlib.metadata.version", side_effect=Exception("not installed")):
                importlib.reload(BPTK_Py)
            self.assertEqual(BPTK_Py.__version__, "UNAVAILABLE")
        finally:
            # Restore the real module state for the rest of the test session.
            importlib.reload(BPTK_Py)


if __name__ == '__main__':
    unittest.main()
