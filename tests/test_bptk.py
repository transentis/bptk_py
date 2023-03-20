import pytest
import pandas as pd
from pandas._testing import assert_frame_equal
from unittest import TestCase
import json


from BPTK_Py import Model
from BPTK_Py import sd_functions as sd
import BPTK_Py
from BPTK_Py.util import timerange, normalize



@pytest.fixture
def sd_model():
    """
    Creating a simple system dynamics model for testing.
    "returns":
    bptk: a varible that stores the whole system dynamics model.
    """
    model = Model(starttime=1, stoptime=10, dt=1, name='test')

    stock = model.stock("stock")
    flow = model.flow("flow")
    constant = model.constant("constant")

    stock.initial_value=0.0

    stock.equation = flow
    flow.equation = constant
    constant.equation = 1.0


    bptk = BPTK_Py.bptk()
    bptk.register_scenario_manager({"firstManager":{"model":model}})
    
    bptk.register_scenarios(
          scenarios=
            {
                "1":
                {
                    "constants":
                    {
                        "constant":1.0
                    }
            }
        
    }, scenario_manager = "firstManager")
    
    bptk.register_scenario_manager({"secondManager": {"model":model}})
    bptk.register_scenarios(
        scenarios={
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
        }, scenario_manager="secondManager")
    yield bptk

def sd_results(bptk):
    """
    The function returns the dataframe results based on the stocks, and equations from the systemd dynnamics model.
    "inputs":
    bptk: a varible that stores the whole system dynamics model
    "returns":
    results: the dataframe generated from the current system dynamics model.
    """
    results = bptk.plot_scenarios(
        scenario_managers=["firstManager"],
        scenarios=["1"],
        equations=["stock", "flow"],
        return_df = True
    )
    return results

def test_floating_point():
    assert normalize(3.6,base=0.25,offset=0.0,precision=2) == 3.5
    assert normalize(3.6,base=0.25,offset=0.1,precision=2) == 3.6
    assert normalize(3.6,base=0.25,offset=0.3,precision=2) == 3.55 
    assert timerange(1,10,1) == [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0]
    assert timerange(3.3,7,0.25) == [3.3,3.55,3.8,4.05,4.3,4.55,4.8,5.05,5.3,5.55,5.8,6.05,6.3,6.55,6.8]
    assert timerange(0.0,0.0005,0.0001) == [0.0,0.0001,0.0002,0.0003,0.0004]
    assert timerange(1,10,1,exclusive=False) == [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0,10.0]
    assert timerange(3.3,7,0.25,exclusive=False) == [3.3,3.55,3.8,4.05,4.3,4.55,4.8,5.05,5.3,5.55,5.8,6.05,6.3,6.55,6.8]
    assert timerange(0.0,0.0005,0.0001,exclusive=False) == [0.0,0.0001,0.0002,0.0003,0.0004,0.0005]
 
    
def test_sd_model_results_data_type(sd_model):
    """
    Testing the datatype of the model if it is pandas dataframe or not.
    "inputs":
    "sd_model": the system dynamics function used to create the model
    """
    bptk = sd_model
    results = sd_results(bptk)
    assert isinstance(results, pd.DataFrame)
    
def test_sd_model_results_col_names(sd_model):
    """
    Testing the column names of the dataframe generated from the model.
    "inputs":
    "sd_model": the system dynamics function used to create the model.
    """
    bptk = sd_model
    results = sd_results(bptk)
    scenario = bptk.get_scenario(scenario_manager="firstManager", scenario="1")
    columns_names = list(results.columns)
    equations = ["stock","flow"]
    assert all(col in equations for col in columns_names) # making sure that the column names exist
    
def test_sd_model_results_content(sd_model):
    """
    Testng the content of the dataframe generated from the system dynamics model.
    "inputs":
    "sd_model": the system dynamics function used to create the model.
    """
    bptk = sd_model
    results = sd_results(bptk)
    test_df = pd.DataFrame({'stock': pd.Series(list(range(10)), dtype='float'),
                            'flow': pd.Series([1.0]*10, dtype='float')})
    test_df.index.name =  "t"
    test_df.index += 1.0
      
    assert_frame_equal(results, test_df)
    
