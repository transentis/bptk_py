# Front matter the .py format cannot carry; injected on export.
# keywords: agent-based modeling, system dynamics,abm, bptk, bptk-py, python, business simulation
# description: An agent-based model of the beer distribution game. Each of the players in the game is modeled as an agent.
import marimo

__generated_with = "0.23.13"
app = marimo.App(app_title="An Agent-based Approach To Modeling The Beer Game")


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell(hide_code=True)
def _(mo):
    # Hidden on purpose: this is plumbing, not documentation. Shown, it put a code block
    # about marimo's table widget at the top of a page about the beer game.
    def as_table(df):
        # marimo's table widget embeds only its first page - ten rows - and this page is
        # rendered rather than run, so there is no runtime to fetch the rest: every table
        # stopped at t = 9. Rendered as HTML, every row is in the page, and the
        # scrolling div keeps a wide table inside its own width instead of over the edge.
        return mo.Html(
            '<div style="overflow-x: auto">'
            + df.to_html(border=0, classes="table table-sm caption-top")
            + "</div>"
        )

    return (as_table,)




@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # An Agent-based Approach To Modeling The Beer Game

    An agent-based model of the beer distribution game. Each of the players in the game is modeled as an agent.

    This page explores the game using deterministic agents; [Training AI to Play the Beer Game](training_ai_beergame.md) lets the agents learn by themselves using a reinforcement learning approach.

    [Agent-based Modeling with BPTK-Py](../../abm/agent_based_modeling/agent_based_modeling.md) explains how agents are built in general; the rules, the costs and the dynamics of the game are on [Understanding the Beer Game](understanding_the_beergame.md).

    ## The Agents

    ![Agents](images/agents.png)

    Each player in the game is modeled by an agent, so there are five agents: the consumer and the agents that are part of the supply chain, i.e. the retailer, the wholesaler, the distributor and the brewery.

    The supply chain agents are essentially all the same - they have an internal state that captures:

    * __Inventory,__ i.e. how much beer the agent has in stock.
    * __Outstanding Orders,__ i.e. how much beer the agent has ordered from its supplier but has not received yet.
    * __Backorder,__ i.e. how much beer the agent's customers have ordered but which the agent hasn't delivered yet.

    In each timestep, the agent has to react to the following events:

    * __Delivery.__ The beer delivered from the agent's supplier.
    * __Order.__ The beer ordered by the agent's customer.

    At the end of each timestep, after the agent has received deliveries and orders, the agent has to make an order decision, which is then passed on to its supplier as an order.

    ![Agents](images/supply_chain_agents.png)
    """)
    return


@app.cell
def _():
    from BPTK_Py.bptk import bptk 

    bptk = bptk()
    return (bptk,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Steady State
    """)
    return


