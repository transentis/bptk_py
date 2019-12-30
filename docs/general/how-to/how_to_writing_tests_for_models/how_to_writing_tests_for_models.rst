
Writing Tests For Models
========================

To verify the behavior of the simulator and of the simulation model, it
is important to check certain assertions. ``bptk_py`` comes with a
simple model checker to verify ``lambda`` functions.

The function is supposed to only return True or False and receives a
data parameter. For example ``lambda data : sum(data)/len(data) < 0``
tests if the average of the data is below 0. To obtain the raw output
data as required for the model checking, we use the parameter
``return_df=True``. This returns a
`dataFrame <https://pandas.pydata.org/pandas-docs/stable/index.html>`__
object. The following example generates this dataframe and uses the
model checker to test if the ``productivity`` series' mean is below 0.
Otherwise it will return the specified message.

.. code:: ipython3

    from BPTK_Py.bptk import bptk
    bptk = bptk()
    
    df=bptk.plot_scenarios(
        scenario_managers=["smSimpleProjectManagement"],
        scenarios=["scenario120"],
        kind="line",
        equations=["productivity"],
        stacked=False, 
        strategy=True,
        freq="D", 
        start_date="1/11/2017",
        title="Added scenario during runtime",
        x_label="Time",
        y_label="Number",
        return_df=True, 
        series_names= {"smSimpleProjectManagement_scenario120_productivity" : "productivity"}
        )
    
    check_function = lambda data : sum(data)/len(data) < 0
    
    bptk.model_check(df["productivity"],check_function,message="Productivity is not <0")


.. parsed-literal::

    [ERROR] Model Checking failed with message: "Productivity is not <0"


