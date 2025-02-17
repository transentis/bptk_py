import unittest
from unittest.mock import patch, MagicMock
import time
import os
import threading
import BPTK_Py.logger.logger as logmod


from BPTK_Py.modelmonitor.model_monitor import ModelMonitor 

class TestModelMonitor(unittest.TestCase):

    @patch("os.path.isfile", return_value=True)  # simulates that a file exists
    @patch("os.getcwd", return_value="testDir")  # simulates that a folder exists
    @patch("os.stat")  # mock for the timestamp
    @patch("BPTK_Py.modelmonitor.model_monitor.compile", return_value="testOutput")  # Mock for `compile`
    def test_monitor_detects_file_change(self, mock_compile, mock_stat, mock_cwd, mock_isfile):
        logmod.loglevel = "INFO"
               
        #cleanup logfile
        try:
            with open(logmod.logfile, "w", encoding="UTF-8") as file:
                pass
        except FileNotFoundError:
            self.fail()

        # simulated timestamp
        mock_stat.return_value.st_mtime = 100

        #setup FileMonitor with mocked update function‚
        mock_update_func = MagicMock()
        modelMonitor = ModelMonitor(source_file="test.itmx", dest="test.py", update_func= mock_update_func)
        modelMonitor._cached_stamp = 50  # older timestamp

        # start `__monitor` as separate thread
        monitor_thread = threading.Thread(target=modelMonitor._ModelMonitor__monitor)
        modelMonitor.running = True
        monitor_thread.start()

        # Wait and let the Thread run
        time.sleep(2)

        # stop 
        modelMonitor.running = False
        monitor_thread.join()

        mock_update_func.assert_called_once_with("test.itmx")

        try:
            with open(logmod.logfile, "r", encoding="UTF-8") as file:
                content = file.read()
        except FileNotFoundError:
            self.fail()

        self.assertIn("[INFO] ABMModel Monitor for test.itmx: Observed a change to the model. Calling the parser", content)  
        self.assertIn("[INFO] ABMModel Monitor for test.itmx: model updated and relaoded scenarios!", content)  

        self.assertEqual(modelMonitor._cached_stamp,100)

if __name__ == "__main__":
    unittest.main()
