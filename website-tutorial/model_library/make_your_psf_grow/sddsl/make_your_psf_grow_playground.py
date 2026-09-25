# Front matter the .py format cannot carry; injected on export.
# description: Run the finished professional services firm model in your browser - set the business development allocation and the hiring, and watch what it does to staff and cash.
# keywords: system dynamics, sd dsl, professional services, business simulation, bptk, bptk-py, python
#
# The one interactive page of this section. The four walk-through pages are static -
# their charts illustrate seven build steps and there is nothing for the reader to
# set - so the levers live here, on a page small enough to hydrate in seconds.
# The model is built inline on purpose: importing it from `src/` would make this page
# static too, because Pyodide never receives the page's directory.
# interactive: true
import marimo

__generated_with = "0.23.13"
app = marimo.App(app_title="Try It Yourself - Grow Your Own PSF")


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Try It Yourself: Grow Your Own PSF

    [Part 2](make_your_psf_grow_part_2.html) builds this model over seven steps and explains
    every equation in it. This page skips the explanation and hands you the finished model,
    so you can run the firm yourself: the two sliders are the two decisions the model
    knows, and the two charts underneath redraw whenever you move one.

    The base case for comparison is the one from part 2, step 7: a fifth of capacity in
    business development, nobody hired, and a firm that neither grows nor shrinks.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## The model

    The whole firm in one cell - stocks, flows, converters, equations. It is the model of
    part 2 after step 7, so if you want to know why a line reads the way it does, that is
    where to look. Edit anything here and both charts follow.
    """)
    return


@app.cell
def _():
    from BPTK_Py import Model, bptk
    from BPTK_Py import sd_functions as sd

    model = Model(starttime=0.0, stoptime=24.0, dt=1.0, name="MakeYourPsfGrow")

    # Cash: the firm collects revenue and pays its cost
    cash = model.stock("cash")
    cashIn = model.flow("cashIn")
    cashOut = model.flow("cashOut")
    cashFlow = model.converter("cashFlow")

    # Cost: salaries, workplaces and overhead
    cost = model.converter("cost")
    staffSalary = model.converter("staffSalary")
    workplaceCost = model.converter("workplaceCost")
    staffCost = model.converter("staffCost")
    overheadCost = model.converter("overheadCost")

    # Revenue: made when work is delivered, collected two months later
    receivables = model.stock("receivables")
    makingRevenue = model.flow("makingRevenue")
    collectingRevenue = model.flow("collectingRevenue")
    collectionTime = model.converter("collectionTime")
    revenue = model.converter("revenue")
    projectDeliveryFee = model.converter("projectDeliveryFee")
    projectDeliveryRate = model.converter("projectDeliveryRate")

    # The project backlog and what can be delivered from it
    projects = model.stock("projects")
    deliveringProjects = model.flow("deliveringProjects")
    projectDeliveryCapacity = model.converter("projectDeliveryCapacity")

    # Staff, and how their time is split between delivering and selling
    professionalStaff = model.stock("professionalStaff")
    workMonth = model.converter("workMonth")
    workCapacity = model.converter("workCapacity")
    businessDevelopmentCapacity = model.converter("businessDevelopmentCapacity")
    businessDevelopmentAllocationPct = model.converter("businessDevelopmentAllocation%")

    # Project acquisition: proposals written, projects won six months later
    proposals = model.stock("proposals")
    prospectingProjects = model.flow("prospectingProjects")
    winningProjects = model.flow("winningProjects")
    proposalRate = model.converter("proposalRate")
    prospectingEffort = model.converter("prospectingEffort")
    projectVolume = model.converter("projectVolume")
    projectAcquisitionDuration = model.converter("projectAcquisitionDuration")

    # Hiring: three months from the decision to the first day of work
    staffInRecruitment = model.stock("staffInRecruitment")
    hiringStaff = model.flow("hiringStaff")
    staffArriving = model.flow("staffArriving")
    hiringRate = model.converter("hiringRate")
    hiringDuration = model.converter("hiringDuration")

    cash.initial_value = 1000.0
    cash.equation = cashIn - cashOut
    cashIn.equation = collectingRevenue
    cashOut.equation = cost
    cashFlow.equation = cashIn - cashOut

    workplaceCost.equation = 1.0
    staffSalary.equation = 80.0 / 12
    overheadCost.equation = 306.0
    staffCost.equation = professionalStaff * (workplaceCost + staffSalary)
    cost.equation = staffCost + overheadCost

    receivables.initial_value = 160 * 17.6 * 2
    receivables.equation = makingRevenue - collectingRevenue
    projectDeliveryFee.equation = 17.6
    revenue.equation = projectDeliveryFee * projectDeliveryRate
    makingRevenue.equation = revenue
    collectionTime.equation = 2.0
    collectingRevenue.equation = sd.delay(model, makingRevenue, collectionTime, 160 * 17.6)

    projects.initial_value = 320.0
    projects.equation = -deliveringProjects + winningProjects
    deliveringProjects.equation = projectDeliveryRate
    projectDeliveryRate.equation = sd.min(projects, projectDeliveryCapacity)

    professionalStaff.initial_value = 200.0
    professionalStaff.equation = staffArriving
    workMonth.equation = 1.0
    workCapacity.equation = professionalStaff * workMonth
    businessDevelopmentAllocationPct.equation = sd.lookup(
        sd.time(), "businessDevelopmentAllocation%"
    )
    businessDevelopmentCapacity.equation = (
        workCapacity * businessDevelopmentAllocationPct / 100
    )
    projectDeliveryCapacity.equation = workCapacity - businessDevelopmentCapacity

    proposals.initial_value = 320.0
    proposals.equation = prospectingProjects - winningProjects
    prospectingEffort.equation = 4.0
    projectVolume.equation = 16.0
    proposalRate.equation = projectVolume * (businessDevelopmentCapacity / prospectingEffort)
    prospectingProjects.equation = proposalRate
    projectAcquisitionDuration.equation = 6.0
    winningProjects.equation = sd.min(
        sd.delay(model, prospectingProjects, projectAcquisitionDuration, 160.0), proposals
    )

    staffInRecruitment.initial_value = 0.0
    staffInRecruitment.equation = hiringStaff - staffArriving
    hiringStaff.equation = hiringRate
    hiringRate.equation = sd.lookup(sd.time(), "hiringRate")
    hiringDuration.equation = 3.0
    staffArriving.equation = sd.delay(model, hiringStaff, hiringDuration)

    bptk = bptk()
    bptk.register_scenario_manager({"psfPlayground": {"model": model}})

    # The base case of part 2, step 7: a fifth of capacity selling, nobody hired
    monate = range(25)
    bptk.register_scenarios(
        scenario_manager="psfPlayground",
        scenarios={
            "base": {
                "points": {
                    "businessDevelopmentAllocation%": [(t, 20) for t in monate],
                    "hiringRate": [(t, 0) for t in monate],
                }
            }
        },
    )
    return bptk, monate


@app.cell
def _(anteil, bptk, einstellung, monate):
    bptk.register_scenarios(
        scenario_manager="psfPlayground",
        scenarios={
            "myPlan": {
                "points": {
                    "businessDevelopmentAllocation%": [
                        (t, anteil.value if t >= 4 else 20) for t in monate
                    ],
                    "hiringRate": [
                        (t, einstellung.value if t == 7 else 0) for t in monate
                    ],
                }
            }
        },
    )
    # `register_scenarios` returns nothing, so this name is what gives the two charts a
    # dependency on the sliders. Without it they have none and nothing redraws.
    mein_plan = f"{anteil.value} % selling, {einstellung.value} hired"
    return (mein_plan,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Your two decisions

    The cell above is what turns two numbers into a scenario the model can run. The two
    sliders underneath are those numbers.

    * **The allocation** is the share of capacity that wins work rather than delivering it.
      Raise it and more projects come in - six months later, because that is how long
      acquisition takes - but the capacity to deliver them is smaller in the meantime.
    * **The hiring** is how many people you take on in month 7. They arrive three months
      later and cost their salary from the day they start.

    The base case runs at 20 % and hires nobody, and the firm holds its ground: a backlog
    of 320 project months, delivered at 160 a month, won back at 160 a month.
    """)
    return


