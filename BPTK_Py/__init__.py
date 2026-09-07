import BPTK_Py.sddsl.functions as sd_functions
from importlib.metadata import version
from .modeling import Event, DelayedEvent, Agent, DataCollector, Model, Scheduler, SimultaneousScheduler, CSVDataCollector, AgentDataCollector
from .sddsl import Module
from .bptk import bptk, conf
from .config import config
from .logger import log
# No Python-version check here: `requires-python = ">=3.11"` in pyproject.toml is the
# one that works, and pip refuses the install below it. The guard that used to stand
# here printed a message about the *server* from the package's own __init__, and could
# never fire.

# Flask ships as bptk-py[server]. Following the pattern externalstateadapter already
# uses for psycopg and redis, the name stays importable and explains itself on use.
try:
    from .server import BptkServer
except ImportError as _server_import_error:
    # Chained deliberately: this catches every ImportError raised while loading the
    # server, not just a missing Flask. Without the cause, a genuine failure inside
    # bptkServer.py would be reported as a missing extra - advice that would be wrong
    # and untraceable.
    #
    # Covered by test_server_extra_missing, which blocks flask in a *subprocess* -
    # which class `BPTK_Py.BptkServer` refers to is decided while BPTK_Py is imported,
    # so the block has to be in place beforehand. Line coverage cannot see into that
    # subprocess, so these lines are reported as missed however well they are tested.
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


def __getattr__(attribute):
    """Expose the plotting configuration as `BPTK_Py.plotting_config`.

    Lazily, through the module protocol, because `BPTK_Py.visualizations` imports
    matplotlib - and BPTK installs without the plotting extra. A headless install can
    still `import BPTK_Py`; it only fails if someone actually asks for this.
    """
    if attribute in ("plotting_config", "PlottingConfig"):
        from BPTK_Py.visualizations import plotting_config, PlottingConfig

        return {"plotting_config": plotting_config, "PlottingConfig": PlottingConfig}[attribute]
    raise AttributeError("module {!r} has no attribute {!r}".format(__name__, attribute))
