# Front matter the .py format cannot carry; injected on export.
# description: Non-negative stocks, biflows and conveyors in the SD DSL - a stock that cuts back its outflows instead of falling below zero, and a stock that works like a conveyor belt
# keywords: system dynamics, systemdynamics, sd dsl, non-negative stock, biflow, outflow priority, conveyor, agecount, fifo, bptk, bptk-py, python, business simulation
import marimo

__generated_with = "0.23.13"
app = marimo.App(app_title="Non-Negative Stocks, Biflows and Conveyors")


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Non-Negative Stocks, Biflows and Conveyors

    A stock is the sum of everything that has flowed in, less everything that has flowed out. Nothing in that arithmetic stops it at zero: if the outflows ask for more than the stock holds, the stock goes negative. For a bank balance that may be what you want. A warehouse, a population or a forest cannot hold less than nothing.

    A **non-negative stock** solves this the way Stella and XMILE do: not by holding the stock at zero, but by cutting back its outflows so that they take no more than there is. This page shows how to build one, how the outflows share what is left, how biflows behave at such a stock, and why simply writing `max(0, ...)` is not the same thing.

    The page has three parts: **non-negative stocks**, **biflows** - flows that run either way, and what they do at a non-negative stock - and **conveyors**, stocks that work like a conveyor belt.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Non-Negative Stocks

    ### Inflows and Outflows as Lists

    Usually a stock's equation is written as an expression, inflows minus outflows. A stock can also be given its flows as two lists. The equation is then written for you - here `receipts - shipments` - and the depot grows by one unit a day:
    """)
    return


@app.cell
def _():
    from BPTK_Py import Model
    from BPTK_Py import sd_functions as sd
    from BPTK_Py.bptk import bptk

    lists_model = Model(starttime=0.0, stoptime=5.0, dt=1.0, name="Lists")
    depot = lists_model.stock("depot")
    depot.initial_value = 10.0
    receipts = lists_model.flow("receipts")
    receipts.equation = 3.0
    shipments = lists_model.flow("shipments")
    shipments.equation = 2.0

    depot.inflows = [receipts]
    depot.outflows = [shipments]

    lists_model.simulate(["depot"])
    return Model, bptk, sd


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    The two lists are what a non-negative stock needs: it has to know which flows leave it, and in which order to serve them.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### A Warehouse That Runs Empty

    The warehouse below starts with 60 units and receives a delivery every day. Two outflows draw on it: sales, and scrap - goods that are written off. Together they want more than is delivered, so the warehouse runs empty after a while.

    The model holds four versions of the warehouse side by side, all driven by the same constants:

    - `warehouse` is non-negative and serves **sales first**
    - `warehouse_scrap_first` is non-negative too, with the outflows in the other order
    - `warehouse_unbounded` is an ordinary stock
    - `warehouse_clamped` is held at zero with `max`, the way an approximation would do it
    """)
    return


