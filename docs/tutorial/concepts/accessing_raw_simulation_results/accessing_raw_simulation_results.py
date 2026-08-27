# Front matter the .py format cannot carry; injected on export.
# description: How to access raw results in the BPTK-Py simulation framework.
# keywords: agent-based modeling, abm, bptk, bptk-py, python
#
# The reader can only look here: the subject is what a DataFrame contains, and every
# variant the page discusses is printed on it side by side. The one thing worth
# changing would be a slice, which teaches pandas rather than BPTK - and running it
# in a browser costs 8 MB of Pyodide for output that is text.
# interactive: false
import marimo

__generated_with = "0.23.13"
app = marimo.App(app_title="Accessing Raw Simulation Results")


@app.cell
def _():
    import marimo as mo

    return (mo,)




@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # How To: Accessing Raw Simulation Results

    In some situations, it is helpful obtain the raw simulation results rather than the plot. To activate this feature, set the ``return_df`` flag to ``True``.

    Below is example code that runs a scenario and sets ``return_df`` to true. This way it is possible to work with the data outside ``BPTK_Py``!
    """)
    return


@app.cell
def _():
    from BPTK_Py.bptk import bptk
    bptk = bptk()
    return (bptk,)


@app.cell
def _():
    #| echo: false
    # '%matplotlib inline' command supported automatically in marimo
    import matplotlib.pyplot as plt
    plt.rcParams['figure.facecolor'] = 'white'
    plt.rcParams['axes.facecolor'] = 'white'
    plt.rcParams['savefig.facecolor'] = 'white'

    # How many columns a printed dataframe shows depends on `display.width`, and pandas
    # guesses it from the terminal. There is no terminal in either place here, and the two
    # guessed differently: the pre-rendered output on this page showed fewer columns than
    # the same cell produced when the reader pressed play. Pinned, so both agree.
    import pandas as pd

    pd.set_option("display.width", 100)
    pd.set_option("display.max_columns", 10)
    return


@app.cell
def _(bptk):
    df = bptk.plot_scenarios(
        scenario_managers=["smSimpleProjectManagement"],
        scenarios=["scenario120"], 
        equations=["openTasks"],
        title="Deadline changes\n",
        x_label="Time",start_date="1/1/2018",freq="ME",
        y_label="Marketing Budget (USD)",
        kind="line",
        return_df=True ## <--- HERE
        ,series_names = {"smSimpleProjectManagement_scenario120_openTasks" : "openTasks"}
        )
    return (df,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    The following code prints useful information by calling the ``head()`` and ``describe()`` functions of the dataFrame. Head return the first 5 elements and Describe gives some important information on the data.
    For instance, we learn that there are 121 elements in the dataFrame ("count"). Further values are the mean, standard deviation, min, max, and the 25th / 50th and 75th percentile.
    """)
    return


@app.cell
def _(df, mo):
    # marimo sends a cell's stdout to the console rather than to its output area.
    # Captured and handed to `mo.plain_text` it comes back as one block, laid out
    # the way `print` wrote it.
    with mo.capture_stdout() as output:
        print("***************************")
        print("Properties of the dataFrame")
        print("\t first 5 elements:")
        print(df.head())
        print("")
        print("Main description of the dataFrame")
        print(df.describe())

    mo.plain_text(output.getvalue())
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    To select only certain periods, two different approaches can be used.

    1. Use the list index representation
    2. Use dates (if you created a time series using ``start_date``)

    In both cases, the selected range is supplied  in square brackets:
    """)
    return


@app.cell
def _(df, mo):
    # Select the first 6 months
    by_index = df[0:6]

    # Select all values of the months January to June 2018:
    by_year = df["2018-01":"2018-06"]

    with mo.capture_stdout() as output_1:
        # The blank lines belong to the labels rather than being printed on their own:
        # a bare `print("")` survives into the live output and gets swallowed on the way
        # into the pre-rendered page, so the two differed by two empty lines.
        print("BY INDEX")
        print(by_index)

        print("\nBY YEAR-MONTH:")
        print(by_year)

        print("\nCHECK FOR EQUALITY OF BOTH")
        print(by_index == by_year)

    mo.plain_text(output_1.getvalue())
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    This allows for versatile and easy analysis of the returned data. For example, equality testing using ``by_index == by_year``. The return type is a ``Series`` that may be used for further computation.

    We now simulate the equation "closedTasks", append it to the existing dataFrame, derive a
    third series from the two by computation, and finally compute the percentage of tasks
    closed. Every value of ``initialOpenTasks`` should come out at 120 — the initial number of
    tasks of the scenario ``scenario120``.

    All four steps live in one cell, so that changing any of them recomputes the rest: each one
    adds a column to the same dataFrame rather than producing a new name of its own, and marimo
    follows names.
    """)
    return


@app.cell
def _(bptk, df, mo):
    df_closed = bptk.plot_scenarios(
        scenario_managers=["smSimpleProjectManagement"],
        scenarios=["scenario120"],
        equations=["closedTasks"],
        title="Deadline changes\n",
        x_label="Time", start_date="1/1/2018", freq="ME",
        y_label="Tasks",
        kind="line",
        return_df=True,
        series_names={"smSimpleProjectManagement_scenario120_closedTasks": "closedTasks"}
        )

    df["closedTasks"] = df_closed["closedTasks"]

    # A new series by computation
    df["initialOpenTasks"] = df["openTasks"] + df["closedTasks"]

    # And the share of tasks closed, as a percentage
    df["Percent Tasks Closed"] = df["closedTasks"] / df["initialOpenTasks"] * 100

    with mo.capture_stdout() as output_2:
        print(df["initialOpenTasks"].head())

    mo.vstack([
        mo.plain_text(output_2.getvalue()),
        df["Percent Tasks Closed"].plot(title="Tasks closed %", figsize=(20, 10)).figure,
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    As you can see, the DataFrame handles all the heavy lifting and we can focus on high-level analysis.
    """)
    return


if __name__ == "__main__":
    app.run()
