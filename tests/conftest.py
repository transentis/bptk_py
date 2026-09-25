import importlib.util
import sys
from pathlib import Path
import pytest

from BPTK_Py.logger import logger as logmod


# --- What can run against a base install -----------------------------------
#
# Most of the suite needs no extra at all. These modules do, and cannot even be
# imported without it, so they are not collected when the extra is absent. With
# everything installed - `just test` and the CI matrix - nothing is skipped.
#
# The list cannot drift silently: a new module that needs an extra fails
# collection in the base-install job and names itself while doing so.
_OPTIONAL_TEST_MODULES = {
    "matplotlib": ["unittests/test_visualize.py"],
    "xmltodict": ["test_sddsl.py",
                  "test_xmile.py",
                  "unittests/test_sdcompiler_generator.py",
                  "unittests/test_sdcompiler_parser.py"],
    "flask": ["test_external_state.py",
              "test_server.py"],
    "psycopg": ["unittests/test_external_state_adapters.py",
                "unittests/test_postgres_adapter.py"],
    "redis": ["unittests/test_redis_adapter.py"],
    # The py3-none-any wheel carries no compiled engine. These import it at
    # module level, so they belong in the same mechanism.
    "BPTK_Py._rust_engine": ["test_parity.py",
                             "test_parity_multidimensional.py",
                             "test_rust_backend.py",
                             "test_rust_engine.py"],
}

def _loadable(name):
    """Whether `name` can actually be imported, not merely be found.

    `find_spec` is enough for the third-party packages above - they are either
    installed or not. It is not enough for the compiled engine: a checkout
    mounted into Pyodide still contains the macOS or Linux `_rust_engine.abi3.so`
    from a local build, which has a spec but fails to load ("need to see wasm
    magic number"). Presence is not availability.
    """
    try:
        importlib.import_module(name)
        return True
    except ImportError:
        return False


RUST_ENGINE_AVAILABLE = _loadable("BPTK_Py._rust_engine")


def _threads_available():
    """Whether this interpreter can start a thread at all.

    Emscripten cannot: `Thread.start()` raises RuntimeError there. A few tests
    are about threading itself and have nothing left to assert without it.
    """
    from threading import Thread
    try:
        thread = Thread(target=lambda: None)
        thread.start()
        thread.join()
        return True
    except RuntimeError:
        return False


THREADS_AVAILABLE = _threads_available()

# Emscripten (Pyodide, i.e. the browser) has no process model, so these cannot
# run there. Everything else about them is fine; it is the platform that is
# missing a capability, not the code.
_NO_SUBPROCESS_MODULES = [
    "test_packaging.py",
    "unittests/test_build_any_wheel.py",
]

collect_ignore = [
    module
    for package, modules in _OPTIONAL_TEST_MODULES.items()
    if not (_loadable(package) if package.startswith("BPTK_Py")
            else importlib.util.find_spec(package) is not None)
    for module in modules
]

if sys.platform == "emscripten":
    collect_ignore += _NO_SUBPROCESS_MODULES

# What each extra installs, for the `requires_extra` marker below. Individual
# tests inside modules that are otherwise fine on a base install carry it.
_EXTRA_PACKAGES = {
    "plotting": ["matplotlib"],
    "xmile": ["parsimonious", "xmltodict", "jinja2"],
    "server": ["flask", "psycopg", "redis"],
    "observability": ["logfire"],
}


def pytest_runtest_setup(item):
    """Skip tests whose extra is not installed, rather than failing them.

    Lets the whole suite run against a base install (the wheel job in
    python-package.yml) without maintaining a second list of what to select.
    With every extra present nothing is skipped.
    """
    for marker in item.iter_markers("requires_extra"):
        for extra in marker.args:
            missing = [package for package in _EXTRA_PACKAGES[extra]
                       if importlib.util.find_spec(package) is None]
            if missing:
                pytest.skip(f"needs bptk-py[{extra}] ({', '.join(missing)} not installed)")

    if not RUST_ENGINE_AVAILABLE and list(item.iter_markers("requires_rust")):
        pytest.skip("needs the compiled Rust engine, which this install has no build of")

    if not THREADS_AVAILABLE and list(item.iter_markers("requires_threads")):
        pytest.skip("needs threads, which this platform cannot start")


