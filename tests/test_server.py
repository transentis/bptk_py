from BPTK_Py.server import BptkServer
from BPTK_Py.server.bptkServer import InstanceManager
from unittest import mock
import json
import sys
import pytest


from BPTK_Py import Model
from BPTK_Py import Agent
from BPTK_Py import sd_functions as sd
import BPTK_Py

token="1234" # token for bearer authentication


def bptk_factory():
    model = Model(starttime=1.0,stoptime=50.0, dt=1.0, name="Test Model")
    stock = model.stock("stock")
    flow = model.flow("flow")
    constant = model.constant("constant")
    stock.initial_value=0.0
    stock.equation=flow
    flow.equation=constant
    constant.equation=1.0

    scenario_manager1={
        "firstManager":{
            "model":model
        }
    }

    scenario_manager2={
        "secondManager":{
            "model":model
        }
    }

    bptk = BPTK_Py.bptk()

    bptk.register_scenario_manager(scenario_manager1)
    bptk.register_scenario_manager(scenario_manager2)

    bptk.register_scenarios(
        scenario_manager="firstManager",
        scenarios=
        {
            "1":{
                "constants":
                {
                    "constant":1.0
                }
            }
        }
    )

    bptk.register_scenarios(
        scenario_manager="secondManager",
        scenarios=
        {
            "1":{
                "constants":
                {
                    "constant":1.0
                }
            },
            "2":{
                "constants":{
                    "constant":2.0
                }
            },
            "3":{
                "constants":{
                    "constant":3.0
                }
            }
        }
    )

    return bptk

@pytest.fixture
def app():
    flask_app = BptkServer(__name__, bptk_factory,None,token)
    yield flask_app

@pytest.fixture
def client(app):
    return app.test_client()

def empty_bptk_factory():
    model = Model(starttime=1.0,stoptime=50.0, dt=1.0, name="Test Model")
    stock = model.stock("stock")
    flow = model.flow("flow")
    constant = model.constant("constant")
    stock.initial_value=0.0
    stock.equation=flow
    flow.equation=constant
    constant.equation=1.0

    bptk = BPTK_Py.bptk()

    return bptk

@pytest.fixture
def empty_app():
    flask_app = BptkServer(__name__, empty_bptk_factory,None,token)
    yield flask_app

@pytest.fixture
def empty_client(empty_app):
    return empty_app.test_client()


# Minimal ABM model defined inline so the ABM fixture matches the SD one
# in style — the test file is self-contained, no external scenario JSON or
# agent-module imports. Mirrors the model that used to live in
# tests/abm_model/src/.

class _AgentOne(Agent):
    def __init__(self, agent_id, model, properties):
        super().__init__(agent_id=agent_id, model=model, properties=properties)
        self.agent_type = "agent_1"
        self.state = "open"
        self.set_property("x", {"type": "Double", "value": 0})

    def act(self, time, round_no, step_no):
        partner = self.model.next_agent("agent_2", "available")
        self.x += partner.y


class _AgentTwo(Agent):
    def __init__(self, agent_id, model, properties):
        super().__init__(agent_id=agent_id, model=model, properties=properties)
        self.agent_type = "agent_2"
        self.state = "available"
        self.set_property("y", {"type": "Double", "value": 1})


class _ModelTestEnv(Model):
    def instantiate_model(self):
        self.register_agent_factory(
            "agent_1", lambda agent_id, model, properties: _AgentOne(agent_id, model, properties))
        self.register_agent_factory(
            "agent_2", lambda agent_id, model, properties: _AgentTwo(agent_id, model, properties))


def abm_bptk_factory():
    """Factory returning a bptk instance with a programmatically registered
    ABM scenario manager. Used by tests that need an actual agent-based
    model on the server side (e.g. /agents happy path, /run with agent
    settings)."""
    bptk_instance = BPTK_Py.bptk()
    bptk_instance.register_scenario_manager({
        "testAbmManager": {
            "type": "abm",
            "name": "testAbmModel",
            "model": _ModelTestEnv(),
            "scenarios": {
                "testScenario": {
                    "runspecs": {"starttime": 1, "stoptime": 10, "dt": 1},
                    "properties": {
                        "deadline": {"type": "Integer", "value": 1},
                    },
                    "agents": [
                        {"name": "agent_1", "count": 1},
                        {"name": "agent_2", "count": 1},
                    ],
                }
            },
        }
    })
    return bptk_instance


@pytest.fixture
def abm_app():
    flask_app = BptkServer(__name__, abm_bptk_factory, None, token)
    yield flask_app


@pytest.fixture
def abm_client(abm_app):
    return abm_app.test_client()

def test_home_resource(app, client):
    response = client.get('/')
    assert response.status_code ==  200
    assert response.data == b"<h1>BPTK REST API Server</h1>"

def test_healthy_resource(app, client):
    response = client.get('/healthy')
    assert response.status_code ==  200
    assert response.data == b"<h1>BPTK Health Check</h1>"


