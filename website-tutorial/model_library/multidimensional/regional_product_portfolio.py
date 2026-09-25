# Front matter the .py format cannot carry; injected on export.
# description: A product portfolio across regions, modelled as a matrix with the multidimensional SD DSL.
# keywords: system dynamics, matrix, arrays, multidimensional, portfolio, revenue, dot product, bptk, bptk-py, python, business simulation
import marimo

__generated_with = "0.23.13"
app = marimo.App(app_title="Regional Product Portfolio")


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # A Regional Product Portfolio

    Three products, two regions, and a different story in every cell. The stripe sells
    steadily in the north and hardly at all in the south. The gizmo is expensive, small
    in volume, and growing fast. Prices differ by region, and so do the margins.

    Six lines of business, then - and everything you want to know spans them. What is
    total revenue? Which line is the strongest, and by how much? What share does each
    line carry, and how is that share shifting? Which lines are above average?

    A **matrix** is the natural shape for this: one dimension for regions, one for
    products. Where the [aging chain](workforce_aging_chain.html) uses a vector to say
    "the same structure at every seniority level", a matrix says "the same structure in
    every region-and-product combination" - and the aggregations then collapse it back
    to the numbers a portfolio review actually asks for.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Setting Up the Matrix

    `setup_named_matrix` takes a dictionary of dictionaries: the outer keys are the rows,
    the inner keys the columns. Every element in this model has the same shape, so the
    equations can treat the whole portfolio as one object.

    | Element | Kind | Meaning |
    |---|---|---|
    | `units[region][product]` | stock | units sold per month |
    | `growth[region][product]` | flow | how that volume changes |
    | `price`, `unit_cost` | constants | the average price and cost of one unit |
    | `revenue`, `margin`, `share` | converters | per line of business |
    | `total_revenue`, `best_line`, ... | converters | the portfolio as a whole |
    """)
    return


@app.cell
def _():
    from BPTK_Py import Model, bptk
    from BPTK_Py import sd_functions as sd

    REGIONS = ("north", "south")
    PRODUCTS = ("stripe", "mohawk", "gizmo")

    portfolio = Model(starttime=0.0, stoptime=24.0, dt=1.0, name="Portfolio")

    units = portfolio.stock("units")
    growth = portfolio.flow("growth")
    growth_rate = portfolio.constant("growth_rate")
    price = portfolio.constant("price")
    unit_cost = portfolio.constant("unit_cost")

    units.setup_named_matrix({
        "north": {"stripe": 1200.0, "mohawk": 800.0, "gizmo": 150.0},
        "south": {"stripe": 400.0, "mohawk": 950.0, "gizmo": 600.0},
    })
    growth_rate.setup_named_matrix({
        "north": {"stripe": 0.01, "mohawk": 0.02, "gizmo": 0.08},
        "south": {"stripe": 0.03, "mohawk": 0.015, "gizmo": 0.05},
    })
    price.setup_named_matrix({
        "north": {"stripe": 49.0, "mohawk": 79.0, "gizmo": 249.0},
        "south": {"stripe": 45.0, "mohawk": 72.0, "gizmo": 219.0},
    })
    unit_cost.setup_named_matrix({
        "north": {"stripe": 31.0, "mohawk": 44.0, "gizmo": 120.0},
        "south": {"stripe": 30.0, "mohawk": 42.0, "gizmo": 118.0},
    })
    return (
        Model,
        PRODUCTS,
        REGIONS,
        bptk,
        growth,
        growth_rate,
        portfolio,
        price,
        sd,
        unit_cost,
        units,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Equations That Hold for Every Cell

    Element-wise arithmetic over a matrix pairs cell with cell: north-stripe with
    north-stripe, south-gizmo with south-gizmo. Volume times price is revenue, price
    minus cost times volume is margin, and each is written once for all six lines.

    The volume itself compounds: each cell grows at its own rate, so `growth` reads the
    stock it feeds. That is the one arrayed feedback loop in this model, and it is what
    makes the mix shift over time.
    """)
    return


