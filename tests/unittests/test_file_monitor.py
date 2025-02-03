import unittest
from unittest.mock import patch, MagicMock
import os
import time
import threading
import BPTK_Py.logger.logger as logmod


from BPTK_Py.modelmonitor.file_monitor import FileMonitor  # Deine Datei mit der Klasse

class TestFileMonitor(unittest.TestCase):

    @patch("os.path.isfile", return_value=True)  # simulates that a file exists
    @patch("os.stat")  # mock for the timestamp
    def test_monitor_detects_file_change(self, mock_stat, mock_isfile):
        logmod.loglevel = "INFO"
               
        #cleanup logfile
        try:
            with open(logmod.logfile, "w", encoding="UTF-8") as file:
                pass
        except FileNotFoundError:
            self.fail()

        # simulated timestamp
        mock_stat.return_value.st_mtime = 100

        #setup FileMonitor with mocked update function
        mock_update_func = MagicMock()
        updater = FileMonitor(json_file="test.json", update_func= mock_update_func)
        updater._cached_stamp = 50  # older timestamp

        # start `__monitor` as separate thread
        monitor_thread = threading.Thread(target=updater._FileMonitor__monitor)
        updater.running = True
        monitor_thread.start()

        # Wait and let the Thread run
        time.sleep(2)

        # stop 
        updater.running = False
        monitor_thread.join()

        # Check if the
        mock_update_func.assert_called_once_with("test.json")

        try:
            with open(logmod.logfile, "r", encoding="UTF-8") as file:
                content = file.read()
        except FileNotFoundError:
            self.fail()

        self.assertIn("[INFO] JSON Monitor: Observed a change to test.json", content)  
        self.assertIn("[INFO] JSON Monitor for test.json: model updated and relaoded scenarios!", content)  

if __name__ == "__main__":
    unittest.main()
