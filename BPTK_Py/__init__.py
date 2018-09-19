

import pkg_resources

from .abm import ABModel
from .abm import Agent
from .abm import DataCollector
from .abm import Event
from .abm import Scheduler
from .abm import SimultaneousScheduler
from .bptk import bptk
from .logger import log

try:
    __version__ = pkg_resources.get_distribution("BPTK_Py").version

except:
    # If I am not installed, I will not be able to set the version
    __version__ = "UNAVAILABLE"


name = "BPTK_Py"

