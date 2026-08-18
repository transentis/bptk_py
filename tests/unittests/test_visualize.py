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