@app.cell
def _(bptk):
    bptk.plot_scenarios(
        scenario_managers=["smBeergame"],
        kind="area",
        scenarios=["steady"],
        agents=["brewery","distributor","wholesaler","retailer"],
        agent_states=["active"],
        agent_properties=["outstanding_orders"],
        agent_property_types=["total"],
        return_df=False, format="axes"
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Typical Player Behavior

    The policy is explained on [Understanding the Beer Game](understanding_the_beergame.md#supply-chain-dynamics-dealing-with-changing-demands-for-beer).
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Typical player behaviour (which leads to the "whiplash" effect).
    """)
    return


@app.cell
def _(bptk):
    bptk.plot_scenarios(
        scenario_managers=["smBeergame"],
        kind="area",
        scenarios=["typical"],
        agents=["brewery","distributor","wholesaler","retailer","consumer"],
        agent_states=["active"],
        agent_properties=["outgoing_order"],
        agent_property_types=["total"],
        return_df=False, format="axes"
    )
    return


@app.cell
def _(bptk):
    bptk.plot_scenarios(
        scenario_managers=["smBeergame"],
        kind="area",
        scenarios=["typical"],
        agents=["brewery","distributor","wholesaler","retailer"],
        agent_states=["active"],
    
        agent_properties=["surplus"],
        agent_property_types=["total"],
        return_df=False, format="axes"
    )
    return


@app.cell
def _(bptk):
    bptk.plot_scenarios(
        scenario_managers=["smBeergame"],
        kind="area",
        scenarios=["typical"],
        agents=["brewery","distributor","wholesaler","retailer"],
        agent_states=["active"],
        agent_properties=["inventory"],
        agent_property_types=["total"],
        return_df=False, format="axes"
    )
    return


@app.cell
def _(bptk):
    bptk.plot_scenarios(
        scenario_managers=["smBeergame"],
        kind="area",
        scenarios=["typical"],
        agents=["brewery", "distributor","wholesaler","retailer"],
        agent_states=["active"],
        agent_properties=["cost"],
        agent_property_types=["total"], format="axes"
    )
    return


@app.cell
def _(bptk):
    bptk.plot_scenarios(
        scenario_managers=["smBeergame"],
        kind="area",
        scenarios=["typical"],
        agents=["controlling"],
        agent_states=["active"],
        agent_properties=["supply_chain_cost","target_supply_chain_cost"],
        agent_property_types=["total"], format="axes"
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Ignore Backorder

    The policy is explained on [Understanding the Beer Game](understanding_the_beergame.md#ignoring-backorders).
    """)
    return


@app.cell
def _(bptk):
    bptk.plot_scenarios(
        scenario_managers=["smSmartBeergame"],
        kind="area",
        scenarios=["ignore_backorder"],
        agents=["retailer"],
        agent_states=["active"],
        agent_properties=["outgoing_order","inventory","incoming_order"],
        agent_property_types=["total"],
        return_df=False, format="axes"
    )
    return


@app.cell
def _(bptk):
    bptk.plot_scenarios(
        scenario_managers=["smSmartBeergame"],
        kind="area",
        scenarios=["ignore_backorder"],
        agents=["retailer"],
        agent_states=["active"],
        agent_properties=["total_cost","target_cost"],
        agent_property_types=["total"],
        return_df=False, format="axes"
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Include Supply Line

    The policy is explained on [Understanding the Beer Game](understanding_the_beergame.md#remembering-open-orders-including-the-supply-line).
    """)
    return


@app.cell
def _(bptk):
    bptk.plot_scenarios(
        scenario_managers=["smSmartBeergame"],
        kind="area",
        scenarios=["include_supply_line"],
        agents=["retailer"],
        agent_states=["active"],
        agent_properties=["outgoing_order","inventory","incoming_order"],
        agent_property_types=["total"],
        return_df=False, format="axes"
    )
    return


@app.cell
def _(bptk):
    bptk.plot_scenarios(
        scenario_managers=["smSmartBeergame"],
        kind="area",
        scenarios=["include_supply_line"],
        agents=["retailer"],
        agent_states=["active"],
        agent_properties=["total_cost","target_cost"],
        agent_property_types=["total"],
        return_df=False, format="axes"
    )
    return


@app.cell
def _(bptk):
    bptk.plot_scenarios(
        scenario_managers=["smSmartBeergame"],
        kind="area",
        scenarios=["include_supply_line"],
        agents=["retailer"],
        agent_states=["active"],
        agent_properties=["surplus"],
        agent_property_types=["total"],
        return_df=False, format="axes"
    )
    return


@app.cell
def _(bptk):
    bptk.plot_scenarios(
        scenario_managers=["smSmartBeergame"],
        kind="area",
        scenarios=["include_supply_line"],
        agents=["brewery","distributor", "wholesaler", "retailer","consumer"],
        agent_states=["active"],
        agent_properties=["outgoing_order"],
        agent_property_types=["total"],
        return_df=False, format="axes"
    )
    return


@app.cell
def _(bptk):
    bptk.plot_scenarios(
        scenario_managers=["smSmartBeergame"],
        kind="area",
        scenarios=["include_supply_line"],
        agents=["controlling"],
        agent_states=["active"],
        agent_properties=["supply_chain_cost","target_supply_chain_cost"],
        agent_property_types=["total"], format="axes"
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Slow Inventory Adjustment

    The policy is explained on [Understanding the Beer Game](understanding_the_beergame.md#avoiding-the-whiplash-effect).
    """)
    return


@app.cell
def _(bptk):
    bptk.plot_scenarios(
        scenario_managers=["smSmartBeergame"],
        kind="area",
        scenarios=["slow_inventory_adjustment"],
        agents=["brewery","distributor", "wholesaler", "retailer","consumer"],
        agent_states=["active"],
        agent_properties=["outgoing_order"],
        agent_property_types=["total"],
        return_df=False, format="axes"
    )
    return


@app.cell
def _(bptk):
    bptk.plot_scenarios(
        scenario_managers=["smSmartBeergame"],
        kind="area",
        scenarios=["slow_inventory_adjustment"],
        agents=["controlling"],
        agent_states=["active"],
        agent_properties=["supply_chain_cost","target_supply_chain_cost"],
        agent_property_types=["total"],
        return_df=False, format="axes"
    )
    return


@app.cell
def _(bptk):
    bptk.plot_scenarios(
        scenario_managers=["smSmartBeergame"],
        kind="area",
        scenarios=["slow_inventory_adjustment"],
        agents=["brewery","distributor","wholesaler","retailer"],
        agent_states=["active"],
        agent_properties=["total_cost"],
        agent_property_types=["total"],
        return_df=False, format="axes"
    )
    return


@app.cell
def _(bptk):
    bptk.plot_scenarios(
        scenario_managers=["smSmartBeergame"],
        kind="area",
        scenarios=["slow_inventory_adjustment"],
        agents=["retailer"],
        agent_states=["active"],
        agent_properties=["total_cost","target_cost"],
        agent_property_types=["total"],
        return_df=False, format="axes"
    )
    return


@app.cell
def _(bptk):
    bptk.plot_scenarios(
        scenario_managers=["smSmartBeergame"],
        kind="area",
        scenarios=["slow_inventory_adjustment"],
        agents=["brewery","distributor", "wholesaler", "retailer"],
        agent_states=["active"],
        agent_properties=["inventory"],
        agent_property_types=["total"],
        return_df=False, format="axes"
    )
    return


@app.cell
def _(bptk):
    bptk.plot_scenarios(
        scenario_managers=["smSmartBeergame"],
        kind="area",
        scenarios=["slow_inventory_adjustment"],
        agents=["retailer"],
        agent_states=["active"],
        agent_properties=["surplus","target_surplus"],
        agent_property_types=["total"], format="axes"
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Order Balance Strategy

    One simple strategy is to manage the order balance, i.e. the difference between incoming orders (those coming from the customer) and outgoing orders (those going to the supplier). Put simply, we would expect the balance to be a constant equal to the desired inventory, so a sensible ordering strategy is:

    `Int(Max(Incoming Order + (2 * Incoming Order + Target Inventory - Order Balance) / Inventory Adjustment Time, 0))`

    This policy is nice and simple, and it is almost good enough to keep the supply chain costs below the target of $29,300.
    """)
    return


@app.cell
def _(bptk):
    bptk.plot_scenarios(
        scenario_managers=["smSmartBeergame"],
        kind="area",
        scenarios=["order_balance"],
        agents=["brewery","distributor", "wholesaler", "retailer","consumer"],
        agent_states=["active"],
        agent_properties=["outgoing_order"],
        agent_property_types=["total"],
        return_df=False, format="axes"
    )
    return


@app.cell
def _(bptk):
    bptk.plot_scenarios(
        scenario_managers=["smSmartBeergame"],
        kind="area",
        scenarios=["order_balance"],
        agents=["brewery","distributor", "wholesaler", "retailer"],
        agent_states=["active"],
        agent_properties=["inventory"],
        agent_property_types=["total"],
        return_df=False, format="axes"
    )
    return


@app.cell
def _(as_table, bptk):
    as_table(bptk.plot_scenarios(
        scenario_managers=["smSmartBeergame"],
        kind="area",
        scenarios=["order_balance"],
        agents=["brewery","distributor","wholesaler","retailer"],
        agent_states=["active"],
        agent_properties=["total_cost"],
        agent_property_types=["total"],
        return_df=True
    ))
    return


@app.cell
def _(bptk):
    bptk.plot_scenarios(
        scenario_managers=["smSmartBeergame"],
        kind="area",
        scenarios=["order_balance"],
        agents=["controlling"],
        agent_states=["active"],
        agent_properties=["supply_chain_cost","target_supply_chain_cost"],
        agent_property_types=["total"],
        return_df=False, format="axes"
    )
    return


@app.cell
def _(bptk):
    bptk.plot_scenarios(
        scenario_managers=["smSmartBeergame"],
        kind="area",
        scenarios=["order_balance"],
        agents=["retailer"],
        agent_states=["active"],
        agent_properties=["backorder"],
        agent_property_types=["total"],
        return_df=False, format="axes"
    )
    return


@app.cell
def _(as_table, bptk):
    as_table(bptk.plot_scenarios(
        scenario_managers=["smSmartBeergame"],
        kind="area",
        scenarios=["order_balance"],
        agents=["brewery","distributor","wholesaler","retailer"],
        agent_states=["active"],
        agent_properties=["order_balance"],
        agent_property_types=["total"],
        return_df=True
    ))
    return


@app.cell
def _(bptk):
    bptk.plot_scenarios(
        scenario_managers=["smSmartBeergame"],
        kind="area",
        scenarios=["order_balance"],
        agents=["retailer"],
        agent_states=["active"],
        agent_properties=["surplus","target_surplus"],
        agent_property_types=["total"], format="axes"
    )
    return


if __name__ == "__main__":
    app.run()
