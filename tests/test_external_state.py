from BPTK_Py.server import BptkServer
import requests
import json
import pytest
from BPTK_Py import FileAdapter
from BPTK_Py.externalstateadapter.redis_adapter import RedisAdapter
import os
from BPTK_Py import Model
import BPTK_Py
import redis
from dotenv import load_dotenv
from BPTK_Py import sd_functions as sd
from tests.test_config import TestConfig, requires_redis

@pytest.fixture(params=[True, False], ids=["externalize_completely", "no_externalize"])
def externalize_state_completely(request):
    """Fixture that provides both externalize_state_completely parameter values."""
    return request.param


def bptk_factory():
    model = Model(starttime=1.0,stoptime=5.0, dt=1.0, name="Test Model")

    model.points["delay"] = [
            (1.0, 2.0), 
            (2.0, 2.0), 
            (3.0, 2.0), 
            (4.0, 2.0), 
            (5.0, 2.0)
        ]
    
    model.points["round"] = [
            (1.0, 1.0), 
            (2.0, 2.0), 
            (3.0, 3.0), 
            (4.0, 4.0), 
            (5.0, 5.0)
        ]
    
    stock = model.stock("stock")
    inflow = model.flow("inflow")
    outflow = model.flow("outflow")
    input = model.constant("input")
    converter = model.converter("converter")
    round = model.converter("round")
    round.equation = sd.lookup(sd.time(), "round")
    delay = model.converter("delay")
    delay.equation = sd.lookup(sd.time(), "delay")
    stock.initial_value=400.0
    stock.equation=inflow-outflow
    inflow.equation=input
    outflow.equation=sd.delay(model,inflow,delay,100.0)
    input.equation=100.0
    converter.equation=stock

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
            "scenario1":{
                "constants":
                {
                    "input":100.0
                }
            }

        }


    )

    bptk.register_scenarios(

        scenario_manager="secondManager",
        scenarios=
        {
            "scenario1":{
                "constants":
                {
                    "input":100.0
                    
                }
            },
            "scenario2":{
                "constants":{
                    "input":200.0
                }
            },
            "scenario3":{
                "constants":{
                    "input":300.0
                }
            }

        }


    )

    return bptk

@pytest.fixture
def file_app(externalize_state_completely):
    import os
    if not os.path.exists("state/"):
        os.mkdir("state/")
    adapter = FileAdapter(compress=True, path=os.path.join(os.getcwd(), "state"))
    flask_app = BptkServer(__name__, bptk_factory, external_state_adapter=adapter, externalize_state_completely=externalize_state_completely)
    yield flask_app

    # Cleanup after test
    print("Tearing down Flask app...")
    try:
        # Clean up any remaining instances
        if hasattr(flask_app, '_instance_manager'):
            print("Cleaning up instance manager...")
            # Force cleanup of all instances
            if hasattr(flask_app._instance_manager, '_instances'):
                for instance_id in list(flask_app._instance_manager._instances.keys()):
                    try:
                        flask_app._instance_manager._delete_instance(instance_id)
                        print(f"Cleaned up instance: {instance_id}")
                    except Exception as e:
                        print(f"Error cleaning up instance {instance_id}: {e}")

        # Teardown Flask app context
        with flask_app.app_context():
            pass  # This ensures proper cleanup of app context

        print("Flask app teardown complete")
    except Exception as e:
        print(f"Error during app teardown: {e}")


@pytest.fixture
def file_client_fixture(file_app):
    return file_app.test_client()

