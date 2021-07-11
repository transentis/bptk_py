**********
BptkServer
**********

.. meta::
   :description: Use the BptkServer class to set up an API that let's you run scenarios via REST-calls.
   :keywords: agent-based modeling, system dynamics, systemdynamics, bptk, abm, xmile, stella

The ``BptkServer`` class provides a REST-API using the Flask framework. 

You will typically start the framework by instantiating the ``bptk`` class within a Jupyer notebook, as follows: ::


   from BPTK_Py.server import BptkServer
   from flask_cors import CORS

   from model import bptk # assuming your model is in a file called model.py that sets up bptk

   # Calling the BptkServer class
   application = BptkServer(__name__, bptk)
   CORS(application)

   if __name__ == "__main__":
      application.run()

   
Assuming you save that code in a file called application.py, you can then start the server fro the command line as follows: ::

   export FLASK_ENV=development
   export FLASK_APP=application.py
   python -m flask run

The server is now available on port 5000 and you can call the endpoints documented below.

Our  `Introduction to BPTK <https://github.com/transentis/bptk_intro>`_ repository on GitHub contains an `introductory notebook <https://github.com/transentis/bptk_intro/blob/master/rest-api/api_usage.ipynb>`_ that illustrates how to use the BPTK Rest API.

.. py:module:: BPTK_Py
.. autoclass:: BptkServer
   :members:

.. autoflask:: BPTK_Py.server:BptkServer("test",None)
   :undoc-static:
   :order: path
