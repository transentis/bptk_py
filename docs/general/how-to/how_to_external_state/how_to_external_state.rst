Persisting the BPTK-Server State
================================

*Using the ExternalStateAdapter*

BPTK-Py offers a way to persist data externally. This allows simulation
instances to be fully restored from a save point - one example of how we
use this in practice is to persist the current state of a `Beer
Distribution Game <https://beergame.transentis.com>`__ session to an
external database. This ensures that a game can be resumed in the case
of a system failure.

Using persistent state
----------------------

To persist state, an instantiation of a class inheriting
``BPTK_Py.ExternalStateAdapter`` must be passed into the BPTK-server
constructor. When an adapter is provided, BPTK will call the
corresponding methods in the provided ``ExternalStateAdapter``
implementation automatically.

BPTK provides ``BPTK_Py.FileAdapter``, an implementation of the
``ExternalStateAdapter`` class that can be used to store the state
locally in JSON files. Creating your own implementation for
``ExternalStateAdapter`` (for example to save the state to an external
database) is trivial.

Let’s look at an example on how to add persistent state using BPTK’s
``FileAdapter``:

.. code:: ipython3

    from BPTK_Py import BptkServer
    from BPTK_Py import FileAdapter
    from model import bptk_factory
    import os
    import json
    
    adapter = FileAdapter(True, os.path.join(os.getcwd(), "state"))

The code above imports all required modules and creates a new
``FileAdapter`` object. The ``FileAdapter`` init method takes two
arguments: 1. Compression. When enabled, BPTK sends a compressed format
of the instance state to the provided ``ExternalStateAdapter`` and
automatically decompresses the instance states on load. 2. Directory
path. The path to which the state will be saved and from which the state
will be loaded. This directory must be empty on first start-up.

.. code:: ipython3

    # Calling the BptkServer class
    application = BptkServer(__name__, bptk_factory, external_state_adapter=adapter)

Running the code above will create a new BPTK-server. The server takes
the ``adapter`` as an optional argument. When no adapter is provided,
the state will not be saved.

How does it work?
-----------------

*To continue this tutorial, run a new BPTK server using the
``run_server.sh`` script (or ``run_server.bat`` under Windows) in the
current Jupyter notebook directory.*

When an ``ExternalStateAdapter`` is provided, BPTK will automatically
call the methods in the adapter implementation. An
``ExternalStateAdapter`` implements the following methods: 1.
``_save_state``: Takes a list of all instance states as an argument.
This method is called when the ``save-state`` endpoint of the
BPTK-server is called. 2. ``_load_state``: Takes no arguments and
returns a list of all instance states that are stored. This method is
called when the ``load-state`` endpoint of the BPTK-server is called and
on BPTK start-up. 3. ``_save_instance``: Takes an instance state as an
argument. This method is called when an instance step is run. 4.
``_load_instance``: Takes an instance id as an argument. This method is
called when an instance cannot be found in local storage. 5.
``delete_instance``: Takes an instance id as an argument. This method is
called when the stop-instance endpoint is called.

The implementation handles IO with the storage solution. Let’s look at
an example:

.. code:: ipython3

    import requests
    
    req = requests.post("http://localhost:5000/start-instance")
    instance_id = req.json()['instance_uuid']


The code above starts a new BPTK simulation instance and returns the
instance id.

.. code:: ipython3

    content = {
        "scenario_managers": [
            "sddsl_customer_acquisition"
        ],
        "scenarios": [
            "interactive_scenario"
        ],
        "equations": [
            "customers","word_of_mouth_success"
        ]
    }
    
    req = requests.post(f'http://localhost:5000/{instance_id}/begin-session', json.dumps(content), headers={'Content-Type': 'application/json'})
    req.json()




.. parsed-literal::

    {'msg': 'session started'}



The code above starts a new session for a given instance.

.. code:: ipython3

    step = {     
        "settings":{
            "sddsl_customer_acquisition":
            {
                "interactive_scenario":
                {
                    "constants":
                    {
                        "word_of_mouth_success":0.7
                    }
                }, 
            }
        }
    }
    
    req = requests.post(f'http://localhost:5000/{instance_id}/run-step', json.dumps(step), headers={'Content-Type': 'application/json'})
    req.json()




.. parsed-literal::

    {'sddsl_customer_acquisition': {'interactive_scenario': {'customers': {'2.0': 1000.0},
       'word_of_mouth_success': {'2.0': 0.7}}}}



When ``run-step`` is called, BPTK will call the provided
``ExternalStateAdapter`` to save that instance. This way, every instance
is always up to date.

You will see a JSON-File with the instance id as its name in the state
directory.

Implementing your own ExternalStateAdapter
------------------------------------------

Implementing your own ``ExternalStateAdapter`` is trivial. All the logic
is handled by BPTK. The adapter must only handle the IO with the storage
solution. Let’s look at an example dummy implementation:

.. code:: ipython3

    from BPTK_Py import ExternalStateAdapter
    from BPTK_Py import InstanceState
    import json
    import datetime
    
    class DBAdapter(ExternalStateAdapter):
        def __init__(self, compress: bool, db_client):
            super().__init__(compress)
            self.db_client = db_client

In the first line we extend ``ExternalStateAdapter``. Then we create a
constructor, taking a boolean and a db_client as an input. - The boolean
value indicates whether the state will be compressed and decompressed by
BPTK. This is recommended, it can drastically reduce the size of an
instance. - The db_client argument represents a dummy database client.
Most database connections work using a database client, adapting this
dummy class to your storage solution should therefore be simple.

.. code:: ipython3

        def _save_state(self, instance_states: list[InstanceState]):
            for state in instance_states:
                self._save_instance(state)
        
    
        def _save_instance(self, state: InstanceState):
            data = { 
                "data": { 
                    "state": json.dumps(state.state), 
                    "instance_id": state.instance_id,
                    "time": str(state.time),
                    "timeout": state.timeout,
                    "step": state.step
                }
            }
            self.db_client.save(key=state.instance_id, data=data)
            
    
        def _load_state(self) -> list[InstanceState]:    
            instances = []
            instance_paths = os.listdir(self.path)
    
            for instance_uuid in instance_paths:
                instances.append(self._load_instance(instance_uuid.split(".")[0]))
    
            return instances
    
        def _load_instance(self, instance_uuid: str) -> InstanceState:
            try:
                instance_data = json.loads(self.db_client.read(key=instance_uuid))
                
                decoded_data = json.loads(instance_data["data"]["state"])
                instance_id = instance_data["data"]["instance_id"]
                timeout = instance_data["data"]["timeout"]
                step = instance_data["data"]["step"]
                
                return InstanceState(decoded_data, instance_id, datetime.datetime.now(), timeout, step)
            except Exception as e:
                print("Error: " + str(e))
                return None
                
        def delete_instance(self, instance_uuid: str):
            try:
                self.db_client.delete(key=instance_uuid)
            except Exception as e:
                print("Error: " + str(e))
                return None

The code above implements all five functions. ``_load_instance`` and
``_delete_instance`` can be called for instances which do not exist in
the database, error handling code is therefore advisable.
