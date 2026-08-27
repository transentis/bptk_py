# Front matter the .py format cannot carry; injected on export.
# description: Creating presistent external state for the BPTK-Server.
# keywords: agent-based modeling, abm, bptk, bptk-py, python
# The page documents HTTP calls against a running BptkServer; the build has none,
# so every request would fail with an empty response. eval: false shows the code
# and suppresses the output rather than rendering a page full of JSONDecodeError
#.
# eval: false
import marimo

__generated_with = "0.23.13"
app = marimo.App(app_title="External State Adapter")


@app.cell
def _():
    import marimo as mo

    return (mo,)




@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # ExternalStateAdapter
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    BPTK-Py offers a way to persist data externally. This allows simulation instances to be fully restored from a save point - one example of how we use this in practice is to persist the current state of a [Beer Distribution Game](https://beergame.transentis.com) session to an external database. This ensures that a game can be resumed in the case of a system failure.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## ExternalStateAdapter Constructor

    **ExternalStateAdapter(compress)**

    Abstract base class. A subclass implements three methods and BPTK handles the rest -
    when they are called, and the compression around them.


    * **Parameters**

        **compress** – Boolean.
        Whether BPTK compresses the state on the way to the adapter and decompresses it on
        the way back. Recommended: it reduces the size of an instance considerably.


    ## ExternalStateAdapter._save_instance

    **\_save_instance(state)**

    Write one instance to your storage. Abstract - a subclass must implement it. Called
    through `save_instance` every time an instance step has run.


    * **Parameters**

        **state** – InstanceState.
        The instance to write.


    ## ExternalStateAdapter._load_instance

    **\_load_instance(instance_uuid)**

    Read one instance back and return it as an `InstanceState`. Abstract. Called through
    `load_instance` when the server does not find an instance in its own memory. Return
    `None` when there is nothing stored under that id.


    * **Parameters**

        **instance_uuid** – String.
        The id of the instance to read.


    ## ExternalStateAdapter.delete_instance

    **delete_instance(instance_uuid)**

    Remove one instance from your storage. Abstract. Called when the `stop-instance`
    endpoint is called, and after every use when the server runs with
    `externalize_state_completely=True`.


    * **Parameters**

        **instance_uuid** – String.
        The id of the instance to remove.


    ## ExternalStateAdapter.save_instance

    **save_instance(state)**

    Provided by the base class, and what `BptkServer` actually calls: it compresses the
    state when compression is on and then calls your `_save_instance`. Override it only if
    your adapter needs to handle compression itself - `FileAdapter` does.


    ## ExternalStateAdapter.load_instance

    **load_instance(instance_uuid)**

    Provided by the base class, the counterpart of `save_instance`: it calls your
    `_load_instance` and decompresses what comes back.


    ## InstanceState

    **InstanceState(state, instance_id, time, timeout, step)**

    The dataclass an adapter reads and writes. `state` is the simulation state itself,
    `instance_id` the id it is stored under, `time` when it was written, `timeout` the
    instance timeout and `step` the step it had reached.


    ## Using persistent state

    To persist state, an instantiation of a class inheriting `BPTK_Py.ExternalStateAdapter` must be passed into the BPTK-server constructor. When an adapter is provided, BPTK will call the corresponding methods in the provided `ExternalStateAdapter` implementation automatically.

    BPTK provides `BPTK_Py.FileAdapter`, an implementation of the `ExternalStateAdapter` class that can be used to store the state locally in JSON files.
    Creating your own implementation for `ExternalStateAdapter` (for example to save the state to an external database) is trivial.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Let's look at an example on how to add persistent state using BPTK's `FileAdapter`:
    """)
    return


@app.cell
def _():
    from BPTK_Py import BptkServer
    from BPTK_Py import FileAdapter
    from model import bptk_factory
    import os
    import json

    adapter = FileAdapter(True, os.path.join(os.getcwd(), "state"))
    return BptkServer, adapter, bptk_factory, json


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    The code above imports all required modules and creates a new `FileAdapter` object. The `FileAdapter` init method takes two arguments:

    1. Compression. When enabled, BPTK sends a compressed format of the instance state to the provided `ExternalStateAdapter` and automatically decompresses the instance states on load.
    2. Directory path. The path to which the state will be saved and from which the state will be loaded. This directory must be empty on first start-up.
    """)
    return