@app.cell
def _(growth, growth_rate, portfolio, price, unit_cost, units):
    growth.equation = units * growth_rate
    units.equation = growth

    revenue = portfolio.converter("revenue")
    revenue.equation = units * price

    margin = portfolio.converter("margin")
    margin.equation = (price - unit_cost) * units
    return margin, revenue


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Collapsing the Matrix to the Numbers You Report

    The aggregations take the whole matrix and return one number. All nine work on a
    matrix exactly as they do on a vector, over every cell:

    | | |
    |---|---|
    | `arr_sum`, `arr_mean` | the total and the average across all six cells |
    | `arr_max`, `arr_min` | the strongest and the weakest line |
    | `arr_median` | the middle line - with six cells, the average of the two middle ones |
    | `arr_stddev` | how unevenly the revenue is spread |
    | `arr_rank(2)` | the second strongest line |
    | `arr_prod` | the product of every cell - see the compounding example further down |
    | `arr_size` | **the length of the first dimension**, so 2 here, not 6 |

    That last one is a trap worth knowing: `arr_size` counts rows, not cells. If you
    want the number of lines of business, multiply the two dimensions yourself.
    """)
    return


@app.cell
def _(bptk, portfolio, price, revenue):
    total_revenue = portfolio.converter("total_revenue")
    total_revenue.equation = revenue.arr_sum()

    average_price = portfolio.converter("average_price")
    average_price.equation = price.arr_mean()

    best_line = portfolio.converter("best_line")
    best_line.equation = revenue.arr_max()

    weakest_line = portfolio.converter("weakest_line")
    weakest_line.equation = revenue.arr_min()

    median_line = portfolio.converter("median_line")
    median_line.equation = revenue.arr_median()

    revenue_spread = portfolio.converter("revenue_spread")
    revenue_spread.equation = revenue.arr_stddev()

    second_best_line = portfolio.converter("second_best_line")
    second_best_line.equation = revenue.arr_rank(2)

    region_count = portfolio.converter("region_count")
    region_count.equation = price.arr_size() * 1.0
    return (
        average_price,
        best_line,
        median_line,
        region_count,
        revenue_spread,
        second_best_line,
        total_revenue,
        weakest_line,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## An Array Meeting Its Own Aggregation

    A share is a cell divided by the total, which means an arrayed element divided by a
    scalar - and the scalar happens to be an aggregation of that same array. That is
    allowed, and it reads exactly as you would write it on paper:
    """)
    return


@app.cell
def _(portfolio, revenue, sd):
    share = portfolio.converter("share")
    share.equation = revenue / revenue.arr_sum()

    # A comparison and a conditional, over the whole matrix: the lines pulling above
    # their weight. `revenue.arr_mean()` is one number, `revenue` is six - so this is
    # six comparisons and six conditionals.
    above_average = portfolio.converter("above_average")
    above_average.equation = sd.If(revenue > revenue.arr_mean(), revenue, 0.0)
    return above_average, share


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Where `arr_prod` Earns Its Keep

    A product of six revenues means nothing. A product of growth factors means quite a
    lot: it is compounding. Four quarterly factors multiplied together give the factor
    for the year, and that is a vector aggregation with a genuine use.
    """)
    return


@app.cell
def _(portfolio):
    quarterly_factor = portfolio.constant("quarterly_factor")
    quarterly_factor.setup_vector(4, [1.02, 1.05, 0.99, 1.08])

    annual_factor = portfolio.converter("annual_factor")
    annual_factor.equation = quarterly_factor.arr_prod()
    return (annual_factor,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Two good quarters, a weak third and a strong fourth: 1.02 x 1.05 x 0.99 x 1.08 gives
    **1.1451**, so 14.5 % of growth over the year. Note that this is not the average
    quarter compounded - averaging the four factors and raising the result to the fourth
    power gives a different, wrong answer. `arr_prod` is the operator that gets it right.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Handing the Model to BPTK

    One thing to watch, and it applies to every model rather than to arrays: a scenario
    manager takes the model's equations when you register it. Elements added *after*
    `register_model` are not part of any scenario, and plotting one reports that it does
    not exist. So the model is registered here, once every element above is defined.
    """)
    return


