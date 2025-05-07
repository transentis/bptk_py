import unittest
from unittest.mock import Mock, MagicMock, patch

from BPTK_Py import Model, bptk
from BPTK_Py.scenariomanager.scenario import SimulationScenario

from BPTK_Py.visualizations.simple_dashboard import ScenarioWidget, SimpleDashboard, ModelConnection

import ipywidgets as widgets


class DummyWidget:
    def __init__(self):
        self.value = 0
        self.observe_called = False

    def observe(self, handler, names):
        self.observe_called = True
        self.handler = handler
        self.names = names

class TestScenarioWidget(unittest.TestCase):
    def setUp(self):
        pass

    def test_init(self):
        widget = DummyWidget()
        widget.value = 100
        trigger = lambda: None
        scenario_widget = ScenarioWidget(widget=widget, element="test_element", trigger=trigger)

        self.assertEqual(scenario_widget.multiply,1.0)
        self.assertEqual(scenario_widget.widget.value, 100)
        self.assertIsNone(scenario_widget.points)
        self.assertEqual(scenario_widget.element,"test_element")
        self.assertEqual(scenario_widget.trigger,trigger)
        self.assertIsNone(scenario_widget.pre_trigger)
        self.assertEqual(scenario_widget.new_value,"None")
        self.assertTrue(widget.observe_called)

    def test_event_handler(self):
        widget = DummyWidget()

        pre_trigger = MagicMock()
        trigger = MagicMock()

        scenario_widget = ScenarioWidget(widget=widget, element="test_element", trigger=trigger, pre_trigger=pre_trigger)

        change = MagicMock()
        change.new = 55

        scenario_widget._event_handler(change)

        pre_trigger.assert_called_once_with(55)
        trigger.assert_called_once()
        self.assertEqual(scenario_widget.new_value, 55)

    def test_set_scenario_value(self):
        widget = DummyWidget()
        widget.value = 10
        
        scenario1 = SimulationScenario(dictionary={}, name="scenario1", model=Model(), scenario_manager_name="testManager")
        scenario_widget1 = ScenarioWidget(widget=widget, element=None, trigger=lambda: None)
        scenario_widget1.set_scenario_value(scenario1)
        self.assertEqual(scenario_widget1.new_value,10)
        self.assertEqual(scenario1.constants,{})
        self.assertEqual(scenario1.points,{})

        scenario2 = SimulationScenario(dictionary={}, name="scenario2", model=Model(), scenario_manager_name="testManager")
        scenario_widget2 = ScenarioWidget(widget=widget, element="test_element",trigger=lambda: None, multiply=2)
        scenario_widget2.set_scenario_value(scenario2)
        self.assertEqual(scenario_widget2.new_value,10)
        self.assertEqual(scenario2.constants["test_element"],20)
        self.assertEqual(scenario2.points,{})

        dict = {"points": {"test_element": [[0, 0], [1, 0], [2, 0]]}}
        scenario3 = SimulationScenario(dictionary=dict, name="scenario1", model=Model(), scenario_manager_name="testManager")
        scenario_widget3 = ScenarioWidget(widget=widget, element="test_element",trigger=lambda: None, multiply=3, points=[0, 1])
        scenario_widget3.set_scenario_value(scenario3)
        self.assertEqual(scenario_widget3.new_value,10)
        self.assertEqual(scenario3.constants,{})
        self.assertEqual(scenario3.points['test_element'][0][1], 30.0)
        self.assertEqual(scenario3.points['test_element'][1][1], 30.0)
        self.assertEqual(scenario3.points['test_element'][2][1], 0)

