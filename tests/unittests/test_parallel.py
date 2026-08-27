import unittest
from threading import Thread

import pytest
from unittest.mock import patch

from BPTK_Py.util.parallel import start_or_run, start_or_skip


class TestStartOrRun(unittest.TestCase):
    """Fan-out that survives an environment without threads.

    Pyodide - BPTK in the browser - raises `RuntimeError: can't start new thread`.
    Measured 2026-08-18: without this, `bptk.run_scenarios()` fails there for both
    SD and agent-based models, which is most of the documented API.

    The tests that exercise that probe pin `sys.platform` away from Emscripten.
    Running under Pyodide they would otherwise take the platform branch before
    ever reaching the probe - and three of them would still pass, because the
    visible result is the same. A test that goes green while measuring something
    else is worse than one that fails.
    """

    @pytest.mark.requires_threads
    def test_runs_the_target_in_a_thread(self):
        collected = []

        thread = start_or_run(collected.append, args=(42,))

        self.assertIsInstance(thread, Thread)
        thread.join()
        self.assertEqual(collected, [42])

    def test_runs_inline_when_no_thread_can_start(self):
        collected = []

        with patch("BPTK_Py.util.parallel.sys.platform", "linux"), \
             patch.object(Thread, "start", side_effect=RuntimeError("can't start new thread")):
            thread = start_or_run(collected.append, args=(42,))

        # None tells the caller there is nothing to join - the work is already done.
        self.assertIsNone(thread)
        self.assertEqual(collected, [42])

    def test_runs_inline_in_the_browser_without_touching_threads(self):
        """The platform is checked, not only the condition.

        A host may replace `threading.Thread` with a shim that schedules on the
        browser event loop - marimo does - so `start()` succeeds and `join()`
        raises about JSPI instead. Emscripten therefore never gets as far as
        building a thread.
        """
        collected = []

        with patch("BPTK_Py.util.parallel.sys.platform", "emscripten"), \
             patch.object(Thread, "start", side_effect=AssertionError("must not be reached")):
            thread = start_or_run(collected.append, args=(42,))

        self.assertIsNone(thread)
        self.assertEqual(collected, [42])

    def test_says_so_in_the_log(self):
        with patch("BPTK_Py.util.parallel.sys.platform", "linux"), \
             patch.object(Thread, "start", side_effect=RuntimeError("can't start new thread")), \
             patch("BPTK_Py.util.parallel.log") as logged:
            start_or_run(lambda: None)

        message = logged.call_args[0][0]
        self.assertIn("[WARN]", message)
        self.assertIn("in sequence", message)

    def test_inline_exceptions_reach_the_caller(self):
        """A difference worth knowing about.

        An exception raised inside a thread never reaches whoever joins it; run
        inline it propagates. This only ever applies where the threaded path
        cannot run at all, so no existing behaviour changes.
        """
        def boom():
            raise ValueError("equation is circular")

        with patch("BPTK_Py.util.parallel.sys.platform", "linux"), \
             patch.object(Thread, "start", side_effect=RuntimeError("can't start new thread")):
            with self.assertRaises(ValueError):
                start_or_run(boom)

    @pytest.mark.filterwarnings("ignore::pytest.PytestUnhandledThreadExceptionWarning")
    @pytest.mark.requires_threads
    def test_a_thread_that_starts_swallows_them(self):
        """The counterpart, asserted so the asymmetry is documented, not implied."""
        def boom():
            raise ValueError("equation is circular")

        thread = start_or_run(boom)   # no exception here
        thread.join()

        self.assertFalse(thread.is_alive())



class TestStartOrSkip(unittest.TestCase):
    """The counterpart to start_or_run, for work that cannot run inline.

    The file monitors watch in an endless loop, so falling back to running them
    in the caller's thread would never return. Skipping is the only degradation
    available - and costs nothing in a browser, where nobody edits the files
    being watched.
    """

    @pytest.mark.requires_threads
    def test_runs_the_target_in_a_thread(self):
        collected = []

        thread = start_or_skip(collected.append, args=(42,))

        self.assertIsInstance(thread, Thread)
        thread.join()
        self.assertEqual(collected, [42])

    def test_skips_rather_than_running_inline(self):
        collected = []

        with patch("BPTK_Py.util.parallel.sys.platform", "linux"), \
             patch.object(Thread, "start", side_effect=RuntimeError("can't start new thread")):
            thread = start_or_skip(collected.append, args=(42,))

        self.assertIsNone(thread)
        # The distinction from start_or_run: the target must NOT have run.
        self.assertEqual(collected, [])

    def test_skips_in_the_browser_without_touching_threads(self):
        """Same reason as in start_or_run, with more at stake.

        Under a shim these monitors would start, and their endless loop would
        take over the browser's event loop.
        """
        collected = []

        with patch("BPTK_Py.util.parallel.sys.platform", "emscripten"), \
             patch.object(Thread, "start", side_effect=AssertionError("must not be reached")):
            thread = start_or_skip(collected.append, args=(42,))

        self.assertIsNone(thread)
        self.assertEqual(collected, [])

    def test_names_what_is_being_skipped(self):
        with patch("BPTK_Py.util.parallel.sys.platform", "linux"), \
             patch.object(Thread, "start", side_effect=RuntimeError("can't start new thread")), \
             patch("BPTK_Py.util.parallel.log") as logged:
            start_or_skip(lambda: None, what="scenario file monitoring")

        message = logged.call_args[0][0]
        self.assertIn("[WARN]", message)
        self.assertIn("scenario file monitoring", message)


if __name__ == "__main__":
    unittest.main()
