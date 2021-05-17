#                                                       /`-
# _                                  _   _             /####`-
# | |                                | | (_)           /########`-
# | |_ _ __ __ _ _ __  ___  ___ _ __ | |_ _ ___       /###########`-
# | __| '__/ _` | '_ \/ __|/ _ \ '_ \| __| / __|   ____ -###########/
# | |_| | | (_| | | | \__ \  __/ | | | |_| \__ \  |    | `-#######/
# \__|_|  \__,_|_| |_|___/\___|_| |_|\__|_|___/  |____|    `- # /
#
# Copyright (c) 2019 transentis labs GmbH
# MIT License

from flask import Flask, redirect, url_for, request, make_response, jsonify
from BPTK_Py.bptk import bptk 
import pandas as pd
import json

######################
##  REST API CLASS  ##
######################


class BptkServer(Flask):
    """
    A bptkServer for running different bptk simulations. The class inherts the properties and methods of flask to run a rest api for any bptk simulation.
    """
    
    def __init__(self, import_name, bptk):
        """
        Initialize the server with the import name and the bptk.
        :param import_name: the name of the application package. Usually __name__. This helps locate the root_path for the blueprint.
        :param bptk: simulations made by the bptk.
        """
        super(BptkServer, self).__init__(import_name)
        self.bptk = bptk
        # specifying the routes and methods of the api
        self.route("/", methods=['GET'])(self.home_resource)
        self.route("/run", methods=['POST', 'PUT'], strict_slashes=False)(self.run_resource)
        self.route("/scenarios", methods=['GET'], strict_slashes=False)(self.scenarios_resource)
        self.route("/equations", methods=['POST'], strict_slashes=False)(self.equations_resource)
        self.route("/agents", methods=['POST', 'PUT'], strict_slashes=False)(self.agents_resource)
        
        
    def home_resource(self):
        return "<h1>BPTK-Py Simulation Service</h1>"

    def run_resource(self):
        
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
                    constants = scenario_settings["constants"]
                    for constant_name, constant_settings in constants.items():
                        scenario.constants[constant_name]=constant_settings
                    points = scenario_settings["points"]
                    for points_name, points_settings in points.items():
                        scenario.points[points_name]=points_settings
                    self.bptk.reset_simulation_model(scenario_manager=scenario_manager_name,scenario=scenario_name)

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


        result = self.bptk.plot_scenarios(
              scenario_managers=scenario_managers,
              scenarios=scenarios,
              equations=equations,
              return_df=True
            )

        if result is not None:
            resp = make_response(result.to_json(), 200)
        else:
            resp = make_response('{"error": "no data was returned from simulation"}', 500)

        resp.headers['Content-Type'] = 'application/json'
        resp.headers['Access-Control-Allow-Origin']='*'
        return resp
    
    def scenarios_resource(self):
        """
        The method gets all the available scenarios for the current simulation.
        """
        scenarions = []
        
        if not self.bptk.get_scenarios():
            resp = make_response('{"error": "expecting the model to have scenarios"}',500)
            resp.headers['Content-Type'] = 'application/json'
            resp.headers['Access-Control-Allow-Origin']='*'
            return resp
            
        for scenario in self.bptk.get_scenarios():
            scenarions.append(scenario)
        scenarions = jsonify(scenarions)

        if scenarions is not None:
            resp = make_response(scenarions, 200)
        else:
            resp = make_response('{"error": "no data was returned from simulation"}', 500)

        return resp
    
    def equations_resource(self):
        """
        Given a current scneario manager and a scenario_name, the equations method gets us all available equations for them.
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
    
    def agents_resource(self):
        
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