@app.cell
def _(BptkServer, adapter, bptk_factory):
    # Calling the BptkServer class
    application = BptkServer(__name__, bptk_factory, external_state_adapter=adapter)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Running the code above will create a new BPTK-server. The server takes the `adapter` as an optional argument. When no adapter is provided, the state will not be saved.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## How does it work?
    *To follow the rest of this page, start a BPTK server yourself: the `run_server.sh` script (or `run_server.bat` under Windows) sits in this page's own directory. The requests below are shown rather than run, because a documentation build has no server to talk to.*

    When an `ExternalStateAdapter` is provided, BPTK calls it by itself. Three methods are
    abstract, so those are the ones a subclass has to provide:

    1. `_save_instance`: takes an `InstanceState` and writes it. Called when an instance step is run.
    2. `_load_instance`: takes an instance id and returns an `InstanceState`. Called when an instance is not in the server's own memory.
    3. `delete_instance`: takes an instance id and removes it. Called when the `stop-instance` endpoint is called.

    The implementation handles nothing but the IO with the storage solution. Let's look at
    an example:
    """)
    return


@app.cell
def _():
    import requests

    req = requests.post("http://localhost:5000/start-instance")
    instance_id = req.json()['instance_uuid']
    return instance_id, requests


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    The code above starts a new BPTK simulation instance and returns the instance id.
    """)
    return


@app.cell
def _(instance_id, json, requests):
    content = {'scenario_managers': ['sddsl_customer_acquisition'], 'scenarios': ['interactive_scenario'], 'equations': ['customers', 'word_of_mouth_success']}
    req_1 = requests.post(f'http://localhost:5000/{instance_id}/begin-session', json.dumps(content), headers={'Content-Type': 'application/json'})
    req_1.json()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    The code above starts a new session for a given instance.
    """)
    return


@app.cell
def _(instance_id, json, requests):
    step = {'settings': {'sddsl_customer_acquisition': {'interactive_scenario': {'constants': {'word_of_mouth_success': 0.7}}}}}
    req_2 = requests.post(f'http://localhost:5000/{instance_id}/run-step', json.dumps(step), headers={'Content-Type': 'application/json'})
    req_2.json()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    When `run-step` is called, BPTK will call the provided `ExternalStateAdapter` to save that instance. This way, every instance is always up to date.

    You will see a JSON-File with the instance id as its name in the state directory.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Implementing your own ExternalStateAdapter

    Implementing your own `ExternalStateAdapter` is trivial. All the logic is handled by BPTK. The adapter must only handle the IO with the storage solution.
    Let's look at an example dummy implementation:
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ```python
    from BPTK_Py import ExternalStateAdapter
    from BPTK_Py import InstanceState
    import datetime
    import json


    class DBAdapter(ExternalStateAdapter):
        def __init__(self, compress: bool, db_client):
            super().__init__(compress)
            self.db_client = db_client

        def _save_instance(self, state: InstanceState):
            self.db_client.save(
                key=state.instance_id,
                data={
                    "state": json.dumps(state.state),
                    "instance_id": state.instance_id,
                    "time": str(state.time),
                    "timeout": state.timeout,
                    "step": state.step,
                },
            )

        def _load_instance(self, instance_uuid: str) -> InstanceState:
            try:
                data = json.loads(self.db_client.read(key=instance_uuid))
                return InstanceState(
                    json.loads(data["state"]),
                    data["instance_id"],
                    datetime.datetime.now(),
                    data["timeout"],
                    data["step"],
                )
            except Exception as e:
                print("Error: " + str(e))
                return None

        def delete_instance(self, instance_uuid: str):
            try:
                self.db_client.delete(key=instance_uuid)
            except Exception as e:
                print("Error: " + str(e))
    ```
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    The code above implements the three abstract methods and nothing else - a real adapter
    needs no more. `_load_instance` and `delete_instance` can be called for instances that
    are not in the database, so error handling is advisable. The block is shown rather than
    run: it needs a database client this page does not have.
    """)
    return


if __name__ == "__main__":
    app.run()
