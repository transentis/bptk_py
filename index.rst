.. bptk_py documentation master file, created by
   sphinx-quickstart on Sat Jan 26 13:45:44 2019.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

###########################################################
BPTK-Py: System Dynamics and Agent-based Modeling In Python
###########################################################

The Business Prototyping Toolkit for Python (BPTK-Py) is a computational modeling framework that enables you to build simulation models using System Dynamics (SD) and/or agent-based modeling (ABM) and manage simulation scenarios with ease.

Next to providing the necessary SD and ABM language constructs to build models directly in Python, the framework also includes a compiler for transpiling  System Dynamics models conforming to the XMILE standard into Python code.

This means you can build models in a XMILE-compatible visual modeling environment (such as `iseesystems Stella <http://www.iseesystems.com>`_) and then use them _independently_ in an Python enviroment.

The best way to get started with BPTK-Py is our tutorial, which contains a number of simulation models and Jupyter notebooks to get you started – you can clone or download the tutorial from our `git repository <https://bitbucket.org/transentis/bptk_py_tutorial/>`_ on Bitbucket.

Main Features
=============

* The BPTK-Py framework supports System Dynamics models in XMILE Format, native SD models and native Agent-based models. You can also build hybrid SD-ABM-Models natively in Python.
* The objective of the framework is to let the modeller concentrate on building simulation models by providing a seamless interface for managing model settings and scenarios and for plotting simulation results.
* All plotting is done using `Matplotlib <http://www.matplotlib.org>`_.
* Simulation results are returned as `Pandas dataframes <http://pandas.pydata.org>`_.
* Model settings and scenarios are kept in JSON files. These settings are automatically loaded by the framework upon initialization, as are the model classes themselves. This makes interactive modeling, coding and testing very painless, especially if using the Jupyter notebook environment.

Getting Help
============

BPTK-Py is developed and maintained by `transentis labs <http://www.transentis.com>`_. For questions regarding installation or usage and for feature requests, please  contact us at: `support@transentis.com <mailto:support@transentis.com>`_.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   docs/usage/installation
   docs/usage/quickstart
   docs/usage/limitations
   docs/how_to/how_to_overview
   docs/in_depth/in_depth_overview
   docs/api/api_overview

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
