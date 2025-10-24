import unittest
import sys
import importlib
from unittest.mock import patch

import BPTK_Py.logger.logfire_adapter as lf_adapter

class TestLogfireAdapter(unittest.TestCase):
    def setUp(self):
        pass    

    def test_import(self):
        self.assertTrue(hasattr(lf_adapter, "LOGFIRE_AVAILABLE"))

    def test_init(self):
        config = {
            "environment": "test",
            "send_to_logfire": False
        }
        
        adapter = lf_adapter.LogfireAdapter(**config)
    
        self.assertTrue(adapter.configured)
        self.assertEqual(adapter.logfire_config, config)
        # Patch logfire.configure im richtigen Namespace!
        with patch("BPTK_Py.logger.logfire_adapter.logfire.configure") as mock_configure:
            adapter = lf_adapter.LogfireAdapter(**config)
            mock_configure.assert_called_once_with(**config)

    def test_logfire_not_available_sets_flag_and_raises(self):
        # Patch sys.modules, such that import logfire failes
        with patch.dict('sys.modules', {'logfire': None}):
            # Remove the module from Cache, such that reload works
            if 'BPTK_Py.logger.logfire_adapter' in sys.modules:
                del sys.modules['BPTK_Py.logger.logfire_adapter']
            import BPTK_Py.logger.logfire_adapter as lf_adapter
            importlib.reload(lf_adapter)
            # Check that it worked
            self.assertFalse(lf_adapter.LOGFIRE_AVAILABLE)
            # Check the ImportError
            with self.assertRaises(ImportError):
                lf_adapter.LogfireAdapter()

if __name__ == '__main__':
    unittest.main()