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


from flask import Flask, redirect, url_for, request, make_response, jsonify, Response, g
from BPTK_Py.bptk import bptk
from BPTK_Py.logger import logger as log_module
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
        session_state = copy.deepcopy(instance['instance'].session_state) if instance['instance'].session_state is not None else None
        step=None
        if session_state is not None:
            session_state["lock"] = False
            step=session_state["step"]
        return InstanceState(session_state, instance_uuid, instance["time"], instance["timeout"], step)
            
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
            log_module.log(f"[INFO] _delete_instance: Deleting instance {instance_id} from memory")
            del self._instances[instance_id]
        else:
            log_module.log(f"[INFO] _delete_instance: Instance {instance_id} not found in memory")

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
        if session_state:
           instance._set_state(session_state)

        instance_data = {
            "instance": instance,
            "time": time,
            "timeout": timeout
        }

        self._instances[instance_uuid] = instance_data
        log_module.log(f"[INFO] _add_instance: Added instance {instance_uuid} to memory")

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


def _check_for_py_callbacks(model_def):
    """
    Walk the JSON expression trees of an ``/execute`` model definition and
    refuse it if any ``py_callback`` node is present.

    ``py_callback`` is the future (Phase 6) node type that lets a Rust model
    invoke a Python function during evaluation. Phase 4 has no mechanism to
    register such functions on the server, so requests containing them
    cannot succeed — we reject them up-front with a clear error rather than
    let the Rust engine fail mid-load with a less obvious message.

    Returns ``None`` if the model is clean, or a human-readable error
    message describing why it was rejected.

    The walk is O(total nodes in the model) and runs once per request. It
    descends into every dict / list value so nodes nested under ``if`` /
    binary-op / call args are caught even when buried deep in an
    expression tree.
    """
    def walk(node):
        if not isinstance(node, dict):
            return None
        if node.get("type") == "py_callback":
            return "py_callback nodes are not supported by /execute (Phase 6)"
        for v in node.values():
            if isinstance(v, dict):
                err = walk(v)
                if err:
                    return err
            elif isinstance(v, list):
                for item in v:
                    err = walk(item)
                    if err:
                        return err
        return None

    if not isinstance(model_def, dict):
        return "model must be a JSON object"

    entities = model_def.get("entities", {})
    # The four entity kinds that carry expression trees. Stocks have both
    # ``initial_value`` and ``equation``; the others only ``equation``.
    for kind in ("stocks", "flows", "biflows", "converters", "constants"):
        for ent in entities.get(kind, []) or []:
            for field in ("equation", "initial_value"):
                if field in ent:
                    err = walk(ent[field])
                    if err:
                        return err
    return None


