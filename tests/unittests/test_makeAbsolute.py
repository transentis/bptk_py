import os
import unittest

from BPTK_Py.sdcompiler.plugins.makeAbsolute import makeExpressionAbsolute


class TestMakeAbsolute(unittest.TestCase):
    def test_dimension_name_is_not_prefixed(self):
        """An identifier that names a dimension is left untouched (not made absolute)."""
        expr = makeExpressionAbsolute(
            "m", {"name": "countries", "type": "identifier"},
            connects={}, entity={}, dimensions={"countries": {}})
        self.assertEqual(expr["name"], "countries")

    def test_ordinary_identifier_is_made_absolute(self):
        """An ordinary identifier is prefixed with the (sanitized) model name."""
        expr = makeExpressionAbsolute(
            "m", {"name": "x", "type": "identifier"},
            connects={}, entity={}, dimensions={})
        self.assertEqual(expr["name"], "m.x")

    def test_connect_replaces_name(self):
        """A name present in the connects map is replaced by the connected target."""
        expr = makeExpressionAbsolute(
            "m", {"name": "x", "type": "identifier"},
            connects={"m.x": "other.y"}, entity={}, dimensions={})
        self.assertEqual(expr["name"], "other.y")


class TestMakeAbsoluteStandaloneImport(unittest.TestCase):
    """makeAbsolute.py carries an absolute-import fallback so it can run as a
    stand-alone script outside the BPTK_Py package. Loading it as a top-level
    module makes the relative import fail, exercising that fallback."""

    def test_standalone_import(self):
        import sys
        import importlib.util
        import BPTK_Py

        sdcompiler_dir = os.path.join(os.path.dirname(BPTK_Py.__file__), "sdcompiler")
        saved_path = list(sys.path)
        saved_modules = set(sys.modules)
        sys.path.insert(0, sdcompiler_dir)
        try:
            spec = importlib.util.spec_from_file_location(
                "standalone_makeAbsolute",
                os.path.join(sdcompiler_dir, "plugins", "makeAbsolute.py"))
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            # sanitizeName resolved through the absolute-import fallback.
            self.assertTrue(hasattr(mod, "sanitizeName"))
            self.assertTrue(hasattr(mod, "makeExpressionAbsolute"))
        finally:
            sys.path[:] = saved_path
            for name in set(sys.modules) - saved_modules:
                del sys.modules[name]


if __name__ == '__main__':
    unittest.main()