def sd_run_scenarios_results(bptk):
    """
    The function returns the dataframe results using the run_scenarios method, based on a simple system dynamics model.
    "inputs":
    bptk: a varible that stores the whole system dynamics model
    "returns":
    results: the dataframe generated from the current system dynamics model.
    """
    results = bptk.run_scenarios(
        scenario_managers=["firstManager"],
        scenarios=["1"],
        equations=["stock", "flow"],
        return_format = "df"
    )
    return results
    
def test_sd_run_scenarios_df_results(sd_model):
    """
    Testing the df return of run simulations in a simple system dynamics model.
    "inputs":
    "sd_model": the system dynamics function used to create the model.
    """
    bptk=sd_model
    results=sd_run_scenarios_results(bptk)
    test_df = pd.DataFrame({'stock': pd.Series(list(range(10)), dtype='float'),
                            'flow': pd.Series([1.0]*10, dtype='float')})
    test_df.index.name =  "t"
    test_df.index += 1.0
      
    assert_frame_equal(results, test_df)
    
def test_sd_run_scenarios_json_results(sd_model):
    """
    Testing the json return of run simulations in a simple system dynamics model.
    "inputs":
    "sd_model": the system dynamics function used to create the model.
    """
    bptk=sd_model
    results=bptk.run_scenarios(
        scenario_managers=["firstManager","secondManager"],
        scenarios=["1"],
        equations=["stock"],
        return_format = "json"
    )
    
    firstManager_stock_df=sd_run_scenarios_results(bptk).rename(columns={"stock": "firstManager_1_stock"})
    secondManager_stock_df=sd_run_scenarios_results(bptk).rename(columns={"stock": "secondManager_1_stock"})

    expected_json={
        "firstManager": {
            "1": {
                "equations": {
                    "stock": firstManager_stock_df["firstManager_1_stock"].to_dict()
                }
            }
        },
        "secondManager":{
            "1":{
                "equations":{
                    "stock": secondManager_stock_df["secondManager_1_stock"].to_dict()
                }
            }
        }
    }
        
    expected_json = json.dumps(expected_json, indent=2)
    assert results==expected_json
    
    
def test_sd_run_scenario_step(sd_model):
    bptk = sd_model
    bptk.begin_session(scenarios=["1","2","3"],scenario_managers=["firstManager","secondManager"],equations=["stock","flow"])
    result = bptk.run_step()

    assert result["firstManager"]["1"]["stock"] == {1.0:0.0}
    assert result["firstManager"]["1"]["flow"] == {1.0:1.0}
    assert result["secondManager"]["2"]["flow"] == {1.0:2.0}

    result=bptk.run_step(settings=
                     {
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
                     })
    
    assert result["firstManager"]["1"]["flow"] == {2.0:7.0}
    assert result["secondManager"]["2"]["stock"] == {2.0:2.0}

    result = bptk.run_step()

    assert result["firstManager"]["1"]["flow"] == {3.0:7.0}
    assert result["firstManager"]["1"]["stock"] == {3.0:8.0}

    bptk.end_session()

    assert bptk.session_state==None



################################
##Testing an Agent Based Model##
################################
@pytest.fixture   
def abm_model():
    """
    The function gets the simple agent based model created inside the abm_model folder.
    "returns":
    bptk: a varible that stores the whole agent-based model
    """
    from abm_model.abmModel import bptk
    yield bptk

def abm_results(bptk):
    """
    The function returns the dataframe results based on scenario 1 of the agent based model provided inside the abm_folder.
    "inputs":
    bptk: a varible that stores the whole agent-based model
    "returns":
    results: the dataframe generated from the current agent-based model.
    """
    results = bptk.plot_scenarios(
        scenario_managers=["testAbmManager"],
        kind="area",
        scenarios=["testScenario"],
        agents=["agent_1"],
        agent_states=["open"],
        agent_properties=["x"],
        agent_property_types=["total"],
        return_df=True
    )    
    return results

def test_abm_get_scenarios(abm_model):
    assert abm_model.get_scenario_names(scenario_managers=["testAbmManager"])==["testScenario2","testScenario"]


def test_abm_results_data_type(abm_model):
    """
    Testing the datatype of the model if it is pandas dataframe or not.
    "inputs":
    "abm_model": the agent-based model function used to extract the model from the abm_folder.
    """
    results = abm_results(abm_model)
    assert isinstance(results, pd.DataFrame)
    
