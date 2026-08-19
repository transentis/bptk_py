"""Tests for the dependency layout itself.

The ordinary suite runs against the working tree with everything installed, so
it cannot see a packaging mistake: a dependency declared in the wrong group, an
extra silently dropped from CI, or a module-level import that pulls an optional
package back into `import BPTK_Py`. These tests cover that seam.

What they cannot cover is what a wheel actually contains - that needs a clean
venv and belongs in CI.
"""

import subprocess
import sys
import textwrap
import tomllib
from pathlib import Path

import pytest


PYPROJECT = Path(__file__).resolve().parent.parent / "pyproject.toml"

EXPECTED_BASE = {"pandas", "scipy", "numpy", "tqdm", "xlsxwriter", "jsonpickle"}

EXPECTED_EXTRAS = {
    "plotting": {"matplotlib"},
    "xmile": {"parsimonious", "xmltodict", "jinja2"},
    "server": {"flask", "psycopg", "redis"},
    "observability": {"logfire"},
}

# Optional packages that must never be reached by `import BPTK_Py`, even when
# they are installed. flask, jinja2, psycopg, redis and logfire are absent from
# this list on purpose: BptkServer and the state adapters are exported eagerly
# from BPTK_Py/__init__.py, so installing those extras does put them in the
# import path. Only the install shrinks, not the import.
MUST_STAY_LAZY = ["matplotlib", "parsimonious", "xmltodict"]


def _requirement_name(requirement):
    """The distribution name out of a requirement string.

    "psycopg[binary,pool]==3.3.2" -> "psycopg"
    """
    for separator in ("[", "==", ">=", "<=", "~=", ">", "<", ";", " "):
        requirement = requirement.split(separator)[0]
    return requirement.strip().lower()


@pytest.fixture(scope="module")
def pyproject():
    if not PYPROJECT.is_file():
        pytest.skip("pyproject.toml not available - running against an install")
    with PYPROJECT.open("rb") as handle:
        return tomllib.load(handle)


class TestDependencyGroups:
    def test_base_dependencies_are_the_agreed_set(self, pyproject):
        declared = {_requirement_name(r) for r in pyproject["project"]["dependencies"]}
        assert declared == EXPECTED_BASE

    def test_extras_are_the_agreed_set(self, pyproject):
        extras = pyproject["project"]["optional-dependencies"]
        assert set(extras) == set(EXPECTED_EXTRAS) | {"test"}

        for extra, expected in EXPECTED_EXTRAS.items():
            declared = {_requirement_name(r) for r in extras[extra]}
            assert declared == expected, f"extra [{extra}] drifted"

    def test_no_optional_package_leaks_into_the_base(self, pyproject):
        base = {_requirement_name(r) for r in pyproject["project"]["dependencies"]}
        for extra, packages in EXPECTED_EXTRAS.items():
            leaked = base & packages
            assert not leaked, f"{leaked} belongs in [{extra}], not in the base install"

    def test_test_extra_covers_every_extra(self, pyproject):
        """Otherwise CI quietly stops exercising whichever extra was forgotten."""
        test_extra = " ".join(pyproject["project"]["optional-dependencies"]["test"])
        for extra in EXPECTED_EXTRAS:
            assert extra in test_extra, f"[{extra}] is not covered by the test extra"


class TestChangelog:
    """The release gate.

    The changelog lives in README.md rather than a CHANGELOG.md, deliberately:
    GitHub renders the README on the repository landing page, so that is where
    it stays visible. It is also the only copy - the one on the documentation
    site is generated from it as of Release B.

    Implemented as a test rather than a separate CI step because publishing is
    already gated on the suite, so this gates it too.
    """

    @staticmethod
    def _readme():
        readme = PYPROJECT.parent / "README.md"
        if not readme.is_file():
            pytest.skip("README.md not available - running against an install")
        return readme.read_text()

    def test_version_has_a_changelog_entry(self, pyproject):
        version = pyproject["project"]["version"]
        assert f"### {version}" in self._readme(), (
            f"pyproject.toml declares {version}, but README.md has no '### {version}' "
            f"changelog entry. Add one before releasing.")

    def test_changelog_section_exists(self):
        """A rename would make the check above vacuous rather than failing."""
        assert "## Changelog" in self._readme()


class TestImportStaysLazy:
    """`import BPTK_Py` must not pull the optional packages it can defer.

    Runs in a subprocess: the test process has already imported everything, so
    checking `sys.modules` in-process would prove nothing.
    """

    @staticmethod
    def _modules_after_import():
        script = textwrap.dedent("""
            import sys
            import BPTK_Py
            print("\\n".join(sorted({m.split(".")[0] for m in sys.modules})))
        """)
        result = subprocess.run([sys.executable, "-c", script],
                                capture_output=True, text=True, check=True)
        return set(result.stdout.split())

    @pytest.mark.parametrize("package", MUST_STAY_LAZY)
    def test_optional_package_is_not_imported(self, package):
        pytest.importorskip(package, reason=f"{package} not installed - nothing to prove")
        assert package not in self._modules_after_import(), (
            f"{package} is reachable from `import BPTK_Py`; a module-level import "
            f"crept back in and the extra it belongs to can no longer be optional")

    def test_the_package_itself_still_imports(self):
        assert "BPTK_Py" in self._modules_after_import()


