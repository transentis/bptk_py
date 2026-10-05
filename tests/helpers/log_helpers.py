"""Clearing and reading the logfile, for tests that assert what was logged.

The logfile is wherever `BPTK_Py.logger.logger.logfile` points when the call is
made, so a test that changes it - or the working directory - reads the right one.
"""

import BPTK_Py.logger.logger as logmod


def clear_log():
    """Empty the logfile, so that what a test reads afterwards is its own."""
    with open(logmod.logfile, "w", encoding="UTF-8"):
        pass


def read_log():
    """Everything logged since the last clear_log()."""
    with open(logmod.logfile, "r", encoding="UTF-8") as file:
        return file.read()
