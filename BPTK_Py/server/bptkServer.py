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

import sys
version = sys.version_info
if(version[0] < 3 or (version[0] == 3 and version[1] < 9)):
    print("BPTK Server requires Python 3.9 or later. Please update Python to use the BPTK Server! Exitting now.")
    sys.exit()


from flask import Flask, redirect, url_for, request, make_response, jsonify, Response
from BPTK_Py.bptk import bptk
import pandas as pd
import json
import copy
import uuid
import datetime
from json import JSONEncoder
import jsonpickle
import copy
import threading
from BPTK_Py.externalstateadapter import InstanceState, ExternalStateAdapter
from functools import wraps

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

    def keep_instance_alive(self,instance_uuid):
        self._update_instance_timestamp(instance_uuid)
        self._timeout_instances()
        return None

    def _get_instance_state(self, instance_uuid):
        instance = self._instances[instance_uuid]
        session_state = copy.deepcopy(instance['instance'].session_state)
        session_state["lock"] = False
        return InstanceState(session_state, instance_uuid, instance["time"], instance["timeout"], session_state["step"])
            
    def get_instance_states(self):
        keys = list(self._instances.keys())
        instances = []

        for key in keys:
            instances.append(self._get_instance_state(key))
            
        return instances
        
    def get_instance(self,instance_uuid):
        if not self.is_valid_instance(instance_uuid):
            return None
        # Add the current time to the instances dictionary with its instance id as a key
        self._update_instance_timestamp(instance_uuid)
        self._timeout_instances()
        try:
            instance = self._instances[instance_uuid]["instance"]
        except KeyError:
            instance = None

        return instance

    def _update_instance_timestamp(self, instance_uuid):
        try:
            if self.is_valid_instance(instance_uuid):
                self._instances[instance_uuid]["time"] = datetime.datetime.now()
        except KeyError:
            pass
    
    def _get_instance_metrics(self):
        self._timeout_instances()
        metrics = dict()

        for key in tuple(self._instances.keys()):
            instance = self._instances[key]

            if(instance == None or instance['instance'] == None or instance['instance'].session_state == None):
                continue

            metrics[key] = {
                "startTime": instance["time"],
                "step": instance['instance'].session_state["step"]
            }

        metrics["instanceCount"] = len(self._instances)
        metrics["threadCount"] = threading.active_count()

        return metrics

        
    def _get_prometheus_instance_metrics(self):
        self._timeout_instances()
        metrics =  "# HELP bptk_instance_count The number of instances in the bptk server\n# TYPE bptk_instance_count gauge\nbptk_instance_count " + str(len(self._instances)) + "\n"
        metrics += "# HELP bptk_thread_count The number of threads in the bptk server\n# TYPE bptk_thread_count gauge\nbptk_thread_count " + str(threading.active_count()) + "\n"
        return metrics

    def _delete_instance(self, instance_id):
        if instance_id in self._instances:
            del self._instances[instance_id]

    def create_instance(self,**timeout):
        """
        The method generates a universally unique identifier in hexadecimal, that is used as key for the instances.

        Returns: String
            The uuid value generated for the current instance.
        """

        self._timeout_instances()

        timeout = {
            "weeks": 0 if "weeks" not in timeout else timeout["weeks"],
            "days": 0 if "days" not in timeout else timeout["days"],
            "hours": 0 if "hours" not in timeout else timeout["hours"],
            "minutes":  0 if "minutes" not in timeout else timeout["minutes"],
            "seconds": 0 if "seconds" not in timeout else timeout["seconds"],
            "milliseconds": 0 if "milliseconds" not in timeout else timeout["milliseconds"],
            "microseconds":0 if "microseconds" not in timeout else timeout["microseconds"]
        }

        instance_data = {
            "instance": self._make_bptk(),
            "time": datetime.datetime.now(),
            "timeout": timeout
        }
        instance_uuid = uuid.uuid1().hex
        self._instances[instance_uuid] = instance_data

        return instance_uuid

    def reconstruct_instance(self,instance_uuid,timeout,time,session_state):
        instance = self._make_bptk()
        instance._set_state(session_state)

        instance_data = {
            "instance": instance,
            "time": time,
            "timeout": timeout
        }

        self._instances[instance_uuid] = instance_data

    def _timeout_instances(self):
        """
        The method checks for the session timeout, and deletes the instance if it is.

        Returns:
            True: Boolean.
                Means that the specified time has already passed, and the session should be terminated.
        """

        for key in tuple(self._instances.keys()): # we're iterating over a copy of the keys here to ensure we don't delete an element from the dictionary while iterating through it.
            current_time = datetime.datetime.now()
            try:
                if "time" in self._instances[key]:
                    if "timeout" in self._instances[key]:
                        timeout = datetime.timedelta(**self._instances[key]["timeout"])
                    else:
                        timeout = datetime.timedelta(hours=12)  # Terminate the session after 12 hours
                    last_call_time = self._instances[key]["time"]
                    if last_call_time:
                        if current_time >= last_call_time + timeout:
                            self._instances[key]['instance'].destroy() #ensure that bptk releases all resources
                            del self._instances[key]
            except KeyError:
                pass

