import sys
import types
import unittest
from unittest import mock

from BPTK_Py.sdcompiler import compile_xmile, XMILE_EXTRA_HINT


class TestSdCompilerLazyImport(unittest.TestCase):
    """The `compile_xmile` wrapper in `BPTK_Py/sdcompiler/__init__.py`.

    It exists so that parsimonious, xmltodict and jinja2 stay out of the import
    path of `import BPTK_Py` - they ship as the optional `bptk-py[xmile]` extra.
    Two behaviours have to hold: the call reaches the real compiler when the
    extra is installed, and it explains itself when it is not.
    """

    def test_delegates_to_the_compiler(self):
        fake_compile = types.ModuleType("BPTK_Py.sdcompiler.compile")
        fake_compile.compile_xmile = mock.Mock(return_value="compiled")

        with mock.patch.dict(sys.modules,
                             {"BPTK_Py.sdcompiler.compile": fake_compile}):
            result = compile_xmile(target="py", src="model.stmx", dest="model.py")

        self.assertEqual(result, "compiled")
        fake_compile.compile_xmile.assert_called_once_with(
            target="py", src="model.stmx", dest="model.py")

    def test_missing_extra_names_the_extra(self):
        """A missing dependency must yield an instruction, not a traceback about parsers."""
        # A None entry in sys.modules makes the import statement raise ImportError,
        # which is what an uninstalled parsimonious looks like from here.
        with mock.patch.dict(sys.modules, {"BPTK_Py.sdcompiler.compile": None}):
            with self.assertRaises(ImportError) as raised:
                compile_xmile(target="py", src="model.stmx", dest="model.py")

        self.assertEqual(str(raised.exception), XMILE_EXTRA_HINT)
        self.assertIn("bptk-py[xmile]", str(raised.exception))
        # The original failure stays reachable for debugging.
        self.assertIsInstance(raised.exception.__cause__, ImportError)

    def test_importing_the_package_pulls_nothing(self):
        """Importing the package alone must not drag the compiler in.

        This is the property the whole wrapper exists for; without it the extra
        cannot be optional.
        """
        for module in list(sys.modules):
            if module.startswith("BPTK_Py.sdcompiler."):
                del sys.modules[module]

        import importlib
        importlib.reload(importlib.import_module("BPTK_Py.sdcompiler"))

        pulled = [m for m in sys.modules if m.startswith("BPTK_Py.sdcompiler.")]
        self.assertEqual(pulled, [])


if __name__ == "__main__":
    unittest.main()
