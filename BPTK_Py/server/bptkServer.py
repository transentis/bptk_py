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
    def __init__(self, bptk_factory):
        self._bptk_factory = bptk_factory
        self._instances = dict()

    def _make_bptk(self):
        return self._bptk_factory()

    def is_valid_instance(self, instance_uuid):
        return instance_uuid in self._instances

    def get_instance(self,instance_uuid):
        if not self.is_valid_instance(instance_uuid):
            return None
        # Add the current time to the instances dictionary with its instance id as a key
        self._update_instance_timestamp(instance_uuid)
        self._timeout_instances()
        return self._instances[instance_uuid]["instance"]

    def _update_instance_timestamp(self, instance_uuid):
        if self.is_valid_instance(instance_uuid):
            self._instances[instance_uuid]["time"]= datetime.datetime.now()

    def create_instance(self):
        """
        The method generates a universally unique identifier in hexadecimal, that is used as key for the instances.

        Returns: String
            The uuid value generated for the current instance.
        """

        self._timeout_instances()

        instance_uuid = uuid.uuid1().hex
        self._instances[instance_uuid] = dict()
        self._instances[instance_uuid]["instance"] = self._make_bptk()
        self._instances[instance_uuid]["time"] = dict()

        return instance_uuid

    def _timeout_instances(self):
        """
        The method checks for the session timeout, and deletes the instance if it is.

        Returns:
            True: Boolean.
                Means that the specified time has already passed, and the session should be terminated.
        """

        timeout = datetime.timedelta(minutes=5)  # Terminate the session after 5 minutes

        for key in tuple(self._instances.keys()): # we're iterating over a copy of the keys here to ensure we don't delete an element from the dictionary while iterating through it.
            current_time = datetime.datetime.now()
            last_call_time = self._instances[key]["time"]
            if last_call_time:
                if current_time >= last_call_time + timeout:
                    del self._instances[key]

######################
##  REST API CLASS  ##
######################


