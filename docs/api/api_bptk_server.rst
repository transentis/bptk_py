**********
BptkServer
**********

.. meta::
   :description: Use the BptkServer class to set up an API that let's you run scenarios via REST-calls.
   :keywords: agent-based modeling, system dynamics, systemdynamics, bptk, abm, xmile, stella

The ``BptkServer`` class provides a REST-API using the Flask framework. 

You will typically start the framework by instantiating the ``bptk`` class within a Jupyer notebook, as follows: ::

   from flask import Flask, redirect, url_for, request, make_response, jsonify

   from BPTK_Py.server import BptkServer
   from flask_cors import CORS

   from model import bptk # assuming your model is in a file called model.py that sets up bptk

   # Calling the BptkServer class
   application = BptkServer(__name__, bptk)
   CORS(application)

   if __name__ == "__main__":
      application.run()

This automatically starts a background process that scans your ``scenario`` directory and imports all scenarios.

.. py:module:: BPTK_Py
.. autoclass:: BptkServer
   :members:


