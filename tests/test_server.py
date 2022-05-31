from BPTK_Py.server import BptkServer
import requests
import json
import pytest


from BPTK_Py import Model
import BPTK_Py


def bptk_factory():
    model = Model(starttime=1.0,stoptime=5.0, dt=1.0, name="Test Model")
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
    flask_app = BptkServer(__name__, bptk_factory)
    yield flask_app


@pytest.fixture
def client(app):
    return app.test_client()
        
def test_home_resource(app, client):
    response = client.get('/')
    assert response.status_code ==  200 
    assert response.data == b"<h1>BPTK-Py REST API Server</h1>"
    
def test_run_resource(app, client):
    query={
        "scenario_managers":["firstManager"],
        "scenarios":["1"],
        "equations":["stock","flow","constant"],
        "settings":{
            
                         "firstManager":
                             {
                                 "1":
                                     {
                                         "constants":
                                         {
                                            "constant":7.0 
                                         }
                                     }
                             }
                     }
            
        
    }

    response = client.post('/run', data=json.dumps(query), content_type = 'application/json')
    
    assert response.status_code == 200 # checking the status code

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

    response = client.post('/start-instance', data=json.dumps(timeout), content_type='application/json')
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

    response = client.post('/' + id + '/begin-session', data=json.dumps(session), content_type='application/json')
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

    response = client.post('/' + id + '/run-step', data=json.dumps(query), content_type = 'application/json')
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

    response = client.post('/start-instance', data=json.dumps(timeout), content_type='application/json')
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

    response = client.post('/' + id + '/begin-session', data=json.dumps(session), content_type='application/json')
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

    response = client.post('/' + id + '/stream-steps', data=json.dumps(query), content_type = 'application/json')
    assert response.status_code == 200 # checking the status code

def test_scenarios_resource(app, client):
    response = client.get('/scenarios')
    data=json.loads(response.data)
    assert data["firstManager"] == ["1"]
    assert data["secondManager"] == ["1","2","3"]
    assert response.status_code == 200 # checking the status code
    
def test_equations_resource(app, client):
    query = {
        "scenarioManager": "firstManager",
        "scenario":"1"
    }
    response = client.post('/equations', data=json.dumps(query), content_type = 'application/json')
    assert response.status_code == 200 # Checking the status code
    equations = [b"constants", b"converters", b"flows", b"points"]
    for equation in equations: # checking words in request data
        assert equation in response.data
    
def test_agents_resource(app, client):
    response = client.post('/agents', content_type = 'application/json')
    assert response.status_code == 400 # System dynamics systems shouldn't have agents 

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


    response = client.post('/start-instance', data=json.dumps(timeout), content_type='application/json')
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

    timeout = {
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


    response = client.post('/start-instance', data=json.dumps(timeout), content_type='application/json')
    assert response.status_code == 200
    id = json.loads(response.data)['instance_uuid']
    
    response = client.post('/start-instance', data=json.dumps(timeout), content_type='application/json')
    assert response.status_code == 200
    
    response = client.get('/full-metrics')
    assert response.status_code == 200
    result = json.loads(response.data)
    assert result['instanceCount'] == 2
    time.sleep(3)
    
    response = client.post('/' + id + "/keep-alive")
    assert response.status_code == 200
    
    response = client.get('/full-metrics')
    assert response.status_code == 200
    result = json.loads(response.data)
    assert result['instanceCount'] == 2
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