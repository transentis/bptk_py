from BPTK_Py.server import BptkServer
import requests
import json
import pytest
from BPTK_Py import FileAdapter
import os
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
    if not os.path.exists("state/"):
        os.mkdir("state/")
    adapter = FileAdapter(True, os.path.join(os.getcwd(), "state"))
    flask_app = BptkServer(__name__, bptk_factory, external_state_adapter=adapter)
    yield flask_app


@pytest.fixture
def client(app):
    return app.test_client()

def test_instance_timeouts(app, client):
    def assert_in_full_metrics(instance_id, contains: bool):
        response = client.get('/full-metrics')
        assert response.status_code == 200, "full-metrics should return 200"
        result = json.loads(response.data)
        if contains:
            assert instance_id in result
        else:
            assert not instance_id in result

    import time


    timeout = {
        "timeout": {
            "weeks":0,
            "days":0,
            "hours":0,
            "minutes":0,
            "seconds":3,
            "milliseconds":0,
            "microseconds":0
        }
    }


    response = client.post('/start-instance', data=json.dumps(timeout), content_type='application/json')
    assert response.status_code == 200, "start-instance should return 200"
    instance_id = json.loads(response.data)['instance_uuid']

    content = {
        "scenario_managers": [
            "firstManager"
        ],
        "scenarios": [
            "1"
        ],
        "equations": [
            "constant"
        ]
    }

    response = client.post(f'http://localhost:500/{instance_id}/begin-session', data=json.dumps(content), content_type='application/json')
    assert response.status_code == 200, "begin-session should return 200"

    run_content = {
        "settings": {

        },
        "flatResults": False
    }

    response = client.post(f'http://localhost:5000/{instance_id}/run-step', data=json.dumps(run_content), content_type='application/json')
    assert response.status_code == 200,"run-step should return 200"

    dir_content = os.listdir("state/")
    assert instance_id + ".json" in dir_content

    assert_in_full_metrics(instance_id, True)

    time.sleep(4)
    assert_in_full_metrics(instance_id, False)

    response = client.post(f'http://localhost:5000/{instance_id}/run-step', data=json.dumps(run_content), content_type='application/json')
    assert response.status_code == 200, "run-step should return 200"

    assert_in_full_metrics(instance_id, True)

    time.sleep(4)

    assert_in_full_metrics(instance_id, False)

    response = client.post('http://localhost:5000/load-state')
    assert response.status_code == 200, "load-state should return 200"

    assert_in_full_metrics(instance_id, True)

    time.sleep(4)

    assert_in_full_metrics(instance_id, False)

    response = client.post('http://localhost:5000/load-state')
    assert response.status_code == 200, "load-state should return 200"

    os.remove(os.path.join("state/", instance_id + ".json"))

    response = client.get('http://localhost:5000/save-state')
    assert response.status_code == 200, "save-state should return 200"


    dir_content = os.listdir("state/")
    assert instance_id + ".json" in dir_content

    response = client.post('http://localhost:5000/load-state')
    assert response.status_code == 200, "load-state should return 200"

    assert_in_full_metrics(instance_id, True)

    response = client.post(f'http://localhost:5000/{instance_id}/stop-instance')
    assert response.status_code == 200, "stop-instance should return 200"

    assert_in_full_metrics(instance_id, False)

    response = client.get('http://localhost:5000/save-state')
    assert response.status_code == 200, "save-state should return 200"

    dir_content = os.listdir("state/")
    assert not instance_id + ".json" in dir_content