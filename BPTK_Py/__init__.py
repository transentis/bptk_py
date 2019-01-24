

import pkg_resources

from .abm import Model
from .abm import Agent
from .abm import DataCollector
from .abm import Event
from .abm import Scheduler
from .abm import SimultaneousScheduler
from .bptk import bptk
from .logger import log
from .config import config
import BPTK_Py.systemdynamics.functions as sd_functions

try:
    __version__ = pkg_resources.get_distribution("BPTK_Py").version

except:
    # If I am not installed, I will not be able to set the version
    __version__ = "UNAVAILABLE"


name = "BPTK_Py"


def instantiate(loglevel="WARN"):
    if loglevel in ["WARN","ERROR","INFO"]:
        config.loglevel = loglevel
    else:
        log("[ERROR] Invalid log level. Not starting up BPTK-Py! Valid loglevels: {}".format(str(["WARN","ERROR","INFO"])))
    return bptk()