@app.cell
def _(above_average, annual_factor, bptk, portfolio, share, total_revenue):
    bptk_portfolio = bptk()
    bptk_portfolio.register_model(portfolio)
    bptk_portfolio.register_scenarios(
        scenario_manager="smPortfolio",
        scenarios={"base": {}, "interactive": {}},
    )
    return (bptk_portfolio,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Month 0 is where the simulation starts, and it is the leftmost point of the plot
    below. Every figure is **revenue per month** - the units a line has on hand times its
    price in that region:

    | Revenue per month | stripe | mohawk | gizmo |
    |---|---|---|---|
    | **north** | 58,800 | 63,200 | 37,350 |
    | **south** | 18,000 | 68,400 | 131,400 |

    The aggregations turn those six cells into the four series the plot draws.
    `total_revenue` adds them up to **377,150** a month; `best_line` is the southern gizmo
    and `weakest_line` the southern stripe, a factor of seven apart. `median_line` is
    **61,000**, which is no cell of the table: with six cells the median is the average of
    the two middle ones. `second_best_line` picks the northern mohawk, and
    `revenue_spread` - the standard deviation over the six cells - says how unevenly that
    revenue is spread.

    Margin is a different quantity from all of those: price minus unit cost, times the
    units. Over the same six cells it comes to **164,050** a month.

    From month 1 on every cell grows at its own rate, so those four lines drift apart -
    and watching them drift is the point of the plot.
    """)
    return


@app.cell
def _(bptk_portfolio):
    bptk_portfolio.plot_scenarios(
        scenario_managers=["smPortfolio"],
        scenarios=["base"],
        equations=["total_revenue", "best_line", "median_line", "weakest_line"],
        series_names={
            "smPortfolio_base_total_revenue": "Total revenue",
            "smPortfolio_base_best_line": "Strongest line",
            "smPortfolio_base_median_line": "Median line",
            "smPortfolio_base_weakest_line": "Weakest line",
        },
        title="The portfolio, and its extremes",
        x_label="Month",
        y_label="Revenue per month",
        format="axes",
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## The Mix Shifts

    Because every cell grows at its own rate, the portfolio in month 24 is not the
    portfolio you started with. The gizmo compounds at 8 % a month in the north and 5 %
    in the south; the stripe crawls along at 1 % and 3 %.

    | Revenue per month | stripe | mohawk | gizmo |
    |---|---|---|---|
    | **north** | 74,660 | 101,653 | 236,843 |
    | **south** | 36,590 | 97,778 | 423,778 |

    The cells are rounded to whole units, so they add up to one less than the
    **971,303** the model reports.

    Revenue and margin per month have both grown about two and a half times. But the
    *shape* has changed more than the size: the two gizmo lines were 45 % of revenue in
    month 0 and are 68 % of it by month 24.

    The plot below is where that shift becomes visible, and it deliberately does **not**
    draw the numbers in the table. It draws `share` - each cell divided by the total - so
    a line stays flat while it merely keeps up with the portfolio and only moves when its
    weight changes.

    Watch `above_average` for a subtlety worth understanding. In month 0, three of the six
    lines are above the mean; in month 12 only *one* is - not because the others shrank,
    but because the southern gizmo has grown enough to drag the mean up past them. By
    month 24 there are two again, the northern gizmo having caught up with the mean it was
    below. A threshold that is itself an aggregation moves with the data.
    """)
    return


