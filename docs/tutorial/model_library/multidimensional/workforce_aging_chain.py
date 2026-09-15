# Front matter the .py format cannot carry; injected on export.
# description: A workforce aging chain over seniority levels, built with the multidimensional SD DSL.
# keywords: system dynamics, aging chain, workforce planning, arrays, vectors, multidimensional, bptk, bptk-py, python, business simulation
import marimo

__generated_with = "0.23.13"
app = marimo.App(app_title="Workforce Aging Chain")


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # A Workforce Aging Chain

    Every professional services firm runs on the same structure: people are hired,
    they gain experience, some of them are promoted, and some of them leave. The
    interesting questions are never about one level in isolation. How long does it take
    for a hiring decision to show up in the senior ranks? What does the pyramid cost
    once it has settled? If we freeze junior hiring for a year, when do we feel it?

    This is an **aging chain**, and it is the classic use of arrays in System Dynamics.
    The structure repeats: every seniority level is a stock, fed by hiring and by
    promotion out of the level below, drained by promotion and attrition. Writing that
    out three times would say the same thing three times over. With the
    multidimensional SD DSL you say it once, over a vector of levels.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## The Structure

    Three seniority levels - **junior**, **mid**, **senior** - and one stock per level:

    | Element | Kind | Meaning |
    |---|---|---|
    | `headcount[level]` | stock | the people at that level |
    | `hiring[level]` | flow | lateral hires arriving from outside |
    | `promotion[level]` | flow | people leaving the level upwards |
    | `attrition[level]` | flow | people leaving the firm |
    | `salary[level]`, `cost[level]` | constant, converter | the cost of the level |
    | `total_headcount`, `total_cost`, `average_salary` | converters | the firm as a whole |

    The chain is what makes this more than three separate models: **promotion out of one
    level is an inflow to the next.** What leaves `junior` upwards arrives in `mid`, and
    what leaves `mid` upwards arrives in `senior`. A senior is never promoted out of the
    chain, so the senior promotion rate is zero.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Declaring the Elements

    An arrayed element starts life like any other. It becomes arrayed when you give it
    a shape - here `setup_named_vector`, which takes a dictionary of index names to
    initial values. The names are yours to choose, and they are what you use to address
    a single level later on.
    """)
    return


@app.cell
def _():
    from BPTK_Py import Model, bptk
    from BPTK_Py import sd_functions as sd

    LEVELS = ("junior", "mid", "senior")

    workforce = Model(starttime=0.0, stoptime=40.0, dt=1.0, name="Workforce")

    headcount = workforce.stock("headcount")
    hiring = workforce.flow("hiring")
    promotion = workforce.flow("promotion")
    attrition = workforce.flow("attrition")
    cost = workforce.converter("cost")

    salary = workforce.constant("salary")
    hiring_rate = workforce.constant("hiring_rate")
    promotion_rate = workforce.constant("promotion_rate")
    attrition_rate = workforce.constant("attrition_rate")

    # A team of 155: a wide junior base, fewer seniors.
    headcount.setup_named_vector({"junior": 100.0, "mid": 40.0, "senior": 15.0})

    # Lateral hiring happens at every level, most of it into the junior base.
    hiring_rate.setup_named_vector({"junior": 12.0, "mid": 3.0, "senior": 1.0})

    # A senior is never promoted out of the chain, hence 0.0.
    promotion_rate.setup_named_vector({"junior": 0.15, "mid": 0.08, "senior": 0.0})
    attrition_rate.setup_named_vector({"junior": 0.10, "mid": 0.06, "senior": 0.04})
    salary.setup_named_vector({"junior": 60000.0, "mid": 90000.0, "senior": 130000.0})

    for _element in (hiring, promotion, attrition, cost):
        _element.setup_named_vector({level: 0.0 for level in LEVELS})
    return (
        LEVELS,
        Model,
        attrition,
        attrition_rate,
        bptk,
        cost,
        headcount,
        hiring,
        hiring_rate,
        promotion,
        promotion_rate,
        salary,
        sd,
        workforce,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Equations That Hold for Every Level

    The three flows and the cost have the same form at every level, so each is written
    once. `headcount * promotion_rate` is an **element-wise** product: it multiplies
    junior by junior, mid by mid and senior by senior, and never mixes them.
    """)
    return


