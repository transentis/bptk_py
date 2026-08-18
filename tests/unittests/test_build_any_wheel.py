import subprocess
import sys
import unittest
from unittest import mock
import zipfile
from pathlib import Path
from tempfile import TemporaryDirectory

SCRIPTS = Path(__file__).resolve().parent.parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))

from build_any_wheel import (ANY_TAG, build_any_wheel, main,  # noqa: E402
                             rewrite_wheel_metadata)


def _make_platform_wheel(target_dir, with_extension=True, tag="cp311-abi3-macosx_11_0_arm64"):
    """Assemble a minimal wheel that looks like one of maturin's.

    Building a real one would need maturin and a Rust toolchain; what the script
    actually cares about is the layout - a package directory, a compiled module
    and a dist-info with a WHEEL file.
    """
    Path(target_dir).mkdir(parents=True, exist_ok=True)   # wheel pack does not create it

    with TemporaryDirectory() as staging:
        unpacked = Path(staging) / "demo-1.0"
        package = unpacked / "demo"
        dist_info = unpacked / "demo-1.0.dist-info"
        package.mkdir(parents=True)
        dist_info.mkdir(parents=True)

        (package / "__init__.py").write_text("value = 1\n")
        if with_extension:
            (package / "_rust_engine.abi3.so").write_bytes(b"\x7fELF fake")

        (dist_info / "METADATA").write_text(
            "Metadata-Version: 2.4\nName: demo\nVersion: 1.0\n"
            "Provides-Extra: plotting\n")
        (dist_info / "WHEEL").write_text(
            "Wheel-Version: 1.0\nGenerator: maturin (1.13.1)\n"
            f"Root-Is-Purelib: false\nTag: {tag}\n")

        subprocess.run([sys.executable, "-m", "wheel", "pack",
                        "-d", str(target_dir), str(unpacked)],
                       check=True, capture_output=True)

    return next(Path(target_dir).glob("*.whl"))


class TestBuildAnyWheel(unittest.TestCase):
    """The derivation of the browser wheel (A.12).

    The `any` wheel has to be the same distribution and version as the platform
    wheels, differing only in the missing extension and the tags - that is what
    lets pip and micropip pick the right one without the user choosing.
    """

    def setUp(self):
        self._tmp = TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def test_produces_a_pure_python_wheel(self):
        source = _make_platform_wheel(self.tmp / "in")
        produced = build_any_wheel(source, self.tmp / "out")

        self.assertTrue(produced.name.endswith(f"-{ANY_TAG}.whl"))
        with zipfile.ZipFile(produced) as archive:
            names = archive.namelist()
            wheel_file = archive.read("demo-1.0.dist-info/WHEEL").decode()

        self.assertFalse([n for n in names if "_rust_engine" in n],
                         "the compiled extension must not survive")
        self.assertIn(f"Tag: {ANY_TAG}", wheel_file)
        self.assertIn("Root-Is-Purelib: true", wheel_file)

    def test_metadata_is_carried_over_untouched(self):
        """The reason for deriving rather than rebuilding: one source of metadata."""
        source = _make_platform_wheel(self.tmp / "in")
        with zipfile.ZipFile(source) as archive:
            before = archive.read("demo-1.0.dist-info/METADATA")

        produced = build_any_wheel(source, self.tmp / "out")
        with zipfile.ZipFile(produced) as archive:
            after = archive.read("demo-1.0.dist-info/METADATA")

        self.assertEqual(before, after)

    def test_record_is_recomputed(self):
        """A stale RECORD would make pip reject the wheel as corrupt."""
        source = _make_platform_wheel(self.tmp / "in")
        produced = build_any_wheel(source, self.tmp / "out")

        with zipfile.ZipFile(produced) as archive:
            record = archive.read("demo-1.0.dist-info/RECORD").decode()

        self.assertNotIn("_rust_engine", record)
        self.assertIn("demo/__init__.py", record)

    def test_refuses_a_wheel_without_an_extension(self):
        """The failure that would otherwise reach PyPI unnoticed.

        A renamed or relocated extension would silently yield an 'any' wheel
        that is in truth platform-specific, and it would only fail on a user's
        machine.
        """
        source = _make_platform_wheel(self.tmp / "in", with_extension=False)

        with self.assertRaises(SystemExit) as raised:
            build_any_wheel(source, self.tmp / "out")

        self.assertIn("_rust_engine", str(raised.exception))
        self.assertEqual(list((self.tmp / "out").glob("*.whl")), [])

    def test_refuses_an_any_wheel_as_input(self):
        source = _make_platform_wheel(self.tmp / "in", tag=ANY_TAG)

        with self.assertRaises(SystemExit) as raised:
            build_any_wheel(source, self.tmp / "out")

        self.assertIn("already", str(raised.exception))

    def test_collapses_multiple_tags(self):
        unpacked = self.tmp / "demo-1.0"
        dist_info = unpacked / "demo-1.0.dist-info"
        dist_info.mkdir(parents=True)
        (dist_info / "WHEEL").write_text(
            "Wheel-Version: 1.0\nRoot-Is-Purelib: false\n"
            "Tag: cp311-abi3-manylinux_2_17_x86_64\n"
            "Tag: cp311-abi3-manylinux2014_x86_64\n")

        rewrite_wheel_metadata(unpacked)

        tags = [line for line in (dist_info / "WHEEL").read_text().splitlines()
                if line.startswith("Tag:")]
        self.assertEqual(tags, [f"Tag: {ANY_TAG}"])

    def test_rejects_a_wheel_without_a_tag(self):
        unpacked = self.tmp / "demo-1.0"
        dist_info = unpacked / "demo-1.0.dist-info"
        dist_info.mkdir(parents=True)
        (dist_info / "WHEEL").write_text("Wheel-Version: 1.0\n")

        with self.assertRaises(SystemExit):
            rewrite_wheel_metadata(unpacked)

    def test_rejects_a_wheel_without_metadata(self):
        """A dist-info that does not hold exactly one WHEEL file is not a wheel."""
        unpacked = self.tmp / "demo-1.0"
        (unpacked / "demo-1.0.dist-info").mkdir(parents=True)

        with self.assertRaises(SystemExit) as raised:
            rewrite_wheel_metadata(unpacked)

        self.assertIn("WHEEL", str(raised.exception))

    def test_command_line(self):
        """The entry point CI and publish.sh actually call."""
        source = _make_platform_wheel(self.tmp / "in")
        out = self.tmp / "out"

        with mock.patch.object(sys, "argv",
                               ["build_any_wheel.py", str(source), "--out", str(out)]):
            main()

        self.assertEqual(len(list(out.glob(f"*-{ANY_TAG}.whl"))), 1)


if __name__ == "__main__":
    unittest.main()