def test_abm_results_col_names(abm_model):
    """
    Testing the column names of the dataframe generated from the model.
    "inputs":
    "abm_model": the agent-based model function used to extract the model from the abm_folder.
    """
    bptk = abm_model
    results = abm_results(bptk)
    scenario = bptk.get_scenario("testAbmManager", "testScenario")
    
    columns_names = list(results.columns)
    
    expected_column_names = []
    for agent in scenario.model.agents:
        for prop in agent.properties.keys():
            col_name = agent.agent_type + "_" + agent.state + "_" + prop + "_total"
            expected_column_names.append(col_name)
        
    assert all(col in expected_column_names for col in columns_names) # making sure that the column names exist
    
def test_abm_results_content(abm_model):
    """
    Testng the content of the dataframe generated from the agent based model.
    "inputs":
    "abm_model": the agent-based model function used to extract the model from the abm_folder.
    """
    bptk = abm_model
    results = abm_results(bptk)
    test_df = pd.DataFrame({'agent_1_open_x_total': pd.Series(list(range(1,11)), dtype='float')})
    test_df.index.name =  "t"
    test_df.index += 1
      
    assert_frame_equal(results, test_df)
    

def abm_run_scenarios_results(bptk, agent_property_type):
    """
    The function returns the dataframe results using the run_scenarios method, based on the agent based model provided inside the abm_folder.
    "inputs":
    bptk: a varible that stores the whole agent-based model
    "returns":
    results: the dataframe generated from the current agent-based model.
    """
    results = bptk.run_scenarios(
        scenario_managers=["testAbmManager"],
        scenarios=["testScenario"],
        agents=["agent_1"],
        agent_states=["open"],
        agent_properties=["x"],
        agent_property_types=[agent_property_type],
        return_format="df"
    )
    return results
    
    
def test_abm_run_scenarios_df_results(abm_model):
    """
    Testing the df return of run simulations in a simple agent-based model.
    "inputs":
    "abm_model": the agent-based model function used to extract the model from the abm_folder.
    """
    bptk=abm_model
    results=abm_run_scenarios_results(bptk, "total")
    column_name = "testAbmManager_testScenario_agent_1_open_x_total"
    test_df = pd.DataFrame({column_name: pd.Series(list(range(1,11)), dtype='float')})
    test_df.index.name =  "t"
    test_df.index += 1
      
    assert_frame_equal(results, test_df)

def test_abm_run_scenarios_json_results(abm_model):
    """
    Testing the json return of run simulations in a simple agent-based model.
    "inputs":
    "abm_model": the agent-based model function used to extract the model from the abm_folder.
    """
    bptk=abm_model
    results=bptk.run_scenarios(
        scenario_managers=["testAbmManager"],
        scenarios=["testScenario"],
        agents=["agent_1"],
        agent_states=["open"],
        agent_properties=["x"],
        agent_property_types=["total", "mean", "max", "min"],
        return_format="json"
    )
    
    total_df = abm_run_scenarios_results(bptk, "total").rename(columns={"testAbmManager_testScenario_agent_1_open_x_total": "open_x_total"})
    min_df = abm_run_scenarios_results(bptk, "min").rename(columns={"testAbmManager_testScenario_agent_1_open_x_min": "open_x_min"})
    mean_df = abm_run_scenarios_results(bptk, "mean").rename(columns={"testAbmManager_testScenario_agent_1_open_x_mean": "open_x_mean"})
    max_df = abm_run_scenarios_results(bptk, "max").rename(columns={"testAbmManager_testScenario_agent_1_open_x_max": "open_x_max"})
    
    
    total_df.index.name=None
    min_df.index.name=None
    mean_df.index.name=None
    max_df.index.name=None
    
    expected_json={
        "testAbmManager": {
            "testScenario": {
                "agents": {
                    "agent_1": {
                        "open": {
                            "properties": {
                                "x": {
                                    "max": max_df["open_x_max"].to_dict(),
                                    "mean": mean_df["open_x_mean"].to_dict(),
                                    "min": min_df["open_x_min"].to_dict(),
                                    "total": total_df["open_x_total"].to_dict()
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    expected_json = json.dumps(expected_json, indent=2)
    assert results==expected_json