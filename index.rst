.. bptk_py documentation master file, created by
   sphinx-quickstart on Sat Jan 26 13:45:44 2019.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

###########################################################
BPTK_PY: System Dynamics and Agent-based Modeling In Python
###########################################################

The Business Prototyping Toolkit for Python (BPTK_Py) provides you with a computational modeling framework that allows you to build and run simulation models using System Dynamics and/or agent-based modeling and manage simulation scenarios with ease.

It gives you the power to quickly build simulation models in Python. If you use the framework with Jupyter Notebooks, you to create beautiful plots of the simulation results - or just run the simulation in Python and use the results however you wish.

The framework also includes our *sdcc parser*  for transpiling  System Dynamics models conforming to the XMILE standard into Python code. This means you can build models using your favorite XMILE environment (such as `iseesystems Stella <http://www.iseesystems.com>`_) and then experiment with them in `Juypter <http://www.jupyter.org>`_.

Our tutorial contains a number of models and Jupyter notebooks to get you started – you can download the tutorial from our `website <https://www.transentis.com/products/business-prototyping-toolkit/>`_.

Main Features
=============

* The BPTK_Py framework supports System Dynamics models in XMILE Format, native SD models, Agent-based models and hybrid SD-ABM-Models
* The objective of the framework is to provide the infrastructure for managing model settings and scenarios and for running and plotting simulation results, so that the modeller can concentrate on modelling.
* The framework automatically collect statistics on agents, their states and their properties, which makes plotting simulation results very easy.
* All plotting is done using `Matplotlib <http://www.matplotlib.org>`_.
* Simulation results can also be returned as `Pandas dataframes <http://pandas.pydata.org>`_.
* The framework uses some advanced Python metaprogramming techniques to ensure the amount of boilerplate code the modeler has to write is kept to a minimum.
* Model settings and scenarios are kept in JSON files. These settings are automatically loaded by the framework upon initialization, as are the model classes themselves. This makes interactive modeling, coding and testing very painless, especially if using the Jupyter notebook environment.

Getting Help
============

BPTK_Py is developed and maintained by `transentis labs <http://www.transentis.com>`_. For questions regarding installation or usage and for feature requests, please  contact us at: `support@transentis.com <mailto:support@transentis.com>`_.



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
