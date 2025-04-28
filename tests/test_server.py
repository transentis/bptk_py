from BPTK_Py.server import BptkServer
import json
import pytest


from BPTK_Py import Model
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

    #To do: Add tests for an actual Agent based or hybrid model

def test_metrics(app, client):
    response = client.get('/metrics')
    assert response.status_code == 200

def test_full_metrics(app, client):
    response = client.get('/full-metrics')
    assert response.status_code == 200
    result = json.loads(response.data)
    assert result['instanceCount'] == 0

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