class BptkServer(Flask):
    """
    This class provides a Flask-based server that provides a REST-API for running bptk scenarios. The class inherts the properties and methods of Flask and doesn't expose any further public methods.
    """
    def __init__(self, import_name, bptk_factory=None, external_state_adapter=None, bearer_token=None, externalize_state_completely=False):
        """
        Initialize the server with the import name and the bptk.
        :param import_name: the name of the application package. Usually __name__. This helps locate the root_path for the blueprint.
        :param bptk: simulations made by the bptk.
        :param externalize_state_completely: if True and external_state_adapter is provided, instances are deleted after every use to ensure statelessness
        """
        super(BptkServer, self).__init__(import_name)
        self._bptk = bptk_factory() if bptk_factory is not None else None
        self._external_state_adapter = external_state_adapter
        self._instance_manager = InstanceManager(bptk_factory)
        self._bearer_token = bearer_token
        self._externalize_state_completely = externalize_state_completely

        # specifying the routes and methods of the api
        self.route("/", methods=['GET'],strict_slashes=False)(self._home_resource)
        self.route("/healthy", methods=['GET'],strict_slashes=False)(self._healthy_resource)
        self.route("/run", methods=['POST', 'PUT'], strict_slashes=False)(self._run_resource)
        # /execute is a self-contained sibling of /run: the request body carries the
        # model definition itself (JSON, same schema as Model.to_json()) and the server
        # runs it through the Rust engine. No pre-registered scenario manager required.
        # Primary consumer: the visual modeler (design doc §6.1).
        self.route("/execute", methods=['POST'], strict_slashes=False)(self._execute_resource)
        self.route("/scenarios", methods=['GET'], strict_slashes=False)(self._scenarios_resource)
        self.route("/equations", methods=['POST'], strict_slashes=False)(self._equations_resource)
        self.route("/agents", methods=['POST', 'PUT'], strict_slashes=False)(self._agents_resource)
        self.route("/start-instance", methods=['POST'], strict_slashes=False)(self._start_instance_resource)
        self.route("/start-instances", methods=['POST'], strict_slashes=False)(self._start_instances_resource)
        self.route("/<instance_uuid>/run-step", methods=['POST'], strict_slashes=False)(self._run_step_resource)
        self.route("/<instance_uuid>/run-steps", methods=['POST'], strict_slashes=False)(self._run_steps_resource)
        self.route("/<instance_uuid>/stream-steps", methods=['POST'], strict_slashes=False)(self._stream_steps_resource)
        self.route("/<instance_uuid>/begin-session", methods=['POST'], strict_slashes=False)(self._begin_session_resource)
        self.route("/<instance_uuid>/end-session", methods=['POST'], strict_slashes=False)(self._end_session_resource)
        self.route("/<instance_uuid>/session-results", methods=['GET'], strict_slashes=False)(self._session_results_resource)
        self.route("/<instance_uuid>/flat-session-results", methods=['GET'], strict_slashes=False)(self._flat_session_results_resource)
        self.route("/<instance_uuid>/keep-alive", methods=['POST'], strict_slashes=False)(self._keep_alive_resource)
        self.route("/metrics", methods=['GET'], strict_slashes=False)(self._metrics_resource)
        self.route("/full-metrics", methods=['GET'], strict_slashes=False)(self._full_metrics_resource)
        self.route("/<instance_uuid>/stop-instance", methods=['POST'], strict_slashes=False)(self._stop_instance_resource)

        # Note: Cleanup is now handled directly in endpoints via _cleanup_instance_if_needed()

    def token_required(f):
        @wraps(f)
        def decorated(self, *args, **kwargs):
            if self._bearer_token is not None:
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

    def _cleanup_instance_if_needed(self, instance_uuid):
        """
        Directly cleanup an instance if external state is configured.
        This is called at the end of endpoints that need cleanup.
        Runs synchronously to avoid race conditions and simplify debugging.
        """
        if self._external_state_adapter and self._externalize_state_completely:
            try:
                log_module.log(f"[INFO] Cleanup: Processing instance {instance_uuid}")
                # Save instance state to external storage
                instance_state = self._instance_manager._get_instance_state(instance_uuid)
                if instance_state:
                    log_module.log(f"[INFO] Cleanup: Saving state for instance {instance_uuid}")
                    self._external_state_adapter.save_instance(instance_state)

                # Delete instance from memory
                log_module.log(f"[INFO] Cleanup: Deleting instance {instance_uuid} from memory")
                self._instance_manager._delete_instance(instance_uuid)
                log_module.log(f"[INFO] Cleanup: Completed for instance {instance_uuid}")
            except Exception as e:
                log_module.log(f"[ERROR] Cleanup failed for instance {instance_uuid}: {str(e)}")

    def _cleanup_new_instances_if_needed(self, instance_uuids):
        """
        Directly cleanup newly created instances if external state is configured.
        This is called at the end of start_instance(s) endpoints.
        Runs synchronously to avoid race conditions and simplify debugging.
        """
        if self._external_state_adapter and self._externalize_state_completely and instance_uuids:
            try:
                log_module.log(f"[INFO] Cleanup: Processing {len(instance_uuids)} new instances")
                for instance_uuid in instance_uuids:
                    try:
                        # Save instance state to external storage
                        instance_state = self._instance_manager._get_instance_state(instance_uuid)
                        if instance_state:
                            log_module.log(f"[INFO] Cleanup: Saving new instance {instance_uuid}")
                            self._external_state_adapter.save_instance(instance_state)

                        # Delete instance from memory
                        log_module.log(f"[INFO] Cleanup: Deleting new instance {instance_uuid} from memory")
                        self._instance_manager._delete_instance(instance_uuid)
                    except Exception as e:
                        log_module.log(f"[ERROR] Cleanup failed for new instance {instance_uuid}: {str(e)}")
                log_module.log(f"[INFO] Cleanup: Completed for new instances")
            except Exception as e:
                log_module.log(f"[ERROR] Cleanup error: {str(e)}")

    # Note: Cleanup is now handled directly in endpoints via _cleanup_instance_if_needed()
    # and _cleanup_new_instances_if_needed() methods

    @token_required
    def _stop_instance_resource(self, instance_uuid):
        # explicitly deletes the instance as its primary function
        with log_module.span("stop_instance", endpoint="/stop-instance", instance_uuid=instance_uuid):
            self._instance_manager._delete_instance(instance_uuid)
            if self._external_state_adapter != None:
                try:
                    self._external_state_adapter.delete_instance(instance_uuid)
                except FileNotFoundError:
                    # Instance might not have been saved to external adapter yet
                    # (when externalize_state_completely=False)
                    log_module.log(f"[INFO] Instance {instance_uuid} not found in external adapter (may have been in-memory only)")
                except Exception as e:
                    log_module.log(f"[WARN] Failed to delete instance {instance_uuid} from external adapter: {e}")

            resp = make_response('{"msg": "Instance deleted."}', 200)
            resp.headers['Content-Type']='application/json'
            resp.headers['Access-Control-Allow-Origin']='*'
            return resp

    
    def _metrics_resource(self):
        """
        Returns metrics in a prometheus compatible format.
        """
        resp = make_response(self._instance_manager._get_prometheus_instance_metrics(), 200)
        resp.headers['Access-Control-Allow-Origin']='*'
        return resp

    def _full_metrics_resource(self):
        """
        Returns metrics in JSON format. Following metrics are returned:
        - Instance count
        - Creation time und current timestep of each instance
        """
        resp = make_response(json.dumps(self._instance_manager._get_instance_metrics(), indent=4, sort_keys=True, default=str), 200)
        resp.headers['Content-Type']='application/json'
        resp.headers['Access-Control-Allow-Origin']='*'
        return resp

    def _home_resource(self):
        """
        The root endpoint returns a simple html page for test purposes.
        """
        return "<h1>BPTK REST API Server</h1>"

    def _healthy_resource(self):
        """
        The root endpoint returns a simple html page for test purposes.
        """
        return "<h1>BPTK Health Check</h1>"

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
        
        log_module.log(f"[INFO] Running scenarios")


        try:
            settings = content["settings"]

            for scenario_manager_name, scenario_manager_data in settings.items():
                
                for scenario_name, scenario_settings in scenario_manager_data.items():
                    self._bptk.reset_scenario_cache(scenario_manager=scenario_manager_name,scenario=scenario_name)
                    scenario = self._bptk.get_scenario(scenario_manager_name,scenario_name)
                    if "constants" in scenario_settings:
                        constants = scenario_settings["constants"]
                        for constant_name, constant_settings in constants.items():
                            scenario.constants[constant_name]=constant_settings
                    if "points" in scenario_settings:
                        points = scenario_settings["points"]
                        for points_name, points_settings in points.items():
                            scenario.points[points_name]=points_settings
                    if "runspecs" in scenario_settings:
                        runspecs = scenario_settings["runspecs"]
                        if "starttime" in runspecs:
                            scenario.starttime = runspecs["starttime"]
                        if "stoptime" in runspecs:
                            scenario.stoptime = runspecs["stoptime"]
                        if "dt" in runspecs:
                            scenario.dt = runspecs["dt"]
                    if "properties" in scenario_settings:
                        scenario.configure_properties(scenario_settings["properties"])
                    if "agents" in scenario_settings:
                        scenario.configure_agents(scenario_settings["agents"])
                        
                    
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
            resp = make_response('{"error": "expecting scenarios to be set"}', 500)
            resp.headers['Content-Type']='application/json'
            resp.headers['Access-Control-Allow-Origin']='*'
            return resp

        equations = []
        agents = []
        agent_states=[]
        agent_properties=[]
        agent_property_types=[]
        

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
       


        result = self._bptk.run_scenarios(
            scenario_managers=scenario_managers,
            scenarios=scenarios,
            equations=equations,
            agents=agents,
            agent_states=agent_states,
            agent_properties=agent_properties,
            agent_property_types=agent_property_types,
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
    def _execute_resource(self):
        """
        Stateless on-the-fly execution of a JSON model through the Rust engine.

        Unlike ``/run``, which selects from scenario managers pre-registered on
        the server via ``bptk_factory``, ``/execute`` receives the **complete
        model definition** in the request body. It does not touch ``self._bptk``,
        the instance manager, or the external state adapter — each request is
        fully self-contained.

        Primary consumer: the visual modeler, where a user designs a model in a
        browser UI and POSTs it to the server for execution. See design doc
        §6.1 and the Phase 4 implementation plan, Substep 4e.

        Request body (Content-Type: application/json)::

            {
              "model": { ... JSON model, same schema as Model.to_json() ... },
              "scenarios": {
                "baseline": {
                  "constants": {"transmission_prob": 0.001, ...},
                  "points":    {"rate_table": [[0, 1], [10, 5]]},
                  "runspecs":  {"starttime": 0.0, "stoptime": 50.0, "dt": 0.25}
                },
                "high_contact": { ... }
              },
              "equations": ["susceptible", "infected", "recovered"]
            }

        ``scenarios`` is optional; if omitted the model runs once under the
        synthetic name ``"default"`` with no overrides. Each scenario applies
        its overrides to a fresh ``RustSdModel`` so per-scenario tweaks do not
        leak into siblings within the same request.

        Response: HTTP 200 with a JSON dict ``{scenario_name: {equation: {t_str: value}}}``
        matching the Rust engine's ``simulate()`` return shape directly.

        Errors:
            * HTTP 400 — malformed request body, missing/empty ``model`` or
              ``equations``, ``py_callback`` node present (rejected as a Phase
              4 non-goal — see Phase 6), or engine load/runtime error from
              user-supplied JSON (unknown function name, bad expression
              shape, etc.).
            * HTTP 500 — Rust engine extension not built on this server.

        Notes:
            * Backend is always Rust — there is no "Python backend" for raw
              JSON because Python execution requires the Element-graph object
              tree, not the engine's flat node format.
            * Floating-point time keys (e.g. ``"0.30000000000000004"`` for
              ``dt=0.1``) carry through verbatim from the engine. See the
              Phase 3 known issue on ``format_time``; the fix lives at the
              engine level and is independent of this endpoint.
        """
        if not request.is_json:
            return self._error_response(
                "please pass the request with content-type application/json", 400
            )

        content = request.get_json()

        # Required fields. Missing keys → 400 with the offending field name so the
        # caller gets a precise error instead of a generic "missing field".
        try:
            model_def = content["model"]
            equations = content["equations"]
        except KeyError as e:
            return self._error_response(
                "missing required field: {}".format(e.args[0]), 400
            )

        if not isinstance(equations, list) or not equations:
            return self._error_response("equations must be a non-empty list", 400)

        # Default to a single anonymous scenario when the client omits the
        # scenarios block entirely — common case for "just run the model".
        scenarios = content.get("scenarios", {"default": {}})

        # Importing here, not at module top, so that environments without the
        # compiled extension can still import bptkServer (e.g. /run-only deployments).
        try:
            from BPTK_Py._rust_engine import RustSdEngine
        except ImportError:
            return self._error_response("Rust engine is not available on this server", 500)

        # Phase 4 hard-rejects py_callback nodes anywhere in the model. Phase 6
        # will lift this once a server-side function registry exists.
        rejection = _check_for_py_callbacks(model_def)
        if rejection:
            return self._error_response(rejection, 400)

        # Re-serialize the dict to a JSON string. The Rust engine's load_model
        # takes a string, not a Python dict.
        try:
            model_json_str = json.dumps(model_def)
        except (TypeError, ValueError) as e:
            return self._error_response(
                "model is not JSON-serializable: {}".format(e), 400
            )

        engine = RustSdEngine()
        results = {}

        try:
            for scenario_name, overrides in scenarios.items():
                # Each scenario gets its own freshly loaded model so per-scenario
                # constant/point overrides do not bleed into the next iteration.
                rust_model = engine.load_model(model_json_str)

                for name, value in overrides.get("constants", {}).items():
                    rust_model.set_constant(name, float(value))

                for name, points in overrides.get("points", {}).items():
                    # PyO3's set_points signature is Vec<(f64, f64)> — tuples
                    # required. JSON has no tuple type, so normalize from
                    # list-of-list, matching the per-step path in sd_runner.
                    rust_model.set_points(
                        name,
                        [(float(x), float(y)) for x, y in points],
                    )

                if "runspecs" in overrides:
                    rs = overrides["runspecs"]
                    specs = model_def.get("specs", {})
                    rust_model.set_runspecs(
                        float(rs.get("starttime", specs.get("starttime"))),
                        float(rs.get("stoptime",  specs.get("stoptime"))),
                        float(rs.get("dt",        specs.get("dt"))),
                    )

                results[scenario_name] = rust_model.simulate(equations)
        except (ValueError, KeyError, TypeError) as e:
            # ValueError covers the most common engine-side failures: unknown
            # function names, malformed expression trees, unknown constant
            # names in overrides, set_runspecs after init (cannot happen on
            # this path but kept for symmetry), etc.
            return self._error_response("Rust engine error: {}".format(e), 400)

        resp = make_response(json.dumps(results), 200)
        resp.headers['Content-Type'] = 'application/json'
        resp.headers['Access-Control-Allow-Origin'] = '*'
        return resp

    def _error_response(self, msg, status):
        """
        Return a JSON error response with the canonical headers.

        Used by ``/execute`` (and reserved for any new endpoints) to keep
        error handling consistent. The existing endpoints (``/run``,
        ``/scenarios``, ``/begin-session``, ...) deliberately keep their
        inline ``make_response('{"error": "..."}', 500)`` pattern — they
        return HTTP 500 for client errors, which is wrong but stable. Phase
        4 leaves that alone to keep the diff focused; a separate cleanup
        can normalise them later.
        """
        resp = make_response(json.dumps({"error": msg}), status)
        resp.headers['Content-Type'] = 'application/json'
        resp.headers['Access-Control-Allow-Origin'] = '*'
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

        # `equations_names` is built as a `{}` literal and only ever has keys
        # added to it — it is never None by construction. No defensive
        # "no data" branch is necessary.
        resp = make_response(equations_names, 200)
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

        resp = make_response(agents_dict, 200)

        return resp

    @token_required
    def _start_instance_resource(self):
        """
        This endpoint starts a new instance of BPTK on the server side, so that simulations can run in a "private" session. The endpoint returns an instance_id, which is needed to identify the instance in later calls.

        Arguments: timeout (dict,optional)
            The timeout period after which the instance is delete if it is not accessed in the meantime. The timer is reset every time the instance is accessed. The timeout dictionary can have the following keys: weeks, days, hours, minutes, seconds, milliseconds, microseconds. Values must be integers.
        """
        with log_module.span("start_instance", endpoint="/start-instance"):
            # store the new instance in the instance dictionary.
            timeout = {"weeks":0, "days":0, "hours":12, "minutes":0,"seconds":0,"milliseconds":0,"microseconds":0}
            instances = 1

            if request.is_json:
                content = request.get_json()
                if "timeout" in content:
                    timeout = content["timeout"]
            # `create_instance` always returns a fresh `uuid.uuid1().hex`,
            # so the previous `if instance_uuid is not None` branch was
            # unreachable in practice — removed to keep the code honest.
            instance_uuid = self._instance_manager.create_instance(**timeout)
            response_data = {"instance_uuid": instance_uuid, "timeout": timeout}
            resp = make_response(json.dumps(response_data), 200)

            resp.headers['Content-Type'] = 'application/json'
            resp.headers['Access-Control-Allow-Origin'] = '*'

            # Cleanup new instance if needed (for stateless operation)
            self._cleanup_new_instances_if_needed([instance_uuid])

            return resp

    @token_required
    def _start_instances_resource(self):
        """
        This endpoint start N new instances of BPTK on the server side. The endpoint returns a list of instance_ids, which is needed to identify the instance in later calls.         
        """

        timeout = {"weeks":0, "days":0, "hours":12, "minutes":0,"seconds":0,"milliseconds":0,"microseconds":0}
        instances = 1
        instance_uuids = []
        
        if request.is_json:
            content = request.get_json()
            if "timeout" in content:
                timeout = content["timeout"]
            if "instances" in content:
                instances = content["instances"]

        for i in range(instances):
            instance_uuid = self._instance_manager.create_instance(**timeout)
            instance_uuids.append(instance_uuid)

        response_data={"instance_uuids":instance_uuids,"timeout":timeout}

        resp = make_response(json.dumps(response_data), 200)
        resp.headers['Content-Type'] = 'application/json'
        resp.headers['Access-Control-Allow-Origin'] = '*'

        # Cleanup new instances if needed (for stateless operation)
        if instance_uuids:
            self._cleanup_new_instances_if_needed(instance_uuids)

        return resp

    @token_required
    def _begin_session_resource(self, instance_uuid):
        """This endpoint starts a session for single step simulation. There can only be one session per instance at a time.
            Currently only System Dynamics scenarios are supported for both SD DSL and XMILE models.
        """
        with log_module.span("begin_session", endpoint="/begin-session", instance_uuid=instance_uuid):
            if not request.is_json:
                resp = make_response('{"error": "please pass the request with content-type application/json"}', 500)
                resp.headers['Content-Type'] = 'application/json'
                resp.headers['Access-Control-Allow-Origin'] = '*'

                # Cleanup instance if needed (for stateless operation)
                self._cleanup_instance_if_needed(instance_uuid)

                return resp

            # Checking if the instance id is valid.
            if not self._ensure_instance_exists(instance_uuid):
                resp = make_response('{"error": "expecting a valid instance id to be given"}', 500)
                resp.headers['Content-Type'] = 'application/json'
                resp.headers['Access-Control-Allow-Origin'] = '*'

                # Cleanup instance if needed (for stateless operation)
                self._cleanup_instance_if_needed(instance_uuid)

                return resp

            content = request.get_json()

            try:
                scenario_managers = content["scenario_managers"]
            except KeyError:
                resp = make_response('{"error": "expecting scenario_managers to be set"}',500)
                resp.headers['Content-Type']='application/json'
                resp.headers['Access-Control-Allow-Origin']='*'

                # Cleanup instance if needed (for stateless operation)
                self._cleanup_instance_if_needed(instance_uuid)

                return resp

            try:
                scenarios = content["scenarios"]
            except KeyError:
                resp = make_response('{"error": "expecting scenarios to be set"}', 500)
                resp.headers['Content-Type']='application/json'
                resp.headers['Access-Control-Allow-Origin']='*'

                # Cleanup instance if needed (for stateless operation)
                self._cleanup_instance_if_needed(instance_uuid)

                return resp
            equations = []
            agents = []
            agent_states=[]
            agent_properties=[]
            agent_property_types=[]
            individual_agent_properties=[]
            settings = {}

            if(not "agents" in content.keys() and not "equations" in content.keys()):
                resp = make_response('{"error": "expecting either equations or agents to be set"}', 500)
                resp.headers['Content-Type']='application/json'
                resp.headers['Access-Control-Allow-Origin']='*'

                # Cleanup instance if needed (for stateless operation)
                self._cleanup_instance_if_needed(instance_uuid)

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
            if("settings" in content.keys()):
                settings = content["settings"]

            # Optional `backend` field — selects the execution backend for the
            # entire session ("python" or "rust"). When omitted, it is left as
            # None so bptk.begin_session falls through to the instance's
            # default_backend (configurable via configuration["default_backend"];
            # itself "python" unless overridden). An explicit value here always
            # wins over the instance default. Invalid values are rejected up
            # front rather than silently falling back, to make configuration
            # errors visible. See Phase 4 design doc §6, Substep 4d for the
            # bptk.begin_session plumbing and Substep 4i for default_backend.
            backend = content.get("backend")
            if backend is not None and backend not in ("python", "rust"):
                # Cleanup instance if needed (for stateless operation)
                self._cleanup_instance_if_needed(instance_uuid)
                return self._error_response(
                    "backend must be 'python' or 'rust', got '{}'".format(backend), 400
                )

            # Optional `seed` field — pins the Rust backend's RNG so a stochastic
            # session replays bit-identically after a process restart (state
            # externalisation / resume). Omitting it lets bptk auto-generate and
            # persist one for Rust sessions; ignored by the Python backend.
            seed = content.get("seed", None)

            instance = self._instance_manager.get_instance(instance_uuid)

            instance.begin_session(
                scenario_managers=scenario_managers,
                scenarios=scenarios,
                settings=settings,
                equations=equations,
                agents=agents,
                agent_states=agent_states,
                agent_properties=agent_properties,
                agent_property_types=agent_property_types,
                individual_agent_properties=individual_agent_properties,
                backend=backend,
                seed=seed,
            )

            resp = make_response('{"msg":"session started"}', 200)
            resp.headers['Content-Type'] = 'application/json'
            resp.headers['Access-Control-Allow-Origin']='*'

            # Cleanup instance if needed (for stateless operation)
            self._cleanup_instance_if_needed(instance_uuid)

            return resp

    @token_required
    def _end_session_resource(self, instance_uuid):
        """This endpoint ends a session for single step simulation and resets the internal cache.
        """
        with log_module.span("end_session", endpoint="/end-session", instance_uuid=instance_uuid):
            # Checking if the instance id is valid.
            if not self._ensure_instance_exists(instance_uuid):
                resp = make_response('{"error": "expecting a valid instance id to be given"}', 500)
                resp.headers['Content-Type'] = 'application/json'
                resp.headers['Access-Control-Allow-Origin'] = '*'

                # Cleanup instance if needed (for stateless operation)
                self._cleanup_instance_if_needed(instance_uuid)

                return resp

            instance = self._instance_manager.get_instance(instance_uuid)
            instance.end_session()

            resp = make_response('{"msg":"session terminated"}', 200)
            resp.headers['Content-Type'] = 'application/json'
            resp.headers['Access-Control-Allow-Origin']='*'

            # Cleanup instance if needed (for stateless operation)
            self._cleanup_instance_if_needed(instance_uuid)

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

            # Cleanup instance if needed (for stateless operation)
            self._cleanup_instance_if_needed(instance_uuid)

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

            # Cleanup instance if needed (for stateless operation)
            self._cleanup_instance_if_needed(instance_uuid)

            return resp

        instance = self._instance_manager.get_instance(instance_uuid)
        result = instance.session_results(index_by_time=False, flat=flat)

        resp = make_response(json.dumps(result), 200)
        resp.headers['Content-Type'] = 'application/json'
        resp.headers['Access-Control-Allow-Origin'] = '*'

        # Cleanup instance if needed (for stateless operation)
        self._cleanup_instance_if_needed(instance_uuid)

        return resp

    @token_required
    def _run_step_resource(self, instance_uuid):
        """
        This endpoint advances the relevant scenarios by one timestep and returns the data for that timestep.

        Arguments:
            instance_uuid: string
                The id of the instance to advance.
        """
        with log_module.span("run_step", endpoint="/run-step", instance_uuid=instance_uuid):
            # Checking if the instance id is valid.
            if not self._ensure_instance_exists(instance_uuid):
                resp = make_response('{"error": "expecting a valid instance id to be given"}', 500)
                resp.headers['Content-Type'] = 'application/json'
                resp.headers['Access-Control-Allow-Origin'] = '*'

                # Cleanup instance if needed (for stateless operation)
                self._cleanup_instance_if_needed(instance_uuid)

                return resp

            instance = self._instance_manager.get_instance(instance_uuid)

            if(instance.is_locked()):
                resp = make_response('{"error": "instance is locked"}', 500)
                resp.headers['Content-Type'] = 'application/json'
                resp.headers['Access-Control-Allow-Origin'] = '*'

                # Cleanup instance if needed (for stateless operation)
                self._cleanup_instance_if_needed(instance_uuid)

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

                    # Cleanup instance if needed (for stateless operation)
                    self._cleanup_instance_if_needed(instance_uuid)

                    return resp

            if result is not None:
                resp = make_response(jsonpickle.dumps(result), 200)
            else:
                resp = make_response('{"error": "no data was returned from run_step"}', 500)

            resp.headers['Content-Type'] = 'application/json'
            resp.headers['Access-Control-Allow-Origin']='*'

            # Cleanup instance if needed (for stateless operation)
            self._cleanup_instance_if_needed(instance_uuid)

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

            # Cleanup instance if needed (for stateless operation)
            self._cleanup_instance_if_needed(instance_uuid)

            return resp
        
        result = []
        try:
            instance = self._instance_manager.get_instance(instance_uuid)
            if not request.is_json:
                resp = make_response('{"error": "please pass the request with content-type application/json"}',500)
                resp.headers['Content-Type'] = 'application/json'
                resp.headers['Access-Control-Allow-Origin']='*'

                # Cleanup instance if needed (for stateless operation)
                self._cleanup_instance_if_needed(instance_uuid)

                return resp

            if(instance.is_locked()):
                resp = make_response('{"error": "instance is locked"}', 500)
                resp.headers['Content-Type'] = 'application/json'
                resp.headers['Access-Control-Allow-Origin'] = '*'

                # Cleanup instance if needed (for stateless operation)
                self._cleanup_instance_if_needed(instance_uuid)

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

                    # Cleanup instance if needed (for stateless operation)
                    self._cleanup_instance_if_needed(instance_uuid)

                    return resp
            else:
                resp = make_response('{"error": "expecting a number of steps to be provided in the body as a json {"numberSteps": int}"}', 500)
                resp.headers['Content-Type'] = 'application/json'
                resp.headers['Access-Control-Allow-Origin'] = '*'

                # Cleanup instance if needed (for stateless operation)
                self._cleanup_instance_if_needed(instance_uuid)

                return resp
        except:
            instance.unlock()
        resp = make_response(jsonpickle.dumps(result), 200)

        resp.headers['Content-Type'] = 'application/json'
        resp.headers['Access-Control-Allow-Origin']='*'

        # Cleanup instance if needed (for stateless operation)
        self._cleanup_instance_if_needed(instance_uuid)

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

            # Cleanup instance if needed (for stateless operation)
            self._cleanup_instance_if_needed(instance_uuid)

            return resp
        
        instance = self._instance_manager.get_instance(instance_uuid)
        is_json = request.is_json
        if is_json:
            content = request.get_json()
            
            if not "settings" in content:
                resp = make_response('{"error": "expecting settings to be set"}', 500)
                resp.headers['Content-Type'] = 'application/json'
                resp.headers['Access-Control-Allow-Origin'] = '*'

                # Cleanup instance if needed (for stateless operation)
                self._cleanup_instance_if_needed(instance_uuid)

                return resp

        if(instance.is_locked()):
            resp = make_response('{"error": "instance is locked"}', 500)
            resp.headers['Content-Type'] = 'application/json'
            resp.headers['Access-Control-Allow-Origin'] = '*'

            # Cleanup instance if needed (for stateless operation)
            self._cleanup_instance_if_needed(instance_uuid)

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
            
        resp = Response(streamer())
        resp.headers['Content-Type'] = 'application/json'
        resp.headers['Access-Control-Allow-Origin'] = '*'

        # Cleanup instance if needed (for stateless operation)
        self._cleanup_instance_if_needed(instance_uuid)

        return resp


    @token_required
    def _keep_alive_resource(self,instance_uuid):
        """
        This endpoint sets the "last accessed time" of the instance to the current time to prevent the instance from timeing out.

        Arguments: None
        """

        if not self._ensure_instance_exists(instance_uuid):
            resp = make_response('{"error": "expecting a valid instance id to be given"}', 500)
        else:
            self._instance_manager.keep_instance_alive(instance_uuid)
            resp = make_response('{"msg":"instance timer reset"}',200)

        resp.headers['Content-Type'] = 'application/json'
        resp.headers['Access-Control-Allow-Origin']='*'

        # Cleanup instance if needed (for stateless operation)
        self._cleanup_instance_if_needed(instance_uuid)

        return resp

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
        
        
