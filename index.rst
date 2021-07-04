.. bptk_py documentation master file, created by
   sphinx-quickstart on Sat Jan 26 13:45:44 2019.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

###########################################################
BPTK-Py: System Dynamics and Agent-based Modeling In Python
###########################################################

.. meta::
   :description: In-depth explanation of agent-based modeling
   :keywords: agent-based modeling, system dynamics, python, bptk, sddsl, xmile, smile, stella, ithink

The Business Prototyping Toolkit for Python (BPTK-Py) is a computational modeling framework that enables you to build simulation models using System Dynamics (SD) and/or agent-based modeling (ABM) and manage simulation scenarios with ease.

Next to providing the necessary SD and ABM language constructs to build models directly in Python, the framework also includes a compiler for transpiling  System Dynamics models conforming to the XMILE standard into Python code.

This means you can build models in a XMILE-compatible visual modeling environment (such as `iseesystems Stella <http://www.iseesystems.com>`_) and then use them *independently* in a Python environment such as `JupyterLabs <https://jupyter.org>`_.

The best way to get started with BPTK-Py is our tutorial, which contains a number of simulation models and Jupyter notebooks to get you started – you can clone or download the tutorial from our `git repository <https://github.com/transentis/bptk_py_tutorial/>`_ on Github.

Main Features
=============

* The BPTK-Py framework supports System Dynamics models in XMILE Format, native SD models and native Agent-based models. You can also build hybrid SD-ABM-Models natively in Python.
* The objective of the framework is to let the modeller concentrate on building simulation models by providing a seamless interface for managing model settings and scenarios and for plotting simulation results.
* All plotting is done using `Matplotlib <http://www.matplotlib.org>`_.
* Simulation results are returned as `Pandas dataframes <http://pandas.pydata.org>`_.
* Model settings and scenarios are kept in JSON files. These settings are automatically loaded by the framework upon initialization, as are the model classes themselves. This makes interactive modeling, coding and testing very painless, especially if using the Jupyter notebook environment.

Getting Help
============

BPTK-Py is developed and maintained by `transentis labs <https://www.transentis.com/business-prototyping-toolkit/en/>`_.

The best place to ask questions about the framework is our `Business Prototyping Toolkit Meetup <https://www.meetup.com/business-prototyping-toolkit>`_, which meets online regularly.

You can also contact us any time at `support@transentis.com <mailto:support@transentis.com>`_, we are always happy to help.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   docs/usage/installation
   docs/usage/quickstart
   docs/usage/limitations
   docs/general/general
   docs/abm/abm
   docs/xmile/xmile
   docs/sd-dsl/sd-dsl
   docs/api/api_overview

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
