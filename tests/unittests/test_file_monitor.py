import unittest
from unittest.mock import patch, MagicMock
import os
import time
import threading
import BPTK_Py.logger.logger as logmod


from BPTK_Py.modelmonitor.file_monitor import FileMonitor 

class TestFileMonitor(unittest.TestCase):

    # FileMonitor.__init__ starts a monitor thread of its own. Without suppressing it,
    # that loop and the one this test starts both see the stale _cached_stamp and race
    # to call update_func — a coin flip that came up "two calls" on macOS + Python 3.13.
    @patch("BPTK_Py.modelmonitor.file_monitor.Thread")  # suppress the constructor's thread
    @patch("os.path.isfile", return_value=True)  # simulates that a file exists
    @patch("os.stat")  # mock for the timestamp
    def test_monitor_detects_file_change(self, mock_stat, mock_isfile, mock_thread):
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
        fileMonitor = FileMonitor(json_file="test.json", update_func= mock_update_func)
        fileMonitor._cached_stamp = 50  # older timestamp

        # start `__monitor` as separate thread
        monitor_thread = threading.Thread(target=fileMonitor._FileMonitor__monitor)
        fileMonitor.running = True
        monitor_thread.start()

        # Wait and let the Thread run
        time.sleep(2)

        # stop 
        fileMonitor.running = False
        monitor_thread.join()

        mock_update_func.assert_called_once_with("test.json")

        try:
            with open(logmod.logfile, "r", encoding="UTF-8") as file:
                content = file.read()
        except FileNotFoundError:
            self.fail()

        self.assertIn("[INFO] JSON Monitor: Observed a change to test.json", content)  
        self.assertIn("[INFO] JSON Monitor for test.json: model updated and relaoded scenarios!", content)  

        self.assertEqual(fileMonitor._cached_stamp,100)

    @patch("BPTK_Py.modelmonitor.file_monitor.Thread")  # suppress the background thread
    @patch("os.stat")
    def test_kill(self, mock_stat, mock_thread):
        """kill() flips the running flag so the monitor thread terminates."""
        mock_stat.return_value.st_mtime = 100
        fileMonitor = FileMonitor(json_file="test.json", update_func=MagicMock())

        self.assertTrue(fileMonitor.running)
        fileMonitor.kill()
        self.assertFalse(fileMonitor.running)

    @patch("BPTK_Py.modelmonitor.file_monitor.Thread")  # suppress the background thread
    @patch("os.path.isfile", return_value=True)
    @patch("os.stat")
    def test_monitor_survives_update_func_error(self, mock_stat, mock_isfile, mock_thread):
        """If the update function raises, the monitor logs a warning and keeps running."""
        mock_stat.return_value.st_mtime = 100

        def raiser(_):
            raise RuntimeError("boom")

        fileMonitor = FileMonitor(json_file="test.json", update_func=raiser)
        fileMonitor._cached_stamp = 50  # force a detected change
        fileMonitor.running = True

        # Run exactly one loop iteration, then stop via the (patched) sleep.
        with patch("BPTK_Py.modelmonitor.file_monitor.time.sleep",
                   side_effect=lambda *_: setattr(fileMonitor, "running", False)):
            fileMonitor._FileMonitor__monitor()

        # The exception was swallowed and the loop exited cleanly.
        self.assertFalse(fileMonitor.running)
        self.assertEqual(fileMonitor._cached_stamp, 100)

    @patch("BPTK_Py.modelmonitor.file_monitor.Thread")  # suppress the background thread
    @patch("BPTK_Py.modelmonitor.file_monitor.os.name", "nt")
    @patch("os.path.isfile", return_value=True)
    @patch("os.stat")
    def test_monitor_windows_path(self, mock_stat, mock_isfile, mock_thread):
        """On Windows the path separators are normalised before stat-ing."""
        mock_stat.return_value.st_mtime = 100

        mock_update_func = MagicMock()
        fileMonitor = FileMonitor(json_file="some/dir/test.json", update_func=mock_update_func)
        fileMonitor._cached_stamp = 50
        fileMonitor.running = True

        with patch("BPTK_Py.modelmonitor.file_monitor.time.sleep",
                   side_effect=lambda *_: setattr(fileMonitor, "running", False)):
            fileMonitor._FileMonitor__monitor()

        mock_update_func.assert_called_once_with("some/dir/test.json")

if __name__ == "__main__":
    unittest.main()
