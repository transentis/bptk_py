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

from flask import Flask, redirect, url_for, request, make_response, jsonify
from BPTK_Py.bptk import bptk
import pandas as pd
import json
import copy
import uuid
import datetime
from json import JSONEncoder


class InstanceManager:
    """
    The class is used to manipulate instances for storing cloned instances, and checking for the session timeout.
    """
    def __init__(self, bptk):
        self.bptk = bptk
        self.instances_dict = dict()
        self.bptk_copy = copy.deepcopy(self.bptk)

    def store_instance(self):
        """
        The method generates a universally unique identifier in hexadecimal, that is used as key for the instances.

        Returns:
            cloned_bptk_uuid: str.
                The uuid value generated for the current instance.
        """

        cloned_bptk_uuid = uuid.uuid1().hex
        self.instances_dict[cloned_bptk_uuid] = dict()
        self.instances_dict[cloned_bptk_uuid]["instance"] = self.bptk_copy
        self.instances_dict[cloned_bptk_uuid]["time"] = dict()

        return cloned_bptk_uuid

    def is_instance_timeout(self):
        """
        The method checks for the session timeout, and deletes the instance if it is.

        Returns:
            True: Boolean.
                Means that the specified time has already passed, and the session should be terminated.
        """

        timeout = datetime.timedelta(minutes=5)  # Terminate the session after 5 minutes

        for key in self.instances_dict.keys():
            current_time = datetime.datetime.now()
            last_call_time = self.instances_dict[key]["time"]
            if last_call_time:
                if current_time >= last_call_time + timeout:
                    del self.instances_dict[key]
                    return True

######################
##  REST API CLASS  ##
######################


class BptkServer(Flask):
    """
    This class provides a Flask-based server that provides a REST-API for running bptk scenarios. The class inherts the properties and methods of Flask and doesn't expose any further public methods.
    """

    def __init__(self, import_name, bptk):
        """
        Initialize the server with the import name and the bptk.
        :param import_name: the name of the application package. Usually __name__. This helps locate the root_path for the blueprint.
        :param bptk: simulations made by the bptk.
        """
        super(BptkServer, self).__init__(import_name)
        self.bptk = bptk
        self.instance_manager = InstanceManager(bptk)
        # specifying the routes and methods of the api
        self.route("/", methods=['GET'])(self._home_resource)
        self.route("/run", methods=['POST', 'PUT'], strict_slashes=False)(self._run_resource)
        self.route("/scenarios", methods=['GET'], strict_slashes=False)(self._scenarios_resource)
        self.route("/equations", methods=['POST'], strict_slashes=False)(self._equations_resource)
        self.route("/agents", methods=['POST', 'PUT'], strict_slashes=False)(self._agents_resource)
        self.route("/start-instance", methods=['POST'], strict_slashes=False)(self._start_instance_resource)
        self.route("/<instance_id>/run-step", methods=['POST', 'PUT'], strict_slashes=False)(self._run_step_resource)

    def _home_resource(self):
        """
        The root endpoint returns a simple html page for test purposes.
        """
        return "<h1>BPTK-Py REST API Server</h1>"

    def _run_resource(self):
        """
        Given a JSON dictionary that defines the relevant simulation scenarios and equations, this endpoint runs those scenarios and returns the data generated by the simulations.
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
            scenario_managers = content["scenario_managers"]
        except KeyError:
            resp = make_response('{"error": "expecting scenario_managers to be set"}',500)
            resp.headers['Content-Type']='application/json'
            resp.headers['Access-Control-Allow-Origin']='*'
            return resp

        try:
            scenarios = content["scenarios"]
        except KeyError:
            resp = make_response('{"error": "expecting scenario_managers to be set"}', 500)
            resp.headers['Content-Type']='application/json'
            resp.headers['Access-Control-Allow-Origin']='*'
            return resp

        try:
            equations = content["equations"]
        except KeyError:
            resp = make_response('{"error": "expecting equations to be set"}', 500)
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
        """
        The endpoint returns all available scenarios for the current simulation.
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
        """
        This endpoint returns all available equations given the name of a scenario manager and of a scenario.
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
        """
        For an agent-based or hybrid model, this endpoint returns all the agents in the model with their corresponding states and properties.
        """

        if not request.is_json:
            resp = make_response('{"error": "please pass the request with content-type application/json"}',500)
            resp.headers['Content-Type'] = 'application/json'
            resp.headers['Access-Control-Allow-Origin'] = '*'
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

        # store the new instance in the instance dictionary.
        cloned_bptk_uuid = self.instance_manager.store_instance()

        # Check for the session timeout
        if self.instance_manager.is_instance_timeout():
            resp = make_response('{"error": "Session has timed out"}', 401)
            resp.headers['Content-Type'] = 'application/json'
            resp.headers['Access-Control-Allow-Origin'] = '*'
            return resp

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
            resp = make_response('{"error": "please pass the request with content-type application/json"}', 500)
            resp.headers['Content-Type'] = 'application/json'
            resp.headers['Access-Control-Allow-Origin'] = '*'
            return resp

        content = request.get_json()


        # Checking if the instance id is valid.
        try:
            self.instance_manager.instances_dict[instance_id]
        except KeyError:
            resp = make_response('{"error": "expecting a valid instance id to be given"}', 500)
            resp.headers['Content-Type'] = 'application/json'
            resp.headers['Access-Control-Allow-Origin'] = '*'
            return resp

        # Add the current time to the instances dictionary with its instance id as a key
        self.instance_manager.instances_dict[instance_id]["time"] = datetime.datetime.now()

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