class TestSimpleDashboard(unittest.TestCase):
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
                            "constant":2.0
                        }
                    }                    
                }, 
            scenario_manager = "testManager") 

    def test_init(self):
        dashboard = SimpleDashboard(bptk=self.testBptk, scenario_manager="testManager", scenario="1")

        self.assertEqual(dashboard.style,{})
        self.assertEqual(dashboard.layout,{})
        self.assertEqual(dashboard.bptk,self.testBptk)
        self.assertEqual(dashboard.scenario_manager,"testManager")
        self.assertEqual(dashboard.scenario,"1")
        self.assertEqual(dashboard.widget_array,[])
        self.assertEqual(dashboard.outputs,[])

    def test_add_plot(self):
        dashboard = SimpleDashboard(bptk=self.testBptk, scenario_manager="testManager", scenario="1")

        output = dashboard.add_plot(
            equations=["stock"], 
            title="test", 
            names=["testStock"], 
            x_label="Time", 
            y_label="Units", 
            kind="line",
            visualize_from_period=0,
            visualize_to_period=5)

        self.assertIsInstance(output, widgets.Output)
       
        self.assertEqual(len(dashboard.outputs), 1)
        plot_data = dashboard.outputs[0]['data']
        self.assertEqual(plot_data["equations"], ["stock"])
        self.assertEqual(plot_data["title"], "test")
        self.assertEqual(plot_data["kind"], "line")
        self.assertEqual(plot_data["x_label"], "Time")
        self.assertEqual(plot_data["y_label"], "Units")
        self.assertEqual(plot_data["start_date"],"")
        self.assertEqual(plot_data["visualize_from_period"], 0)
        self.assertEqual(plot_data["visualize_to_period"], 5)
        self.assertEqual(plot_data["freq"], "D")
        self.assertEqual(plot_data["agents"],[])
        self.assertEqual(plot_data["agent_states"],[])
        self.assertEqual(plot_data["agent_properties"],[])
        self.assertEqual(plot_data["agent_property_types"],[])
        self.assertEqual(plot_data["series_names"]["testManager_1_stock"], "testStock")

    def test_add_custom_plot(self):
        def dummy_plot():
            pass

        dashboard = SimpleDashboard(bptk=self.testBptk, scenario_manager="testManager", scenario="1")

        output = dashboard.add_custom_plot(dummy_plot)

        self.assertIsInstance(output, widgets.Output)

        self.assertEqual(len(dashboard.outputs), 1)
        self.assertIs(dashboard.outputs[0]['plot_function'], dummy_plot)      

    def test_update_plot_data(self):
        dashboard = SimpleDashboard(bptk=self.testBptk, scenario_manager="testManager", scenario="1")
        dashboard.add_plot(
            equations=["stock"], 
            title="test", 
            names=["testStock"], 
            x_label="Time", 
            y_label="Units", 
            kind="line",
            visualize_from_period=0,
            visualize_to_period=5)

        dashboard.update_plot_data(attribute="visualize_from_period", value=1, plot=-1)
        dashboard.update_plot_data(attribute="visualize_to_period",value=6, plot=0)

        plot_data = dashboard.outputs[0]['data']
        self.assertEqual(plot_data["visualize_from_period"], 1)
        self.assertEqual(plot_data["visualize_to_period"], 6)

    def test_update_plot_data_invalid(self):
        def dummy_plot():
            pass

        dashboard = SimpleDashboard(bptk=self.testBptk, scenario_manager="testManager", scenario="1")
        dashboard.add_custom_plot(dummy_plot)

        #Redirect the console output
        import sys, io
        old_stdout = sys.stdout
        new_stdout = io.StringIO()
        sys.stdout = new_stdout 

        dashboard.update_plot_data(attribute="invalid", value="test", plot=0)

        #Remove the redirection of the console output
        sys.stdout = old_stdout
        output = new_stdout.getvalue()

        self.assertIn("Can't update plot data of a custom plot!", output) 

    def test_update(self):
        dashboard1 = SimpleDashboard(bptk=self.testBptk, scenario_manager="testManager", scenario="1")
        widget = widgets.IntSlider(value=5)
        dashboard1.add_widget(widget=widget, model_connection="constant")
        dashboard1.add_plot(
            equations=["stock"], 
            title="test", 
            names=["testStock"], 
            x_label="Time", 
            y_label="Units", 
            kind="line",
            visualize_from_period=0,
            visualize_to_period=5)

        with patch('matplotlib.pyplot.show') as mock_show:
            dashboard1._update()
            assert mock_show.called

        updated_scenario = self.testBptk.get_scenario("testManager", "1")
        self.assertEqual(updated_scenario.constants["constant"],5)            

        #plot function
        dummy_plot = Mock()
        dashboard2 = SimpleDashboard(bptk=self.testBptk, scenario_manager="testManager", scenario="1")
        dashboard2.add_custom_plot(dummy_plot)

        dashboard2._update()
        dummy_plot.assert_called_once()

    def test_start(self):
        dashboard = SimpleDashboard(bptk=self.testBptk, scenario_manager="testManager", scenario="1")
        dashboard.add_plot(
            equations=["stock"], 
            title="test", 
            names=["testStock"], 
            x_label="Time",
            y_label="Units", 
            kind="line",
            visualize_from_period=0,
            visualize_to_period=5)

        with patch('matplotlib.pyplot.show') as mock_show:
            dashboard.start()
            assert mock_show.called

    def test_add_widget(self):
        dashboard = SimpleDashboard(bptk=self.testBptk, scenario_manager="testManager", scenario="1")

        widget = widgets.IntSlider()
        dashboard.add_widget(widget=widget, model_connection="test")

        self.assertEqual(len(dashboard.widget_array), 1)
        scenario_widget = dashboard.widget_array[0]
        self.assertIsInstance(scenario_widget, ScenarioWidget)
        self.assertEqual(scenario_widget.element, "test")
        self.assertEqual(scenario_widget.widget, widget)
        self.assertEqual(scenario_widget.trigger, dashboard._update)

    def test_add_model_widget(self):
        #Callable
        dashboard1 = SimpleDashboard(bptk=self.testBptk, scenario_manager="testManager", scenario="1")
        
        widget = widgets.IntSlider()
        dummy_callable = Mock()
        dashboard1.add_widget(widget=widget,model_connection=dummy_callable)

        self.assertEqual(len(dashboard1.widget_array), 1)
        scenario_widget1 = dashboard1.widget_array[0]
        self.assertIsInstance(scenario_widget1, ScenarioWidget)
        self.assertIsNone(scenario_widget1.element)
        self.assertEqual(scenario_widget1.widget, widget)
        self.assertEqual(scenario_widget1.trigger, dashboard1._update)
        self.assertEqual(scenario_widget1.pre_trigger, dummy_callable)

        #ModelConnection
        dashboard2 = SimpleDashboard(bptk=self.testBptk, scenario_manager="testManager", scenario="1")

        model_conn = ModelConnection(element="test", points=[0, 1], multiply=2.0, call=dummy_callable)
        dashboard2.add_widget(widget, model_conn)

        self.assertEqual(len(dashboard2.widget_array), 1)
        scenario_widget2 = dashboard2.widget_array[0]
        self.assertIsInstance(scenario_widget2, ScenarioWidget)
        self.assertEqual(scenario_widget2.element, model_conn.element)
        self.assertEqual(scenario_widget2.points, model_conn.points)
        self.assertEqual(scenario_widget2.multiply, model_conn.multiply)
        self.assertEqual(scenario_widget2.pre_trigger, model_conn.call)
        self.assertEqual(scenario_widget2.trigger, dashboard2._update)

if __name__ == '__main__':
    unittest.main()