@pytest.fixture(autouse=True)
def reset_logfire_state():
    """Restore the logger module's Logfire state after every test.

    Several logger tests call the real `configure_logfire()`, which sets the module
    globals `logfire_enabled` / `logfire_adapter` and leaves them set. Every `log()`
    call in every test that runs afterwards is then routed through that adapter as
    well. That is harmless while the tests pass `send_to_logfire: False`, but with a
    real token in the environment it would ship test noise to a live Logfire project
    — so the state is reset here rather than in each test class.
    """
    enabled, adapter = logmod.logfire_enabled, logmod.logfire_adapter
    yield
    logmod.logfire_enabled, logmod.logfire_adapter = enabled, adapter


@pytest.fixture(scope="session", autouse=True)
def cleanup_compiled_models():
    """Clean up .py files generated by XMILE compilation after the test session."""
    yield
    test_models_dir = Path(__file__).parent / "test_models"
    for file_path in test_models_dir.glob("*.py"):
        file_path.unlink()


# Log messages that would mean "the Rust engine did not run, and Python ran instead".
# Since 3.2.0 the library no longer does that - it raises `RustBackendError` - so none
# of these is emitted any more. The list stays because a later phase could add a path,
# and a silent substitution is the failure that looks green.
# Deliberately excluded: the invalid-backend-string messages (bptk.py) - those are
# input validation, not engine failures - and the export_state message, where Rust
# did run and only the resume shortcut fell back to replay.
_RUST_FALLBACK_MARKERS = (
    "rust step failed",
    "rust engine failed",
    "cannot serialize model to json",
    "falling back to python engine for scenario",
    "cannot run with rust backend",
)


# --- Did the engine actually run? ------------------------------------------
#
# The fallback guard below is negative evidence: it fails a test when bptk said
# it gave up. That leaves one hole. A backend argument that is neither "python"
# nor "rust" - a typo, a renamed constant - takes the Python branch at every
# decision site without logging anything at all, because nothing failed. A
# comparison test written that way compares Python with Python and passes.
#
# So this records both halves and pairs them: every request for a non-Python
# backend, and every model the engine actually loaded. A test that asked for one
# and never got one is a test whose Rust assertions are empty.
#
# Both probes wrap rather than replace, so behaviour is unchanged. `load_model`
# is patched on the class itself, not on the module attribute, because the test
# modules import `RustSdEngine` directly and a module-level patch would miss them.

class _RustUse:
    """Per-test record of what was asked for and what the engine did."""

    def __init__(self):
        self.reset()

    def reset(self):
        self.requested = []      # backend values asked for, other than "python"
        self.loaded = 0          # models the engine loaded successfully


RUST_USE = _RustUse()


def _backend_index(func):
    """Position of the `backend` parameter, so the wrapper need not bind a signature."""
    import inspect
    params = list(inspect.signature(func).parameters)
    return params.index("backend") if "backend" in params else None


def _wrap_backend_arg(owner, name):
    """Record every non-Python backend this entry point is asked for."""
    func = getattr(owner, name)
    index = _backend_index(func)
    if index is None:  # pragma: no cover - the caller picked the name from the signature
        return

    def wrapper(*args, **kwargs):
        if "backend" in kwargs:
            value = kwargs["backend"]
        elif len(args) > index:
            value = args[index]
        else:
            value = None
        if value is not None and value != "python":
            RUST_USE.requested.append("{}.{}({!r})".format(owner.__name__, name, value))
        return func(*args, **kwargs)

    wrapper.__name__ = name
    setattr(owner, name, wrapper)


