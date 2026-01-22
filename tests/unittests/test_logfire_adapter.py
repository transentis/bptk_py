import unittest
import sys
import importlib
from unittest.mock import patch, MagicMock

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

    def test_logfire_not_available(self):
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
            with self.assertRaises(ImportError) as cm:
                lf_adapter.LogfireAdapter()
            self.assertIn("Logfire is not installed", str(cm.exception))
            self.assertIn("Please install it with: pip install logfire", str(cm.exception))

    @patch("BPTK_Py.logger.logfire_adapter.logfire")
    def test_logging(self, mock_logfire):
        config = {
            "environment": "test",
            "send_to_logfire": False
        }
        
        adapter = lf_adapter.LogfireAdapter(**config)

        adapter.configured = False  # Force re-configuration for testing

        #Testing INFO-level
        adapter.log("[INFO] Info Message")
        mock_logfire.info.assert_called_once_with("Info Message")   
        self.assertTrue(adapter.configured)

        # Reset the mock for the next call
        mock_logfire.info.reset_mock()

        #Testing WARN-level
        adapter.log("[WARN] Warning Message")
        mock_logfire.warn.assert_called_once_with("Warning Message")   

        # Reset the mock for the next call
        mock_logfire.info.reset_mock()

        #Testing ERROR-level
        adapter.log("[ERROR] Error Message")
        mock_logfire.error.assert_called_once_with("Error Message")   

        # Reset the mock for the next call
        mock_logfire.info.reset_mock()

        #Testing logging of json
        adapter.log("{\"key\": \"value\"}")
        mock_logfire.info.assert_called_once_with('{{"key": "value"}}')

if __name__ == '__main__':
    unittest.main()