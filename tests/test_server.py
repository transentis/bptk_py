from BPTK_Py.server import BptkServer
import requests
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

    response = client.post('/run', data=json.dumps(query), content_type = 'application/json',headers={"Authorization": f"Bearer {token}"})
    
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

def test_scenarios_resource(app, client):
    response = client.get('/scenarios',headers={"Authorization": f"Bearer {token}"})
    data=json.loads(response.data)
    assert data["firstManager"] == ["1"]
    assert data["secondManager"] == ["1","2","3"]
    assert response.status_code == 200 # checking the status code
    
def test_equations_resource(app, client):
    query = {
        "scenarioManager": "firstManager",
        "scenario":"1"
    }
    response = client.post('/equations', data=json.dumps(query), content_type = 'application/json',headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200 # Checking the status code
    equations = [b"constants", b"converters", b"flows", b"points"]
    for equation in equations: # checking words in request data
        assert equation in response.data
    
def test_agents_resource(app, client):
    response = client.post('/agents', content_type = 'application/json',headers={"Authorization": f"Bearer {token}"})
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
    assert response.status_code == 200, "begin-session response should be 200"


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

    response = client.post('/' + id + '/run-steps', data=json.dumps(query), content_type = 'application/json',headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200, "run-steps response should be 200"

    result = json.loads(response.data)
    assert len(result) == 20

    response = client.post(f"/{id}/end-session", content_type='application/json',headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200, "end-session response should be 200"


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
    t1 = threading.Thread(target=_run_steps_lock, args=[thread_results, 0])
    t2 = threading.Thread(target=_run_steps_lock, args=[thread_results, 1])
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
    t1 = threading.Thread(target=_stream_steps_lock, args=[thread_results, 0])
    t2 = threading.Thread(target=_stream_steps_lock, args=[thread_results, 1])
    t1.start()
    t2.start()

    t1.join()
    t2.join()

    assert thread_results[0].status_code == 200
    assert thread_results[1].status_code == 500
    
    result = json.loads(thread_results[0].data)
    assert len(result) == 50