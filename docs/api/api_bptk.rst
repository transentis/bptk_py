****
bptk
****

The ``bptk`` class provides high level functions that let you interact with your simulation models and scenarios.

You will typically start the framework by instantiating the ``bptk`` class within a Jupyer notebook, as follows: ::

 import BPTK_PY
 bptk=bptk()

This automatically starts a background process that scans your ``scenario`` directory and imports all scenarios.

The method returns nothing or a Pandas dataframe with simulation results if return_df=True

.. py:module:: BPTK_Py.bptk
.. autoclass:: bptk
   :members:


