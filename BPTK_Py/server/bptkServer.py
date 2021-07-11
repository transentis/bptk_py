#                                                       /`-
# _                                  _   _             /####`-
# | |                                | | (_)           /########`-
# | |_ _ __ __ _ _ __  ___  ___ _ __ | |_ _ ___       /###########`-
# | __| '__/ _` | '_ \/ __|/ _ \ '_ \| __| / __|   ____ -###########/
# | |_| | | (_| | | | \__ \  __/ | | | |_| \__ \  |    | `-#######/
# \__|_|  \__,_|_| |_|___/\___|_| |_|\__|_|___/  |____|    `- # /
#
# Copyright (c) 2021 transentis labs GmbH
# MIT License

#from flask import Flask, redirect, url_for, request, make_response, jsonify
from flask import Flask, request, make_response
#from BPTK_Py.bptk import bptk  #not needed?
#import pandas as pd #not needed?
#import json #TODO not needed?
import copy
import uuid
#from json import JSONEncoder #TODO not needed?

class BptkServer(Flask):
    """
    This class provides a Flask-based server that provides a REST-API for running bptk scenarios. Currently only SD scenarios are supported (both SD DSL and XMILE).
    
    The class inherts the properties and methods of Flask and doesn't expose any further public methods.

    The default port of the server is 5000.
    
    Initialize the server with the import name and the bptk.

    Parameters:
        import_name: String.
            The name of the application package. Usually __name__. This helps locate the root_path for the blueprint.
        bptk: bptk Object.
            An instance of bptk that contains all relevant scenarios. These are then made available via REST endpoints.
    """
    
    def __init__(self, import_name, bptk):
        super(BptkServer, self).__init__(import_name)
        self.bptk = bptk
        self.bptk_copy = copy.deepcopy(self.bptk)
        self.instances_dict = dict()
        # specifying the routes and methods of the api
        self.route("/", methods=['GET'])(self._home_resource)
        self.route("/run", methods=['PUT','POST'], strict_slashes=False)(self._run_resource)
        self.route("/scenarios", methods=['GET'], strict_slashes=False)(self._scenarios_resource)
        self.route("/equations", methods=['PUT','POST'], strict_slashes=False)(self._equations_resource)
        self.route("/agents", methods=['PUT','POST'], strict_slashes=False)(self._agents_resource)
        #self.route("/start-instance", methods=['POST'], strict_slashes=False)(self._start_instance_resource)
        #self.route("/<instance_id>/run-step", methods=['POST', 'PUT'], strict_slashes=False)(self._run_step_resource)
        
    def _home_resource(self):
        """
        The root endpoint returns a simple html page for test purposes.

        Returns:
             Returns the HTML string "<h1>BPTK-Py REST API Server</h1>".

        """
        return "<h1>BPTK-Py REST API Server</h1>"

    def _run_resource(self):
        """Runs a s set of scenarios with given settings and returns the results.

        You can override the scenario settings, thus allowing interactive simulations.

        This endpoint runs the scenario through all timesteps.

        Parameters:
            scenario managers: List.
                JSON list of scenario managers that should be run.
            scenarios: List.
                JSON list of scenarios that should be run.
            equations: List.
                JSON list of equations that data should be retrieved for.
            settings: Dictionary.
                JSON dictionary that has scenario managers as the key. For each scenario manager there is a dictionary of scenarios, which contains a dictionary of constants and their settings.
        
        Returns:
            A JSON dictionary that contains the simulation results ordered by scenario_manager, scenario, equations. The equations dictionary contains the timesteps as keys with the simulation results as values.
        """
 
        
        self.logger.info("Request is JSON: {}".format(request.is_json))
        self.logger.info("Request is JSON: {}".format(request.data))

        if not request.is_json:
            resp = make_response('{"error": "please pass the request with content-type application/json"}',500)
            resp.headers['Content-Type'] = 'application/json'
            resp.headers['Access-Control-Allow-Origin']='*'
            return resp

        content = request.get_json()

        try:
            settings = content["settings"]
        
            for scenario_manager_name, scenario_manager_data in settings.items():
                for scenario_name, scenario_settings in scenario_manager_data.items():
                    scenario = self.bptk.get_scenario(scenario_manager_name,scenario_name)
                    if "constants" in scenario_settings:
                        constants = scenario_settings["constants"]
                        for constant_name, constant_settings in constants.items():
                            scenario.constants[constant_name]=constant_settings
                    if "points" in scenario_settings:
                        points = scenario_settings["points"]
                        for points_name, points_settings in points.items():
                            scenario.points[points_name]=points_settings
                    self.bptk.reset_scenario_cache(scenario_manager=scenario_manager_name,scenario=scenario_name)
        except KeyError:
            self.logger.info("Settings not specified")
            pass


        try:
            scenario_managers=content["scenario_managers"]
        except KeyError:
            resp = make_response('{"error": "expecting scenario_managers to be set"}',500)
            resp.headers['Content-Type']='application/json'
            resp.headers['Access-Control-Allow-Origin']='*'
            return resp

        try:
            scenarios=content["scenarios"]
        except KeyError:
            resp = make_response('{"error": "expecting scenario_managers to be set"}',500)
            resp.headers['Content-Type']='application/json'
            resp.headers['Access-Control-Allow-Origin']='*'
            return resp

        try:
            equations=content["equations"]
        except KeyError:
            resp = make_response('{"error": "expecting equations to be set"}',500)
            resp.headers['Content-Type']='application/json'
            resp.headers['Access-Control-Allow-Origin']='*'
            return resp


        result = self.bptk.run_scenarios(
              scenario_managers=scenario_managers,
              scenarios=scenarios,
              equations=equations,
              return_format="json"
            )

        if result is not None:
            resp = make_response(result, 200)
        else:
            resp = make_response('{"error": "no data was returned from simulation"}', 500)

        resp.headers['Content-Type'] = 'application/json'
        resp.headers['Access-Control-Allow-Origin']='*'
        return resp
    
    def _scenarios_resource(self):
        """Returns all available scenarios for the current simulation.

        Returns:
            A JSON dictionary containing the scenario manager names as keys and a list of scenario names as the values. 

        """

        scenarios = self.bptk.get_scenario_names(format="dict")

        if not scenarios:
            resp = make_response('{"error": "expecting the model to have scenarios"}',500)
            resp.headers['Content-Type'] = 'application/json'
            resp.headers['Access-Control-Allow-Origin']='*'
            return resp
        
        resp = make_response(scenarios, 200)

        return resp
    
    def _equations_resource(self):
        """Returns all available equations given the name of a scenario manager and of a scenario.

        Parameters:
            A JSON dictionary with the keys "scenarioManager" and "scenario".

        Returns:
            A JSON dictionary with the keys "constants", "converters","flows", "points" and "stocks". Each key contains a list of the scenario's equations.

        """
        
        if not request.is_json:
            resp = make_response('{"error": "please pass the request with content-type application/json"}',500)
            resp.headers['Content-Type'] = 'application/json'
            resp.headers['Access-Control-Allow-Origin']='*'
            return resp
    
        content = request.get_json()
        
        try:
            scenario_manager_name = content["scenarioManager"]
        except KeyError:
            resp = make_response('{"error": "expecting scenarioManager to be set"}',500)
            resp.headers['Content-Type']='application/json'
            resp.headers['Access-Control-Allow-Origin']='*'
            return resp
        
        try:
            scenario_name = content["scenario"]
        except KeyError:
            resp = make_response('{"error": "expecting scenario to be set"}',500)
            resp.headers['Content-Type']='application/json'
            resp.headers['Access-Control-Allow-Origin']='*'
            return resp
            
  
        scenario = self.bptk.get_scenario(scenario_manager_name,scenario_name)

        equations_names = {}
        stocks_names = set()
        flows_names = set()
        converters_names = set()
        constants_names = set()
        points_names = set()        

        for equation in sorted(scenario.model.stocks):
            stocks_names.add(equation)
        for equation in sorted(scenario.model.flows):
            flows_names.add(equation)
        for equation in sorted(scenario.model.converters):
            converters_names.add(equation)
        for equation in sorted(scenario.model.constants):
            constants_names.add(equation)
        for equation in sorted(scenario.model.points):
            points_names.add(equation)

        equations_names["stocks"] = [name for name in stocks_names]
        equations_names["flows"] = [name for name in flows_names]
        equations_names["converters"] = [name for name in converters_names]
        equations_names["constants"] = [name for name in constants_names]
        equations_names["points"] = [name for name in points_names]

        if equations_names is not None:
            resp = make_response(equations_names, 200)
        else:
            resp = make_response('{"error": "no data was returned from simulation"}', 500)

        return resp
    
    def _agents_resource(self):
        
        if not request.is_json:
            resp = make_response('{"error": "please pass the request with content-type application/json"}',500)
            resp.headers['Content-Type'] = 'application/json'
            resp.headers['Access-Control-Allow-Origin']='*'
            return resp
        
        content = request.get_json()
        try:
            scenario_manager_name = content["scenarioManager"]
        except KeyError:
            resp = make_response('{"error": "expecting scenarioManager to be set"}',500)
            resp.headers['Content-Type']='application/json'
            resp.headers['Access-Control-Allow-Origin']='*'
            return resp
        
        try:
            scenario_name = content["scenario"]
        except KeyError:
            resp = make_response('{"error": "expecting scenario to be set"}',500)
            resp.headers['Content-Type']='application/json'
            resp.headers['Access-Control-Allow-Origin']='*'
            return resp

        scenario = self.bptk.get_scenario(scenario_manager_name,scenario_name)
        
        if not scenario.model.agents: # Checking if the model has agents
            resp = make_response('{"error": "expecting the model to have agents"}',500)
            resp.headers['Content-Type'] = 'application/json'
            resp.headers['Access-Control-Allow-Origin']='*'
            return resp
        
        agents_dict = dict()

        for agent in scenario.model.agents:
            agent_name = agent.agent_type
            agent_state = agent.state
            agents_dict[agent_name] = {}
            agents_dict[agent_name]["states"] = [agent_state]
            agent_properties = list(agent.properties.keys())
            agents_dict[agent_name]["properties"] = agent_properties
            
        if agents_dict is not None:
            resp = make_response(agents_dict, 200)
        else:
            resp = make_response('{"error": "no data was returned from simulation"}', 500)

        return resp
 
    def _start_instance_resource(self):
        """
        This endpoint starts a new instance of BPTK on the server side, so that simulations can run in a "private" session. The endpoint returns an instance_id, which is needed to identify the instance in later calls.
        """
        
        # Create a universally unique identifier in hex to store 
        cloned_bptk_uuid = uuid.uuid1().hex
        
        self.instances_dict[cloned_bptk_uuid] = self.bptk_copy
        
        if cloned_bptk_uuid is not None:
            resp = make_response(cloned_bptk_uuid, 200)
        else:
            resp = make_response('{"error": "no data was returned from simulation"}', 500)

        return resp
    
    def _run_step_resource(self, instance_id):
        """
        This endpoint advances the relevant scenarios by one timestep and returns the data for that timestep.
        """
        
        if not request.is_json:
            resp = make_response('{"error": "please pass the request with content-type application/json"}',500)
            resp.headers['Content-Type'] = 'application/json'
            resp.headers['Access-Control-Allow-Origin']='*'
            return resp

        content = request.get_json()

        try:
            settings = content["settings"]

            for scenario_manager_name, scenario_manager_data in settings.items():
                for scenario_name, scenario_settings in scenario_manager_data.items():
                    scenario = self.bptk.get_scenario(scenario_manager_name,scenario_name)
                    if "constants" in scenario_settings:
                        constants = scenario_settings["constants"]
                        for constant_name, constant_settings in constants.items():
                            scenario.constants[constant_name]=constant_settings
                    if "points" in scenario_settings:
                        points = scenario_settings["points"]
                        for points_name, points_settings in points.items():
                            scenario.points[points_name]=points_settings
                    self.bptk.reset_scenario_cache(scenario_manager=scenario_manager_name,scenario=scenario_name)
        except KeyError:
            self.logger.info("Settings not specified")
            pass
        
        try:
            scenario_managers=content["scenario_managers"]
        except KeyError:
            resp = make_response('{"error": "expecting scenario_managers to be set"}',500)
            resp.headers['Content-Type']='application/json'
            resp.headers['Access-Control-Allow-Origin']='*'
            return resp

        try:
            scenarios=content["scenarios"]
        except KeyError:
            resp = make_response('{"error": "expecting scenario_managers to be set"}',500)
            resp.headers['Content-Type']='application/json'
            resp.headers['Access-Control-Allow-Origin']='*'
            return resp

        try:
            equations=content["equations"]
        except KeyError:
            resp = make_response('{"error": "expecting equations to be set"}',500)
            resp.headers['Content-Type']='application/json'
            resp.headers['Access-Control-Allow-Origin']='*'
            return resp
        
        # getting the results for the first time step only
        result = self.bptk.plot_scenarios(
              scenario_managers=scenario_managers,
              scenarios=scenarios,
              equations=equations,
              visualize_to_period = 1,
              return_df=True
            )

        if result is not None:
            resp = make_response(result.to_json(), 200)
        else:
            resp = make_response('{"error": "no data was returned from simulation"}', 500)

        resp.headers['Content-Type'] = 'application/json'
        resp.headers['Access-Control-Allow-Origin']='*'
        return resp