# Front matter the .py format cannot carry; injected on export.
# description: BPTK API Documentation for the BptkServer class
# keywords: system dynamics, agent-based modeling, flask, REST, bptk, bptk-py, python, business prototyping
# The page documents HTTP calls against a running BptkServer; the build has none,
# so every request would fail with an empty response. eval: false shows the code
# and suppresses the output rather than rendering a page full of JSONDecodeError
#.
# eval: false
import marimo

__generated_with = "0.23.13"
app = marimo.App(app_title="BptkServer")


@app.cell
def _():
    import marimo as mo

    return (mo,)




@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # BptkServer
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    The REST API server is essentially a wrapper around the regular `bptk`class. The server is implemented using Flask and provides all the REST Endpoints / Routes that you need to interact with a simulation scenario.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ![Overview](./bptk_rest_api_server.svg)
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    The `BptkServer` class provides a REST-API using the Flask framework.

    It is essentially a wrapper around the bptk class that forwards REST API calls to bptk.

    You will typically start the framework by instantiating the `bptk` class within a Jupyer notebook, as follows:

    ```default
    from BPTK_Py.server import BptkServer
    from flask_cors import CORS

    from model import bptk # assuming your model is in a file called model.py that sets up bptk

    # Calling the BptkServer class
    application = BptkServer(__name__, bptk)
    CORS(application)

    if __name__ == "__main__":
       application.run()
    ```

    Assuming you save that code in a file called application.py, you can then start the server fro the command line as follows:

    ```default
    export FLASK_ENV=development
    ```
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## BptkServer Constructor

    **BptkServer(import_name, bptk_factory=None, external_state_adapter=None, bearer_token=None, externalize_state_completely=False)**

    This class provides a Flask-based server that provides a REST-API for running bptk scenarios. The class inherts the properties and methods of Flask and doesn’t expose any further public methods.


    * **Parameters**


        * **import_name** – String.
        Flask's own first argument; pass `__name__`.


        * **bptk_factory** – Callable.
        Called once per instance to build a `bptk` object with the scenario managers this
        server should serve. It is a factory rather than an instance because every
        simulation instance needs its own: two clients must not share one model's state.
        This is also where a server-wide execution engine is set - see
        [Execution Backends](../../concepts/execution_backends/execution_backends.md).


        * **external_state_adapter** – [ExternalStateAdapter](../api_external_state_adapter/api_external_state_adapter.md).
        Where instance state is kept when it is not in this process's memory. Without one,
        state lives and dies with the process.


        * **bearer_token** – String.
        When set, every request must carry it as `Authorization: Bearer …`.


        * **externalize_state_completely** – Boolean (Default=False).
        Makes the server **stateless**. With `False` an instance stays in memory *and* is
        written to the adapter, so the adapter is a safety net. With `True` the instance is
        deleted from memory after every use and read back from the adapter on the next
        request, so this process holds nothing between requests - which is what lets
        several server processes share one workload behind a load balancer, and what lets
        any of them restart without losing a session. It needs an
        `external_state_adapter`; without one there is nowhere to externalise to.

    ## agents

    **POST /agents**

    For an agent-based or hybrid model, this endpoint returns all the agents in the model with their corresponding states and properties.

    ## begin-session

    **POST /{instance_uuid}/begin-session**

    This endpoint starts a session for single step simulation. There can only be one session per instance at a time.

    Besides the scenarios to run, the body takes two optional fields:

    * **backend** – `"python"` or `"rust"`, and it decides the engine for the **whole
      session**: a session keeps the engine it started on for its lifetime. Omit it and the
      server's own default applies. An unknown value is rejected with 400 rather than
      quietly falling back, so a typo is visible.
    * **seed** – pins the Rust engine's random number generator. It matters for a
      **stochastic** session that has to survive a restart: with a seed the resumed session
      replays identically, without one the numbers after the restart are different ones.
      The Python engine ignores it.

    ```json
    {
      "scenario_managers": ["smSirModel"],
      "scenarios": ["base"],
      "equations": ["infected"],
      "backend": "rust",
      "seed": 42
    }
    ```

    ## end-session

    **POST /{instance_uuid}/end-session**

    This endpoint ends a session for single step simulation and resets the internal cache.

    ## execute

    **POST /execute**

    Runs a model that arrives **in the request body**, rather than one registered on the
    server. Where `/run` picks from the scenario managers the server was started with,
    `/execute` is fully self-contained: it touches neither the server's own `bptk`
    instance, nor the instance manager, nor the external state adapter. Its first
    consumer is the visual modeler, where a model is designed in a browser and posted
    here to be run.

    The body carries the model in the same JSON schema that `Model.to_json()` produces,
    a `scenarios` dict of overrides and the `equations` to return:

    ```json
    {
      "model": { "...": "JSON model, same schema as Model.to_json()" },
      "scenarios": {
        "baseline":     { "constants": { "transmission_prob": 0.001 } },
        "high_contact": { "constants": { "transmission_prob": 0.01 } }
      },
      "equations": ["susceptible", "infected", "recovered"]
    }
    ```

    `scenarios` is optional — without it the model runs once under the name `default`.
    Each scenario gets a fresh model, so overrides do not leak between them.

    The response is `{scenario_name: {equation: {t: value}}}`.

    **This endpoint always runs on the Rust engine.** There is no Python alternative for
    a raw JSON model: the Python engine needs the element graph, not the engine's flat
    node format. A server without the compiled engine answers 500; a malformed body, a
    missing `model` or `equations`, or a model the engine cannot load answers 400 naming
    the field or the problem.

    ## equations

    **POST /equations**

    This endpoint returns all available equations given the name of a scenario manager and of a scenario.

    ## flat-session-results

    **GET /{instance_uuid}/flat-session-results**

    Returns the accumulated results of a session, from the first step to the last step that was run in a flat format.

    ## full-metrics

    **GET /full-metrics**

    Returns metrics in JSON format. This endpoint is unprotected.

    The following metrics are returned:

    - Instance count
    - Creation time und current timestep of each instance

    ## healthy

    **GET /healthy**

    Unprotected endpoint useful for health checks, e.g. when running as a Kubernetes pod. It simply returns a HTTP 200 response and doesn't interact with the bptk factory.

    ## keep-alive

    **POST /{instance_uuid}/keep-alive**
    This endpoint sets the “last accessed time” of the instance to the current time to prevent the instance from timeing out.

    Arguments: None

    ## load-state

    **GET /load-state**

    Loads all instances using the external state adapter

    ## root

    **GET /**

    The root endpoint returns a simple html page that can be used for test purposes. The root endpoint is unprotected even if bearer token authorization is turned on.

    ## run-step

    **POST /{instance_uuid}/run-step**

    This endpoint advances the relevant scenarios by one timestep and returns the data for that timestep.

    Arguments:

        instance_uuid: string

            The id of the instance to advance.

    ## run-steps

    **POST /{instance_uuid}/run-steps**

    This endpoint advances the relevant scenarios by one timestep and returns the data for that timestep.

    Arguments:

        instance_uuid: string

            The id of the instance to advance.

    ## session-results

    **GET /{instance_uuid}/session-results**

    Returns the accumulated results of a session, from the first step to the last step that was run.

    ## metrics

    **GET /metrics**

    Returns metrics in a [Prometheus](https://prometheus.io) compatible format. This endpoint is unprotected.

    ## run

    **POST /run**

    Given a JSON dictionary that defines the relevant simulation scenarios and equations, this endpoint runs those scenarios and returns the data generated by the simulations.

    ## save-state

    **GET /save-state**

    Save all instances with the provided external state adapter.

    ## scenarios

    **GET /scenarios**

    The endpoint returns all available scenarios for the current simulation.

    ## start-instance

    **POST /start-instance**

    This endpoint starts a new instance of BPTK on the server side, so that simulations can run in a “private” session. The endpoint returns an instance_id, which is needed to identify the instance in later calls.

    * __Arguments:__

        * __timeout (dict,optional).__ The timeout period after which the instance is delete if it is not accessed in the meantime. The timer is reset every time the instance is accessed. The timeout dictionary can have the following keys: weeks, days, hours, minutes, seconds, milliseconds, microseconds. Values must be integers.

    ## start-instances

    **POST /start-instances**

    This endpoint starts a number of new instances of BPTK on the server side, so that simulations can run in “private” sessions. The endpoint returns a list of instance_id's, which are needed to identify the instances in later calls.

    * __Arguments:__

        * __timeout (dict,optional).__ The timeout period after which the instance is delete if it is not accessed in the meantime. The timer is reset every time the instance is accessed. The timeout dictionary can have the following keys: weeks, days, hours, minutes, seconds, milliseconds, microseconds. Values must be integers.
        * __instances (Integer).__ Number of instances to create
    * __Response:__
       * __instance_uuids.__ List of instance UUIDs.
       * __timeout__:_ The timeouts the instances where started with.

    ## stop-instance

    **POST /{instance_uuid}/stop-instance**

    Deletes the instance and, when the server runs with an external state adapter, its
    stored state as well. Use it to release an instance you are done with rather than
    waiting for it to time out.

    ## stream-steps

    **POST /{instance_uuid}/stream-steps**

    This endpoint is used to stream a simulation. This is useful for long-running simulations, the result of each simulation step is streamed accross the API:

    Arguments:

    > instance_uuid: string

    >     The id of the instance to stream.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Usage

    The following illustrates how to use the BPTK REST API. To get started you first need to start the server for the customer acquisition model from a Terminal console by running the `run_server.sh` script in this directory. The server should then be running on port 5000.
    """)
    return


@app.cell
def _():
    # find documentation for the requests library on https://docs.python-requests.org/
    import requests
    import json

    return (requests,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## List scenarios
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Get a list of scenarios that the server knows about:
    """)
    return


@app.cell
def _(requests):
    response = requests.get("http://localhost:5000/scenarios")
    return (response,)


@app.cell
def _(response):
    response
    return


@app.cell
def _(response):
    response.json()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## List equations
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Get the equations known to the dashboard scenario:
    """)
    return


@app.cell
def _(requests):
    response_1 = requests.post(url='http://localhost:5000/equations', json={'scenarioManager': 'sddsl_customer_acquisition', 'scenario': 'interactive_scenario'})
    return (response_1,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Check the response
    """)
    return


@app.cell
def _(response_1):
    response_1
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Read the response content
    """)
    return


@app.cell
def _(response_1):
    response_1.json()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Run some scenarios
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Get some data for a scenario and some equations:
    """)
    return


@app.cell
def _(requests):
    response_2 = requests.post(url='http://localhost:5000/run', json={'scenario_managers': ['sddsl_customer_acquisition'], 'scenarios': ['base', 'low_word_of_mouth', 'high_word_of_mouth', 'interactive_scenario'], 'equations': ['customers', 'customer_acquisition', 'market_saturation'], 'settings': {'sddsl_customer_acquisition': {'interactive_scenario': {'constants': {'word_of_mouth_success': 0.5}}}}})
    return (response_2,)


@app.cell
def _(response_2):
    response_2
    return


@app.cell
def _(response_2):
    response_2.json()['sddsl_customer_acquisition']['base']['equations']['market_saturation']
    return


@app.cell
def _(requests):
    response_3 = requests.post(url='http://localhost:5000/start-instance')
    return (response_3,)


@app.cell
def _(response_3):
    response_3
    return


@app.cell
def _(response_3):
    instance_uuid = response_3.json()['instance_uuid']
    return (instance_uuid,)


@app.cell
def _(instance_uuid):
    instance_uuid
    return


@app.cell
def _(instance_uuid, requests):
    response_4 = requests.post(url=f'http://localhost:5000/{instance_uuid}/begin-session', json={'scenario_managers': ['sddsl_customer_acquisition'], 'scenarios': ['interactive_scenario'], 'equations': ['customers', 'word_of_mouth_success']})
    return (response_4,)


@app.cell
def _(response_4):
    response_4
    return


@app.cell
def _(response_4):
    response_4.json()
    return


@app.cell
def _(instance_uuid, requests):
    response_5 = requests.post(url=f'http://localhost:5000/{instance_uuid}/run-step')
    return (response_5,)


@app.cell
def _(response_5):
    response_5
    return


@app.cell
def _(response_5):
    response_5.json()
    return


@app.cell
def _(instance_uuid, requests):
    response_6 = requests.post(url=f'http://localhost:5000/{instance_uuid}/run-step', json={'settings': {'sddsl_customer_acquisition': {'interactive_scenario': {'constants': {'word_of_mouth_success': 0.7}}}}})
    return (response_6,)


@app.cell
def _(response_6):
    response_6.json()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    You can start as many instances as you like - typically one for every user that starts an interactive session via a front-end. Let's sart another session to illustrate this.
    """)
    return


@app.cell
def _(requests):
    response_7 = requests.post(url='http://localhost:5000/start-instance')
    return (response_7,)


@app.cell
def _(response_7):
    another_instance_uuid = response_7.json()['instance_uuid']
    return (another_instance_uuid,)


@app.cell
def _(another_instance_uuid):
    another_instance_uuid
    return


@app.cell
def _(another_instance_uuid, requests):
    response_8 = requests.post(url=f'http://localhost:5000/{another_instance_uuid}/begin-session', json={'scenario_managers': ['sddsl_customer_acquisition'], 'scenarios': ['interactive_scenario'], 'equations': ['customers', 'word_of_mouth_success']})
    return


@app.cell
def _(another_instance_uuid, requests):
    response_9 = requests.post(url=f'http://localhost:5000/{another_instance_uuid}/run-step', json={'settings': {'sddsl_customer_acquisition': {'interactive_scenario': {'constants': {'word_of_mouth_success': 0.1}}}}})
    return (response_9,)


@app.cell
def _(response_9):
    response_9.json()
    return


@app.cell
def _(instance_uuid, requests):
    response_10 = requests.post(url=f'http://localhost:5000/{instance_uuid}/run-step', json={'settings': {'sddsl_customer_acquisition': {'interactive_scenario': {'constants': {'word_of_mouth_success': 0.07}}}}})
    return (response_10,)


@app.cell
def _(response_10):
    response_10.json()
    return


if __name__ == "__main__":
    app.run()
