import pytest
import unittest
from unittest.mock import patch, MagicMock
import contextlib
import io
import os
import BPTK_Py.logger.logger as logmod


from BPTK_Py.modelmonitor.model_monitor import ModelMonitor
from tests.helpers.log_helpers import clear_log, read_log

class TestModelMonitor(unittest.TestCase):

    # ModelMonitor.__init__ starts a monitor thread of its own. Without suppressing it,
    # that loop and the one this test starts both see the stale _cached_stamp and race
    # to call update_func — the same coin flip that made the FileMonitor test fail on
    # macOS + Python 3.13.
    @patch("BPTK_Py.modelmonitor.model_monitor.start_or_skip")  # suppress the constructor's thread
    @patch("os.path.isfile", return_value=True)  # simulates that a file exists
    @patch("os.getcwd", return_value="testDir")  # simulates that a folder exists
    @patch("os.stat")  # mock for the timestamp
    @patch("BPTK_Py.modelmonitor.model_monitor.compile", return_value="testOutput")  # Mock for `compile`
    def test_monitor_detects_file_change(self, mock_compile, mock_stat, mock_cwd, mock_isfile, mock_thread):
        logmod.loglevel = "INFO"
               
        #cleanup logfile
        clear_log()

        # simulated timestamp
        mock_stat.return_value.st_mtime = 100

        #setup FileMonitor with mocked update function‚
        mock_update_func = MagicMock()
        modelMonitor = ModelMonitor(source_file="test.itmx", dest="test.py", update_func= mock_update_func)
        modelMonitor._cached_stamp = 50  # older timestamp

        # One pass of the loop, run here rather than in a thread: the patched sleep
        # at its end stops it. Waiting two seconds for a thread showed nothing more.
        modelMonitor.running = True
        with patch("BPTK_Py.modelmonitor.model_monitor.time.sleep",
                   side_effect=lambda *_: setattr(modelMonitor, "running", False)):
            modelMonitor._ModelMonitor__monitor()

        mock_update_func.assert_called_once_with("test.itmx")

        content = read_log()

        self.assertIn("[INFO] ABMModel Monitor for test.itmx: Observed a change to the model. Calling the parser", content)  
        self.assertIn("[INFO] ABMModel Monitor for test.itmx: model updated and relaoded scenarios!", content)  

        self.assertEqual(modelMonitor._cached_stamp,100)

    @patch("BPTK_Py.modelmonitor.model_monitor.start_or_skip")  # suppress the background thread
    @patch("os.stat")
    def test_kill(self, mock_stat, mock_thread):
        """kill() flips the running flag so the monitor thread terminates."""
        mock_stat.return_value.st_mtime = 100
        modelMonitor = ModelMonitor(source_file="test.itmx", dest="test.py", update_func=MagicMock())

        self.assertTrue(modelMonitor.running)
        modelMonitor.kill()
        self.assertFalse(modelMonitor.running)

    @patch("BPTK_Py.modelmonitor.model_monitor.start_or_skip")  # suppress the background thread
    @patch("os.path.isfile", return_value=True)
    @patch("os.getcwd", return_value="testDir")
    @patch("os.stat")
    @patch("BPTK_Py.modelmonitor.model_monitor.compile", return_value="Some ERROR occurred")
    def test_monitor_stops_on_compile_error(self, mock_compile, mock_stat, mock_cwd, mock_isfile, mock_thread):
        """A compile error stops the monitor and skips the scenario reload."""
        mock_stat.return_value.st_mtime = 100

        mock_update_func = MagicMock()
        modelMonitor = ModelMonitor(source_file="test.itmx", dest="test.py", update_func=mock_update_func)
        modelMonitor._cached_stamp = 50  # force a detected change
        modelMonitor.running = True

        # compile() returns an "error" string -> running is set False and __monitor returns.
        with contextlib.redirect_stdout(io.StringIO()):
            modelMonitor._ModelMonitor__monitor()

        mock_update_func.assert_not_called()
        self.assertFalse(modelMonitor.running)

    @patch("BPTK_Py.modelmonitor.model_monitor.start_or_skip")  # suppress the background thread
    @patch("BPTK_Py.modelmonitor.model_monitor.os.name", "nt")
    @patch("os.path.isfile", return_value=True)
    @patch("os.getcwd", return_value="testDir")
    @patch("os.stat")
    @patch("BPTK_Py.modelmonitor.model_monitor.compile", return_value="ok")
    def test_monitor_windows_path(self, mock_compile, mock_stat, mock_cwd, mock_isfile, mock_thread):
        """On Windows the path separators are normalised before stat-ing."""
        mock_stat.return_value.st_mtime = 100

        mock_update_func = MagicMock()
        modelMonitor = ModelMonitor(source_file="some/dir/test.itmx", dest="test.py", update_func=mock_update_func)
        modelMonitor._cached_stamp = 50
        modelMonitor.running = True

        with patch("BPTK_Py.modelmonitor.model_monitor.time.sleep",
                   side_effect=lambda *_: setattr(modelMonitor, "running", False)), \
                contextlib.redirect_stdout(io.StringIO()):
            modelMonitor._ModelMonitor__monitor()

        mock_update_func.assert_called_once_with("some/dir/test.itmx")

    @patch("BPTK_Py.modelmonitor.model_monitor.start_or_skip", return_value=None)
    @patch("os.stat")
    def test_stops_when_no_thread_can_start(self, mock_stat, mock_start):
        """See the FileMonitor test of the same name."""
        mock_stat.return_value.st_mtime = 100

        monitor = ModelMonitor(source_file="model.stmx", dest="model", update_func=MagicMock())

        self.assertFalse(monitor.running)