@app.cell
def _(Model, sd):
    model = Model(starttime=0.0, stoptime=60.0, dt=1.0, name="Warehouse")

    delivery_rate = model.constant("delivery_rate")
    delivery_rate.equation = 10.0
    sales_demand = model.constant("sales_demand")
    sales_demand.equation = 8.0
    scrap_demand = model.constant("scrap_demand")
    scrap_demand.equation = 4.0

    warehouse = model.stock("warehouse")
    warehouse.initial_value = 60.0
    delivery = model.flow("delivery")
    delivery.equation = delivery_rate
    sales = model.flow("sales")
    sales.equation = sales_demand
    scrap = model.flow("scrap")
    scrap.equation = scrap_demand
    warehouse.inflows = [delivery]
    warehouse.outflows = [sales, scrap]
    warehouse.non_negative = True

    warehouse_scrap_first = model.stock("warehouse_scrap_first")
    warehouse_scrap_first.initial_value = 60.0
    delivery_b = model.flow("delivery_b")
    delivery_b.equation = delivery_rate
    sales_b = model.flow("sales_b")
    sales_b.equation = sales_demand
    scrap_b = model.flow("scrap_b")
    scrap_b.equation = scrap_demand
    warehouse_scrap_first.inflows = [delivery_b]
    warehouse_scrap_first.outflows = [scrap_b, sales_b]
    warehouse_scrap_first.non_negative = True

    warehouse_unbounded = model.stock("warehouse_unbounded")
    warehouse_unbounded.initial_value = 60.0
    warehouse_unbounded.equation = delivery_rate - sales_demand - scrap_demand

    warehouse_clamped = model.stock("warehouse_clamped")
    warehouse_clamped.initial_value = 60.0
    warehouse_clamped.equation = sd.max(
        delivery_rate - sales_demand - scrap_demand, -warehouse_clamped / sd.dt(model)
    )

    received = model.stock("received")
    received.initial_value = 60.0
    received.equation = delivery_rate
    shipped = model.stock("shipped")
    shipped.equation = sales + scrap
    shipped_clamped = model.stock("shipped_clamped")
    shipped_clamped.equation = sales_demand + scrap_demand
    return (model,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    The last three stocks keep the books: `received` is everything that ever arrived, the initial 60 included, and the two `shipped` stocks add up what left the non-negative and the clamped warehouse.
    """)
    return


@app.cell
def _(bptk, model):
    warehouse_bptk = bptk()
    warehouse_bptk.register_model(model)
    warehouse_bptk.register_scenario_manager({"warehouse": {"model": model, "base_constants": {}}})
    warehouse_bptk.register_scenarios(scenario_manager="warehouse", scenarios={"interactive": {}})
    return (warehouse_bptk,)


@app.cell
def _(mo):
    delivery_slider = mo.ui.slider(start=0, stop=20, step=1, value=10, show_value=True, label="Delivery per day")
    sales_slider = mo.ui.slider(start=0, stop=20, step=1, value=8, show_value=True, label="Sales demand per day")
    scrap_slider = mo.ui.slider(start=0, stop=20, step=1, value=4, show_value=True, label="Scrap per day")
    return delivery_slider, sales_slider, scrap_slider


@app.cell
def _(delivery_slider, mo, sales_slider, scrap_slider, warehouse_bptk):
    scenario = warehouse_bptk.get_scenario("warehouse", "interactive")
    scenario.constants["delivery_rate"] = delivery_slider.value
    scenario.constants["sales_demand"] = sales_slider.value
    scenario.constants["scrap_demand"] = scrap_slider.value
    warehouse_bptk.reset_scenario_cache(scenario_manager="warehouse", scenario="interactive")

    def plot(equations, names, title):
        return warehouse_bptk.plot_scenarios(
            scenario_managers=["warehouse"],
            scenarios=["interactive"],
            equations=equations,
            series_names={"warehouse_interactive_" + equation: name for equation, name in zip(equations, names)},
            title=title,
            x_label="Day",
            y_label="Units",
            format="axes",
        ).figure

    mo.vstack([
        mo.hstack([delivery_slider, sales_slider, scrap_slider]),
        mo.ui.tabs({
            "Stock": plot(
                ["warehouse", "warehouse_unbounded", "warehouse_clamped"],
                ["Non-negative", "Unbounded", "Clamped with max"],
                "Warehouse",
            ),
            "Outflows": plot(["sales", "scrap"], ["Sales", "Scrap"], "What leaves the non-negative warehouse"),
            "Priority": plot(
                ["sales", "sales_b", "scrap", "scrap_b"],
                ["Sales, sales first", "Sales, scrap first", "Scrap, sales first", "Scrap, scrap first"],
                "Who is served first",
            ),
            "Books": plot(
                ["received", "shipped", "shipped_clamped"],
                ["Received", "Shipped, non-negative", "Shipped, clamped with max"],
                "Material in and out",
            ),
        }),
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    What the tabs show, with the default settings:

    - **Stock.** The unbounded warehouse goes negative once it is empty. The non-negative one and the clamped one both stay at zero - on this chart they look the same.
    - **Outflows.** Once the warehouse is empty, on day 30, the outflows of the non-negative warehouse share what is delivered each day, 10 units: sales gets its 8 in full, scrap the remaining 2.
    - **Priority.** With the order reversed, scrap gets its 4 and sales only 6. The order of the `outflows` list decides who goes short.
    - **Books.** Here the two zero lines part. The non-negative warehouse never ships more than it received. The clamped one goes on reporting 12 units leaving per day while only 10 arrive: from the day it runs empty, the gap between `shipped_clamped` and `received` is material that came out of nothing.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### How the Outflows Are Cut Back

    In each timestep an outflow of a non-negative stock takes what its equation asks for, but at most

    $$
    \frac{stock}{dt} + \sum inflows - \sum outflows\ served\ before\ it
    $$

    The first outflow in the list is served first, the second gets what is left, and so on. The flows report what they actually took - `sales` and `scrap` above are the cut-back values, not the demand. That is the difference to `max(0, ...)`: holding the stock at zero hides the shortage in the stock, while the outflows go on as if nothing had happened.

    The limit is a rate. With a smaller `dt` the same stock supports larger outflows for a shorter time; what leaves within one timestep never exceeds what the stock held plus what arrived.

    Three rules come with it:

    - **A non-negative stock needs its lists.** A stock whose equation was written directly raises an error when it is made non-negative, and writing the equation of a non-negative stock raises as well.
    - **An outflow that depends on another outflow of the same stock comes after it.** The other way round it would have to wait for itself; the error names both flows.
    - **An inflow that depends on an outflow of the same stock does not count** towards what the outflows may take. Only the stock's content does, as in Stella.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Arrayed Stocks

    An arrayed stock is cut back cell by cell. Its outflows have its shape, and each cell serves its own outflows in the order of the list. Here two warehouses start with different stock and face the same demand:
    """)
    return