@app.cell
def _(mo):
    anteil = mo.ui.slider(
        0, 60, step=5, value=20, label="Business development allocation from month 4 (%)"
    )
    einstellung = mo.ui.slider(0, 400, step=50, value=0, label="Staff hired in month 7")
    # Created and shown here, read in the next cell: marimo forbids reading a UI
    # element's value in the cell that created it.
    mo.vstack([anteil, einstellung])
    return anteil, einstellung


@app.cell
def _(bptk, mein_plan):
    bptk.plot_scenarios(
        scenario_managers=["psfPlayground"],
        scenarios=["base", "myPlan"],
        equations=["professionalStaff"],
        title=f"Professional staff: base case against {mein_plan}",
        x_label="Months",
        y_label="People",
        format="axes",
    )
    return


@app.cell
def _(bptk, mein_plan):
    bptk.plot_scenarios(
        scenario_managers=["psfPlayground"],
        scenarios=["base", "myPlan"],
        equations=["cash"],
        title=f"Cash: base case against {mein_plan}",
        x_label="Months",
        y_label="k€",
        format="axes",
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Three things worth trying

    Every number below is what the charts show, not a guess - the base case ends the two
    years with EUR 24.44 million.

    * **Sell harder and hire nobody.** Push the allocation to 45 % and cash ends at
      **8.6 million** instead of 24.44. You win more work than you can deliver: the backlog
      grows, the delivery capacity you gave up is what would have earned the revenue, and
      the revenue you do win arrives six months after you paid for winning it.
    * **Hire without selling more.** Leave the allocation at 20 % and hire 200 people. They
      arrive in month 12 and the staff chart steps from 200 to 400, cash dips while they are
      paid out of a backlog that is not growing, and recovers to **18.6 million** - still
      short of doing nothing.
    * **Both together.** 40 % and 200 hires ends with 400 people and **15.1 million**.

    That is the lesson of the page: within two years **every** growth path costs cash. The
    firm gets bigger, not richer, and no setting of these two sliders reaches the easy cash
    target of EUR 30 million. Which is exactly the question
    [part 3](make_your_psf_grow_part_3.html) starts from.
    """)
    return


if __name__ == "__main__":
    app.run()
