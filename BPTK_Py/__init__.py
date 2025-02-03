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
    from .server import BptkServer
    from .externalstateadapter import ExternalStateAdapter, InstanceState, FileAdapter

try:
    __version__ = version("wheel")

except:
    # If I am not installed, I will not be able to set the version
    __version__ = "UNAVAILABLE"


name = "BPTK_Py"


def instantiate(loglevel="WARN",configuration=None):
    return bptk(loglevel,configuration=configuration)