@app.cell
def _(bptk_portfolio):
    bptk_portfolio.plot_scenarios(
        scenario_managers=["smPortfolio"],
        scenarios=["base"],
        equations=["share[north][gizmo]", "share[south][gizmo]",
                   "share[north][stripe]", "share[south][stripe]"],
        series_names={
            "smPortfolio_base_share[north][gizmo]": "North / gizmo",
            "smPortfolio_base_share[south][gizmo]": "South / gizmo",
            "smPortfolio_base_share[north][stripe]": "North / stripe",
            "smPortfolio_base_share[south][stripe]": "South / stripe",
        },
        title="Revenue share by line of business",
        x_label="Month",
        y_label="Share of total revenue",
        format="axes",
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Note the naming: a cell of a matrix is addressed with **nested** brackets -
    `share[north][gizmo]`. That is the name in a plot, in a scenario constant and in the
    simulation results, and it is the name the Rust engine sees as well.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## The Dot Product

    Everything so far has been element-wise: cells paired with matching cells. The dot
    product is the operator that does something else - it *sums across* a dimension, and
    that is what turns a matrix of volumes and a list of prices into revenue per region.

    Written out, revenue in the north is
    `units[north][stripe] * price[stripe] + units[north][mohawk] * price[mohawk] + ...`.
    That is exactly a matrix times a vector: a 2x3 matrix of volumes and a vector of
    three prices give a vector of two revenues.

    **One restriction to know:** `dot` works on **unnamed** arrays only. A named matrix
    raises rather than guessing how to line up the labels, so the model below uses
    positional indices - rows 0 and 1 for the regions, columns 0, 1 and 2 for the
    products - and a comment to say which is which. That is a real limitation and worth
    stating plainly; for element-wise work and the aggregations, named arrays are the
    better choice.
    """)
    return


@app.cell
def _(Model, bptk):
    # Rows are regions (0 = north, 1 = south), columns are products
    # (0 = stripe, 1 = mohawk, 2 = gizmo).
    trade = Model(starttime=0.0, stoptime=12.0, dt=1.0, name="Trade")

    volume = trade.constant("volume")
    volume.setup_matrix([2, 3], [[1200.0, 800.0, 150.0],
                                 [400.0, 950.0, 600.0]])

    list_price = trade.constant("list_price")
    list_price.setup_vector(3, [49.0, 79.0, 249.0])

    # Matrix . vector -> one revenue per region.
    revenue_per_region = trade.converter("revenue_per_region")
    revenue_per_region.equation = volume.dot(list_price)

    total_group_revenue = trade.converter("total_group_revenue")
    total_group_revenue.equation = revenue_per_region.arr_sum()
    return list_price, revenue_per_region, total_group_revenue, trade, volume


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    With one price list applied to both regions, the north brings in **159,350** a month
    and the south **244,050**. The northern figure is the one the named model produced,
    because the northern prices *are* the list prices there; the southern figure is higher
    than the named model's, and that difference is the model speaking rather than a
    mistake. A matrix times a *vector* of
    prices says "one price list for every region". If prices really differ by region, the
    element-wise `units * price` above is the honest formulation.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Matrix Times Matrix

    Give the second operand a second dimension and the same operator answers a bigger
    question. Put the price *and* the unit cost of each product side by side - a 3x2
    matrix, products by measure - and multiply:

    `volume (2x3) . rates (3x2)` gives a 2x2 matrix: for each region, its revenue and
    its cost. The margin per region is then one subtraction away.
    """)
    return