class BptkServer(Flask):
    """
    This class provides a Flask-based server that provides a REST-API for running bptk scenarios. The class inherts the properties and methods of Flask and doesn't expose any further public methods.
    """

    def __init__(self, import_name, bptk_factory=None):
        """
        Initialize the server with the import name and the bptk.
        :param import_name: the name of the application package. Usually __name__. This helps locate the root_path for the blueprint.
        :param bptk: simulations made by the bptk.
        """
        super(BptkServer, self).__init__(import_name)
        self._bptk = bptk_factory() if bptk_factory is not None else None
        
        
        self._instance_manager = InstanceManager(bptk_factory)
        # specifying the routes and methods of the api
        self.route("/", methods=['GET'])(self._home_resource)
        self.route("/run", methods=['POST', 'PUT'], strict_slashes=False)(self._run_resource)
        self.route("/scenarios", methods=['GET'], strict_slashes=False)(self._scenarios_resource)
        self.route("/equations", methods=['POST'], strict_slashes=False)(self._equations_resource)
        self.route("/agents", methods=['POST', 'PUT'], strict_slashes=False)(self._agents_resource)
        self.route("/start-instance", methods=['POST'], strict_slashes=False)(self._start_instance_resource)
        self.route("/<instance_uuid>/run-step", methods=['POST'], strict_slashes=False)(self._run_step_resource)
        self.route("/<instance_uuid>/begin-session", methods=['POST'], strict_slashes=False)(self._begin_session_resource)
        self.route("/<instance_uuid>/end-session", methods=['POST'], strict_slashes=False)(self._end_session_resource)

    def _home_resource(self):
        """
        The root endpoint returns a simple html page for test purposes.
        """
        return "<h1>BPTK-Py REST API Server</h1>"

    def _run_resource(self):
        """
        Given a JSON dictionary that defines the relevant simulation scenarios and equations, this endpoint runs those scenarios and returns the data generated by the simulations.
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
                    scenario = self._bptk.get_scenario(scenario_manager_name,scenario_name)
                    if "constants" in scenario_settings:
                        constants = scenario_settings["constants"]
                        for constant_name, constant_settings in constants.items():
                            scenario.constants[constant_name]=constant_settings
                    if "points" in scenario_settings:
                        points = scenario_settings["points"]
                        for points_name, points_settings in points.items():
                            scenario.points[points_name]=points_settings
                    self._bptk.reset_scenario_cache(scenario_manager=scenario_manager_name,scenario=scenario_name)
        except KeyError:
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

        result = self._bptk.run_scenarios(
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

        scenarios = self._bptk.get_scenario_names(format="dict")

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

        if ("scenarioManager" not in content) and ("scenario_manager" not in content):
            resp = make_response('{"error": "expecting scenarioManager or scenario_manager to be set"}',500)
            resp.headers['Content-Type']='application/json'
            resp.headers['Access-Control-Allow-Origin']='*'
            return resp

        if "scenario_manager" in content:
            scenario_manager_name=content["scenario_manager"]
        else:
            scenario_manager_name=content["scenarioManager"]

        try:
            scenario_name = content["scenario"]
        except KeyError:
            resp = make_response('{"error": "expecting scenario to be set"}',500)
            resp.headers['Content-Type']='application/json'
            resp.headers['Access-Control-Allow-Origin']='*'
            return resp

        scenario = self._bptk.get_scenario(scenario_manager_name,scenario_name)

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

        scenario = self._bptk.get_scenario(scenario_manager_name,scenario_name)

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
        instance_uuid = self._instance_manager.create_instance()

        if instance_uuid is not None:
            resp = make_response(f'{{"instance_uuid":"{instance_uuid}"}}', 200)
        else:
            resp = make_response('{"error": "instance could not be started"}', 500)

        return resp

    def _begin_session_resource(self, instance_uuid):
        """This endpoint starts a session for single step simulation. There can only be one session per instance at a time.
        Currently only System Dynamics scenarios are supported for both SD DSL and XMILE models.
        """

        if not request.is_json:
            resp = make_response('{"error": "please pass the request with content-type application/json"}', 500)
            resp.headers['Content-Type'] = 'application/json'
            resp.headers['Access-Control-Allow-Origin'] = '*'
            return resp

        # Checking if the instance id is valid.
        if not self._instance_manager.is_valid_instance(instance_uuid):
            resp = make_response('{"error": "expecting a valid instance id to be given"}', 500)
            resp.headers['Content-Type'] = 'application/json'
            resp.headers['Access-Control-Allow-Origin'] = '*'
            return resp

        content = request.get_json()

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
            resp = make_response('{"error": "expecting scenarios to be set"}', 500)
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

        instance = self._instance_manager.get_instance(instance_uuid)

        instance.begin_session(
            scenario_managers=scenario_managers,
            scenarios=scenarios,
            equations=equations
        )

        resp = make_response('{"msg":"session started"}', 200)
        resp.headers['Content-Type'] = 'application/json'
        resp.headers['Access-Control-Allow-Origin']='*'
        return resp

    def _end_session_resource(self, instance_uuid):
        """This endpoint ends a session for single step simulation and resets the internal cache.
        """
        # Checking if the instance id is valid.
        if not self._instance_manager.is_valid_instance(instance_uuid):
            resp = make_response('{"error": "expecting a valid instance id to be given"}', 500)
            resp.headers['Content-Type'] = 'application/json'
            resp.headers['Access-Control-Allow-Origin'] = '*'
            return resp

        instance = self._instance_manager.get_instance(instance_uuid)
        instance.end_session()

        resp = make_response('{"msg":"session terminated"}', 200)
        resp.headers['Content-Type'] = 'application/json'
        resp.headers['Access-Control-Allow-Origin']='*'
        return resp

    def _run_step_resource(self, instance_uuid):
        """
        This endpoint advances the relevant scenarios by one timestep and returns the data for that timestep.

        Arguments:
            settings: JSON
                Dictionary structure with a key "settings" that contains the settings to apply for that step. These can be constants and points.
        """
        # Checking if the instance id is valid.
        if not self._instance_manager.is_valid_instance(instance_uuid):
            resp = make_response('{"error": "expecting a valid instance id to be given"}', 500)
            resp.headers['Content-Type'] = 'application/json'
            resp.headers['Access-Control-Allow-Origin'] = '*'
            return resp

        instance = self._instance_manager.get_instance(instance_uuid)

        if not request.is_json:
            result = instance.run_step()
        else:
            content = request.get_json()
            if "settings" in content:
                result = instance.run_step(settings=content["settings"])
            else:
                resp = make_response('{"error": "expecting settings to be set"}', 500)
                resp.headers['Content-Type'] = 'application/json'
                resp.headers['Access-Control-Allow-Origin'] = '*'
                return resp

        if result is not None:
            resp = make_response(json.dumps(result), 200)
        else:
            resp = make_response('{"error": "no data was returned from run_step"}', 500)

        resp.headers['Content-Type'] = 'application/json'
        resp.headers['Access-Control-Allow-Origin']='*'
        return resp