@app.cell
def _(Model):
    arrayed_model = Model(starttime=0.0, stoptime=4.0, dt=1.0, name="Two Warehouses")
    stock = arrayed_model.stock("stock")
    stock.setup_named_vector({"north": 10.0, "south": 2.0})
    orders = arrayed_model.flow("orders")
    orders.setup_named_vector({"north": 3.0, "south": 3.0})
    stock.outflows = [orders]
    stock.non_negative = True

    arrayed_model.simulate(["stock[north]", "orders[north]", "stock[south]", "orders[south]"])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    The south warehouse ships its 2 units on the first day and nothing after; the north one ships 3 a day until its last unit goes on day three.

    Non-negative stocks run on the Python engine for now. Asking for `backend="rust"` raises `RustBackendError` naming the stock. The details of the API are on the [Stock](../../api/api_stock.md#stock.non_negative) page.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Biflows

    A biflow can move material in either direction, so which list it is in does not tell on its own whether it fills the stock or drains it. The sign does. In the `inflows` list a positive biflow brings material in, as any inflow would; a negative one takes material out - it is an outflow in effect. In the `outflows` list it is the other way round: positive, it takes material out; negative, it brings material in - an inflow in effect.

    A non-negative stock goes by what the biflow actually does at the moment:

    | Listed in  | Value    | What it does | At a non-negative stock |
    |------------|----------|--------------|-------------------------|
    | `inflows`  | positive | fills        | counts towards what the outflows may take |
    | `inflows`  | negative | drains       | cut back, served **after every outflow** |
    | `outflows` | positive | drains       | cut back, served **at its place in the list** |
    | `outflows` | negative | fills        | counts towards what the outflows may take |

    A biflow that fills the stock is never cut back - nothing can make a stock negative by adding to it. A biflow that drains it is cut back like any outflow. Among the outflows it already has a place in the order; among the inflows it has none, so it comes last, after every outflow, and several of them are served in the order of the `inflows` list.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    The store below shows all four cases. It receives a supply of 5 units a day and sells 3. Two biflows are attached to it:

    - `returns`, among the **inflows**: goods coming back from customers when positive, goods sent back to the supplier when negative
    - `transfer`, among the **outflows**, after sales: goods sent to a branch when positive, goods received from the branch when negative

    With the default settings the store sends 4 units a day back to the supplier and 2 to the branch, more than the supply leaves, so it runs empty on day 5. From then on the 5 units supplied each day go to sales first (3), then to the transfer, the next outflow in the list (2), and the returns, which drain the stock from the inflows list, come last and get nothing.

    Things to try:

    - Set the transfer to **-4**: the branch now sends goods, the transfer fills the store and counts as supply. With the returns at **-10** the store is empty again, and the returns get what sales leaves of the 9 units available: 6.
    - Set the returns to **+4** and the transfer to **+8**: the returns now fill the store and count, 9 units are available, sales takes 3 and the transfer is cut back to 6 once the store is empty.
    """)
    return


@app.cell
def _(Model, bptk):
    biflow_model = Model(starttime=0.0, stoptime=30.0, dt=1.0, name="Returns")
    returns_rate = biflow_model.constant("returns_rate")
    returns_rate.equation = -4.0
    transfer_rate = biflow_model.constant("transfer_rate")
    transfer_rate.equation = 2.0

    store = biflow_model.stock("store")
    store.initial_value = 20.0
    supply = biflow_model.flow("supply")
    supply.equation = 5.0
    returns = biflow_model.biflow("returns")
    returns.equation = returns_rate
    store_sales = biflow_model.flow("store_sales")
    store_sales.equation = 3.0
    transfer = biflow_model.biflow("transfer")
    transfer.equation = transfer_rate
    store.inflows = [supply, returns]
    store.outflows = [store_sales, transfer]
    store.non_negative = True

    returns_bptk = bptk()
    returns_bptk.register_model(biflow_model)
    returns_bptk.register_scenario_manager({"returns": {"model": biflow_model, "base_constants": {}}})
    returns_bptk.register_scenarios(scenario_manager="returns", scenarios={"interactive": {}})
    return (returns_bptk,)


@app.cell
def _(mo):
    returns_slider = mo.ui.slider(start=-10, stop=10, step=1, value=-4, show_value=True, label="Returns per day")
    transfer_slider = mo.ui.slider(start=-10, stop=10, step=1, value=2, show_value=True, label="Transfer per day")
    return returns_slider, transfer_slider


@app.cell
def _(mo, returns_bptk, returns_slider, transfer_slider):
    returns_scenario = returns_bptk.get_scenario("returns", "interactive")
    returns_scenario.constants["returns_rate"] = returns_slider.value
    returns_scenario.constants["transfer_rate"] = transfer_slider.value
    returns_bptk.reset_scenario_cache(scenario_manager="returns", scenario="interactive")

    mo.vstack([
        mo.hstack([returns_slider, transfer_slider]),
        returns_bptk.plot_scenarios(
            scenario_managers=["returns"],
            scenarios=["interactive"],
            equations=["store", "supply", "store_sales", "transfer", "returns"],
            series_names={
                "returns_interactive_store": "Store",
                "returns_interactive_supply": "Supply",
                "returns_interactive_store_sales": "Sales",
                "returns_interactive_transfer": "Transfer",
                "returns_interactive_returns": "Returns",
            },
            title="A store with two biflows",
            x_label="Day",
            y_label="Units",
            format="axes",
        ).figure,
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Conveyors

    A conveyor is a stock that works like a conveyor belt: material put on at one end travels along it and comes off at the other end after the **transit time** - every unit stays exactly that long. Leakage flows take a share of it on the way.

    Take the age group from 20 to 40. Those turning 20 enter it; 20 years later they leave as 40-year-olds, and on the way some die. An ordinary stock with an outflow of `stock / 20` gets the average right but nothing else: some of its members "turn 40" after a year, others after sixty. A conveyor keeps the age exact.

    The conveyor computes its outflow and its leakage itself, so those flows are created without an equation. The leakage gets its share in `leaks`:
    """)
    return


