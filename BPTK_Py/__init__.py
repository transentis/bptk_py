#from .scenario_manager.scenario import simulation_scenario

import pkg_resources

from .logger import log
from .widgetdecorator import *

from .modelchecker import *

from .simulator import *
from .visualizations import *
from .simulator import *
from .modelmonitor import *

from .scenariomanager import *

from .bptk import bptk


try:
    __version__ = pkg_resources.get_distribution("BPTK_Py").version

except:
    # If I am not installed, I will not be able to set the version
    __version__ = "UNAVAILABLE"


name = "BPTK_Py"

