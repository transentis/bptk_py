
import pkg_resources

import BPTK_Py.sddsl.functions as sd_functions
from .modeling import Event, DelayedEvent, Agent, DataCollector, Model, Scheduler, SimultaneousScheduler
from .bptk import bptk, conf
from .config import config
from .logger import log
from .server import BptkServer

try:
    __version__ = pkg_resources.get_distribution("BPTK_Py").version

except:
    # If I am not installed, I will not be able to set the version
    __version__ = "UNAVAILABLE"


name = "BPTK_Py"


def instantiate(loglevel="WARN",configuration=None):
    return bptk(loglevel,configuration=configuration)
