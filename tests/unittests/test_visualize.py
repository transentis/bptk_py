import sys
import unittest
from unittest.mock import patch, MagicMock

from BPTK_Py import Model, bptk
from BPTK_Py.visualizations.visualize import (visualizer, require_matplotlib,
                                              PLOTTING_EXTRA_HINT)

import pandas as pd
import matplotlib.pyplot as plt
import statistics

class TestVisualizer(unittest.TestCase):
    def setUp(self):
        model = Model(starttime=1, stoptime=10, dt=1, name='test')

        stock = model.stock("stock")
        flow = model.flow("flow")
        constant = model.constant("constant")

        stock.initial_value=0.0

        stock.equation = flow
        flow.equation = constant
        constant.equation = 1.0

        self.testBptk = bptk()
        self.testBptk.register_scenario_manager({"testManager": {"model": model}})

        self.testBptk.register_scenarios(
            scenarios=
                {
                    "1":
                    {
                        "constants":
                        {
                            "constant":1.0
                        }
                    },
                    "2":
                    {
                        "constants":
                        {
                            "constant":100.0
                        }
                    }                    
                }, 
            scenario_manager = "testManager") 

    def test_plot(self):
        ##start_date maintained
        result = self.testBptk.plot_scenarios(
            scenario_managers=["testManager"],
            scenarios=["1"],
            equations=["stock"],
            visualize_from_period=2,
            visualize_to_period=10,
            start_date="01/01/2018",
            return_df=True
        )        

        self.assertIsInstance(result.index, pd.DatetimeIndex)
        self.assertEqual(result.index[0],pd.to_datetime("01/03/2018"))
        self.assertEqual(result.index[1],pd.to_datetime("01/04/2018"))
        self.assertEqual(result.index[7],pd.to_datetime("01/10/2018"))

        ##return_df=false, not plot_data
        #Redirect the console output
        import sys, io
        old_stdout = sys.stdout
        new_stdout = io.StringIO()
        sys.stdout = new_stdout 

        result = self.testBptk.plot_scenarios(
            scenario_managers=["testManager"],
            scenarios=["1"],
            equations=["stock"],
            visualize_from_period=2,
            visualize_to_period=2      
        )

        #Remove the redirection of the console output
        sys.stdout = old_stdout
        output = new_stdout.getvalue()

        self.assertIn("[INFO] No data to plot for period t=2 to t=2", output)         
        self.assertIsNone(result)

        ##return_df=false, visualize_to > len(df)
        result = self.testBptk.plot_scenarios(
            scenario_managers=["testManager"],
            scenarios=["1"],
            equations=["stock"],
            visualize_from_period=2,
            visualize_to_period=15
        )

        self.assertIsNone(result)

        ##return_df=true, not plot_data
        #Redirect the console output
        old_stdout = sys.stdout
        new_stdout = io.StringIO()
        sys.stdout = new_stdout 

        result = self.testBptk.plot_scenarios(
            scenario_managers=["testManager"],
            scenarios=["1"],
            equations=["stock"],
            visualize_from_period=2,
            visualize_to_period=2,
            return_df=True     
        )

        #Remove the redirection of the console output
        sys.stdout = old_stdout
        output = new_stdout.getvalue()

        self.assertIn("[INFO] No data for period t=3 to t=3", output)         
        self.assertIsNone(result)

        ##return_df=true, visualize_to > len(df)
        result = self.testBptk.plot_scenarios(
            scenario_managers=["testManager"],
            scenarios=["1"],
            equations=["stock"],
            visualize_from_period=2,
            visualize_to_period=15,
            return_df=True
        )

        self.assertEqual(len(result),8)

    def test_label_format(self):
        # y_tick: mean <=2 
        self.testBptk.plot_scenarios(
            scenario_managers=["testManager"],
            scenarios=["1"],
            equations=["stock"],
            visualize_from_period=0,
            visualize_to_period=2
        )

        ax = plt.gca()
        formatter = ax.yaxis.get_major_formatter()

        self.assertEqual(formatter(1.2345,None),str(1.23))

        # y_tick: 2<= mean <=10
        self.testBptk.plot_scenarios(
            scenario_managers=["testManager"],
            scenarios=["1"],
            equations=["stock"],
            visualize_from_period=0,
            visualize_to_period=5
        )

        ax = plt.gca()
        formatter = ax.yaxis.get_major_formatter()

        self.assertEqual(formatter(1.2345,None),str(1.2))        

        # y_tick: mean > 10
        self.testBptk.plot_scenarios(
            scenario_managers=["testManager"],
            scenarios=["2"],
            equations=["stock"],
            visualize_from_period=0,
            visualize_to_period=2
        )

        ax = plt.gca()
        formatter = ax.yaxis.get_major_formatter()

        self.assertEqual(formatter(1.2345,None),str(1))

    def test_plot_returns_axes(self):
        """With format="axes" the plot returns the matplotlib Axes object."""
        import matplotlib.axes
        df = pd.DataFrame({"stock": [1.0, 2.0, 3.0]}, index=[1.0, 2.0, 3.0])

        ax = self.testBptk.visualizer.plot(
            df=df, return_df=False, visualize_from_period=0, visualize_to_period=0,
            stacked=False, kind="line", title="t", alpha=1.0, x_label="", y_label="",
            format="axes",
        )

        self.assertIsInstance(ax, matplotlib.axes.Axes)

    def test_plot_sets_the_axis_labels_it_is_given(self):
        """`x_label` and `y_label` are only applied when non-empty, and nothing ran that.

        Every other test passes empty strings, so the two `if` branches that put a label
        on the chart were never taken - the arguments could have stopped working without
        a single test noticing.
        """
        df = pd.DataFrame({"stock": [1.0, 2.0, 3.0]}, index=[1.0, 2.0, 3.0])

        ax = self.testBptk.visualizer.plot(
            df=df, return_df=False, visualize_from_period=0, visualize_to_period=0,
            stacked=False, kind="line", title="t", alpha=1.0,
            x_label="time", y_label="units", format="axes",
        )

        self.assertEqual(ax.get_xlabel(), "time")
        self.assertEqual(ax.get_ylabel(), "units")

    def test_plot_with_axes_registers_no_figure(self):
        """The registry-free Figure, which had no test of its own.

        Fixed in the code since August; the property it guarantees was never asserted,
        so nothing would have noticed it being undone. Its twin lives in
        test_element.py - the two paths into `df.plot()` need the same guard.
        """
        import matplotlib.pyplot as plt
        df = pd.DataFrame({"stock": [1.0, 2.0, 3.0]}, index=[1.0, 2.0, 3.0])

        plt.close("all")
        before = set(plt.get_fignums())

        for _ in range(5):
            self.testBptk.visualizer.plot(
                df=df, return_df=False, visualize_from_period=0, visualize_to_period=0,
                stacked=False, kind="line", title="t", alpha=1.0, x_label="", y_label="",
                format="axes",
            )

        self.assertEqual(set(plt.get_fignums()), before)

    def _configured_bptk(self, manager, configuration=None):
        model = Model(starttime=1, stoptime=4, dt=1, name="colours")
        stock = model.stock("headcount")
        stock.initial_value = 10.0
        flow = model.flow("hiring")
        flow.equation = 1.0
        stock.equation = flow

        instance = bptk(configuration=configuration) if configuration else bptk()
        instance.register_scenario_manager({manager: {"model": model}})
        instance.register_scenarios(scenarios={"base": {}}, scenario_manager=manager)
        return instance

    @staticmethod
    def _first_series_colour(instance, manager):
        axes = instance.plot_scenarios(scenario_managers=[manager], scenarios=["base"],
                                       equations=["headcount"], format="axes")
        return axes.get_lines()[0].get_color()

    def test_a_configuration_reaches_the_instance_it_was_given_to(self):
        instance = self._configured_bptk("own_look",
                                         {"colors": ["#ff0000"], "kind": "line"})

        self.assertEqual(self._first_series_colour(instance, "own_look"), "#ff0000")

    def test_a_configuration_does_not_reach_the_next_instance(self):
        """Two cells of a notebook used to restyle each other.

        `bptk(configuration=...)` wrote into the package-wide configuration, so whichever
        instance was built last decided how all of them looked - the symptom the move off
        `plt.rcParams` was meant to remove, arriving through `colors` and `kind` instead.
        """
        from BPTK_Py.visualizations import plotting_config

        self._configured_bptk("loud_look", {"colors": ["#ff0000"], "kind": "line"})
        plain = self._configured_bptk("plain_look")

        drawn = self._first_series_colour(plain, "plain_look")
        self.assertNotEqual(drawn, "#ff0000")
        self.assertEqual(drawn, plotting_config["colors"][0])

    def test_an_instance_starts_from_the_package_wide_look(self):
        """Set the look once for the process and everything built after it follows."""
        from BPTK_Py.visualizations import plotting_config

        plotting_config.reset()
        try:
            plotting_config.update({"colors": ["#00ff00"], "kind": "line"})
            instance = self._configured_bptk("inherited_look")

            self.assertEqual(self._first_series_colour(instance, "inherited_look"),
                             "#00ff00")
        finally:
            plotting_config.reset()

    def test_a_later_package_wide_change_leaves_a_built_instance_alone(self):
        """The notebook guarantee: a cell's look does not change under it.

        An instance takes the package-wide look when it is built and keeps it. Reading
        the object at drawing time instead is what made the same cell look different
        depending on which cell had been run before it.
        """
        from BPTK_Py.visualizations import plotting_config

        plotting_config.reset()
        try:
            instance = self._configured_bptk("built_early")
            before = self._first_series_colour(instance, "built_early")

            plotting_config.update({"colors": ["#00ff00"], "kind": "line"})

            self.assertEqual(self._first_series_colour(instance, "built_early"), before)
        finally:
            plotting_config.reset()

    def test_a_configuration_leaves_the_package_wide_one_alone(self):
        from BPTK_Py.visualizations import plotting_config

        # From the package defaults, so that what is compared is not a colour an
        # earlier test already wrote into the same object
        plotting_config.reset()
        before = dict(plotting_config.settings)

        try:
            self._configured_bptk("quiet_look",
                                  {"colors": ["#123456"], "kind": "line"})
            self.assertEqual(dict(plotting_config.settings), before)
        finally:
            plotting_config.reset()

    def test_element_plot_still_follows_the_package_wide_configuration(self):
        """It has no `bptk()` in reach, so the package-wide one is what it can read."""
        from BPTK_Py.visualizations import plotting_config

        model = Model(starttime=1, stoptime=4, dt=1, name="element_look")
        stock = model.stock("headcount")
        stock.initial_value = 10.0
        flow = model.flow("hiring")
        flow.equation = 1.0
        stock.equation = flow

        try:
            plotting_config.update({"colors": ["#0000ff"], "kind": "line"})
            axes = stock.plot(format="axes")
            self.assertEqual(axes.get_lines()[0].get_color(), "#0000ff")
        finally:
            plotting_config.reset()

    def test_plotting_config_update_of_nothing_keeps_the_settings(self):
        """`update(None)` and `update({})` are no-ops rather than resets.

        The scenario runners hand their configuration straight through, and most of them
        have none.
        """
        from BPTK_Py.visualizations import PlottingConfig

        config = PlottingConfig()
        before = dict(config.settings), dict(config.matplotlib_rc_settings)

        config.update(None)
        config.update({})

        self.assertEqual((dict(config.settings), dict(config.matplotlib_rc_settings)), before)

    def test_series_names_warns_about_a_key_that_matches_nothing(self):
        """A key that renames nothing used to do so in silence.

        A column of a multi-scenario result is called `manager_scenario_equation`, so a
        key naming a manager the call does not use renames nothing and the chart keeps
        its raw column name. Seven such keys sat in the documentation for months.
        """
        import BPTK_Py.logger.logger as logmod

        df = pd.DataFrame({"sm_base_stock": [1.0, 2.0]}, index=[1.0, 2.0])

        with open(logmod.logfile, "w", encoding="UTF-8") as file:
            pass
        self.testBptk.visualizer.plot(
            df=df, return_df=True, visualize_from_period=0, visualize_to_period=0,
            stacked=False, kind="line", title="t", alpha=1.0, x_label="", y_label="",
            series_names={"anderer_manager_base_stock": "Stock"},
        )
        with open(logmod.logfile, "r", encoding="UTF-8") as file:
            content = file.read()
        self.assertIn("matched no column", content)
        self.assertIn("anderer_manager_base_stock", content)

    def test_series_names_stays_quiet_when_every_key_matches(self):
        import BPTK_Py.logger.logger as logmod

        df = pd.DataFrame({"sm_base_stock": [1.0, 2.0]}, index=[1.0, 2.0])

        with open(logmod.logfile, "w", encoding="UTF-8") as file:
            pass
        result = self.testBptk.visualizer.plot(
            df=df, return_df=True, visualize_from_period=0, visualize_to_period=0,
            stacked=False, kind="line", title="t", alpha=1.0, x_label="", y_label="",
            series_names={"sm_base_stock": "Stock"},
        )
        with open(logmod.logfile, "r", encoding="UTF-8") as file:
            content = file.read()
        self.assertNotIn("matched no column", content)
        self.assertIn("Stock", list(result.columns))


