
import pkg_resources

import BPTK_Py.sddsl.functions as sd_functions
from .modeling import Event, DelayedEvent, Agent, DataCollector, Model, Scheduler, SimultaneousScheduler
from .sddsl import Module
from .bptk import bptk, conf
from .config import config
from .logger import log
import sys
version = sys.version_info
if(version[0] < 3 or (version[0] == 3 and version[1] < 9)):
    print("BPTK Server requires Python 3.9 or later. Please update Python to use the BPTK Server!")
else:
    from .server import BptkServer
    from .externalstateadapter import ExternalStateAdapter, InstanceState, FileAdapter

try:
    __version__ = pkg_resources.get_distribution("BPTK_Py").version

except:
    # If I am not installed, I will not be able to set the version
    __version__ = "UNAVAILABLE"


name = "BPTK_Py"


def instantiate(loglevel="WARN",configuration=None):
    return bptk(loglevel,configuration=configuration)