@app.cell
def _(trade, volume):
    # Rows are products, columns are measures (0 = price, 1 = unit cost).
    rates = trade.constant("rates")
    rates.setup_matrix([3, 2], [[49.0, 31.0],
                                [79.0, 44.0],
                                [249.0, 120.0]])

    # Matrix . matrix -> region x measure.
    financials = trade.converter("financials")
    financials.equation = volume.dot(rates)

    region_margin = trade.converter("region_margin")
    region_margin.setup_vector(2, [0.0, 0.0])
    for _region in (0, 1):
        region_margin[_region].equation = financials[_region][0] - financials[_region][1]
    return financials, region_margin


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    | | revenue | cost | margin |
    |---|---|---|---|
    | **north** | 159,350 | 90,400 | 68,950 |
    | **south** | 244,050 | 126,200 | 117,850 |

    One operator, and the whole regional profit and loss falls out. This is the case
    where the dot product pays for the positional indices: written element-wise, the same
    result needs six products, two sums per region and a subtraction.
    """)
    return


@app.cell
def _(bptk, financials, region_margin, trade):
    bptk_trade = bptk()
    bptk_trade.register_model(trade)
    return (bptk_trade,)


@app.cell
def _(bptk_trade):
    bptk_trade.plot_scenarios(
        scenario_managers=["smTrade"],
        scenarios=["base"],
        equations=["revenue_per_region[0]", "revenue_per_region[1]",
                   "region_margin[0]", "region_margin[1]"],
        series_names={
            "smTrade_base_revenue_per_region[0]": "North revenue",
            "smTrade_base_revenue_per_region[1]": "South revenue",
            "smTrade_base_region_margin[0]": "North margin",
            "smTrade_base_region_margin[1]": "South margin",
        },
        title="Revenue and margin per region, from two dot products",
        x_label="Month",
        format="axes",
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Experiment With the Portfolio

    Two levers, each addressing a single cell of a matrix by its nested name. The price
    of the northern stripe is a pricing decision; the growth rate of the southern gizmo
    is the bet on the fastest-moving line.

    Worth trying: drop the northern stripe price and watch how little the total moves -
    it is a large volume at a small price, and the portfolio no longer lives there. Then
    take the southern gizmo growth to 8 % and watch the mix run away with itself.
    """)
    return


@app.cell
def _(mo):
    stripe_price = mo.ui.slider(
        start=20.0, stop=80.0, step=1.0, value=49.0, show_value=True,
        label="Price: north / stripe"
    )
    gizmo_growth = mo.ui.slider(
        start=0.0, stop=0.1, step=0.005, value=0.05, show_value=True,
        label="Growth rate: south / gizmo"
    )
    return gizmo_growth, stripe_price


@app.cell
def _(bptk_portfolio, gizmo_growth, mo, stripe_price):
    _scenario = bptk_portfolio.get_scenario("smPortfolio", "interactive")
    _scenario.constants["price[north][stripe]"] = stripe_price.value
    _scenario.constants["growth_rate[south][gizmo]"] = gizmo_growth.value
    bptk_portfolio.reset_scenario_cache(
        scenario_manager="smPortfolio", scenario="interactive"
    )

    def _diagram(equations, names, title, y_label):
        axes = bptk_portfolio.plot_scenarios(
            scenario_managers=["smPortfolio"],
            scenarios=["interactive"],
            equations=equations,
            series_names={
                f"smPortfolio_interactive_{equation}": name
                for equation, name in zip(equations, names)
            },
            title=title,
            x_label="Month",
            y_label=y_label,
            format="axes",
        )
        return axes.figure

    mo.vstack([
        stripe_price,
        gizmo_growth,
        mo.ui.tabs({
            "Totals": _diagram(
                ["total_revenue"], ["Total revenue"],
                "Total revenue per month", "Revenue"),
            "Shares": _diagram(
                ["share[north][stripe]", "share[south][gizmo]"],
                ["North / stripe", "South / gizmo"],
                "Two lines, as a share of the portfolio", "Share"),
            "Extremes": _diagram(
                ["best_line", "weakest_line", "revenue_spread"],
                ["Strongest line", "Weakest line", "Spread"],
                "How evenly the revenue is spread", "Revenue"),
        }),
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Two Limits This Model Ran Into

    Both are worth naming because the model had to work around them, and both are in
    [the reference page's list](../../sd-dsl/sd_dsl_multidimensional/sd_dsl_multidimensional.html#what-is-not-supported)
    along with the rest.

    * **`dot` needs unnamed arrays**, which is why the section above switches from
      region and product names to positional indices.
    * **An aggregation always takes the whole array.** There is no "sum along the rows",
      so the per-region totals came from a dot product rather than from `arr_sum`. Where
      a row total is all you need, address the row itself: `revenue["north"].arr_sum()`
      works, because a row of a named matrix is a named vector in its own right.
    """)
    return


if __name__ == "__main__":
    app.run()