@app.cell
def _(attrition, attrition_rate, cost, headcount, hiring, hiring_rate, promotion, promotion_rate, salary):
    hiring.equation = hiring_rate
    promotion.equation = headcount * promotion_rate
    attrition.equation = headcount * attrition_rate
    cost.equation = headcount * salary
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    The chain itself is the one part that has to be written level by level, and that is
    not a shortcoming of the notation - it is the model. Each level has a different
    neighbour above and below, so `headcount[mid]` genuinely references
    `promotion[junior]`, which is a *different index* of a *different element*. An
    element-wise equation cannot express that, and should not.
    """)
    return


@app.cell
def _(attrition, headcount, hiring, promotion):
    headcount["junior"].equation = (
        hiring["junior"] - promotion["junior"] - attrition["junior"]
    )
    headcount["mid"].equation = (
        hiring["mid"] + promotion["junior"] - promotion["mid"] - attrition["mid"]
    )
    headcount["senior"].equation = (
        hiring["senior"] + promotion["mid"] - attrition["senior"]
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## The Firm as a Whole

    Three aggregations turn the vector back into single numbers. `arr_sum` adds every
    index, `arr_mean` averages them - and the result is an ordinary scalar element, so
    you can plot it, reference it from another equation, or read it in a scenario.
    """)
    return


@app.cell
def _(bptk, cost, headcount, salary, workforce):
    total_headcount = workforce.converter("total_headcount")
    total_headcount.equation = headcount.arr_sum()

    total_cost = workforce.converter("total_cost")
    total_cost.equation = cost.arr_sum()

    average_salary = workforce.converter("average_salary")
    average_salary.equation = salary.arr_mean()

    bptk_workforce = bptk()
    bptk_workforce.register_model(workforce)
    bptk_workforce.register_scenarios(
        scenario_manager="smWorkforce",
        scenarios={"base": {}, "interactive": {}},
    )
    return (bptk_workforce,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## How the Pyramid Settles

    The firm starts with 100 juniors, 40 mids and 15 seniors, and the plot below shows
    what the current policy does with that. Each level is a separate series, addressed
    by its flattened name - `headcount[junior]` is how a sub-element appears in a plot,
    in a scenario constant, and in the simulation results.
    """)
    return


@app.cell
def _(bptk_workforce):
    bptk_workforce.plot_scenarios(
        scenario_managers=["smWorkforce"],
        scenarios=["base"],
        equations=["headcount[junior]", "headcount[mid]", "headcount[senior]"],
        series_names={
            "smWorkforce_base_headcount[junior]": "Junior",
            "smWorkforce_base_headcount[mid]": "Mid",
            "smWorkforce_base_headcount[senior]": "Senior",
        },
        title="Headcount by seniority level",
        x_label="Month",
        y_label="People",
        format="axes",
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Three levels, three quite different stories, from one set of equations:

    * **Junior** collapses, from 100 to 48 within a year. Twelve hires a month cannot
      keep up with a quarter of the level leaving it every month - 15 % promoted, 10 %
      leaving the firm.
    * **Mid** jumps the other way, from 40 to about 76 in six months, fed by the juniors
      promoted into it, then eases back to 73 as that wave passes.
    * **Senior** grows and keeps growing: 141 people by month 40, and still climbing
      long after the other two have settled.

    That last one is the whole point of the model, and it is worth being precise about
    why. A level's **time constant** is one divided by its total outflow rate. Junior
    loses 25 % a month, so its time constant is four months. Senior loses 4 %, so its
    time constant is twenty-five months. The senior level is the slow part of the
    system: it takes years to build, years to unwind, and it carries the highest
    salary. Every question about this firm's cost structure is really a question about
    the senior level.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Where it ends up can be worked out by hand, by setting each level's inflow equal to
    its outflow:

    $$junior = \frac{12}{0.15 + 0.10} = 48.0$$

    $$mid = \frac{3 + 0.15 \cdot junior}{0.08 + 0.06} = 72.9$$

    $$senior = \frac{1 + 0.08 \cdot mid}{0.04} = 170.7$$

    So the pyramid inverts. The firm ends up with more seniors than juniors - 171
    against 48 - which at these salaries is a very different cost base from the one it
    started with. Note how long that takes: the plot above stops at month 40, where the
    senior level has reached 141 of its eventual 171. Junior and mid have been settled
    for years by then; senior needs about fifteen.

    The cost line tells the same story in money. The firm starts at 11.6 million a
    month, is at 27.8 million by month 40, and settles at 31.6 million - nearly three
    times the starting cost, from a headcount that only grows from 155 to 292. The
    difference is the mix: the level that grows is the expensive one.
    """)
    return