@app.cell
def _(Model, sd):
    cohort_model = Model(starttime=0.0, stoptime=80.0, dt=1.0, name="Cohorts")
    entering = cohort_model.constant("entering")
    entering.equation = 100.0
    extra = cohort_model.constant("extra")
    extra.equation = 50.0
    years = cohort_model.constant("years")
    years.equation = 20.0
    mortality = cohort_model.constant("mortality")
    mortality.equation = 0.02

    turning_20 = cohort_model.flow("turning_20")
    turning_20.equation = entering + sd.step(extra, 10)
    turning_40 = cohort_model.flow("turning_40")
    deaths = cohort_model.flow("deaths")

    cohort = cohort_model.conveyor("cohort")
    cohort.transit_time = years
    cohort.initial_value = 0.0
    cohort.inflows = [turning_20]
    cohort.outflows = [turning_40]
    cohort.leaks = {deaths: mortality}
    cohort.exponential_leak = True

    cohort_model.converter("aged_20_to_25").equation = sd.agecount(cohort, 0, 5)
    return cohort_model, mortality, years


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    For comparison the same model holds an ordinary stock that loses `pool / years` and `pool * mortality` a year:
    """)
    return


@app.cell
def _(bptk, cohort_model, mortality, years):
    turning_20_pool = cohort_model.flow("turning_20_pool")
    turning_20_pool.equation = cohort_model.flows["turning_20"].equation
    leaving_pool = cohort_model.flow("leaving_pool")
    dying_pool = cohort_model.flow("dying_pool")
    pool = cohort_model.stock("pool")
    leaving_pool.equation = pool / years
    dying_pool.equation = pool * mortality
    pool.inflows = [turning_20_pool]
    pool.outflows = [leaving_pool, dying_pool]

    cohort_bptk = bptk()
    cohort_bptk.register_model(cohort_model)
    cohort_bptk.register_scenario_manager({"cohorts": {"model": cohort_model, "base_constants": {}}})
    cohort_bptk.register_scenarios(scenario_manager="cohorts", scenarios={"interactive": {}})
    return (cohort_bptk,)


@app.cell
def _(mo):
    years_slider = mo.ui.slider(start=5, stop=30, step=1, value=20, show_value=True, label="Transit time in years")
    mortality_slider = mo.ui.slider(start=0.0, stop=0.1, step=0.005, value=0.02, show_value=True, label="Mortality per year")
    return mortality_slider, years_slider


@app.cell
def _(cohort_bptk, mo, mortality_slider, years_slider):
    cohort_scenario = cohort_bptk.get_scenario("cohorts", "interactive")
    cohort_scenario.constants["years"] = years_slider.value
    cohort_scenario.constants["mortality"] = mortality_slider.value
    cohort_bptk.reset_scenario_cache(scenario_manager="cohorts", scenario="interactive")

    def cohort_plot(equations, names, title):
        return cohort_bptk.plot_scenarios(
            scenario_managers=["cohorts"],
            scenarios=["interactive"],
            equations=equations,
            series_names={"cohorts_interactive_" + equation: name for equation, name in zip(equations, names)},
            title=title,
            x_label="Year",
            y_label="People",
            format="axes",
        ).figure

    mo.vstack([
        mo.hstack([years_slider, mortality_slider]),
        mo.ui.tabs({
            "Leaving": cohort_plot(["turning_20", "turning_40", "leaving_pool"],
                                   ["Turning 20", "Turning 40, conveyor", "Leaving, ordinary stock"],
                                   "Who turns 40"),
            "Dying": cohort_plot(["deaths", "dying_pool"], ["Conveyor", "Ordinary stock"], "Deaths on the way"),
            "On the belt": cohort_plot(["cohort", "aged_20_to_25", "pool"],
                                       ["Conveyor", "Of them aged 20 to 25", "Ordinary stock"],
                                       "People aged 20 to 40"),
        }),
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    The model starts empty, and from year 10 on 150 instead of 100 turn 20 each year. What the tabs show:

    - **Leaving.** Nobody leaves the conveyor for the first 20 years - nobody has been on it long enough. Then those who survived the 20 years leave, and the rise of year 10 arrives at the front exactly 20 years later, as a step. The ordinary stock lets people leave from the first year on, and its outflow bends towards the new level instead of stepping.
    - **Dying.** The conveyor's deaths grow while the belt fills and stop growing once it is full; with exponential leakage they are 2 % of everyone on the belt.
    - **On the belt.** `aged_20_to_25` is `agecount(cohort, 0, 5)` - the material that has been on the belt for less than five years.

    ### Leakage, linear or exponential

    What a share in `leaks` means depends on `exponential_leak`:

    | `exponential_leak` | The share is | `0.2` means |
    |---|---|---|
    | `False` - the default, as in XMILE | the part of each cohort that leaks out over its whole time on the belt, in equal amounts each timestep | 20 % of what entered leak out before the rest leaves |
    | `True` | a rate per time unit, taken from what is still on the belt | 20 % of the remainder leak out each time unit |

    Several linear leaks are served in the order of `leaks`, and a later one may get less once the first ones have taken everything. Several exponential leaks add up.

    ### When the transit time changes: FIFO

    The transit time can be an expression and is read anew every timestep. What a change does depends on `fifo`:

    - `fifo = False`, the default: material keeps the transit time it entered with. When the transit time shrinks, newer material overtakes older material.
    - `fifo = True`: first in, first out. The whole belt moves at the current transit time, so a shorter transit time speeds up everything on it at once.

    With a constant transit time the two are the same. Below, two conveyors carry 250 units a year with a transit time of 4 years until year 8, and the value of the slider after that:
    """)
    return