class TestMissingExtrasExplainThemselves:
    """The user-facing behaviour of a base install, checked in a subprocess.

    Blocking the import inside the running interpreter is not enough for
    BptkServer: which class `BPTK_Py.BptkServer` refers to is decided while
    BPTK_Py is imported, so the block has to be in place beforehand.
    """

    # Kept as a flat string rather than an indented block: the body is spliced
    # in at column zero, so any dedent gymnastics here would fight with it.
    PREAMBLE = (
        "import sys\n"
        "class _Blocker:\n"
        "    def __init__(self, names):\n"
        "        self.names = names\n"
        "    def find_spec(self, name, path=None, target=None):\n"
        "        if name.split('.')[0] in self.names:\n"
        "            raise ImportError('blocked for test: ' + name)\n"
        "        return None\n"
        "sys.meta_path.insert(0, _Blocker({blocked!r}))\n"
        "import BPTK_Py\n"
    )

    @classmethod
    def _run_with_blocked(cls, blocked, body):
        script = cls.PREAMBLE.format(blocked=set(blocked)) + textwrap.dedent(body).strip() + "\n"
        return subprocess.run([sys.executable, "-c", script],
                              capture_output=True, text=True)

    def test_server_extra_missing(self):
        result = self._run_with_blocked(["flask"], """
            try:
                BPTK_Py.BptkServer(__name__, None)
                print("NO ERROR")
            except ImportError as error:
                print(error)
                print("CAUSE:", error.__cause__)
        """)
        assert result.returncode == 0, result.stderr
        assert "bptk-py[server]" in result.stdout
        # The stub catches every ImportError raised while loading the server, so
        # the original has to survive - otherwise a real failure inside
        # bptkServer.py would be reported as a missing extra.
        assert "flask" in result.stdout

    @pytest.mark.parametrize("adapter", ["PostgresAdapter", "RedisAdapter"])
    def test_state_adapters_name_the_server_extra(self, adapter):
        """psycopg and redis ship as [server], so that is what the stubs must name."""
        result = self._run_with_blocked(["psycopg", "redis"], """
            from BPTK_Py.externalstateadapter import {adapter}
            try:
                {adapter}()
                print("NO ERROR")
            except ImportError as error:
                print(error)
        """.format(adapter=adapter))
        assert result.returncode == 0, result.stderr
        assert "bptk-py[server]" in result.stdout

    def test_plotting_extra_missing(self):
        result = self._run_with_blocked(["matplotlib"], """
            model = BPTK_Py.Model(starttime=1, stoptime=3, dt=1, name="m")
            constant = model.constant("constant")
            constant.equation = 1.0
            print(len(constant.plot(return_df=True)), "rows without matplotlib")
            try:
                constant.plot()
                print("NO ERROR")
            except ImportError as error:
                print(error)
        """)
        assert result.returncode == 0, result.stderr
        assert "3 rows without matplotlib" in result.stdout
        assert "bptk-py[plotting]" in result.stdout

    def test_xmile_extra_missing(self):
        result = self._run_with_blocked(["parsimonious"], """
            from BPTK_Py.sdcompiler import compile_xmile
            try:
                compile_xmile(target="py", src="a.stmx", dest="a.py")
                print("NO ERROR")
            except ImportError as error:
                print(error)
        """)
        assert result.returncode == 0, result.stderr
        assert "bptk-py[xmile]" in result.stdout

    def test_observability_extra_missing(self):
        result = self._run_with_blocked(["logfire"], """
            import BPTK_Py.logger.logger as logmod
            try:
                logmod.configure_logfire(environment="test", send_to_logfire=False)
                print("NO ERROR")
            except ImportError as error:
                print(error)
        """)
        assert result.returncode == 0, result.stderr
        assert "bptk-py[observability]" in result.stdout

    def test_base_install_still_simulates(self):
        """Blocking every extra must leave the actual product working."""
        result = self._run_with_blocked(
            ["matplotlib", "flask", "parsimonious", "xmltodict", "logfire"], """
            model = BPTK_Py.Model(starttime=0.0, stoptime=10.0, dt=1.0, name="base")
            stock = model.stock("population")
            flow = model.flow("growth")
            rate = model.constant("rate")
            stock.initial_value = 100.0
            rate.equation = 0.1
            flow.equation = stock * rate
            stock.equation = flow
            print(round(model.evaluate_equation("population", 10.0), 4))
        """)
        assert result.returncode == 0, result.stderr
        assert result.stdout.strip() == "259.3742"
