# Front matter the .py format cannot carry; injected on export.
# keywords: agent-based modeling, reinforcement-learning, beergame, beer distribution game
# description: Test notebook
import marimo

__generated_with = "0.23.13"
app = marimo.App(app_title="Beer Distribution Game Reinforcement Learning")


@app.cell
def _():
    import marimo as mo

    return (mo,)




@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Beer Distribution Game Reinforcement Learning
    """)
    return


@app.cell
def _():
    from BPTK_Py.bptk import bptk 
    bptk = bptk()
    bptk.train_scenarios(
        episodes=10,
        scenario_managers=["smBeergameQlOB"],
        scenarios=["train_agents"],
        agents=["controlling"],
        agent_states=["active"],
        agent_properties=["supply_chain_reward"],
        agent_property_types=["total"],
        return_df=False,
        progress_bar=True
    )
    return (bptk,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Persist Q-Tables
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    It takes quite some time to train q-tables and they can become quite large:
    """)
    return


@app.cell
def _(mo):
    from src.abm.q_learning_ob.beergame import BeergameQlOB

    # Captured: marimo sends a cell's stdout to the console, not into the page.
    with mo.capture_stdout() as q_table_counts:
        print("Q-Table Counts")
        print("Brewery: {}".format(BeergameQlOB.brewery_q_table.count()))
        print("Distributor: {}".format(BeergameQlOB.distributor_q_table.count()))
        print("Wholesaler: {}".format(BeergameQlOB.wholesaler_q_table.count()))
        print("Retailer: {}".format(BeergameQlOB.retailer_q_table.count()))

    mo.plain_text(q_table_counts.getvalue())
    return (BeergameQlOB,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Hence it makes sense to dump the trained q-tables so they can be reused:

    This is the one cell on this page that is **shown rather than run**: it writes into
    `data/`, which a documentation build has no business doing - the q-tables there are
    tracked inputs of the other beergame pages. Nothing reads `q_tables_10.json`, so the
    call is here to show how it is done.

    ```python
    BeergameQlOB.dump_q_tables("data/q_tables_10.json", "JSON")
    ```
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Load Q-Tables
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Reset the q-tables:
    """)
    return


@app.cell
def _(BeergameQlOB):
    from src.abm.q_learning_base.sparseQTable import SparseQTable
    BeergameQlOB.brewery_q_table=SparseQTable(dimension=1)
    BeergameQlOB.distributor_q_table=SparseQTable(dimension=1)
    BeergameQlOB.wholesaler_q_table=SparseQTable(dimension=1)
    BeergameQlOB.retailer_q_table=SparseQTable(dimension=1)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Load previously saved q-tables:
    """)
    return


@app.cell
def _(BeergameQlOB):
    BeergameQlOB.load_q_tables("data/q_tables_50000.json","JSON")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Use Training Results
    """)
    return


@app.cell
def _(bptk):
    bptk.reset_scenario(scenario_manager="smBeergameQlOB",scenario="smart_agents")
    return


@app.cell
def _(bptk):
    bptk.plot_scenarios(
        scenario_managers=["smBeergameQlOB"],
        kind="area",
        scenarios=["smart_agents"],
        agents=["brewery","distributor","wholesaler","retailer"],
        agent_states=["active"],
        agent_properties=["order_balance"],
        agent_property_types=["total"], format="axes"
    )
    return


@app.cell
def _(bptk):
    bptk.plot_scenarios(
        scenario_managers=["smBeergameQlOB"],
        kind="area",
        scenarios=["smart_agents"],
        agents=["brewery","distributor","wholesaler","retailer"],
        agent_states=["active"],
        agent_properties=["outgoing_order"],
        agent_property_types=["total"], format="axes"
    )
    return


@app.cell
def _(bptk):
    bptk.plot_scenarios(
        scenario_managers=["smBeergameQlOB"],
        kind="area",
        scenarios=["smart_agents"],
        agents=["brewery","distributor","wholesaler","retailer"],
        agent_states=["active"],
        agent_properties=["total_cost"],
        agent_property_types=["total"], format="axes"
    )
    return


@app.cell
def _(bptk):
    bptk.plot_scenarios(
        scenario_managers=["smBeergameQlOB"],
        kind="area",
        scenarios=["smart_agents"],
        agents=["controlling"],
        agent_states=["active"],
        agent_properties=["supply_chain_cost","target_supply_chain_cost"],
        agent_property_types=["total"], format="axes"
    )
    return


@app.cell
def _(bptk):
    bptk.plot_scenarios(
        scenario_managers=["smBeergameQlOB"],
        kind="area",
        scenarios=["smart_agents"],
        agents=["brewery","distributor","wholesaler","retailer"],
        agent_states=["active"],
        agent_properties=["inventory"],
        agent_property_types=["total"], format="axes"
    )
    return


@app.cell
def _(bptk):
    bptk.plot_scenarios(
        scenario_managers=["smBeergameQlOB"],
        kind="area",
        scenarios=["smart_agents"],
        agents=["brewery","distributor","wholesaler","retailer"],
        agent_states=["active"],
        agent_properties=["backorder"],
        agent_property_types=["total"], format="axes"
    )
    return


if __name__ == "__main__":
    app.run()
