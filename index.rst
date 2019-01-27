.. bptk_py documentation master file, created by
   sphinx-quickstart on Sat Jan 26 13:45:44 2019.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

BPTK_PY: System Dynamics and Agent-based Modeling In Python
===========================================================

The Business Prototyping Toolkit for Python (BPTK_Py) provides you with a framework to build and run simulation models using System Dynamics and/or agent-based modeling.

It gives you the power to quickly build simulation models in Python and create beautiful plots of the simulation results in Jupyter Notebooks - or just run the simulation in Python and use the results however you wish.

The framework also ships with our *sdcc parser*  for transpiling  System Dynamics models conforming to the XMILE standard into Python code. This means you can build models using your favorite XMILE environment (such as `iseesystems Stella <http://www.iseesystems.com>`_) and then experiment with them in Juypter.

Main Features
-------------

* Build simulation models using System Dynamics and/or agent-based modeling and run them in Jupyter.
* Retrieve simulation results as `Pandas DataFrame <https://github.com/pandas-dev/pandas>`_ timeseries data
* Create plots from simulation results
* Build interactive dashboards
* Manage simulation scenarios
* Automatically convert XMILE models into Python and run them in Jupyter

Getting Help
____________

BPTK_Py is developed and maintained by `transentis labs <http://www.transentis.com>`_. For questions regarding installation or usage and for feature requests, please  contact us at: `support@transentis.com <mailto:support@transentis.com>`_.



.. toctree::
   :maxdepth: 1
   :caption: Contents:

   docs/usage/installation
   docs/usage/quickstart
   docs/usage/dependencies
   docs/usage/limitations
   docs/api/api_overview

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