def _install_rust_probes():
    from BPTK_Py._rust_engine import RustSdEngine
    from BPTK_Py.bptk import bptk as bptk_class
    from BPTK_Py.modeling.model import Model
    from BPTK_Py.scenariorunners.sd_runner import SdRunner

    load_model = RustSdEngine.load_model

    def counting_load_model(self, *args, **kwargs):
        model = load_model(self, *args, **kwargs)
        RUST_USE.loaded += 1
        return model

    RustSdEngine.load_model = counting_load_model

    # Deliberately not `begin_session`: it records an intention in the session
    # state and runs nothing, so a test that only asserts that state would be
    # flagged for an engine run it never asked to happen. `run_scenario_step`
    # is where a session's steps arrive, carrying the backend the session was
    # started with - so the session path is covered where it is actually run.
    for owner, name in ((bptk_class, "run_scenarios"),
                        (bptk_class, "plot_scenarios"),
                        (SdRunner, "run_scenario_step"),
                        (Model, "simulate")):
        _wrap_backend_arg(owner, name)


if RUST_ENGINE_AVAILABLE:
    _install_rust_probes()


def _logfile_size():
    logfile = Path(logmod.logfile)
    return logfile.stat().st_size if logfile.exists() else 0


def _fallback_lines_since(offset):
    """Fallback log lines appended since `offset`, if any."""
    logfile = Path(logmod.logfile)
    if not logfile.exists():
        return []
    # A test may have truncated the logfile; then our offset is meaningless.
    if logfile.stat().st_size < offset:
        return []
    with logfile.open("r", encoding="UTF-8", errors="replace") as f:
        f.seek(offset)
        appended = f.read()
    return [
        line for line in appended.splitlines()
        if any(marker in line.lower() for marker in _RUST_FALLBACK_MARKERS)
    ]


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_call(item):
    """Fail any test during which bptk silently fell back from Rust to Python.

    Such a fallback used to be a production feature: when the engine could not load or
    run a model, bptk logged a [WARN] and computed in Python, so results stayed correct.
    In tests it was a trap - a parity test comparing "python" against a "rust" run that
    never happened compares Python with Python and passes for the wrong reason, which is
    how the delay-cycle limitation stayed hidden until 2026-08-11. Since 3.2.0 the
    library raises instead, for the same reason one release later.

    The guard stays, because a later phase could add a path back. A test that writes
    such a line on purpose opts out with ``@pytest.mark.allow_rust_fallback``.

    Separately, a test asking for a non-Python backend that the engine never
    serves also fails - see RUST_USE above. A test that stubs the engine call
    out, so it is never meant to be reached, opts out of that second check with
    ``@pytest.mark.allow_rust_unused``.

    Limitation: detection is log-based, so a test that sets ``loglevel="ERROR"``
    suppresses the [WARN] line and can hide a fallback.
    """
    if item.get_closest_marker("allow_rust_fallback"):
        yield
        return

    # On a pure-Python install there is no engine to fall back *from*: falling
    # back is the designed behaviour, not a silent failure. Guarding here would
    # fail every test that touches the Rust path, which is the whole point of
    # that wheel.
    if not RUST_ENGINE_AVAILABLE:
        yield
        return

    offset = _logfile_size()
    RUST_USE.reset()
    outcome = yield

    # Do not mask a genuine failure with our own.
    if outcome.excinfo is not None:
        return

    hits = _fallback_lines_since(offset)
    if hits:
        outcome.force_exception(AssertionError(
            "the Rust backend fell back to Python during this test, so anything "
            "it asserts about Rust is meaningless:\n  " + "\n  ".join(hits)
            + "\n(if the fallback is the point of the test, mark it with "
              "@pytest.mark.allow_rust_fallback)"
        ))
        return

    if (RUST_USE.requested and RUST_USE.loaded == 0
            and not item.get_closest_marker("allow_rust_unused")):
        outcome.force_exception(AssertionError(
            "a non-Python backend was requested but the engine never loaded a "
            "model, so this test ran entirely in Python:\n  "
            + "\n  ".join(RUST_USE.requested)
            + "\n(a backend value that is neither \"python\" nor \"rust\" takes the "
              "Python branch without logging anything)"
        ))
