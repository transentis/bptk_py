import BPTK_Py.sddsl.functions as sd_functions
from importlib.metadata import version
from .modeling import Event, DelayedEvent, Agent, DataCollector, Model, Scheduler, SimultaneousScheduler, CSVDataCollector, AgentDataCollector
from .sddsl import Module
from .bptk import bptk, conf
from .config import config
from .logger import log
import sys
sys_version = sys.version_info
if(sys_version[0] < 3 or (sys_version[0] == 3 and sys_version[1] < 11)):
    print("BPTK Server requires Python 3.11 or later. Please update Python to use the BPTK Server!")
else:
    # Flask ships as bptk-py[server]. Following the pattern
    # externalstateadapter already uses for psycopg and redis, the name stays
    # importable and explains itself on use.
    try:
        from .server import BptkServer
    except ImportError as _server_import_error:
        # Chained deliberately: this catches every ImportError raised while
        # loading the server, not just a missing Flask. Without the cause, a
        # genuine failure inside bptkServer.py would be reported as a missing
        # extra - advice that would be wrong and untraceable.
        _server_error = _server_import_error

        class BptkServer:
            def __init__(self, *args, **kwargs):
                raise ImportError(
                    "BptkServer requires the server extra. "
                    "Install it with: pip install bptk-py[server]"
                ) from _server_error

    from .externalstateadapter import ExternalStateAdapter, InstanceState, FileAdapter

try:
    __version__ = version("BPTK-Py")

except:
    # If I am not installed, I will not be able to set the version
    __version__ = "UNAVAILABLE"


name = "BPTK_Py"


def instantiate(loglevel="WARN",configuration=None):
    return bptk(loglevel,configuration=configuration)