def external_state_base(client):
    response = client.post('/start-instance')

    assert response.status_code == 200, "start-instance should return 200"
    result = json.loads(response.data)

    assert "instance_uuid" in result, "start_instance should return an instance id"
    instance_uuid= result["instance_uuid"]

    # Prepare content for begin-session
    content = {
        "scenario_managers": [
            "firstManager"
        ],
        "scenarios": [
            "scenario1"
        ],
        "equations": [
            "converter",
            "delay",
            "inflow",
            "outflow",
            "input",
            "round"
        ]
    }

    response = client.post(f'{instance_uuid}/begin-session', data=json.dumps(content), content_type='application/json')
    assert response.status_code == 200, "begin-session should return 200"

    # Prepare content for run-step
    def make_run_content(value):
        content={
            "settings":{ 
                "firstManager":{
                    "scenario1":{
                "constants":{
                    "input":value
                }
            }}
            },
            "flatResults": False
        }
        return content

    # run some steps
    response = client.post(f'{instance_uuid}/run-step', data=json.dumps(make_run_content(100.0)), content_type='application/json')
    assert response.status_code == 200, "run-step should return 200"

    data= json.loads(response.data)
    assert data["firstManager"]["scenario1"]["input"]["1.0"]==100.0 , "input should have value 100.0"
    assert data["firstManager"]["scenario1"]["converter"]["1.0"]==400.0 , "converter should have value 400.0"
    assert data["firstManager"]["scenario1"]["delay"]["1.0"]==2.0 , "delay should have value 2.0"
    assert data["firstManager"]["scenario1"]["inflow"]["1.0"]==100.0 , "inflow should have value 100.0"
    assert data["firstManager"]["scenario1"]["outflow"]["1.0"]==100.0 , "outflow should have value 100.0"
    response = client.post(f'{instance_uuid}/run-step', data=json.dumps(make_run_content(400.0)), content_type='application/json')
    assert response.status_code == 200, "run-step should return 200"

    data= json.loads(response.data)
    assert data["firstManager"]["scenario1"]["input"]["2.0"]==400.0 , "input should have value 100.0"
    assert data["firstManager"]["scenario1"]["converter"]["2.0"]==400.0 , "converter should have value 400.0"
    assert data["firstManager"]["scenario1"]["delay"]["2.0"]==2.0 , "delay should have value 2.0"
    assert data["firstManager"]["scenario1"]["inflow"]["2.0"]==400.0 , "inflow should have value 100.0"
    assert data["firstManager"]["scenario1"]["outflow"]["2.0"]==100.0 , "outflow should have value 100.0"
    response = client.post(f'{instance_uuid}/run-step', data=json.dumps(make_run_content(400.0)), content_type='application/json')
    assert response.status_code == 200, "run-step should return 200"

    data= json.loads(response.data)
    assert data["firstManager"]["scenario1"]["converter"]["3.0"]==700.0 , "converter should have value 700.0"
    assert data["firstManager"]["scenario1"]["delay"]["3.0"]==2.0 , "delay should have value 2.0"
    assert data["firstManager"]["scenario1"]["inflow"]["3.0"]==400.0 , "inflow should have value 100.0"
    assert data["firstManager"]["scenario1"]["outflow"]["3.0"]==100.0 , "outflow should have value 100.0"

    response = client.post(f'{instance_uuid}/run-step', data=json.dumps(make_run_content(400.0)), content_type='application/json')
    assert response.status_code == 200, "run-step should return 200"

    data= json.loads(response.data)

    assert data["firstManager"]["scenario1"]["converter"]["4.0"]==1000.0 , "converter should have value 1000.0"

    # Cleanup - stop the instance to properly clean up resources
    print("Cleaning up instance...")
    response = client.post(f'{instance_uuid}/stop-instance')
    print("Stop-instance response:", response.status_code)
    assert response.status_code == 200, "stop-instance should return 200"
    
def test_external_state_file(file_client_fixture):
    external_state_base(file_client_fixture)

@pytest.fixture
def redis_app(externalize_state_completely):
    """Create Flask app with Redis adapter"""
    try:
        import redis
        from BPTK_Py.externalstateadapter import RedisAdapter
    except ImportError:
        return None

    redis_url = TestConfig.get_redis_config()

    print(f"Redis URL configured: {bool(redis_url)}")

    try:
        # Connect to Redis
        redis_client = redis.from_url(redis_url, decode_responses=False)

        # Test connection
        redis_client.ping()
    except Exception as e:
        pytest.skip(f"Could not connect to Redis: {e}")
        return None

    # Create Redis adapter
    adapter = RedisAdapter(redis_client, compress=True, key_prefix="bptk:test")
    flask_app = BptkServer(__name__, bptk_factory, external_state_adapter=adapter, externalize_state_completely=externalize_state_completely)

    yield flask_app

    # Cleanup after test
    print("Tearing down Redis Flask app...")
    try:
        # Clean up any remaining instances
        if hasattr(flask_app, '_instance_manager'):
            print("Cleaning up instance manager...")
            if hasattr(flask_app._instance_manager, '_instances'):
                for instance_id in list(flask_app._instance_manager._instances.keys()):
                    try:
                        flask_app._instance_manager._delete_instance(instance_id)
                        print(f"Cleaned up instance: {instance_id}")
                        # Also clean up from Redis
                        adapter.delete_instance(instance_id)
                        print(f"Cleaned up Redis data for instance: {instance_id}")
                    except Exception as e:
                        print(f"Error cleaning up instance {instance_id}: {e}")

        # Clean up any test keys from Redis
        try:
            pattern = "bptk:test:*"
            for key in redis_client.scan_iter(match=pattern):
                redis_client.delete(key)
                print(f"Cleaned up Redis key: {key}")
        except Exception as e:
            print(f"Error cleaning up Redis keys: {e}")

        # Teardown Flask app context
        with flask_app.app_context():
            pass  # This ensures proper cleanup of app context

        print("Redis Flask app teardown complete")
    except Exception as e:
        print(f"Error during Redis app teardown: {e}")


@pytest.fixture
def redis_client_fixture(redis_app):
    return redis_app.test_client()


@requires_redis
def test_external_state_redis(redis_client_fixture):
    """Test external state with Redis adapter - equivalent to file adapter test"""
    external_state_base(redis_client_fixture)


def test_instance_timeouts(file_client_fixture, externalize_state_completely):
    client = file_client_fixture
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
            "scenario1"
        ],
        "equations": [
            "input"
        ]
    }

    response = client.post(f'http://localhost:5000/{instance_id}/begin-session', data=json.dumps(content), content_type='application/json')
    assert response.status_code == 200, "begin-session should return 200"

    run_content = {
        "settings": {

        },
        "flatResults": False
    }

    response = client.post(f'http://localhost:5000/{instance_id}/run-step', data=json.dumps(run_content), content_type='application/json')
    assert response.status_code == 200,"run-step should return 200"

    # Only check for file existence if we're externalizing state completely
    # When externalize_state_completely=False, the instance is kept in memory
    # and only saved to the adapter during cleanup
    if externalize_state_completely:
        dir_content = os.listdir("state/")
        assert instance_id + ".json" in dir_content

  

    
