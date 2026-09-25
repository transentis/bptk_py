# Front matter the .py format cannot carry; injected on export.
# description: In-depth explanation of agent-based modeling.
# keywords: agent-based modeling, abm, bptk, python
#
# A section overview: prose and nothing else - not one chart, and no cell that offers
# a decision to take. Left reactive it booted Pyodide, some 8 MB, to display text, and
# it is the page a reader arrives on first.
# interactive: false
import marimo

__generated_with = "0.23.13"
app = marimo.App(app_title="Agent Based Modeling")


@app.cell
def _():
    import marimo as mo

    return (mo,)




@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Agent-based Modeling

    This section gives an in-depth explanation of agent-based modeling.

    ## Contents

    - [Agent-based Modeling With BPTK-Py](./agent_based_modeling/agent_based_modeling.ipynb)
    - [Custom Data Collectors](./custom_datacollectors/custom_datacollectors.ipynb)
    """)
    return


if __name__ == "__main__":
    app.run()
