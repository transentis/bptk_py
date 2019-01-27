********************
Package dependencies
********************

If for any reason, you want to install the requirements manually or need to know why we need the packages, here comes the list.

If you observe malfunctions in the framework and believe the reason may be incompatibilities with newer versions of the packages, please inform us.

So far, we tested the framework with Python 3.4, 3.6 and 3.7. It should work fine with other Python 3.x versions.

============ ============================================= =====================
Package name What we use it for                            Latest tested version
============ ============================================= =====================
pandas       DataFrames and internal results storage       0.23.4
matplotlib   Plotting environment                          2.2.2
ipywidgets   Widget environment for notebooks              7.4.0
scipy        Linear interpolation for graphical functions  1.1.0
numpy        Linear interpolation and required by pandas   1.15.0
============ ============================================= =====================

If you are using `Jupyter Lab <https://jupyterlab.readthedocs.io>`_, you need the jupyter lab extension for ipywidgets.