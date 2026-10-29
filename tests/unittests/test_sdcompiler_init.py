import sys
import types
import unittest
from unittest import mock

from BPTK_Py.sdcompiler import compile_xmile


class TestSdCompilerLazyImport(unittest.TestCase):
    """The `compile_xmile` wrapper in `BPTK_Py/sdcompiler/__init__.py`.

    It exists so that the compiler stays out of the import path of `import BPTK_Py`.
    Two behaviours have to hold: importing the package pulls nothing, and the call
    reaches the real compiler.
    """

    def test_delegates_to_the_compiler(self):
        fake_compile = types.ModuleType("BPTK_Py.sdcompiler.compile")
        fake_compile.compile_xmile = mock.Mock(return_value="compiled")

        with mock.patch.dict(sys.modules,
                             {"BPTK_Py.sdcompiler.compile": fake_compile}):
            result = compile_xmile(target="py-sddsl", src="model.stmx", dest="model.py")

        self.assertEqual(result, "compiled")
        fake_compile.compile_xmile.assert_called_once_with(
            target="py-sddsl", src="model.stmx", dest="model.py")

    def test_importing_the_package_pulls_nothing(self):
        """Importing the package alone must not drag the compiler in.

        This is the property the whole wrapper exists for.
        """
        for module in list(sys.modules):
            if module.startswith("BPTK_Py.sdcompiler."):
                del sys.modules[module]

        import importlib
        importlib.reload(importlib.import_module("BPTK_Py.sdcompiler"))

        pulled = [m for m in sys.modules if m.startswith("BPTK_Py.sdcompiler.")]
        self.assertEqual(pulled, [])
