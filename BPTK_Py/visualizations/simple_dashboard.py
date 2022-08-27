from dataclasses import dataclass
import dataclasses
from typing import Callable, List, Union
import matplotlib.pyplot as plt
from ipywidgets import interact
import ipywidgets as widgets
from enum import Enum

class ScenarioWidget:
    def _event_handler(self, change):
        self.new_value = change.new
        if(self.pre_trigger != None):
            self.pre_trigger(change.new)
        self.trigger()


    def __init__(self, widget, element, trigger, points=None, multiply=1.0, pre_trigger=None):
        self.multiply = multiply
        self.widget = widget
        self.points = points
        self.element = element
        self.trigger = trigger
        self.pre_trigger = pre_trigger
        self.new_value = "None"
        widget.observe(self._event_handler, names="value")
 
    def set_scenario_value(self, scenario):
        if self.new_value == "None":
            self.new_value=self.widget.value

        if(self.element == None):
            return

        if self.points == None:
            scenario.constants[self.element] = self.new_value * self.multiply
        else:
            for p in self.points:
                scenario.points[self.element][p][1] = self.new_value * self.multiply


@dataclasses.dataclass
class ModelConnection:
    """
    Defines the connection of a widget to the model. When the dashboard updates all widgets update the model with their current values.

    Arguments:
        element: string
            The element of the model the widget is connected to. If points is not set, it defaults to a model constant, otherwise it uses a model points.
        points: string - Optional
            A list of points indices to update.
        multiply: int - Optional
            Multiply the widget value by this amount.
        call: Callable - Optional
            Reference to function that gets called when the value of this widget is changed.
    """
    element: str
    points: List[int] = None
    multiply: float = 1.0
    call: Callable = None

