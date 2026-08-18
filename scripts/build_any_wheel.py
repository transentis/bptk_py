#                                                       /`-
# _                                  _   _             /####`-
# | |                                | | (_)           /########`-
# | |_ _ __ __ _ _ __  ___  ___ _ __ | |_ _ ___       /###########`-
# | __| '__/ _` | '_ \/ __|/ _ \ '_ \| __| / __|   ____ -###########/
# | |_| | | (_| | | | \__ \  __/ | | | |_| \__ \  |    | `-#######/
# \__|_|  \__,_|_| |_|___/\___|_| |_|\__|_|___/  |____|    `- # /
#
# Copyright (c) 2018 transentis labs GmbH
# MIT License

"""Derive the pure-Python `py3-none-any` wheel from a platform wheel.

Why this exists (A.12 in docs/internal/architecture/marimo-documentation.md):
Pyodide cannot load a native extension, so `micropip.install("bptk-py")` needs a
wheel without `_rust_engine`. It has to be the *same distribution and version*
as the platform wheels, so that pip and micropip select by platform tag without
the user choosing anything.

Why derive rather than build separately: maturin has no pure-Python mode, and
the obvious alternative - a second build backend with its own pyproject.toml -
would create a second declaration of dependencies and extras that can drift from
the first. Deriving guarantees the metadata is identical because it *is* the
same metadata; only the compiled module and the tags change.

Usage:
    python scripts/build_any_wheel.py dist/bptk_py-2.4.1-cp311-abi3-macosx_11_0_arm64.whl
    python scripts/build_any_wheel.py dist/bptk_py-*.whl --out dist
"""

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

EXTENSION_GLOB = "_rust_engine*"
ANY_TAG = "py3-none-any"


def rewrite_wheel_metadata(unpacked_wheel):
    """Retag an unpacked wheel as pure Python.

    Two lines matter. `Tag` decides which installs the wheel is offered for, and
    `Root-Is-Purelib` decides whether the contents land in purelib or platlib -
    maturin sets it to false because it ships a binary, which is no longer true
    once the extension is gone.
    """
    wheel_files = list(Path(unpacked_wheel).glob("*.dist-info/WHEEL"))
    if len(wheel_files) != 1:
        raise SystemExit(f"Expected exactly one WHEEL file, found {len(wheel_files)}")

    lines = []
    seen_tag = False
    for line in wheel_files[0].read_text().splitlines():
        if line.startswith("Tag:"):
            if seen_tag:
                continue          # a multi-tag wheel collapses into the single any tag
            line = f"Tag: {ANY_TAG}"
            seen_tag = True
        elif line.startswith("Root-Is-Purelib:"):
            line = "Root-Is-Purelib: true"
        lines.append(line)

    if not seen_tag:
        raise SystemExit(f"{wheel_files[0]} carries no Tag line")

    wheel_files[0].write_text("\n".join(lines) + "\n")


def build_any_wheel(platform_wheel, out_dir):
    """Strip the compiled extension out of `platform_wheel` and retag the result."""
    platform_wheel = Path(platform_wheel).resolve()
    out_dir = Path(out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    if ANY_TAG in platform_wheel.name:
        raise SystemExit(f"{platform_wheel.name} is already a pure-Python wheel")

    with tempfile.TemporaryDirectory() as workdir:
        workdir = Path(workdir)
        subprocess.run([sys.executable, "-m", "wheel", "unpack",
                        "-d", str(workdir), str(platform_wheel)], check=True)

        unpacked = next(workdir.iterdir())

        removed = [path for path in unpacked.rglob(EXTENSION_GLOB) if path.is_file()]
        if not removed:
            # Refusing here is the point of the check: a renamed or relocated
            # extension would otherwise yield an "any" wheel that is in truth
            # platform-specific, and nothing downstream would notice until it
            # failed on a user's machine.
            raise SystemExit(
                f"No {EXTENSION_GLOB} found in {platform_wheel.name}. Either it was not built "
                "by maturin, or the extension was renamed. Not producing an 'any' wheel.")
        for path in removed:
            print(f"  removed {path.relative_to(unpacked)}")
            path.unlink()

        rewrite_wheel_metadata(unpacked)

        # wheel pack recomputes RECORD, so its hashes match the stripped content.
        subprocess.run([sys.executable, "-m", "wheel", "pack",
                        "-d", str(out_dir), str(unpacked)], check=True)

    produced = sorted(out_dir.glob(f"*-{ANY_TAG}.whl"), key=lambda p: p.stat().st_mtime)
    if not produced:
        raise SystemExit("wheel pack produced no py3-none-any wheel")
    return produced[-1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("wheel", help="a platform wheel built by maturin")
    parser.add_argument("--out", default="dist", help="output directory (default: dist)")
    args = parser.parse_args()

    print(f"Building the pure-Python wheel from {Path(args.wheel).name}")
    print(f"Built {build_any_wheel(args.wheel, args.out)}")


if __name__ == "__main__":
    main()
