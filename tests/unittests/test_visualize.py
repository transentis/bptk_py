import unittest
from unittest.mock import patch, MagicMock

from BPTK_Py import Model, bptk
from BPTK_Py.visualizations.visualize import visualizer

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

if __name__ == '__main__':
    unittest.main()