######################
##  REST API CLASS  ##
######################


class BptkServer(Flask):
    """
    This class provides a Flask-based server that provides a REST-API for running bptk scenarios. The class inherts the properties and methods of Flask and doesn't expose any further public methods.
    """
    def __init__(self, import_name, bptk_factory=None, external_state_adapter=None, authenticate = False, bearer_token=None):
        """
        Initialize the server with the import name and the bptk.
        :param import_name: the name of the application package. Usually __name__. This helps locate the root_path for the blueprint.
        :param bptk: simulations made by the bptk.
        """
        super(BptkServer, self).__init__(import_name)
        self._bptk = bptk_factory() if bptk_factory is not None else None
        self._external_state_adapter = external_state_adapter
        self._instance_manager = InstanceManager(bptk_factory)
        self._bearer_token = bearer_token		
        self._authenticate = authenticate

        # Loading the full state on startup
        if external_state_adapter != None:
            result = self._external_state_adapter.load_state()
            for instance_data in result:
                self._instance_manager.reconstruct_instance(instance_data.instance_id, instance_data.timeout, instance_data.time, instance_data.state)

        # specifying the routes and methods of the api
        self.route("/", methods=['GET'])(self._home_resource)
        self.route("/run", methods=['POST', 'PUT'], strict_slashes=False)(self._run_resource)
        self.route("/scenarios", methods=['GET'], strict_slashes=False)(self._scenarios_resource)
        self.route("/equations", methods=['POST'], strict_slashes=False)(self._equations_resource)
        self.route("/agents", methods=['POST', 'PUT'], strict_slashes=False)(self._agents_resource)
        self.route("/start-instance", methods=['POST'], strict_slashes=False)(self._start_instance_resource)
        self.route("/<instance_uuid>/run-step", methods=['POST'], strict_slashes=False)(self._run_step_resource)
        self.route("/<instance_uuid>/run-steps", methods=['POST'], strict_slashes=False)(self._run_steps_resource)
        self.route("/<instance_uuid>/stream-steps", methods=['POST'], strict_slashes=False)(self._stream_steps_resource)
        self.route("/<instance_uuid>/begin-session", methods=['POST'], strict_slashes=False)(self._begin_session_resource)
        self.route("/<instance_uuid>/end-session", methods=['POST'], strict_slashes=False)(self._end_session_resource)
        self.route("/<instance_uuid>/session-results", methods=['GET'], strict_slashes=False)(self._session_results_resource)
        self.route("/<instance_uuid>/flat-session-results", methods=['GET'], strict_slashes=False)(self._flat_session_results_resource)
        self.route("/<instance_uuid>/keep-alive", methods=['POST'], strict_slashes=False)(self._keep_alive_resource)
        self.route("/metrics", methods=['GET'], strict_slashes=False)(self._metrics)
        self.route("/full-metrics", methods=['GET'], strict_slashes=False)(self._full_metrics)
        self.route("/save-state", methods=['GET'], strict_slashes=False)(self._save_state_resource)
        self.route("/load-state", methods=['GET'], strict_slashes=False)(self._load_state_resource)
        self.route("/<instance_uuid>/stop-instance", methods=['GET'], strict_slashes=False)(self._stop_instance)

    def token_required(f):
        @wraps(f)
        def decorated(self, *args, **kwargs):
            if self._authenticate:
                token = None
                if "Authorization" in request.headers:
                    token = request.headers["Authorization"].split(" ")[1]

                if token is None:
                    resp = make_response('{"Unauthorized": "Authentication Token is missing!"}', 401)
                    return resp
                
                if token != self._bearer_token:
                    resp = make_response('{"Unauthorized": "Authentication Token is wrong!"}', 401)
                    return resp

            return f(self, *args, **kwargs)
        return decorated

    @token_required
    def _stop_instance(self, instance_uuid):
        self._instance_manager._delete_instance(instance_uuid)
        if self._external_state_adapter != None:
            self._external_state_adapter.delete_instance(instance_uuid)

        resp = make_response("Instance deleted.", 200)
        resp.headers['Content-Type']='application/json'
        resp.headers['Access-Control-Allow-Origin']='*'
        return resp

    @token_required
    def _save_state_resource(self):
        """
        Save all instances with the provided external state adapter.
        """
        if(self._external_state_adapter == None):
            return

        instance_states = self._instance_manager.get_instance_states()
        self._external_state_adapter.save_state(instance_states)

        resp = make_response(jsonpickle.dumps(instance_states), 200)
        resp.headers['Content-Type']='application/json'
        resp.headers['Access-Control-Allow-Origin']='*'
        return resp
    
    @token_required
    def _load_state_resource(self):
        """
        Loads all instances using the external state adapter
        """
        
        if(self._external_state_adapter == None):
            return

        result = self._external_state_adapter.load_state()

        for instance_data in result:
            self._instance_manager.reconstruct_instance(instance_data.instance_id, instance_data.timeout, instance_data.time, instance_data.state)

        resp = make_response("Success", 200)
        resp.headers['Access-Control-Allow-Origin']='*'
        return resp

    @token_required
    def _metrics(self):
        """
        Returns metrics in a prometheus compatible format.
        """
        resp = make_response(self._instance_manager._get_prometheus_instance_metrics(), 200)
        resp.headers['Access-Control-Allow-Origin']='*'
        return resp

    @token_required
    def _full_metrics(self):
        """
        Returns metrics in JSON format. Following metrics are returned:
        - Instance count
        - Creation time und current timestep of each instance
        """
        resp = make_response(json.dumps(self._instance_manager._get_instance_metrics(), indent=4, sort_keys=True, default=str), 200)
        resp.headers['Content-Type']='application/json'
        resp.headers['Access-Control-Allow-Origin']='*'
        return resp

    @token_required
    def _home_resource(self):
        """
        The root endpoint returns a simple html page for test purposes.
        """
        return "<h1>BPTK-Py REST API Server</h1>"

    @token_required
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

    @token_required
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

    @token_required
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

    @token_required
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

    @token_required
    def _start_instance_resource(self):
        """
        This endpoint starts a new instance of BPTK on the server side, so that simulations can run in a "private" session. The endpoint returns an instance_id, which is needed to identify the instance in later calls.

        Arguments: timeout (dict,optional)
            The timeout period after which the instance is delete if it is not accessed in the meantime. The timer is reset every time the instance is accessed. The timeout dictionary can have the following keys: weeks, days, hours, minutes, seconds, milliseconds, microseconds. Values must be integers.
        """

        # store the new instance in the instance dictionary.
        timeout = {"weeks":0, "days":0, "hours":12, "minutes":0,"seconds":0,"milliseconds":0,"microseconds":0}
        if request.is_json:
            content = request.get_json()
            if "timeout" in content:
                timeout = content["timeout"]
        instance_uuid = self._instance_manager.create_instance(**timeout)

        if instance_uuid is not None:
            resp = make_response(f'{{"instance_uuid":"{instance_uuid}","timeout":"{timeout}"}}', 200)
        else:
            resp = make_response('{"error": "instance could not be started"}', 500)

        resp.headers['Content-Type']='application/json'
        resp.headers['Access-Control-Allow-Origin']='*'
        return resp

    @token_required
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
        if not self._ensure_instance_exists(instance_uuid):
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
        equations = []
        agents = []
        agent_states=[]
        agent_properties=[]
        agent_property_types=[]
        individual_agent_properties=[]

        if(not "agents" in content.keys() and not "equations" in content.keys()):
            resp = make_response('{"error": "expecting either equations or agents to be set"}', 500)
            resp.headers['Content-Type']='application/json'
            resp.headers['Access-Control-Allow-Origin']='*'
            return resp
        if("agents" in content.keys()):
            agents = content["agents"]
        if("equations" in content.keys()):
            equations = content["equations"]
        if("agent_states" in content.keys()):
            agent_states = content["agent_states"]
        if("agent_properties" in content.keys()):
            agent_properties = content["agent_properties"]
        if("agent_property_types" in content.keys()):
            agent_property_types = content["agent_property_types"]
        if("individual_agent_properties" in content.keys()):
            individual_agent_properties = content["individual_agent_properties"]



        instance = self._instance_manager.get_instance(instance_uuid)

        instance.begin_session(
            scenario_managers=scenario_managers,
            scenarios=scenarios,
            equations=equations,
            agents=agents,
            agent_states=agent_states,
            agent_properties=agent_properties,
            agent_property_types=agent_property_types,
            individual_agent_properties=individual_agent_properties
        )

        resp = make_response('{"msg":"session started"}', 200)
        resp.headers['Content-Type'] = 'application/json'
        resp.headers['Access-Control-Allow-Origin']='*'
        return resp

    @token_required
    def _end_session_resource(self, instance_uuid):
        """This endpoint ends a session for single step simulation and resets the internal cache.
        """
        # Checking if the instance id is valid.
        if not self._ensure_instance_exists(instance_uuid):
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

    @token_required
    def _flat_session_results_resource(self,instance_uuid):
        """
        Returns the accumulated results of a session, from the first step to the last step that was run in a flat format.
        """
        if not self._ensure_instance_exists(instance_uuid):
            resp = make_response('{"error": "expecting a valid instance id to be given"}', 500)
            resp.headers['Content-Type'] = 'application/json'
            resp.headers['Access-Control-Allow-Origin'] = '*'
            return resp

        return self._session_results_resource(instance_uuid, True)

    @token_required
    def _session_results_resource(self,instance_uuid,flat=False):
        """
        Returns the accumulated results of a session, from the first step to the last step that was run.
        """
        
        if not self._ensure_instance_exists(instance_uuid):
            resp = make_response('{"error": "expecting a valid instance id to be given"}', 500)
            resp.headers['Content-Type'] = 'application/json'
            resp.headers['Access-Control-Allow-Origin'] = '*'
            return resp

        instance = self._instance_manager.get_instance(instance_uuid)
        result = instance.session_results(index_by_time=False, flat=flat)

        resp = make_response(json.dumps(result), 200)
        resp.headers['Content-Type'] = 'application/json'
        resp.headers['Access-Control-Allow-Origin'] = '*'
        return resp

    @token_required
    def _run_step_resource(self, instance_uuid):
        """
        This endpoint advances the relevant scenarios by one timestep and returns the data for that timestep.

        Arguments:
            instance_uuid: string
                The id of the instance to advance.
        """
        # Checking if the instance id is valid.
        if not self._ensure_instance_exists(instance_uuid):
            resp = make_response('{"error": "expecting a valid instance id to be given"}', 500)
            resp.headers['Content-Type'] = 'application/json'
            resp.headers['Access-Control-Allow-Origin'] = '*'
            return resp
        
        instance = self._instance_manager.get_instance(instance_uuid)

        if(instance.is_locked()):
            resp = make_response('{"error": "instace is locked"}', 500)
            resp.headers['Content-Type'] = 'application/json'
            resp.headers['Access-Control-Allow-Origin'] = '*'
            return resp

        if not request.is_json:
            result = instance.run_step()
        else:
            content = request.get_json()
            if "settings" in content:
                result = instance.run_step(settings=content["settings"], flat="flatResults" in content and content["flatResults"] == True)
            else:
                resp = make_response('{"error": "expecting settings to be set"}', 500)
                resp.headers['Content-Type'] = 'application/json'
                resp.headers['Access-Control-Allow-Origin'] = '*'
                return resp

        if result is not None:
            resp = make_response(jsonpickle.dumps(result), 200)
        else:
            resp = make_response('{"error": "no data was returned from run_step"}', 500)

        if self._external_state_adapter != None:
            self._external_state_adapter.save_instance(self._instance_manager._get_instance_state(instance_uuid))

        resp.headers['Content-Type'] = 'application/json'
        resp.headers['Access-Control-Allow-Origin']='*'
        return resp

    @token_required
    def _run_steps_resource(self, instance_uuid):
        """
        This endpoint advances the relevant scenarios by one timestep and returns the data for that timestep.

        Arguments:
            instance_uuid: string
                The id of the instance to advance.
        """
        # Checking if the instance id is valid.
        if not self._ensure_instance_exists(instance_uuid):
            resp = make_response('{"error": "expecting a valid instance id to be given"}', 500)
            resp.headers['Content-Type'] = 'application/json'
            resp.headers['Access-Control-Allow-Origin'] = '*'
            return resp
        
        result = []
        try:
            instance = self._instance_manager.get_instance(instance_uuid)
            if not request.is_json:
                resp = make_response('{"error": "expecting a number of steps to be provided in the body as a json {numberSteps: int}"}', 500)
                resp.headers['Content-Type'] = 'application/json'
                resp.headers['Access-Control-Allow-Origin'] = '*'
                return resp

            if(instance.is_locked()):
                resp = make_response('{"error": "instace is locked"}', 500)
                resp.headers['Content-Type'] = 'application/json'
                resp.headers['Access-Control-Allow-Origin'] = '*'
                return resp
            content = request.get_json()
            if "numberSteps" in content:
                if "settings" in content:
                    instance.lock()
                    for i in range(0,content["numberSteps"]):
                        result.append(instance.run_step(settings=content["settings"], flat="flatResults" in content and content["flatResults"] == True))
                    instance.unlock()
                else:
                    resp = make_response('{"error": "expecting settings to be set"}', 500)
                    resp.headers['Content-Type'] = 'application/json'
                    resp.headers['Access-Control-Allow-Origin'] = '*'
                    return resp
            else:
                resp = make_response('{"error": "expecting a number of steps to be provided in the body as a json {"numberSteps": int}"}', 500)
                resp.headers['Content-Type'] = 'application/json'
                resp.headers['Access-Control-Allow-Origin'] = '*'
                return resp
        except:
            instance.unlock()
        if result is not None:
            resp = make_response(jsonpickle.dumps(result), 200)
        else:
            resp = make_response('{"error": "no data was returned from run_step"}', 500)

        if self._external_state_adapter != None:
            self._external_state_adapter.save_instance(self._instance_manager._get_instance_state(instance_uuid))

        resp.headers['Content-Type'] = 'application/json'
        resp.headers['Access-Control-Allow-Origin']='*'
        return resp


    @token_required
    def _stream_steps_resource(self, instance_uuid):
        """
        This endpoint is used to stream a simulation.

        Arguments:
            
            instance_uuid: string
                The id of the instance to stream.
        """
        # Checking if the instance id is valid.
        if not self._ensure_instance_exists(instance_uuid):
            resp = make_response('{"error": "expecting a valid instance id to be given"}', 500)
            resp.headers['Content-Type'] = 'application/json'
            resp.headers['Access-Control-Allow-Origin'] = '*'
            return resp
        
        instance = self._instance_manager.get_instance(instance_uuid)
        is_json = request.is_json
        if is_json:
            content = request.get_json()
            
            if not "settings" in content:
                resp = make_response('{"error": "expecting settings to be set"}', 500)
                resp.headers['Content-Type'] = 'application/json'
                resp.headers['Access-Control-Allow-Origin'] = '*'
                return resp

        if(instance.is_locked()):
            resp = make_response('{"error": "instace is locked"}', 500)
            resp.headers['Content-Type'] = 'application/json'
            resp.headers['Access-Control-Allow-Origin'] = '*'
            return resp

        def streamer():
            try:
                instance.lock()
                yield "["
                first = True
                while instance.progress() <= 1.0:
                    if first:
                        first = False
                    else:
                        yield ","
                        
                    if is_json:
                        result = instance.run_step(settings=content["settings"], flat="flatResults" in content and content["flatResults"] == True)
                    else:
                        result = instance.run_step()
                    if result is not None:
                        yield jsonpickle.dumps(result)
                    else:
                        yield '{"error": "no data was returned from run_step"}'
                yield "]"
            except:
                instance.unlock()
            if self._external_state_adapter != None:
                self._external_state_adapter.save_instance(self._instance_manager._get_instance_state(instance_uuid))

        resp = Response(streamer())
        resp.headers['Content-Type'] = 'application/json'
        resp.headers['Access-Control-Allow-Origin'] = '*'
        return resp


    @token_required
    def _keep_alive_resource(self,instance_uuid):
        """
        This endpoint sets the "last accessed time" of the instance to the current time to prevent the instance from timeing out.

        Arguments: None
        """

        if not self._instance_manager.is_valid_instance(instance_uuid):
            resp = make_response('{"error": "expecting a valid instance id to be given"}', 500)
        else:
            self._instance_manager.keep_instance_alive(instance_uuid)
            resp = make_response('{"msg":"instance timer reset"}',200)

        resp.headers['Content-Type'] = 'application/json'
        resp.headers['Access-Control-Allow-Origin']='*'
        return resp

    @token_required
    def _ensure_instance_exists(self, instance_uuid) -> bool:
        if self._instance_manager.is_valid_instance(instance_uuid):
            return True
        
        if(self._external_state_adapter == None):
            return False
        
        instance = self._external_state_adapter.load_instance(instance_uuid)
        if instance == None:
            return False

        self._instance_manager.reconstruct_instance(instance.instance_id, instance.timeout, instance.time, instance.state)
        return True
        
        
