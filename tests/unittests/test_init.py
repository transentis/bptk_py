import importlib
import unittest
from unittest import mock

import BPTK_Py
from BPTK_Py.bptk import bptk


class TestPackageInit(unittest.TestCase):
    def test_instantiate_returns_bptk(self):
        """The package-level instantiate() helper returns a bptk instance."""
        self.assertIsInstance(BPTK_Py.instantiate(), bptk)

    def test_version_falls_back_to_unavailable(self):
        """If the installed package version cannot be resolved, __version__ falls
        back to "UNAVAILABLE"."""
        try:
            with mock.patch("importlib.metadata.version", side_effect=Exception("not installed")):
                importlib.reload(BPTK_Py)
            self.assertEqual(BPTK_Py.__version__, "UNAVAILABLE")
        finally:
            # Restore the real module state for the rest of the test session.
            importlib.reload(BPTK_Py)


    def test_plotting_config_is_reachable_as_a_package_attribute(self):
        """`BPTK_Py.plotting_config` imports the visualization module on first use.

        The attribute is served by the module's own `__getattr__` rather than an import
        at the top, so that a headless install without the plotting extra can still
        `import BPTK_Py` - it only fails if someone asks for this.
        """
        from BPTK_Py.visualizations import plotting_config, PlottingConfig

        self.assertIs(BPTK_Py.plotting_config, plotting_config)
        self.assertIs(BPTK_Py.PlottingConfig, PlottingConfig)

    def test_an_attribute_the_package_does_not_have_raises(self):
        with self.assertRaises(AttributeError):
            BPTK_Py.no_such_attribute


if __name__ == '__main__':
    unittest.main()