@app.cell
def _(Model, bptk, sd):
    belts_model = Model(starttime=0.0, stoptime=20.0, dt=0.25, name="Belts")
    later_transit = belts_model.constant("later_transit")
    later_transit.equation = 2.0
    transit = belts_model.converter("transit")
    transit.equation = sd.If(sd.time() < 8, 4.0, later_transit)
    for kind in ("traditional", "fifo"):
        belt_in = belts_model.flow("into_" + kind)
        belt_in.equation = 250.0
        belt_out = belts_model.flow("out_of_" + kind)
        belt = belts_model.conveyor(kind)
        belt.transit_time = transit
        belt.initial_value = 1000.0
        belt.inflows = [belt_in]
        belt.outflows = [belt_out]
        belt.fifo = kind == "fifo"

    belts_bptk = bptk()
    belts_bptk.register_model(belts_model)
    belts_bptk.register_scenario_manager({"belts": {"model": belts_model, "base_constants": {}}})
    belts_bptk.register_scenarios(scenario_manager="belts", scenarios={"interactive": {}})
    return (belts_bptk,)


@app.cell
def _(mo):
    transit_slider = mo.ui.slider(start=1, stop=8, step=1, value=2, show_value=True, label="Transit time from year 8")
    return (transit_slider,)


@app.cell
def _(belts_bptk, mo, transit_slider):
    belts_scenario = belts_bptk.get_scenario("belts", "interactive")
    belts_scenario.constants["later_transit"] = transit_slider.value
    belts_bptk.reset_scenario_cache(scenario_manager="belts", scenario="interactive")

    mo.vstack([
        transit_slider,
        belts_bptk.plot_scenarios(
            scenario_managers=["belts"],
            scenarios=["interactive"],
            equations=["out_of_traditional", "out_of_fifo"],
            series_names={
                "belts_interactive_out_of_traditional": "Traditional",
                "belts_interactive_out_of_fifo": "FIFO",
            },
            title="What leaves the belt",
            x_label="Year",
            y_label="Units per year",
            format="axes",
        ).figure,
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    With the transit time halved to 2, the FIFO belt doubles its outflow at once, until the material that was on it in year 8 has left; the traditional belt goes on at 250 until year 10, when the first material entered under the new transit time arrives beside the old. Set the slider above 4 and the belts slow down: the FIFO belt lets less out at once, the traditional one carries on until year 12 and then lets nothing out until the first new material arrives.

    ### What else to know

    - **The start.** `initial_value` as a number is the total on the belt, spread in the equilibrium its leakage implies. As a list it gives one value per time unit, **the first leaving first**.
    - **Arrays.** An arrayed conveyor has a belt per cell. A scalar outflow or leakage flow gets the conveyor's shape; transit time and shares can be arrayed elements.
    - **What is refused.** An equation on the conveyor or on a flow it drives, a biflow among its inflows, and more than one outflow - leakage goes into `leaks`.
    - Conveyors and `agecount` run on the Python engine only for now; the Rust engine raises `RustBackendError` naming the conveyor.

    The details are on the [Conveyor](../../api/api_conveyor.md) page.
    """)
    return


if __name__ == "__main__":
    app.run()
