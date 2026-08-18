// Runs the BPTK suite inside Pyodide - the browser as a fourth platform (A.28).
//
// The source tree is mounted rather than a wheel installed, mirroring the
// editable install the other three platforms use. The Rust engine is absent by
// construction, which tests/conftest.py handles: it drops what cannot run here
// (no threads, no subprocesses, no compiled engine) and skips nothing anywhere
// else.
//
//   node scripts/run_suite_in_pyodide.mjs [path-to-repo]
//
// Needs `npm install pyodide` first; `just test-browser` does both.
import { resolve } from "node:path";

// Pyodide narrates every wheel it fetches - a screenful before the first test,
// repeated on every run. Filtered rather than silenced: anything it says that is
// not this bookkeeping still gets through, and errors are untouched.
const bookkeeping = /^(Didn't find package |Package .+ loaded from |Loading |Loaded )/;
const passThrough = console.log;
console.log = (...args) => {
  if (typeof args[0] === "string" && bookkeeping.test(args[0])) return;
  passThrough(...args);
};

// Imported dynamically, i.e. after the filter above is in place: Pyodide binds
// console.log when its module is evaluated, so a static import would capture the
// original and print regardless.
const { loadPyodide } = await import("pyodide");

// Resolved, because mountNodeFS hands the path to Emscripten as-is and a
// relative one depends on a working directory Pyodide does not share.
const repo = resolve(process.argv[2] ?? process.cwd());
passThrough("Mounting", repo, "at /src");

const py = await loadPyodide();
py.mountNodeFS("/src", repo);

// Provided by Pyodide itself; the rest comes from PyPI below.
await py.loadPackage(["micropip", "numpy", "pandas", "scipy", "matplotlib", "pytest"],
                     { messageCallback: () => {} });

// Installing and testing are two calls so that stdout can be filtered for the
// first and left alone for the second: micropip reports progress through Python's
// stdout, and the callback fires per write rather than per line - which would put
// every one of pytest's progress dots on a line of its own.
py.setStdout({ batched: (line) => { if (!bookkeeping.test(line)) passThrough(line); } });

// Wrapped in Python's own try/except: an exception escaping runPythonAsync
// surfaces as a 60 KB dump of the Pyodide module, which says nothing about what
// actually failed.
const installed = await py.runPythonAsync(`
import sys, os, traceback

async def install():
    import tomllib
    import micropip

    with open("/src/pyproject.toml", "rb") as handle:
        project = tomllib.load(handle)["project"]

    # Taken from pyproject.toml, not from a second list here: an unpinned
    # xmltodict silently dropped stocks from compiled XMILE models until 3.0.0.
    wanted = list(project["dependencies"])
    for extra in ("plotting", "xmile"):
        wanted += project["optional-dependencies"][extra]

    # Pyodide ships these itself, and its builds are the only ones that work here.
    provided = {"pandas", "numpy", "scipy", "matplotlib"}
    requirements = [r for r in wanted
                    if r.split("=")[0].split("[")[0].strip() not in provided]

    print("Installing from PyPI:", ", ".join(requirements), flush=True)
    await micropip.install(requirements)

    sys.path.insert(0, "/src")
    os.chdir("/src")
    return 0

try:
    result = await install()
except BaseException:
    print()
    print("Installing the dependencies failed:", flush=True)
    traceback.print_exc()
    result = 99
result
`).catch(reportJsFailure);

py.setStdout();   // back to the default, so pytest formats its own output

const exitCode = Number(installed) !== 0 ? installed : await py.runPythonAsync(`
import traceback
try:
    import pytest
    result = pytest.main(["--no-header", "-p", "no:cacheprovider"])
except BaseException:
    print()
    print("pytest could not run:", flush=True)
    traceback.print_exc()
    result = 99
result
`).catch(reportJsFailure);

console.log();
console.log("pytest exit code:", exitCode);
process.exit(Number(exitCode) === 0 ? 0 : 1);

function reportJsFailure(error) {
  // A JavaScript-level failure - Pyodide itself, the mount, the CDN.
  console.error();
  console.error("Pyodide failed to run the suite:");
  console.error(error?.message ?? error);
  return 98;
}
