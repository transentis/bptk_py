#from .scenario_manager.scenario import simulation_scenario

import pkg_resources

from .abm import *
from .bptk import bptk
from .logger import log
#from .modelchecker import *
#from .modelmonitor import *
#from .scenariomanager import *
#from .sdsimulator import *
#from .sdsimulator import *
#from .simulationrunners import *
#from .visualizations import *
#from .widgetdecorator import *

try:
    __version__ = pkg_resources.get_distribution("BPTK_Py").version

except:
    # If I am not installed, I will not be able to set the version
    __version__ = "UNAVAILABLE"


name = "BPTK_Py"