class TestPlottingExtraGuard(unittest.TestCase):
    """matplotlib ships as `bptk-py[plotting]`.

    Plotting runs through `df.plot()`, so an absent matplotlib would otherwise
    surface as an ImportError from inside pandas. `require_matplotlib` turns it
    into an instruction. A None entry in `sys.modules` makes the import
    statement raise, which is what an uninstalled matplotlib looks like here.
    """

    def test_require_matplotlib_passes_when_installed(self):
        require_matplotlib()  # must not raise - the suite installs the extra

    def test_require_matplotlib_names_the_extra(self):
        with patch.dict(sys.modules, {"matplotlib": None}):
            with self.assertRaises(ImportError) as raised:
                require_matplotlib()

        self.assertEqual(str(raised.exception), PLOTTING_EXTRA_HINT)
        self.assertIn("bptk-py[plotting]", str(raised.exception))
        self.assertIsInstance(raised.exception.__cause__, ImportError)

    def test_visualizer_plot_guards_the_plotting_branch(self):
        df = pd.DataFrame({"stock": [1.0, 2.0, 3.0]}, index=[1.0, 2.0, 3.0])

        with patch.dict(sys.modules, {"matplotlib": None}):
            with self.assertRaises(ImportError) as raised:
                visualizer(config=bptk().config).plot(
                    df=df, return_df=False, visualize_from_period=0,
                    visualize_to_period=0, stacked=False, kind="line", title="t",
                    alpha=1.0, x_label="", y_label="")

        self.assertIn("bptk-py[plotting]", str(raised.exception))

    def test_dataframe_branch_needs_no_matplotlib(self):
        """`return_df=True` is what a headless server calls - it must not be guarded."""
        df = pd.DataFrame({"stock": [1.0, 2.0, 3.0]}, index=[1.0, 2.0, 3.0])

        with patch.dict(sys.modules, {"matplotlib": None}):
            result = visualizer(config=bptk().config).plot(
                df=df, return_df=True, visualize_from_period=0,
                visualize_to_period=0, stacked=False, kind="line", title="t",
                alpha=1.0, x_label="", y_label="")

        self.assertEqual(len(result), 3)

    def test_element_plot_guards_only_the_plotting_branch(self):
        model = Model(starttime=1, stoptime=3, dt=1, name="guard")
        constant = model.constant("constant")
        constant.equation = 1.0

        with patch.dict(sys.modules, {"matplotlib": None}):
            self.assertEqual(len(constant.plot(return_df=True)), 3)

            with self.assertRaises(ImportError) as raised:
                constant.plot()

        self.assertIn("bptk-py[plotting]", str(raised.exception))


if __name__ == '__main__':
    unittest.main()