def test_run_resource(app, client):
    query={
        "scenario_managers":["firstManager"],
        "scenarios":["1"],
        "equations":["stock","flow","constant"],
        "agents" : ["agent"],
        "agent_states": ["agent_state"],
        "agent_properties" : ["agent_property"],
        "agent_property_types" : ["agent_property_type"],
        "settings":{
            "firstManager":{
                "1":{
                    "constants": {
                        "constant":7.0
                    },
                    "points": {
                        "point" : [
                           [0, 0.1],
                           [1, 0.9]
                       ]           
                     },
                    "runspecs": {
                        "starttime": 1.0,
                        "stoptime": 15.0,
                        "dt": 1.0
                    }
                    #properties and agents not defined for SimulationScenario -> Bug?
                }
            }
        }
    }

    response = client.post('/run', data=json.dumps(query), content_type = 'application/json',headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200 # checking the status code

    #error if data is not json 
    response_with_not_json = client.post('/run', data=query, headers={"Authorization": f"Bearer {token}"})

    assert response_with_not_json.status_code == 500 # checking the status code    
    assert b'please pass the request with content-type application/json' in response_with_not_json.data

    #errors for no result (missing content included)

    query_with_missing_settings={
        "scenario_managers":["firstManager"],
        "scenarios":["1"],
        "agents":["agent"],
    }

    response_with_missing_settings = client.post('/run', data=json.dumps(query_with_missing_settings), content_type = 'application/json',headers={"Authorization": f"Bearer {token}"})

    assert response_with_missing_settings.status_code == 500 # checking the status code    
    assert b'no data was returned from simulation' in response_with_missing_settings.data

    query_with_missing_manager={
        "scenarios":["1"],
        "equations":["stock","flow","constant"],
        "settings":{
            "firstManager":{
                "1":{
                    "constants": {
                        "constant":7.0
                    }
                }
            }
        }        
    }

    response_with_missing_manager = client.post('/run', data=json.dumps(query_with_missing_manager), content_type = 'application/json',headers={"Authorization": f"Bearer {token}"})

    assert response_with_missing_manager.status_code == 500 # checking the status code    
    assert b'expecting scenario_managers to be set' in response_with_missing_manager.data

    query_with_missing_scenarios={
        "scenario_managers":["firstManager"],
        "equations":["stock","flow","constant"],
        "settings":{
            "firstManager":{
                "1":{
                    "constants": {
                        "constant":7.0
                    }
                }
            }
        }        
    }

    response_with_missing_scenarios = client.post('/run', data=json.dumps(query_with_missing_scenarios), content_type = 'application/json',headers={"Authorization": f"Bearer {token}"})

    assert response_with_missing_scenarios.status_code == 500 # checking the status code    
    assert b'expecting scenarios to be set' in response_with_missing_scenarios.data 

    query_with_missing_equations_and_agents={
        "scenario_managers":["firstManager"],
        "scenarios":["1"],
        "settings":{
            "firstManager":{
                "1":{
                    "constants": {
                        "constant":7.0
                    }
                }
            }
        }        
    }

    response_with_missing_equations_and_agents = client.post('/run', data=json.dumps(query_with_missing_equations_and_agents), content_type = 'application/json',headers={"Authorization": f"Bearer {token}"})

    assert response_with_missing_equations_and_agents.status_code == 500 # checking the status code
    assert b'expecting either equations or agents to be set' in response_with_missing_equations_and_agents.data

    # bearer-token enforcement: missing token → 401
    response_no_auth = client.post('/run', data=json.dumps(query), content_type='application/json')
    assert response_no_auth.status_code == 401
    assert b'missing' in response_no_auth.data

    # wrong token → 401
    response_wrong_token = client.post('/run', data=json.dumps(query), content_type='application/json',
                                       headers={"Authorization": "Bearer not-the-real-token"})
    assert response_wrong_token.status_code == 401
    assert b'wrong' in response_wrong_token.data

def test_run_steps_resource(app, client):

    timeout = {
        "timeout": {
            "weeks":0,
            "days":0,
            "hours":0,
            "minutes":10,
            "seconds":0,
            "milliseconds":0,
            "microseconds":0
        }
    }

    response = client.post('/start-instance', data=json.dumps(timeout), content_type='application/json',headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    id = json.loads(response.data)['instance_uuid']

    session = {
        "scenario_managers": [
            "firstManager"
        ],
        "scenarios": [
            "1"
        ],
        "equations": [
            "stock",
            "flow",
            "constant",
        ]
    }

    response = client.post('/' + id + '/begin-session', data=json.dumps(session), content_type='application/json',headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200

    query={
        "settings": {
            "firstManager": {
                "1": {
                    "constants": {
                        "constant":7.0
                    }
                }
            }
        }
    }

    response = client.post('/' + id + '/run-step', data=json.dumps(query), content_type = 'application/json',headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200 # checking the status code


def test_stream_steps_resource(app, client):

    timeout = {
        "timeout": {
            "weeks":0,
            "days":0,
            "hours":0,
            "minutes":10,
            "seconds":0,
            "milliseconds":0,
            "microseconds":0
        }
    }

    response = client.post('/start-instance', data=json.dumps(timeout), content_type='application/json',headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    id = json.loads(response.data)['instance_uuid']

    session = {
        "scenario_managers": [
            "firstManager"
        ],
        "scenarios": [
            "1"
        ],
        "equations": [
            "stock",
            "flow",
            "constant",
        ]
    }

    response = client.post('/' + id + '/begin-session', data=json.dumps(session), content_type='application/json',headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200

    query={
        "settings": {
            "firstManager": {
                "1": {
                    "constants": {
                        "constant":7.0
                    }
                }
            }
        }
    }

    response = client.post('/' + id + '/stream-steps', data=json.dumps(query), content_type = 'application/json',headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200 # checking the status code

    #stream-steps without a JSON body must use the streamer's no-settings
    #branch: it advances the simulation with bare instance.run_step() calls.
    #A fresh instance + session is required because the previous one has
    #already streamed to completion.
    response = client.post('/start-instance', data=json.dumps(timeout), content_type='application/json',headers={"Authorization": f"Bearer {token}"})
    id_no_body = json.loads(response.data)['instance_uuid']
    response = client.post('/' + id_no_body + '/begin-session', data=json.dumps(session), content_type='application/json',headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    response_no_body = client.post('/' + id_no_body + '/stream-steps', headers={"Authorization": f"Bearer {token}"})
    body_no_body = response_no_body.data  # consume the generator
    assert response_no_body.status_code == 200
    assert body_no_body.startswith(b'[') and body_no_body.endswith(b']')

    #stream-steps where instance.run_step returns None must emit the
    #per-step "no data" chunk inside the streamed array. We can't simply
    #patch run_step to always return None: progress() relies on run_step
    #to advance, so the streamer's `while progress() <= 1.0` would loop
    #forever. Instead, return None on the first call and raise on the
    #second — the streamer's bare `except` catches the exception, unlocks,
    #and exits the generator cleanly, leaving the first "no data" chunk
    #in the response body for us to assert on.
    response = client.post('/start-instance', data=json.dumps(timeout), content_type='application/json',headers={"Authorization": f"Bearer {token}"})
    id_no_result = json.loads(response.data)['instance_uuid']
    response = client.post('/' + id_no_result + '/begin-session', data=json.dumps(session), content_type='application/json',headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    instance_no_result = app._instance_manager.get_instance(id_no_result)
    with mock.patch.object(instance_no_result, "run_step",
                           side_effect=[None, RuntimeError("stop streamer")]):
        response_no_result = client.post('/' + id_no_result + '/stream-steps', data=json.dumps(query),
                                         content_type='application/json',
                                         headers={"Authorization": f"Bearer {token}"})
        body_no_result = response_no_result.data
    assert response_no_result.status_code == 200
    assert b'no data was returned from run_step' in body_no_result

def test_scenarios_resource(app, client, empty_app, empty_client):
    response = client.get('/scenarios',headers={"Authorization": f"Bearer {token}"})
    data=json.loads(response.data)
    assert data["firstManager"] == ["1"]
    assert data["secondManager"] == ["1","2","3"]
    assert response.status_code == 200 # checking the status code

    #check for missing scenarios
    reponse_with_missing_scenarios = empty_client.get('/scenarios',headers={"Authorization": f"Bearer {token}"})    
    assert reponse_with_missing_scenarios.status_code == 500
    assert b'expecting the model to have scenarios' in reponse_with_missing_scenarios.data 

def test_equations_resource(app, client):
    query1 = {
        "scenarioManager": "firstManager",
        "scenario":"1"
    }
    query2 = {
        "scenario_manager": "firstManager",
        "scenario":"1"
    }
    response1 = client.post('/equations', data=json.dumps(query1), content_type = 'application/json',headers={"Authorization": f"Bearer {token}"})
    assert response1.status_code == 200 # Checking the status code
    equations1 = [b"constants", b"converters", b"flows", b"points"]
    for equation in equations1: # checking words in request data
        assert equation in response1.data
    response2 = client.post('/equations', data=json.dumps(query2), content_type = 'application/json',headers={"Authorization": f"Bearer {token}"})
    assert response2.status_code == 200 # Checking the status code
    equations2 = [b"constants", b"converters", b"flows", b"points"]
    for equation in equations2: # checking words in request data
        assert equation in response2.data

    #error if data is not json 
    response_with_not_json = client.post('/equations', data=query1, headers={"Authorization": f"Bearer {token}"})
    assert response_with_not_json.status_code == 500 # checking the status code    
    assert b'please pass the request with content-type application/json' in response_with_not_json.data

    #error if scenarioManager is Missing
    query_with_missing_manager = {
        "scenario":"1"
    }    
    response_with_missing_manager = client.post('/equations', data=json.dumps(query_with_missing_manager), content_type = 'application/json',headers={"Authorization": f"Bearer {token}"})
    assert response_with_missing_manager.status_code == 500 # checking the status code    
    assert b'expecting scenarioManager or scenario_manager to be set' in response_with_missing_manager.data

    #error if scenario is Missing
    query_with_missing_scenario = {
        "scenarioManager": "firstManager"
    }
    response_with_missing_scenario = client.post('/equations', data=json.dumps(query_with_missing_scenario), content_type = 'application/json',headers={"Authorization": f"Bearer {token}"})
    assert response_with_missing_scenario.status_code == 500 # checking the status code
    assert b'expecting scenario to be set' in response_with_missing_scenario.data

    # A second scenario built around a model that has an actual converter
    # and a graphical-function table — exercises the converters/points
    # iteration bodies, which the default fixture model leaves empty.
    def _factory_with_converter_and_points():
        model = Model(starttime=1.0, stoptime=10.0, dt=1.0, name="With Converter")
        flow = model.flow("flow")
        rate = model.converter("rate")
        constant = model.constant("constant")
        stock = model.stock("stock")
        stock.initial_value = 0.0
        stock.equation = flow
        flow.equation = rate
        constant.equation = 1.0
        model.points["rate_table"] = [[0, 0], [1, 1]]
        rate.equation = sd.lookup(sd.time(), "rate_table")

        bptk_extra = BPTK_Py.bptk()
        bptk_extra.register_scenario_manager({"converterManager": {"model": model}})
        bptk_extra.register_scenarios(
            scenarios={"1": {"constants": {"constant": 1.0}}},
            scenario_manager="converterManager",
        )
        return bptk_extra

    extra_server = BptkServer(__name__, _factory_with_converter_and_points, None, token)
    extra_client = extra_server.test_client()
    query_extra = {"scenarioManager": "converterManager", "scenario": "1"}
    resp_extra = extra_client.post('/equations', data=json.dumps(query_extra),
                                   content_type='application/json',
                                   headers={"Authorization": f"Bearer {token}"})
    assert resp_extra.status_code == 200
    extras = json.loads(resp_extra.data)
    assert "rate" in extras["converters"]
    assert "rate_table" in extras["points"]

def test_agents_resource(app, client):
    #error if data is not json
    empty_query = {}
    response_with_not_json = client.post('/agents', data=empty_query, headers={"Authorization": f"Bearer {token}"})
    assert response_with_not_json.status_code == 500 # checking the status code    
    assert b'please pass the request with content-type application/json' in response_with_not_json.data

    #error if scenarioManager is Missing
    query_with_missing_manager = {
        "scenario":"1"
    }    
    response_with_missing_manager = client.post('/agents', data=json.dumps(query_with_missing_manager), content_type = 'application/json',headers={"Authorization": f"Bearer {token}"})
    assert response_with_missing_manager.status_code == 500 # checking the status code    
    assert b'expecting scenarioManager to be set' in response_with_missing_manager.data

    #error if scenario is Missing
    query_with_missing_scenario = {
        "scenarioManager": "firstManager"
    }    
    response_with_missing_scenario = client.post('/agents', data=json.dumps(query_with_missing_scenario), content_type = 'application/json',headers={"Authorization": f"Bearer {token}"})
    assert response_with_missing_scenario.status_code == 500 # checking the status code    
    assert b'expecting scenario to be set' in response_with_missing_scenario.data    

    #error if scenario has no agents
    query = {
        "scenarioManager": "firstManager",
        "scenario":"1"    }    
    response = client.post('/agents', data=json.dumps(query), content_type = 'application/json',headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 500 # checking the status code
    assert b'expecting the model to have agents' in response.data


def test_agents_resource_abm(abm_app, abm_client):
    """The /agents happy path against an actual agent-based model. The SD
    test above covers all the error branches; this confirms the
    agents-dict construction returns each agent's states and properties."""
    query = {"scenarioManager": "testAbmManager", "scenario": "testScenario"}
    response = abm_client.post('/agents', data=json.dumps(query),
                               content_type='application/json',
                               headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = json.loads(response.data)
    assert "agent_1" in data and "agent_2" in data
    assert data["agent_1"]["states"] == ["open"]
    assert "properties" in data["agent_1"]


def test_run_resource_abm(abm_app, abm_client):
    """``/run`` against an ABM scenario exercises the ``properties`` and
    ``agents`` branches inside the settings loop, which the SD-only
    ``test_run_resource`` can't reach."""
    query = {
        "scenario_managers": ["testAbmManager"],
        "scenarios": ["testScenario"],
        "agents": ["agent_1"],
        "agent_states": ["open"],
        "agent_properties": ["x"],
        "agent_property_types": ["total"],
        "settings": {
            "testAbmManager": {
                "testScenario": {
                    "properties": {
                        "deadline": {"type": "Integer", "value": 2},
                    },
                    "agents": [
                        {"name": "agent_1", "count": 1},
                        {"name": "agent_2", "count": 1},
                    ],
                }
            }
        },
    }
    response = abm_client.post('/run', data=json.dumps(query),
                               content_type='application/json',
                               headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200


def test_begin_session_with_agent_body(app, client):
    """``/begin-session`` body that carries ``agent_states`` /
    ``agent_properties`` / ``agent_property_types`` / ``individual_agent_properties``
    on top of an SD scenario exercises the optional-field unpacking branches
    that the existing tests skip (they only set ``equations``).

    ``begin_session`` itself doesn't support ABM scenarios — its scenario-
    cache initialisation goes through ``SimulationScenario._get_cache``,
    which ABM models don't implement. So we cover the endpoint's body-
    unpacking branches with an SD scenario plus empty agent arrays; the
    fields still populate from the request and SD execution stays happy."""
    timeout = {"timeout": {"minutes": 10}}
    response = client.post('/start-instance', data=json.dumps(timeout),
                           content_type='application/json',
                           headers={"Authorization": f"Bearer {token}"})
    instance_id = json.loads(response.data)['instance_uuid']

    session = {
        "scenario_managers": ["firstManager"],
        "scenarios": ["1"],
        "equations": ["stock", "flow", "constant"],
        # Empty agent fields — exercise the dict-key unpacking branches
        # without triggering the SD/ABM-mismatch path inside begin_session.
        "agents": [],
        "agent_states": [],
        "agent_properties": [],
        "agent_property_types": [],
        "individual_agent_properties": [],
        "settings": {},
    }
    response = client.post(f'/{instance_id}/begin-session',
                           data=json.dumps(session),
                           content_type='application/json',
                           headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200


def test_begin_session_backend_field(app, client):
    """The optional ``backend`` field on ``/begin-session`` selects the
    execution backend for the session. Defaults to ``"python"`` when
    omitted (legacy behaviour); accepts ``"python"`` or ``"rust"``;
    rejects any other value with 400.

    Full Python-vs-Rust step parity through the server endpoints is
    already covered by ``test_run_steps_resource`` (Python) plus the
    interleaved parity suite in ``test_rust_backend.py``. This test only
    confirms the endpoint wiring: the field is read, validated, and
    forwarded to ``bptk.begin_session``.
    """
    timeout = {"timeout": {"minutes": 10}}
    session_body = {
        "scenario_managers": ["firstManager"],
        "scenarios": ["1"],
        "equations": ["stock", "flow", "constant"],
    }

    # Omitted backend → defaults to "python", session starts normally.
    resp = client.post('/start-instance', data=json.dumps(timeout),
                       content_type='application/json',
                       headers={"Authorization": f"Bearer {token}"})
    id_default = json.loads(resp.data)['instance_uuid']
    resp = client.post(f'/{id_default}/begin-session', data=json.dumps(session_body),
                       content_type='application/json',
                       headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    instance_default = app._instance_manager.get_instance(id_default)
    assert instance_default.session_state["backend"] == "python"

    # Explicit "python" → same behaviour.
    resp = client.post('/start-instance', data=json.dumps(timeout),
                       content_type='application/json',
                       headers={"Authorization": f"Bearer {token}"})
    id_py = json.loads(resp.data)['instance_uuid']
    resp = client.post(f'/{id_py}/begin-session',
                       data=json.dumps({**session_body, "backend": "python"}),
                       content_type='application/json',
                       headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert app._instance_manager.get_instance(id_py).session_state["backend"] == "python"

    # Explicit "rust" → session starts; advancing one step exercises the
    # full Rust dispatch path (begin_session → run_step → SdRunner →
    # _run_scenario_step_rust → RustSdEngine.init → step). Round-trip
    # parity values are validated elsewhere; here we just confirm the
    # session can complete a step without errors.
    resp = client.post('/start-instance', data=json.dumps(timeout),
                       content_type='application/json',
                       headers={"Authorization": f"Bearer {token}"})
    id_rust = json.loads(resp.data)['instance_uuid']
    resp = client.post(f'/{id_rust}/begin-session',
                       data=json.dumps({**session_body, "backend": "rust"}),
                       content_type='application/json',
                       headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert app._instance_manager.get_instance(id_rust).session_state["backend"] == "rust"

    step_body = {"settings": {"firstManager": {"1": {"constants": {"constant": 7.0}}}}}
    resp = client.post(f'/{id_rust}/run-step', data=json.dumps(step_body),
                       content_type='application/json',
                       headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200

    # Invalid backend → 400 with a message naming both the offending value
    # and the allowed set.
    resp = client.post('/start-instance', data=json.dumps(timeout),
                       content_type='application/json',
                       headers={"Authorization": f"Bearer {token}"})
    id_invalid = json.loads(resp.data)['instance_uuid']
    resp = client.post(f'/{id_invalid}/begin-session',
                       data=json.dumps({**session_body, "backend": "go"}),
                       content_type='application/json',
                       headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 400
    assert b'go' in resp.data
    assert b"'python'" in resp.data and b"'rust'" in resp.data


def _rust_default_factory():
    """Same model as ``bptk_factory``, but the bptk instance is configured with
    ``default_backend="rust"``. This is the Substep 4i opt-in mechanism: a server
    (e.g. the beergame server) can flip its whole instance to Rust with one config
    line, and ``/begin-session`` requests that omit the ``backend`` field pick it
    up automatically."""
    model = Model(starttime=1.0, stoptime=50.0, dt=1.0, name="Test Model")
    stock = model.stock("stock")
    flow = model.flow("flow")
    constant = model.constant("constant")
    stock.initial_value = 0.0
    stock.equation = flow
    flow.equation = constant
    constant.equation = 1.0

    bptk = BPTK_Py.bptk(configuration={"default_backend": "rust"})
    bptk.register_scenario_manager({"firstManager": {"model": model}})
    bptk.register_scenarios(
        scenario_manager="firstManager",
        scenarios={"1": {"constants": {"constant": 1.0}}},
    )
    return bptk


def test_default_backend_propagates():
    """Substep 4i: a bptk configured with ``default_backend="rust"`` runs
    ``/begin-session`` sessions on Rust when the request omits the ``backend``
    field — no per-request override needed."""
    server = BptkServer(__name__, _rust_default_factory, None, token)
    client = server.test_client()
    timeout = {"timeout": {"minutes": 10}}
    session_body = {
        "scenario_managers": ["firstManager"],
        "scenarios": ["1"],
        "equations": ["stock", "flow", "constant"],
    }

    resp = client.post('/start-instance', data=json.dumps(timeout),
                       content_type='application/json',
                       headers={"Authorization": f"Bearer {token}"})
    instance_id = json.loads(resp.data)['instance_uuid']
    resp = client.post(f'/{instance_id}/begin-session', data=json.dumps(session_body),
                       content_type='application/json',
                       headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    instance = server._instance_manager.get_instance(instance_id)
    assert instance.default_backend == "rust"
    # backend field omitted ⇒ session inherits the instance default.
    assert instance.session_state["backend"] == "rust"


def test_request_backend_wins_over_default():
    """Substep 4i: an explicit ``backend`` in the ``/begin-session`` body overrides
    the instance ``default_backend``, keeping A/B comparison against Python
    possible even when the server defaults to Rust."""
    server = BptkServer(__name__, _rust_default_factory, None, token)
    client = server.test_client()
    timeout = {"timeout": {"minutes": 10}}
    session_body = {
        "scenario_managers": ["firstManager"],
        "scenarios": ["1"],
        "equations": ["stock", "flow", "constant"],
        "backend": "python",
    }

    resp = client.post('/start-instance', data=json.dumps(timeout),
                       content_type='application/json',
                       headers={"Authorization": f"Bearer {token}"})
    instance_id = json.loads(resp.data)['instance_uuid']
    resp = client.post(f'/{instance_id}/begin-session', data=json.dumps(session_body),
                       content_type='application/json',
                       headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    instance = server._instance_manager.get_instance(instance_id)
    assert instance.default_backend == "rust"
    # Explicit "python" in the request body wins over the "rust" instance default.
    assert instance.session_state["backend"] == "python"


def test_resume_rust_session_externalized(tmp_path):
    """Substep 4g end-to-end: a Rust-backed session that externalises its state
    completely (instance saved + deleted after every request) must produce
    correct results across the implied process restarts.

    With ``externalize_state_completely=True`` the instance is reconstructed from
    the FileAdapter on *every* ``/run-step`` — so the live RustSdModel is gone
    each time and the runner replays ``settings_log`` to rebuild the cursor. The
    accumulated trajectory must match a single-process, in-memory Rust session.
    """
    from BPTK_Py.externalstateadapter.file_adapter import FileAdapter

    # Local factory with a *non-numeric* scenario name. The FileAdapter restores
    # JSON keys by coercing digit-strings back to ints, which would mangle a
    # scenario literally named "1"; that quirk is orthogonal to the resume path
    # under test, so we sidestep it with the name "base".
    def _resume_factory():
        model = Model(starttime=1.0, stoptime=50.0, dt=1.0, name="Resume Model")
        stock = model.stock("stock")
        flow = model.flow("flow")
        constant = model.constant("constant")
        stock.initial_value = 0.0
        stock.equation = flow
        flow.equation = constant
        constant.equation = 1.0
        b = BPTK_Py.bptk()
        b.register_scenario_manager({"chain": {"model": model}})
        b.register_scenarios(scenario_manager="chain",
                             scenarios={"base": {"constants": {"constant": 1.0}}})
        return b

    headers = {"Authorization": f"Bearer {token}"}
    session_body = {
        "scenario_managers": ["chain"],
        "scenarios": ["base"],
        "equations": ["stock", "flow", "constant"],
        "backend": "rust",
    }

    # ---- Reference: single in-memory Rust session via direct bptk calls. ----
    ref = _resume_factory()
    ref.begin_session(scenario_managers=["chain"], scenarios=["base"],
                      equations=["stock", "flow", "constant"], backend="rust")
    ref_steps = [ref.run_step() for _ in range(6)]
    ref.end_session()

    # ---- Externalised server: instance round-trips through disk each call. ----
    adapter = FileAdapter(compress=True, path=str(tmp_path))
    server = BptkServer(__name__, _resume_factory, adapter, token,
                        externalize_state_completely=True)
    client = server.test_client()

    resp = client.post('/start-instance', data=json.dumps({"timeout": {"minutes": 10}}),
                       content_type='application/json', headers=headers)
    instance_id = json.loads(resp.data)['instance_uuid']

    resp = client.post(f'/{instance_id}/begin-session', data=json.dumps(session_body),
                       content_type='application/json', headers=headers)
    assert resp.status_code == 200

    # The instance is not in memory between requests — each /run-step reloads it.
    assert not server._instance_manager.is_valid_instance(instance_id)

    server_steps = []
    step_body = {"settings": {}}
    for _ in range(6):
        resp = client.post(f'/{instance_id}/run-step', data=json.dumps(step_body),
                           content_type='application/json', headers=headers)
        assert resp.status_code == 200, resp.data
        server_steps.append(json.loads(resp.data))

    # Compare the resumed-each-step server trajectory to the in-memory reference.
    for i in range(6):
        ref_sc = ref_steps[i]["chain"]["base"]
        srv_sc = server_steps[i]["chain"]["base"]
        for eq in ("stock", "flow", "constant"):
            (ref_t, ref_v), = ref_sc[eq].items()
            srv_eq = srv_sc[eq]
            # Server JSON keys are strings; match the single value regardless of key form.
            (srv_v,) = srv_eq.values()
            assert ref_v == pytest.approx(srv_v, rel=1e-9), \
                f"step {i} eq {eq}: reference={ref_v} server={srv_v}"


def test_metrics(app, client):
    response = client.get('/metrics')
    assert response.status_code == 200

def test_full_metrics(app, client):
    response = client.get('/full-metrics')
    assert response.status_code == 200
    result = json.loads(response.data)
    assert result['instanceCount'] == 0

    # When an instance has an active session, its per-uuid entry in the
    # metrics dict must carry the current step and start time. Without an
    # active session the metrics walker skips the instance entirely.
    timeout = {"timeout": {"hours": 0, "minutes": 10}}
    resp = client.post('/start-instance', data=json.dumps(timeout), content_type='application/json',
                       headers={"Authorization": f"Bearer {token}"})
    instance_id = json.loads(resp.data)['instance_uuid']

    session = {
        "scenario_managers": ["firstManager"],
        "scenarios": ["1"],
        "equations": ["stock", "flow", "constant"],
    }
    resp = client.post(f'/{instance_id}/begin-session', data=json.dumps(session),
                       content_type='application/json',
                       headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200

    resp = client.get('/full-metrics')
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert instance_id in data
    assert "step" in data[instance_id]
    assert "startTime" in data[instance_id]

def test_instance_timeouts(app, client):
    import time

    timeout = {
        "timeout": {
            "weeks":0,
            "days":0,
            "hours":0,
            "minutes":0,
            "seconds":10,
            "milliseconds":0,
            "microseconds":0
        }
    }


    response = client.post('/start-instance', data=json.dumps(timeout), content_type='application/json',headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    id = json.loads(response.data)['instance_uuid']

    response = client.get('/full-metrics')
    assert response.status_code == 200
    result = json.loads(response.data)
    assert result['instanceCount'] == 1
    time.sleep(6)

    response = client.get('/full-metrics')
    assert response.status_code == 200
    result = json.loads(response.data)
    assert result['instanceCount'] == 1
    time.sleep(6)

    response = client.get('/full-metrics')
    assert response.status_code == 200
    result = json.loads(response.data)
    assert result['instanceCount'] == 0


def test_keep_alive(app, client):
    import time

    timeout_data = {
        "timeout": {
            "weeks":0,
            "days":0,
            "hours":0,
            "minutes":0,
            "seconds":5,
            "milliseconds":0,
            "microseconds":0
        }
    }

    instances_data = {
        "timeout": {
            "weeks":0,
            "days":0,
            "hours":0,
            "minutes":0,
            "seconds":5,
            "milliseconds":0,
            "microseconds":0
        },
        "instances":2
    }


    response = client.post('/start-instance', data=json.dumps(timeout_data), content_type='application/json',headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    id = json.loads(response.data)['instance_uuid']

    response = client.post('/start-instance', data=json.dumps(timeout_data), content_type='application/json',headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200

    response = client.post('/start-instances', data=json.dumps(instances_data), content_type='application/json',headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    result = json.loads(response.data)
    assert len(result["instance_uuids"])==2



    response = client.get('/full-metrics')
    assert response.status_code == 200
    result = json.loads(response.data)
    assert result['instanceCount'] == 4
    time.sleep(3)

    response = client.post('/' + id + "/keep-alive",headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200

    response = client.get('/full-metrics')
    assert response.status_code == 200
    result = json.loads(response.data)
    assert result['instanceCount'] == 4
    time.sleep(3)

    response = client.get('/full-metrics')
    assert response.status_code == 200
    result = json.loads(response.data)
    assert result['instanceCount'] == 1
    time.sleep(3)

    response = client.get('/full-metrics')
    assert response.status_code == 200
    result = json.loads(response.data)
    assert result['instanceCount'] == 0

    # keep-alive with an unknown uuid returns 500 with the canonical message
    # rather than touching the timestamp dict.
    response_invalid = client.post('/never-existed-uuid/keep-alive',
                                   headers={"Authorization": f"Bearer {token}"})
    assert response_invalid.status_code == 500
    assert b'expecting a valid instance id' in response_invalid.data




def test_instance_timeouts(app, client):
    import time

    timeout = {
        "timeout": {
            "weeks":0,
            "days":0,
            "hours":0,
            "minutes":0,
            "seconds":10,
            "milliseconds":0,
            "microseconds":0
        }
    }


    response = client.post('/start-instance', data=json.dumps(timeout), content_type='application/json',headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    id = json.loads(response.data)['instance_uuid']

    response = client.get('/full-metrics')
    assert response.status_code == 200
    result = json.loads(response.data)
    assert result['instanceCount'] == 1
    time.sleep(6)

    response = client.get('/full-metrics')
    assert response.status_code == 200
    result = json.loads(response.data)
    assert result['instanceCount'] == 1
    time.sleep(6)

    response = client.get('/full-metrics')
    assert response.status_code == 200
    result = json.loads(response.data)
    assert result['instanceCount'] == 0



def test_run_steps(app, client):

    timeout = {
        "timeout": {
            "weeks":0,
            "days":0,
            "hours":0,
            "minutes":10,
            "seconds":0,
            "milliseconds":0,
            "microseconds":0
        }
    }

    response = client.post('/start-instance', data=json.dumps(timeout), content_type='application/json',headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200, "start-instance response should be 200"
    id = json.loads(response.data)['instance_uuid']
    invalid_id= id + '1'

    #error if scenario manager is missing
    session_with_missing_sm = {
        "scenarios": [
            "1"
        ],
        "equations": [
            "stock",
            "flow",
            "constant",
        ]        
    }
    response_with_no_sm = client.post('/' + id + '/begin-session', data=json.dumps(session_with_missing_sm), content_type='application/json',headers={"Authorization": f"Bearer {token}"})
    assert response_with_no_sm.status_code == 500 # checking the status code    
    assert b'expecting scenario_managers to be set' in response_with_no_sm.data

    #error if scenario is missing
    session_with_missing_scenario = {
        "scenario_managers": [
            "firstManager"
        ],
        "equations": [
            "stock",
            "flow",
            "constant",
        ]        
    }
    response_with_no_scenario = client.post('/' + id + '/begin-session', data=json.dumps(session_with_missing_scenario), content_type='application/json',headers={"Authorization": f"Bearer {token}"})
    assert response_with_no_scenario.status_code == 500 # checking the status code    
    assert b'expecting scenarios to be set' in response_with_no_scenario.data

    #error if equations and agents are missing
    session_with_missing_equations_and_agents = {
        "scenario_managers": [
            "firstManager"
        ],
        "scenarios": [
            "1"
        ],
    }
    response_with_no_equations_and_agents = client.post('/' + id + '/begin-session', data=json.dumps(session_with_missing_equations_and_agents), content_type='application/json',headers={"Authorization": f"Bearer {token}"})
    assert response_with_no_equations_and_agents.status_code == 500 # checking the status code    
    assert b'expecting either equations or agents to be set' in response_with_no_equations_and_agents.data

    session = {
        "scenario_managers": [
            "firstManager"
        ],
        "scenarios": [
            "1"
        ],
        "equations": [
            "stock",
            "flow",
            "constant",
        ]
    }

    #error if data is not json
    response_with_not_json = client.post('/' + id + '/begin-session', data=session, headers={"Authorization": f"Bearer {token}"})
    assert response_with_not_json.status_code == 500 # checking the status code    
    assert b'please pass the request with content-type application/json' in response_with_not_json.data

    #error if instance id does not exist
    response_with_invalid_id = client.post('/' + invalid_id + '/begin-session', data=json.dumps(session), content_type='application/json',headers={"Authorization": f"Bearer {token}"})
    assert response_with_invalid_id.status_code == 500 # checking the status code    
    assert b'expecting a valid instance id to be given' in response_with_invalid_id.data

    #valid request
    response = client.post('/' + id + '/begin-session', data=json.dumps(session), content_type='application/json',headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200, "begin-session response should be 200"

    #run step: error if instance id does not exist
    query_single_step={
        "settings": {
            "firstManager": {
                "1": {
                    "constants": {
                        "constant":7.0
                    }
                }
            }
        }
    }    
    response_with_invalid_id_step = client.post(f"/{invalid_id}/run-step", data=json.dumps(query_single_step), content_type='application/json',headers={"Authorization": f"Bearer {token}"})
    assert response_with_invalid_id_step.status_code == 500 # checking the status code    
    assert b'expecting a valid instance id to be given' in response_with_invalid_id_step.data

    #run step: error if settings are missing
    empty_query={}
    response_without_settings = client.post(f"/{id}/run-step", data=json.dumps(empty_query), content_type='application/json',headers={"Authorization": f"Bearer {token}"})
    assert response_without_settings.status_code == 500 # checking the status code
    assert b'expecting settings to be set' in response_without_settings.data

    #run step: non-json request advances the simulation with no per-step overrides
    response_run_step_no_body = client.post(f"/{id}/run-step", headers={"Authorization": f"Bearer {token}"})
    assert response_run_step_no_body.status_code == 200

    #run step: locked instance → 500
    instance = app._instance_manager.get_instance(id)
    instance.lock()
    response_run_step_locked = client.post(f"/{id}/run-step", data=json.dumps(query_single_step),
                                           content_type='application/json',
                                           headers={"Authorization": f"Bearer {token}"})
    assert response_run_step_locked.status_code == 500
    assert b'locked' in response_run_step_locked.data
    instance.unlock()

    #run step: if instance.run_step returns None, the endpoint returns 500
    with mock.patch.object(instance, "run_step", return_value=None):
        response_run_step_none = client.post(f"/{id}/run-step", headers={"Authorization": f"Bearer {token}"})
        assert response_run_step_none.status_code == 500
        assert b'no data was returned' in response_run_step_none.data

    #run steps: error if instance id does not exist
    query={
        "settings": {
            "firstManager": {
                "1": {
                    "constants": {
                        "constant":7.0
                    }
                }
            }
        },
        "numberSteps": 20
    }
    response_with_invalid_id_steps = client.post(f"/{invalid_id}/run-steps", data=json.dumps(query), content_type='application/json',headers={"Authorization": f"Bearer {token}"})
    assert response_with_invalid_id_steps.status_code == 500 # checking the status code    
    assert b'expecting a valid instance id to be given' in response_with_invalid_id_steps.data

    #run steps: error if settings are missing
    query_with_missing_settings={
        "numberSteps": 20
    }
    response_with_missing_settings = client.post(f"/{id}/run-steps", data=json.dumps(query_with_missing_settings), content_type='application/json',headers={"Authorization": f"Bearer {token}"})
    assert response_with_missing_settings.status_code == 500 # checking the status code    
    assert b'expecting settings to be set' in response_with_missing_settings.data

    #run steps: error if number of steps are missing
    query_with_missing_number_of_steps={
        "settings": {
            "firstManager": {
                "1": {
                    "constants": {
                        "constant":7.0
                    }
                }
            }
        },
    }
    response_with_missing_number_of_steps = client.post(f"/{id}/run-steps", data=json.dumps(query_with_missing_number_of_steps), content_type='application/json',headers={"Authorization": f"Bearer {token}"})
    assert response_with_missing_number_of_steps.status_code == 500 # checking the status code    
    assert b'expecting a number of steps to be provided in the body as a json' in response_with_missing_number_of_steps.data

    #run steps: error if request is not json
    response_with_not_json = client.post('/' + id + '/run-steps', data=query, headers={"Authorization": f"Bearer {token}"})
    assert response_with_not_json.status_code == 500 # checking the status code    
    assert b'please pass the request with content-type application/json' in response_with_not_json.data

    #run steps: valid request
    response = client.post('/' + id + '/run-steps', data=json.dumps(query), content_type = 'application/json',headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200, "run-steps response should be 200"

    result = json.loads(response.data)
    assert len(result) == 20

    #run steps: if instance.run_step raises mid-loop, the bare except must
    #unlock the instance so subsequent calls aren't permanently blocked.
    instance = app._instance_manager.get_instance(id)

    def _raise(*args, **kwargs):
        raise RuntimeError("simulated run_step failure")

    with mock.patch.object(instance, "run_step", side_effect=_raise):
        client.post('/' + id + '/run-steps', data=json.dumps(query),
                    content_type='application/json',
                    headers={"Authorization": f"Bearer {token}"})
    assert not instance.is_locked()

    #flat session results: error if instance id does not exist
    response_with_invalid_id_flat = client.get(f"/{invalid_id}/flat-session-results", content_type='application/json',headers={"Authorization": f"Bearer {token}"})
    assert response_with_invalid_id_flat.status_code == 500 # checking the status code    
    assert b'expecting a valid instance id to be given' in response_with_invalid_id_flat.data

    #flat session results: valid request
    response = client.get(f"/{id}/flat-session-results", content_type='application/json',headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200, "flat-session-results response should be 200"

    #session results: error if instance id does not exist
    response_with_invalid_id_session = client.get(f"/{invalid_id}/session-results", content_type='application/json',headers={"Authorization": f"Bearer {token}"})
    assert response_with_invalid_id_session.status_code == 500 # checking the status code    
    assert b'expecting a valid instance id to be given' in response_with_invalid_id_session.data

    #session results: valid request
    response = client.get(f"/{id}/session-results", content_type='application/json',headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200, "session-results response should be 200"

    #stream steps: error if instance id does not exists
    response_stream_with_invalid_id = client.post(f"/{invalid_id}/stream-steps", data=json.dumps(query), content_type='application/json',headers={"Authorization": f"Bearer {token}"})
    assert response_stream_with_invalid_id.status_code == 500 # checking the status code    
    assert b'expecting a valid instance id to be given' in response_stream_with_invalid_id.data

    #stream steps: error if steps are missing
    response_stream_without_settings= client.post(f"/{id}/stream-steps", data=json.dumps(empty_query), content_type='application/json',headers={"Authorization": f"Bearer {token}"})
    assert response_stream_without_settings.status_code == 500 # checking the status code    
    assert b'expecting settings to be set' in response_stream_without_settings.data

    #end session: error if instance id does not exist
    response_with_invalid_id_end = client.post(f"/{invalid_id}/end-session", content_type='application/json',headers={"Authorization": f"Bearer {token}"})
    assert response_with_invalid_id_end.status_code == 500 # checking the status code    
    assert b'expecting a valid instance id to be given' in response_with_invalid_id_end.data

    #end session: valid request
    response = client.post(f"/{id}/end-session", content_type='application/json',headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200, "end-session response should be 200"

    #stop instance
    response = client.post(f"/{id}/stop-instance", content_type='application/json',headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200, "stop-instance response should be 200"


def test_run_steps_lock(app, client):

    timeout = {
        "timeout": {
            "weeks":0,
            "days":0,
            "hours":0,
            "minutes":10,
            "seconds":0,
            "milliseconds":0,
            "microseconds":0
        }
    }

    response = client.post('/start-instance', data=json.dumps(timeout), content_type='application/json',headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    id = json.loads(response.data)['instance_uuid']

    session = {
        "scenario_managers": [
            "firstManager"
        ],
        "scenarios": [
            "1"
        ],
        "equations": [
            "stock",
            "flow",
            "constant",
        ]
    }

    response = client.post('/' + id + '/begin-session', data=json.dumps(session), content_type='application/json',headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200

    query={
        "settings": {
            "firstManager": {
                "1": {
                    "constants": {
                        "constant":7.0
                    }
                }
            }
        },
        "numberSteps": 20
    }

    thread_results = [None, None]

    def _run_steps_lock(requests, index):
        requests[index] = client.post('/' + id + '/run-steps', data=json.dumps(query), content_type = 'application/json',headers={"Authorization": f"Bearer {token}"})

    import threading
    import time
    t1 = threading.Thread(target=_run_steps_lock, daemon=True, args=[thread_results, 0])
    t2 = threading.Thread(target=_run_steps_lock, daemon=True, args=[thread_results, 1])
    t1.start()
    t2.start()

    t1.join()
    t2.join()

    assert thread_results[0].status_code == 200
    assert thread_results[1].status_code == 500

    result = json.loads(thread_results[0].data)
    assert len(result) == 20

    time.sleep(1)
    request = client.post('/' + id + '/run-steps', data=json.dumps(query), content_type = 'application/json',headers={"Authorization": f"Bearer {token}"})
    assert request.status_code == 200
    result = json.loads(request.data)
    assert len(result) == 20

def test_stream_steps_lock(app, client):

    timeout = {
        "timeout": {
            "weeks":0,
            "days":0,
            "hours":0,
            "minutes":10,
            "seconds":0,
            "milliseconds":0,
            "microseconds":0
        }
    }

    response = client.post('/start-instance', data=json.dumps(timeout), content_type='application/json',headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    id = json.loads(response.data)['instance_uuid']

    session = {
        "scenario_managers": [
            "firstManager"
        ],
        "scenarios": [
            "1"
        ],
        "equations": [
            "stock",
            "flow",
            "constant",
        ]
    }

    response = client.post('/' + id + '/begin-session', data=json.dumps(session), content_type='application/json',headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200


    query={
        "settings": {
            "firstManager": {
                "1": {
                    "constants": {
                        "constant":7.0
                    }
                }
            }
        }
    }

    thread_results = [None, None]

    def _stream_steps_lock(requests, index):
        requests[index] = client.post('/' + id + '/stream-steps', data=json.dumps(query), content_type = 'application/json',headers={"Authorization": f"Bearer {token}"})

    import threading
    import time
    t1 = threading.Thread(target=_stream_steps_lock, daemon=True, args=[thread_results, 0])
    t2 = threading.Thread(target=_stream_steps_lock, daemon=True, args=[thread_results, 1])
    t1.start()
    t2.start()

    t1.join()
    t2.join()

    assert thread_results[0].status_code == 200
    assert thread_results[1].status_code == 500

    result = json.loads(thread_results[0].data)
    assert len(result) == 50


# ----------------------------------------------------------------------------
# /execute endpoint 
#
# /execute is a self-contained sibling of /run: the request body carries the
# JSON model definition itself (same schema as Model.to_json()) and the server
# runs it through the Rust engine. No scenario manager is pre-registered, so
# these tests deliberately use the `empty_app` / `empty_client` fixtures —
# proving the endpoint doesn't accidentally depend on self._bptk.
# ----------------------------------------------------------------------------

def _build_execute_simple_model_dict():
    """Trivial constant model — `x = 42` for 6 timesteps.

    Returned as a Python dict (not a JSON string) so test cases can tweak
    fields before serialising into the request body.
    """
    model = Model(starttime=0, stoptime=5, dt=1, name="simple")
    c = model.constant("x")
    c.equation = 42.0
    return json.loads(model.to_json())


def _build_execute_sir_model_dict():
    """SIR epidemic model — mirrors the SIR fixture in test_rust_backend.py
    so /execute exercises the same shape of model as the run_scenarios tests."""
    model = Model(starttime=0, stoptime=20, dt=0.25, name="SIR")
    susceptible = model.stock("susceptible")
    infected = model.stock("infected")
    recovered = model.stock("recovered")
    infection = model.flow("infection")
    recovery = model.flow("recovery")
    contact_rate = model.constant("contact_rate")
    transmission_prob = model.constant("transmission_prob")
    duration = model.constant("duration")

    susceptible.initial_value = 990.0
    infected.initial_value = 10.0
    recovered.initial_value = 0.0

    susceptible.equation = -infection
    infected.equation = infection - recovery
    recovered.equation = recovery

    infection.equation = contact_rate * transmission_prob * susceptible * infected
    recovery.equation = infected / duration

    contact_rate.equation = 10.0
    transmission_prob.equation = 0.001
    duration.equation = 5.0
    return json.loads(model.to_json())


def _build_execute_lookup_model_dict():
    """Model with a graphical function. Lets /execute exercise the `points`
    override path, which has to normalise list-of-list JSON into the
    `Vec<(f64, f64)>` shape PyO3's set_points requires."""
    model = Model(starttime=0, stoptime=10, dt=1, name="lookup_test")
    stock = model.stock("stock")
    flow = model.flow("flow")
    rate = model.converter("rate")
    stock.initial_value = 0.0
    stock.equation = flow
    flow.equation = rate
    model.points["rate_table"] = [[0, 1], [5, 5], [10, 2]]
    rate.equation = sd.lookup(sd.time(), "rate_table")
    return json.loads(model.to_json())


def test_execute_resource(empty_app, empty_client):
    """Covers /execute happy paths and every 400-error branch in one
    function, matching the single-big-test style of test_run_resource above.

    Branches exercised:
      * minimal single-scenario request (default scenario name)
      * full SIR model with multiple equations
      * multiple scenarios with constant overrides isolated per scenario
      * runspec override changes the number of timesteps in the response
      * points override accepts list-of-list (no JSON tuples)
      * 400 paths: non-JSON body, missing model, missing equations,
        empty equations, invalid model (unknown function), py_callback node
    """

    # ── Happy path: minimal model, no scenarios block ─────────────────────
    payload = {
        "model": _build_execute_simple_model_dict(),
        "equations": ["x"],
    }
    response = empty_client.post(
        '/execute',
        data=json.dumps(payload),
        content_type='application/json',
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200, response.data
    data = json.loads(response.data)
    # Default scenario name kicks in when the request omits the `scenarios` key.
    assert "default" in data
    x_series = data["default"]["x"]
    assert len(x_series) == 6  # t = 0,1,2,3,4,5
    for t in range(6):
        assert x_series["{:.1f}".format(t)] == 42.0

    # ── Happy path: SIR model with multiple equations ─────────────────────
    payload = {
        "model": _build_execute_sir_model_dict(),
        "scenarios": {"baseline": {}},
        "equations": ["susceptible", "infected", "recovered"],
    }
    response = empty_client.post(
        '/execute',
        data=json.dumps(payload),
        content_type='application/json',
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200, response.data
    data = json.loads(response.data)
    assert "baseline" in data
    assert set(data["baseline"].keys()) == {"susceptible", "infected", "recovered"}
    # Initial state at t=0 — value parity with the Python backend is validated
    # elsewhere (test_rust_backend.py); here we only confirm response contract.
    assert data["baseline"]["susceptible"]["0.0"] == pytest.approx(990.0)
    assert data["baseline"]["infected"]["0.0"] == pytest.approx(10.0)
    assert data["baseline"]["recovered"]["0.0"] == pytest.approx(0.0)

    # ── Happy path: per-scenario constant overrides are isolated ──────────
    payload = {
        "model": _build_execute_sir_model_dict(),
        "scenarios": {
            "low":  {"constants": {"transmission_prob": 0.0005}},
            "high": {"constants": {"transmission_prob": 0.002}},
        },
        "equations": ["infected"],
    }
    response = empty_client.post(
        '/execute',
        data=json.dumps(payload),
        content_type='application/json',
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200, response.data
    data = json.loads(response.data)
    last_key = "20.0"
    # The two scenarios are separate engines — high transmission must drive
    # the epidemic further than low transmission by the final timestep.
    assert data["high"]["infected"][last_key] != data["low"]["infected"][last_key]

    # ── Happy path: runspec override changes step count ───────────────────
    payload = {
        "model": _build_execute_simple_model_dict(),  # default stoptime=5, dt=1 → 6 steps
        "scenarios": {
            "short": {},
            "long":  {"runspecs": {"stoptime": 10.0}},
        },
        "equations": ["x"],
    }
    response = empty_client.post(
        '/execute',
        data=json.dumps(payload),
        content_type='application/json',
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200, response.data
    data = json.loads(response.data)
    assert len(data["short"]["x"]) == 6
    assert len(data["long"]["x"]) == 11

    # ── Happy path: points override accepts list-of-list ──────────────────
    payload = {
        "model": _build_execute_lookup_model_dict(),
        "scenarios": {
            "flat": {"points": {"rate_table": [[0, 10], [5, 10], [10, 10]]}},
        },
        "equations": ["rate"],
    }
    response = empty_client.post(
        '/execute',
        data=json.dumps(payload),
        content_type='application/json',
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200, response.data
    data = json.loads(response.data)
    # Flat 10-everywhere lookup → rate should be 10 at every timestep.
    for value in data["flat"]["rate"].values():
        assert value == pytest.approx(10.0)

    # ── 400: non-JSON request body ────────────────────────────────────────
    response_not_json = empty_client.post(
        '/execute',
        data="not json at all",
        content_type='text/plain',
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response_not_json.status_code == 400
    assert b'application/json' in response_not_json.data

    # ── 400: missing `model` field ────────────────────────────────────────
    payload_missing_model = {"equations": ["x"]}
    response_missing_model = empty_client.post(
        '/execute',
        data=json.dumps(payload_missing_model),
        content_type='application/json',
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response_missing_model.status_code == 400
    assert b'model' in response_missing_model.data

    # ── 400: missing `equations` field ────────────────────────────────────
    payload_missing_eqs = {"model": _build_execute_simple_model_dict()}
    response_missing_eqs = empty_client.post(
        '/execute',
        data=json.dumps(payload_missing_eqs),
        content_type='application/json',
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response_missing_eqs.status_code == 400
    assert b'equations' in response_missing_eqs.data

    # ── 400: empty equations list ────────────────────────────────────────
    payload_empty_eqs = {
        "model": _build_execute_simple_model_dict(),
        "equations": [],
    }
    response_empty_eqs = empty_client.post(
        '/execute',
        data=json.dumps(payload_empty_eqs),
        content_type='application/json',
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response_empty_eqs.status_code == 400
    assert b'non-empty list' in response_empty_eqs.data

    # ── 400: invalid model — unknown function name surfaces from the
    #        Rust engine and is translated to a 400 client error, not a 500.
    payload_invalid_model = {
        "model": {
            "name": "broken",
            "specs": {"starttime": 0.0, "stoptime": 1.0, "dt": 1.0},
            "entities": {
                "constants": [{
                    "name": "x",
                    "equation": {
                        "type": "call",
                        "function": "this_function_does_not_exist",
                        "args": [],
                    },
                }],
            },
        },
        "equations": ["x"],
    }
    response_invalid_model = empty_client.post(
        '/execute',
        data=json.dumps(payload_invalid_model),
        content_type='application/json',
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response_invalid_model.status_code == 400
    assert b'Rust engine error' in response_invalid_model.data

    # ── 400: py_callback nodes are a Phase 6 feature; the endpoint must
    #        reject any model containing them anywhere in the expression
    #        tree (here: nested inside a binary_op, proving the walker
    #        descends into every child).
    payload_py_callback = {
        "model": {
            "name": "with_callback",
            "specs": {"starttime": 0.0, "stoptime": 1.0, "dt": 1.0},
            "entities": {
                "constants": [{
                    "name": "x",
                    "equation": {
                        "type": "binary_op",
                        "op": "add",
                        "left": {"type": "literal", "value": 1.0},
                        "right": {"type": "py_callback", "function": "user_fn"},
                    },
                }],
            },
        },
        "equations": ["x"],
    }
    response_py_callback = empty_client.post(
        '/execute',
        data=json.dumps(payload_py_callback),
        content_type='application/json',
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response_py_callback.status_code == 400
    assert b'py_callback' in response_py_callback.data


def test_execute_resource_authentication(empty_app, empty_client):
    """Bearer-token enforcement: /execute is behind @token_required and must
    reject unauthenticated requests before any other validation runs."""
    payload = {
        "model": _build_execute_simple_model_dict(),
        "equations": ["x"],
    }

    # No Authorization header at all → 401.
    response_no_auth = empty_client.post(
        '/execute',
        data=json.dumps(payload),
        content_type='application/json',
    )
    assert response_no_auth.status_code == 401

    # Wrong token → 401 (consistent with the rest of the server).
    response_bad_token = empty_client.post(
        '/execute',
        data=json.dumps(payload),
        content_type='application/json',
        headers={"Authorization": "Bearer wrong-token"},
    )
    assert response_bad_token.status_code == 401

    # Right token → request is processed (200 confirms it reached the body).
    response_ok = empty_client.post(
        '/execute',
        data=json.dumps(payload),
        content_type='application/json',
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response_ok.status_code == 200


# InstanceManager direct unit tests
#
# These cover paths the public REST API can't easily reach — race-condition
# guards (KeyError swallowing) and direct-method outputs.

class _FaultyKeyDict(dict):
    """Dict that lies: keys appear in `.keys()` and `__contains__`, but
    `__getitem__` raises KeyError. Reproduces the race condition the
    `try/except KeyError` guards in InstanceManager are designed to swallow."""
    def __getitem__(self, key):
        raise KeyError(key)


def test_instance_manager_get_instance_invalid():
    """``InstanceManager.get_instance`` must return ``None`` both when the
    UUID is unknown and when the entry is malformed (missing the nested
    ``instance`` key)."""
    instance_manager = InstanceManager(bptk_factory="test")

    # Unknown UUID → None.
    assert instance_manager.get_instance(instance_uuid=1) is None

    # UUID is present but the entry is missing the "instance" key; the
    # method must not raise, just return None.
    instance_manager._instances = {1: {"time": 0}}
    assert instance_manager.get_instance(instance_uuid=1) is None


def test_instance_manager_get_instance_states_returns_all():
    """``get_instance_states`` walks every registered instance and returns
    one ``InstanceState`` per entry."""
    im = InstanceManager(bptk_factory=lambda: BPTK_Py.bptk())

    uuid_a = im.create_instance(hours=1)
    uuid_b = im.create_instance(hours=1)

    states = im.get_instance_states()
    assert len(states) == 2
    assert {s.instance_id for s in states} == {uuid_a, uuid_b}


def test_instance_manager_update_timestamp_swallows_keyerror():
    """``_update_instance_timestamp`` must swallow ``KeyError`` when the
    entry it looks up has been removed between the ``is_valid_instance``
    check and the subsequent indexing — a race-condition guard."""
    im = InstanceManager(bptk_factory=lambda: BPTK_Py.bptk())
    # The faulty dict reports "u1" present (so is_valid_instance returns
    # True) but raises KeyError on __getitem__, matching the production race.
    im._instances = _FaultyKeyDict({"u1": None})
    im._update_instance_timestamp("u1")  # must not raise


def test_instance_manager_timeout_instances_swallows_keyerror():
    """``_timeout_instances`` must swallow ``KeyError`` if an entry vanishes
    mid-iteration. Same race-condition pattern as the timestamp updater."""
    im = InstanceManager(bptk_factory=lambda: BPTK_Py.bptk())
    im._instances = _FaultyKeyDict({"u1": None})
    im._timeout_instances()  # must not raise


# Configurable external state adapter
#
# A hand-rolled adapter that lets each method be set to raise, return None,
# or behave normally. Used by the cleanup / _ensure_instance_exists tests
# below to drive the failure branches that a real FileAdapter / RedisAdapter
# would rarely hit but the server must handle gracefully.

class _ConfigurableAdapter:
    """Drop-in for ExternalStateAdapter that does NOT inherit from it (to
    skip the abstract-method dance). Implements just the surface the server
    actually calls: save_instance / load_instance / delete_instance."""

    def __init__(self):
        self.save_raises = None         # set to an Exception instance to raise
        self.load_returns = "missing"   # "missing" → return None, else return value
        self.delete_raises = None       # FileNotFoundError or generic Exception
        self.saved_states = []
        self.deleted_ids = []
        self.load_calls = 0

    def save_instance(self, state):
        if self.save_raises is not None:
            raise self.save_raises
        self.saved_states.append(state)

    def load_instance(self, instance_uuid):
        self.load_calls += 1
        if self.load_returns == "missing":
            return None
        return self.load_returns

    def delete_instance(self, instance_uuid):
        if self.delete_raises is not None:
            raise self.delete_raises
        self.deleted_ids.append(instance_uuid)


def test_cleanup_instance_swallows_adapter_failure():
    """When the adapter's save_instance raises while cleanup is running, the
    error must be logged and swallowed — clients never see a 500 from this
    path."""
    adapter = _ConfigurableAdapter()
    adapter.save_raises = RuntimeError("simulated save failure")
    server = BptkServer(__name__, bptk_factory, adapter, token,
                        externalize_state_completely=True)
    client = server.test_client()

    timeout = {"timeout": {"hours": 0, "minutes": 10}}
    resp = client.post('/start-instance', data=json.dumps(timeout),
                       content_type='application/json',
                       headers={"Authorization": f"Bearer {token}"})
    # The save raised inside cleanup, but the request itself still returned
    # successfully — the exception is swallowed.
    assert resp.status_code == 200


def test_cleanup_new_instances_inner_exception_swallowed():
    """Inner try/except in _cleanup_new_instances_if_needed catches per-
    instance failures so one bad instance doesn't break the others."""
    adapter = _ConfigurableAdapter()
    adapter.save_raises = RuntimeError("simulated save failure")
    server = BptkServer(__name__, bptk_factory, adapter, token,
                        externalize_state_completely=True)
    client = server.test_client()

    # /start-instances creates N instances and runs cleanup on each in turn.
    # Per-instance failures get swallowed; the endpoint still returns 200.
    instances_data = {"instances": 3, "timeout": {"minutes": 10}}
    resp = client.post('/start-instances', data=json.dumps(instances_data),
                       content_type='application/json',
                       headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200


def test_cleanup_new_instances_outer_exception_swallowed():
    """If the outer iteration itself blows up (e.g. someone passes a non-
    iterable), the outer try/except catches it."""
    server = BptkServer(__name__, bptk_factory, _ConfigurableAdapter(), token,
                        externalize_state_completely=True)
    # 12345 is not iterable; the bare `except Exception` must swallow.
    server._cleanup_new_instances_if_needed(12345)


def test_stop_instance_handles_file_not_found():
    """When the adapter's delete_instance raises FileNotFoundError (e.g. the
    instance was never persisted), /stop-instance must still return 200."""
    adapter = _ConfigurableAdapter()
    adapter.delete_raises = FileNotFoundError("not on disk")
    server = BptkServer(__name__, bptk_factory, adapter, token,
                        externalize_state_completely=False)
    client = server.test_client()

    timeout = {"timeout": {"hours": 0, "minutes": 10}}
    resp = client.post('/start-instance', data=json.dumps(timeout),
                       content_type='application/json',
                       headers={"Authorization": f"Bearer {token}"})
    instance_id = json.loads(resp.data)['instance_uuid']

    resp = client.post(f'/{instance_id}/stop-instance',
                       headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200


def test_stop_instance_handles_generic_adapter_exception():
    """Same as above but with a non-FileNotFoundError exception — must hit
    the second ``except Exception`` arm."""
    adapter = _ConfigurableAdapter()
    adapter.delete_raises = RuntimeError("simulated adapter failure")
    server = BptkServer(__name__, bptk_factory, adapter, token,
                        externalize_state_completely=False)
    client = server.test_client()

    timeout = {"timeout": {"hours": 0, "minutes": 10}}
    resp = client.post('/start-instance', data=json.dumps(timeout),
                       content_type='application/json',
                       headers={"Authorization": f"Bearer {token}"})
    instance_id = json.loads(resp.data)['instance_uuid']

    resp = client.post(f'/{instance_id}/stop-instance',
                       headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200


def test_ensure_instance_exists_returns_false_when_adapter_has_no_state():
    """When the adapter returns None for load_instance, _ensure_instance_exists
    must return False — not crash and not reconstruct a phantom instance."""
    adapter = _ConfigurableAdapter()  # default: load_instance returns None
    server = BptkServer(__name__, bptk_factory, adapter, token,
                        externalize_state_completely=False)
    client = server.test_client()

    # Any endpoint that goes through _ensure_instance_exists with an unknown
    # uuid drives the adapter consult; /begin-session is a convenient choice.
    session = {"scenario_managers": ["firstManager"], "scenarios": ["1"],
               "equations": ["stock"]}
    resp = client.post('/never-existed-uuid/begin-session',
                       data=json.dumps(session), content_type='application/json',
                       headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 500
    assert b'expecting a valid instance id' in resp.data
    assert adapter.load_calls == 1  # confirms the adapter was consulted


# ---------------------------------------------------------------------------
# bptkServer coverage: model-definition validator, cleanup failure, and the
# "Rust engine unavailable" import guard.
# ---------------------------------------------------------------------------

def test_check_for_py_callbacks_edge_cases():
    """The py_callback validator handles non-dict models, list-nested callbacks
    and list-nested non-dict leaves."""
    from BPTK_Py.server.bptkServer import _check_for_py_callbacks

    # A model that is not a JSON object at all.
    assert _check_for_py_callbacks("not a dict") == "model must be a JSON object"

    # py_callback buried inside a list-valued arg must be rejected (the walker
    # descends into list items, not just dict children).
    model_list_callback = {"entities": {"constants": [
        {"name": "x", "equation": {"type": "call", "args": [{"type": "py_callback"}]}}]}}
    assert "py_callback" in _check_for_py_callbacks(model_list_callback)

    # A clean model whose list arg contains a non-dict leaf is accepted.
    model_list_scalar = {"entities": {"constants": [
        {"name": "x", "equation": {"type": "call", "args": [5.0]}}]}}
    assert _check_for_py_callbacks(model_list_scalar) is None


def test_cleanup_instance_failure_is_logged():
    """A failure during instance cleanup is caught and logged, never raised."""
    import BPTK_Py.logger.logger as logmod
    logmod.loglevel = "INFO"
    with open(logmod.logfile, "w", encoding="UTF-8"):
        pass

    server = BptkServer(__name__, empty_bptk_factory,
                        external_state_adapter=mock.Mock(),
                        externalize_state_completely=True)
    # Force the cleanup body to raise.
    server._instance_manager._get_instance_state = mock.Mock(side_effect=RuntimeError("boom"))

    server._cleanup_instance_if_needed("some-uuid")  # must not raise

    with open(logmod.logfile, "r", encoding="UTF-8") as f:
        content = f.read()
    assert "[ERROR] Cleanup failed for instance some-uuid" in content


def test_execute_rust_engine_unavailable(empty_client):
    """/execute returns 500 when the compiled Rust engine cannot be imported."""
    body = json.dumps({"model": _build_execute_simple_model_dict(), "equations": ["x"]})
    # Setting the module to None in sys.modules makes `import ...` raise ImportError.
    with mock.patch.dict("sys.modules", {"BPTK_Py._rust_engine": None}):
        resp = empty_client.post('/execute', data=body, content_type='application/json',
                                 headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 500
    assert b"Rust engine is not available" in resp.data
