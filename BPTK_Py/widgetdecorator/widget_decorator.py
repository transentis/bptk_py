from __future__ import print_function
import BPTK_Py.config.config as config
from BPTK_Py.logger.logger import log
from ipywidgets import interact, interactive, fixed, interact_manual
import ipywidgets as widgets


#############################
### Class widgetDecorator ###
#############################

## This class simply decorates an output of "plotScenarios" of bptk with an arbitrary amount of sliders
## Later maybe even other interactive projects
## This is the core of the interactive plotting module
class widgetDecorator():
    def __init__(self, bptk):
        self.bptk = bptk
        log("[INFO] widgetFactory created")

    # This method will be passed over to the user and used to modify the graph output

    



    def generate_sliders(self, scenario_names, equations, scenario_managers=[], kind=config.configuration["kind"],
                         alpha=config.configuration["alpha"], stacked=config.configuration["stacked"],
                         freq="D", start_date="1/1/2018", title="", visualize_from_period=0, x_label="", y_label="",
                         series_names=[], strategy=True,
                         return_df=False, constants=[("cash.cash", 0, 10), ("earnings.earnings", 0, 10)]):

        self.scenarios = self.bptk.scenario_manager_factory.get_scenarios(scenario_managers=scenario_managers,
                                                                          scenario_names=scenario_names)

        ## Only store data and create sliders and pack them
        log("[INFO] Creating slider objects for interactive plot of scenarios {}".format(str(scenario_names)))



        # Generate the slider objects
        sliders = {}
        for val in constants:
            name = val[0]
            start = val[1]
            end = val[2]

            if type(start) == float:
                slider = widgets.FloatSlider(min=start, max=end, value=(end-start)/2,description=name,style=config.configuration["slider_style"],layout=config.configuration["slider_layout"])
            else:
                slider = widgets.IntSlider(min=start, max=end, step=1, value=(end-start)/2, description=name,style=config.configuration["slider_style"],layout=config.configuration["slider_layout"])
            sliders[name] = slider

        # Actual method for building the slider objects and plotting.
        if len(sliders) ==1:

            slider_names = list(sliders.keys())
            slider_list = list(sliders.values())


            @interact(slider1=slider_list[0])
            def compute_new_plot(slider1):

                for name, scenario_obj in self.scenarios.items():
                    if not slider1 == None:
                        scenario_obj.model.equations[slider_names[0]] = lambda t: slider1




                    self.bptk.reset_simulation_model(scenario_manager=scenario_obj.group, scenario_name=name)

                self.bptk.plot_scenarios(scenario_names=scenario_names, equations=equations,
                                         scenario_managers=scenario_managers, kind=kind, alpha=alpha,
                                         stacked=stacked,
                                         freq=freq, start_date=start_date, title=title,
                                         visualize_from_period=visualize_from_period, x_label=x_label,
                                         y_label=y_label,
                                         series_names=series_names, strategy=strategy,
                                         return_df=return_df)

                return None

        if len(sliders) ==2:

            slider_names = list(sliders.keys())
            slider_list = list(sliders.values())


            @interact(slider1=slider_list[0],
                      slider2=slider_list[1],
                      )
            def compute_new_plot(slider1,slider2):

                for name, scenario_obj in self.scenarios.items():
                    if not slider1 == None:
                        scenario_obj.model.equations[slider_names[0]] = lambda t: slider1
                    if not slider2==None:
                        scenario_obj.model.equations[slider_names[1]] = lambda t: slider2



                    self.bptk.reset_simulation_model(scenario_manager=scenario_obj.group, scenario_name=name)

                self.bptk.plot_scenarios(scenario_names=scenario_names, equations=equations,
                                         scenario_managers=scenario_managers, kind=kind, alpha=alpha,
                                         stacked=stacked,
                                         freq=freq, start_date=start_date, title=title,
                                         visualize_from_period=visualize_from_period, x_label=x_label,
                                         y_label=y_label,
                                         series_names=series_names, strategy=strategy,
                                         return_df=return_df)

                return None


        if len(sliders) ==3:

            slider_names = list(sliders.keys())
            slider_list = list(sliders.values())


            @interact(slider1=slider_list[0],
                      slider2=slider_list[1],
                      slider3=slider_list[2],
                      )
            def compute_new_plot(slider1,slider2,slider3):

                for name, scenario_obj in self.scenarios.items():
                    if not slider1 == None:
                        scenario_obj.model.equations[slider_names[0]] = lambda t: slider1
                    if not slider2==None:
                        scenario_obj.model.equations[slider_names[1]] = lambda t: slider2
                    if not slider3 == None:
                        scenario_obj.model.equations[slider_names[2]] = lambda t: slider3


                    self.bptk.reset_simulation_model(scenario_manager=scenario_obj.group, scenario_name=name)

                self.bptk.plot_scenarios(scenario_names=scenario_names, equations=equations,
                                         scenario_managers=scenario_managers, kind=kind, alpha=alpha,
                                         stacked=stacked,
                                         freq=freq, start_date=start_date, title=title,
                                         visualize_from_period=visualize_from_period, x_label=x_label,
                                         y_label=y_label,
                                         series_names=series_names, strategy=strategy,
                                         return_df=return_df)

                return None



        if len(sliders) ==4:

            slider_names = list(sliders.keys())
            slider_list = list(sliders.values())


            @interact(slider1=slider_list[0],
                      slider2=slider_list[1],
                      slider3=slider_list[2],
                      slider4=slider_list[3],
                      )
            def compute_new_plot(slider1,slider2,slider3,slider4):

                for name, scenario_obj in self.scenarios.items():
                    if not slider1 == None:
                        scenario_obj.model.equations[slider_names[0]] = lambda t: slider1
                    if not slider2==None:
                        scenario_obj.model.equations[slider_names[1]] = lambda t: slider2
                    if not slider3 == None:
                        scenario_obj.model.equations[slider_names[2]] = lambda t: slider3
                    if not slider4==None:
                        scenario_obj.model.equations[slider_names[3]] = lambda t: slider4


                    self.bptk.reset_simulation_model(scenario_manager=scenario_obj.group, scenario_name=name)

                self.bptk.plot_scenarios(scenario_names=scenario_names, equations=equations,
                                         scenario_managers=scenario_managers, kind=kind, alpha=alpha,
                                         stacked=stacked,
                                         freq=freq, start_date=start_date, title=title,
                                         visualize_from_period=visualize_from_period, x_label=x_label,
                                         y_label=y_label,
                                         series_names=series_names, strategy=strategy,
                                         return_df=return_df)

                return None



        if len(sliders) ==5:

            slider_names = list(sliders.keys())
            slider_list = list(sliders.values())


            @interact(slider1=slider_list[0],
                      slider2=slider_list[1],
                      slider3=slider_list[2],
                      slider4=slider_list[3],
                      slider5=slider_list[4]
                      )
            def compute_new_plot(slider1,slider2,slider3,slider4,slider5):

                for name, scenario_obj in self.scenarios.items():
                    if not slider1 == None:
                        scenario_obj.model.equations[slider_names[0]] = lambda t: slider1
                    if not slider2==None:
                        scenario_obj.model.equations[slider_names[1]] = lambda t: slider2
                    if not slider3 == None:
                        scenario_obj.model.equations[slider_names[2]] = lambda t: slider3
                    if not slider4==None:
                        scenario_obj.model.equations[slider_names[3]] = lambda t: slider4
                    if not slider5==None:
                        scenario_obj.model.equations[slider_names[4]] = lambda t: slider5

                    self.bptk.reset_simulation_model(scenario_manager=scenario_obj.group, scenario_name=name)

                self.bptk.plot_scenarios(scenario_names=scenario_names, equations=equations,
                                         scenario_managers=scenario_managers, kind=kind, alpha=alpha,
                                         stacked=stacked,
                                         freq=freq, start_date=start_date, title=title,
                                         visualize_from_period=visualize_from_period, x_label=x_label,
                                         y_label=y_label,
                                         series_names=series_names, strategy=strategy,
                                         return_df=return_df)

                return None






