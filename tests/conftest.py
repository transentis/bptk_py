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


# Log messages the bptk layers emit when they give up on the Rust engine and
# compute in Python instead. Each of these means "the Rust engine did not run".
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

    The fallback is a production feature: when the engine cannot load or run a
    model, bptk logs a [WARN] and computes in Python, so results stay correct.
    In tests it is a trap - a parity test that compares "python" against a "rust"
    run that never happened compares Python with Python and passes for the wrong
    reason. That is how the delay-cycle limitation stayed hidden until 2026-08-11
    (see docs/internal/architecture/rust-engine-delay-cycle-issue.md).

    Tests that exercise the fallback on purpose opt out with
    ``@pytest.mark.allow_rust_fallback``.

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
