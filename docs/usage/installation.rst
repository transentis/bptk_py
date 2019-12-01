############
Installation
############

Like every piece of software, BPTK-Py and its dependencies have to be installed correctly.

******************
For Advanced Users
******************

Once you know what you are doing and yo already have a running Python environment, you only need to call ``pip install BPTK-Py`` or ``pip3 install BPTK-Py``.

If you are not an advanced user, it is best to start with our BPTK-Py tutorial, which you can clone or download from our `git repository <https://bitbucket.org/transentis/bptk_py_tutorial/>`_ on Bitbucket.

************************************
Installing Our Tutorial Using Docker
************************************

If you have Docker installed (e.g. Docker Desktop on MacOS or on Windows), follow these steps:

1. On the command line, move into a directory where you would like to store the BPTK-Py tutorial.
2. Clone the BPTK-Py tutorial repository using git clone: ``git clone https://bitbucket.org/transentis/bptk_py_tutorial.git``
3. Run ``docker-compose up``
4. Point your browser at `http://localhost:8888 <http://localhost:8888>`_ – this will open JupyterLab showing the contents of your directory.
5. Open the notebook ``readme.ipynb`` from within JupyterLab.
6. When you are finished, close your browser and call ``docker-compose down`` from within your directory. This will stop and remove the container.

*********************************************
Installing Our Tutorial Starting From Scratch
*********************************************

Assuming you are starting from scratch, you need to perform the following steps:

1. Install Python
2. Clone the BPTK-Py tutorial
3. Set up a virtual environment
4. Install BPTK-Py and JupyterLab
5. Start JupyterLab

Install Python
==============

First of all, you need `Python <https://www.python.org/>`_. Download the latest version for your operating system.

BPTK-Py was tested with Python 3.7, 3.6 and 3.4.

Clone the BPTK-Py tutorial
==========================

On the command line, move into a directory where you would like to store the BPTK-Py tutorial.

Clone the BPTK-Py tutorial repository using ``git clone``::

    git clone https://bitbucket.org/transentis/bptk_py_tutorial.git


Set up a virtual environment
============================

A virtual environment is a local copy of your Python distribution that stores all packages required and does not interfere with your system's packages.

Following steps are required to set up a virtual environment in a folder called ``venv``::

    python3 -m venv venv

Enter the virtual environment using one of the following commands appropriate:::

    source venv/bin/activate  #  For UNIX/Linux/Mac OS X
    venv\Scripts\activate.bat # For Windows

Now you should see "(venv)" at the beginning of your command prompt.

Install BPTK-Py and JupyterLab
==============================

Now we have a virtual environment, we can install BPTK-Py and JupyterLab::

    pip install -r requirements.txt #installs BPTK-Py and JupyterLab
    jupyter labextension install @jupyter-widgets/jupyterlab-manager #installs some extensions for JupyterLab

Start JupyterLab
================

Now you have a functioning version of JupyterLab and can start working  interactively using jupyter notebooks.

Just type ``jupyter lab`` in the terminal to get started. This will automatically open your browser with JupyterLab running in it, pointing at the directory of the tutorial

Open the notebook ``readme.ipynb`` from within JupyterLab.

Once you are finished, close your browser and kill the JupyterLab process in your terminal.

********************
Package dependencies
********************

If for any reason, you want to install the requirements manually or need to know why we need the packages, here comes the list.

If you observe malfunctions in the framework and believe the reason may be incompatibilities with newer versions of the packages, please inform us.

We have tested the framework with Python 3.4, 3.6 and 3.7. It should work fine with other Python 3.x versions.

============ ================================================
Package name What we use it for
============ ================================================
pandas       DataFrames and internal results storage
matplotlib   Plotting environment
ipywidgets   Widget environment for notebooks
jinja2       Generating python classes for XMILE SD models
parsimonious Parsing XMILE models
pyyaml       Using YAML to specify scenarios (instead of JSON)
scipy        Linear interpolation for graphical functions
numpy        Linear interpolation and required by pandas
xlsxwriter   Exporting simulation results to CSV files
xmltodict    Reading XMILE files
============ ================================================

If you are using `JupyterLab <https://jupyterlab.readthedocs.io>`_, you need the jupyter lab extension for ipywidgets.