class SimpleDashboard:
    def __init__(self, bptk, scenario_manager, scenario, style = {}, layout = {}):
        """
        Arguments:
            bptk: bptk
                Reference to bptk.
            scenario_manager: string
                The scenario manager to plot.
            scenario: string
                The scenario to plot.
            style: dictionary - Optional
                The style used for widgets.
            layout: dictionary - Optional
                The layout used for widgets.
        """
        self.style = style
        self.layout = layout
        self.bptk = bptk
        self.scenario_manager = scenario_manager
        self.scenario = scenario
        self.widget_array = []
        self.outputs = []

    def update_plot_data(self, attribute: str, value: str, plot: int):
        """
        Arguments:
            attribute: string
                The attribute of the plot that will be updated.
            value: string
                The value the attribute will be set to.
            plot: int
                The plot id to update. Plot ids are returned when plots are added to the dashboard using the add_plot function.
                If plot < 0, all plots that contain the attribute will be updated.
        """
        if(plot < 0):
            for output in self.outputs:
                if('data' in output):
                    output['data'][attribute] = value
        else:
            if('data' in self.outputs[plot]):
                self.outputs[plot]['data'][attribute] = value
            else:
                print("Can't update plot data of a custom plot!")

    def _update(self):
        scenario = self.bptk.get_scenario(self.scenario_manager,self.scenario)
        self.bptk.reset_scenario_cache(scenario_manager=self.scenario_manager, scenario=self.scenario)

        for w in self.widget_array:
            w.set_scenario_value(scenario)

        for output in self.outputs:
            output['output'].clear_output(wait=True)

        for output in self.outputs:
            with output['output']:
                plt.ioff()
                if('data' in output):
                    self.bptk.plot_scenarios(
                        scenario_managers=[self.scenario_manager],
                        scenarios=[self.scenario],
                        equations=output['data']['equations'],
                        title=output['data']['title'],
                        kind=output['data']['kind'],
                        x_label=output['data']['x_label'],
                        y_label=output['data']['y_label'],
                        start_date=output['data']['start_date'],
                        visualize_from_period=output['data']['visualize_from_period'],
                        visualize_to_period=output['data']['visualize_to_period'],
                        freq=output['data']['freq'],
                        agents=output['data']['agents'],
                        agent_states=output['data']['agent_states'],
                        agent_properties=output['data']['agent_properties'],
                        agent_property_types=output['data']['agent_property_types'],
                        series_names=output['data']['series_names'],
                    )
                    plt.show()
                else:
                    output['plot_function']()
                plt.ion()  


    def start(self):
        """
        Starts the dashboard. Call this at the end of the script.
        """
        self._update()

    def add_plot(self, equations: List[str], title: str, names: List[str], x_label = "",
                 y_label = "", start_date = "", kind: str = None, visualize_from_period = 0, visualize_to_period = 0, 
                 freq = "D", agents: List[str] = [], agent_states: List[str] = [], agent_properties: List[str] = [],
                 agent_property_types: List[str] = []
    ) -> int:
        """
        Wrapper function for bptk.plot_scenarios.
        Args:
            equations: List.
                Names of equations to plot (System Dynamics, SD).
            title: String.
                Title of plot
            names: List
                Names of equations. Used to map equation names to human readable names.
            x_label: String.
                Label for x axis.
            y_label: String.
                Label for y axis.
            start_date: String.
                Start date for time series.
            kind: String.
                Type of graph to plot ("line" or "area").
            visualize_from_period: Integer
                Visualize from specific period onwards.
            visualize_to_period: Integer
                Visualize until a specific period.
            freq: String.
                Frequency of time series. Uses the pandas offset aliases. 
            agents: List.
                List of agents to plot (Agent based modeling).
            agent_states: List:
                List of agent states to plot, REQUIRES "AGENTS" param
            agent_properties: List.
                List of agent properties to plot, REQUIRES "AGENTS" param
            agent_property_types: List.
                List of agent property types to plot, REQUIRES "AGENTS" param
                
        Returns:
            Plot id (used for identification when plot data is updated).
        """
        series_names = dict()

        for i in range(len(equations)):
            series_names[self.scenario_manager + "_" + self.scenario + "_" + equations[i]] = names[i]


        output = widgets.Output()
        self.outputs.append({'output': output, 'data': {
            'equations': equations,
            'title': title,
            'kind': kind,
            'x_label': x_label,
            'y_label': y_label,
            'start_date': start_date,
            'visualize_from_period': visualize_from_period,
            'visualize_to_period': visualize_to_period,
            'freq': freq,
            'agents': agents,
            'agent_states': agent_states,
            'agent_properties': agent_properties,
            'agent_property_types': agent_property_types,
            'series_names': series_names
        }})

        return output

    def add_custom_plot(self, plot: Callable) -> widgets.Output:
        """
        Adds custom plot. Plotting must be handeled in the function.
        Args:
            equations: Callable
                Reference to function that plots.        
        
        Returns:
            widgets.Output: The output the plot gets drawn on.
        """
        output = widgets.Output()
        self.outputs.append({'output': output, 'plot_function': plot})

        return output

    def add_widget(self, widget, model_connection: Union[str, ModelConnection, Callable, None] = None):
        """
        Add any custom widget to the dashboard

        Args:
            widget: Widget
            model_connection: Union[str, ModelConnection, Callable, None] - Optional
                The connection this widget has to the model. Can either be a direct connection to a constant using a string, a ModelConnection or a Callable, that gets called when the widget updates.
        """
        if(model_connection != None):
            self._add_model_widget(widget, model_connection)

    def _add_model_widget(self, widget, model_connection: Union[str, ModelConnection, Callable]):
        if(isinstance(model_connection, str)):
            self.widget_array.append(ScenarioWidget(widget, model_connection, self._update))
        elif(isinstance(model_connection, Callable)):
            self.widget_array.append(ScenarioWidget(widget, None, self._update, pre_trigger=model_connection))
        else:
            self.widget_array.append(ScenarioWidget(widget, model_connection.element, self._update, model_connection.points, model_connection.multiply, pre_trigger=model_connection.call))
    