@app.cell
def _(bptk_workforce):
    bptk_workforce.plot_scenarios(
        scenario_managers=["smWorkforce"],
        scenarios=["base"],
        equations=["total_cost"],
        series_names={"smWorkforce_base_total_cost": "Total salary cost"},
        title="Total salary cost per month",
        x_label="Month",
        y_label="Cost",
        format="axes",
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Experiment With the Policy

    The three rates below are the policy levers, and each one addresses a single index of
    an arrayed constant. `hiring_rate[junior]` is a name like any other, so a scenario
    can set it, a slider can drive it, and everything downstream follows.

    Two experiments worth running:

    * Pull **junior hiring** down to zero - a hiring freeze. The junior level empties
      quickly, but the senior level keeps growing for years on the promotions already in
      the pipe. The cost line barely notices at first.
    * Push **senior attrition** from 4 % to 8 %. That halves the senior time constant,
      and the whole cost base moves - more than any change to hiring does.
    """)
    return


@app.cell
def _(mo):
    junior_hiring = mo.ui.slider(
        start=0.0, stop=30.0, step=1.0, value=12.0, show_value=True,
        label="Junior hires per month"
    )
    junior_promotion = mo.ui.slider(
        start=0.0, stop=0.4, step=0.01, value=0.15, show_value=True,
        label="Junior promotion rate"
    )
    mid_promotion = mo.ui.slider(
        start=0.0, stop=0.4, step=0.01, value=0.08, show_value=True,
        label="Mid promotion rate"
    )
    senior_attrition = mo.ui.slider(
        start=0.01, stop=0.3, step=0.01, value=0.04, show_value=True,
        label="Senior attrition rate"
    )
    return junior_hiring, junior_promotion, mid_promotion, senior_attrition


@app.cell
def _(bptk_workforce, junior_hiring, junior_promotion, mid_promotion, mo, senior_attrition):
    _scenario = bptk_workforce.get_scenario("smWorkforce", "interactive")
    _scenario.constants["hiring_rate[junior]"] = junior_hiring.value
    _scenario.constants["promotion_rate[junior]"] = junior_promotion.value
    _scenario.constants["promotion_rate[mid]"] = mid_promotion.value
    _scenario.constants["attrition_rate[senior]"] = senior_attrition.value
    bptk_workforce.reset_scenario_cache(
        scenario_manager="smWorkforce", scenario="interactive"
    )

    def _diagram(equations, names, title, y_label):
        axes = bptk_workforce.plot_scenarios(
            scenario_managers=["smWorkforce"],
            scenarios=["interactive"],
            equations=equations,
            series_names={
                f"smWorkforce_interactive_{equation}": name
                for equation, name in zip(equations, names)
            },
            title=title,
            x_label="Month",
            y_label=y_label,
            format="axes",
        )
        return axes.figure

    mo.vstack([
        junior_hiring,
        junior_promotion,
        mid_promotion,
        senior_attrition,
        mo.ui.tabs({
            "Headcount": _diagram(
                ["headcount[junior]", "headcount[mid]", "headcount[senior]"],
                ["Junior", "Mid", "Senior"],
                "Headcount by seniority level", "People"),
            "Cost": _diagram(
                ["cost[junior]", "cost[mid]", "cost[senior]"],
                ["Junior", "Mid", "Senior"],
                "Salary cost by seniority level", "Cost"),
            "Totals": _diagram(
                ["total_headcount"], ["Total headcount"],
                "The firm as a whole", "People"),
        }),
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Why Three Flows and Not One

    A level that both rises and falls looks like a job for a single signed flow, and
    this model deliberately does not do that: **a flow never goes negative** - see
    [the reference page](../../sd-dsl/sd_dsl_multidimensional/sd_dsl_multidimensional.html#what-is-not-supported).
    Hiring, promotion and attrition are three flows because each of them genuinely has a
    direction, which is also the clearer way to read the chain: what leaves one level
    upwards is what arrives in the next.

    The other thing worth taking away: **an arrayed element is a parent with
    sub-elements.** `headcount` holds no value of its own; `headcount["junior"]` does.
    That is why the plots above name `headcount[junior]`, and it is what makes an arrayed
    model cheap - to everything downstream, a sub-element is an ordinary scalar element.
    """)
    return


if __name__ == "__main__":
    app.run()
