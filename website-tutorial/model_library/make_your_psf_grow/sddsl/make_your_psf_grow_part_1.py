# Front matter the .py format cannot carry; injected on export.
# description: The growth strategies open to a professional services firm, and why selling more and delivering more pull against each other.
# keywords: system dynamics, professional services firm, growth, business simulation, bptk, bptk-py, python, sd dsl
#
# The reader can only look here - this page walks through how the model is built and
# every chart illustrates one of those steps, so no cell offers a decision to take.
# The levers live on their own page, `make_your_psf_grow_playground`, which is small
# enough to hydrate in seconds; these pages would have cost 8 MB of Pyodide to show
# pictures that are already in them.
# interactive: false
import marimo

__generated_with = "0.23.13"
app = marimo.App(app_title="Make Your Professional Service Firm Grow (Part 1, SD DSL)")


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Make Your Professional Service Firm Grow (Part 1)
    ## Growth Strategies In Professional Service Firms
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Making professional service firms grow is hard - you not only need to compete for business, but also for the professionals that deliver your services. And you have to allocate their time wisely between business development and service delivery. This post first sketches the dynamics that govern growth in professional service firms and then presents a little game to challenge your thinking and prepare the ground for future posts.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    When speaking to entrepreneurs and executives I often hear that "business is tough" and "being a businessman is hard" and I think most people take this to mean that market conditions are bad and therefore there is too little business around.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    But actually business can also be really tough when the market is booming and you are trying to make your company grow - in fact, as I will demonstrate, if you grow your company and are not careful you may end up with higher revenue but less money in the bank than you would have made if you had kept the company at the size it was in the beginning (i.e. by not growing at all).
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    To be specific, I will use our business prototyping approach to investigate growth strategies in professional service firms (such as management consultants, IT consultants and creative agencies). Making professional service firms (PSFs) grow is particularly hard for the following reasons:
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    - You are not only competing for customers but also for human resources, i.e. the professionals you need to deliver your service. When market conditions are good for selling services, they are often bad for hiring professionals, because all your competitors are also trying to recruit fresh talent. This is why professional service firms are much less scalable then firms that create consumer goods or firms that provide online services.
    - When you bring new professionals on board, it takes a while for them to learn about how you go about your business. Not only are they not productive themselves, they also bring down the productivity of the experience professionals who are showing them the ropes.
    - You need these professionals both to acquire new business (e.g. for service development effort and pre-sales bidding effort that is not billable) and also to deliver the associated service. If you don't do this well, you can easily end up with an oscillating business where you first have to much business, but to few professional resources, then you have to little business and to many resources and so on.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Please note that the first of these points is about market conditions (which you can't really influence) while the other two points are about conditions within your company (which you definitely can influence). As we will see, even if market conditions are perfect you can still make better or worse decisions about how to use these conditions to your advantage.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    To investigate growth strategies, we'll first sketch the key dynamics that govern growth. We will then use this as a basis to create a quantitative model to experiment with.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Let me start with how the professional service firm (PSF) makes money. To keep our discussion simple I assume the PSF delivers its service in the form of projects. The projects are billed regularly (e.g. weekly). The revenue is then calculated as the project delivery rate (measured in staff weeks per week) times the weekly project delivery fee (which I assume is identical for each staff member). The project delivery rate itself will depend on how many staff members are working on projects, the volume of the projects (measured in staff weeks) and the duration of the projects (measured in calendar weeks). These factors determine the PSFs revenue, I've illustrated them in the causal loop diagram below.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    <div align="center"><img src="images/resource_allocation_dynamics_10.svg" width="90%"></div>
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    After a delay the revenue is collected and arrives in the PSFs bank account, increasing its stock of cash. Of course the cash balance also has a negative influence, viz. the costs, which are determined by the cost of the professional staff (salaries, workplace costs) and fixed costs (such as marketing costs, administrative overhead, ...). I've added these connections to the diagram below.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    <div align="center"><img src="images/resource_allocation_dynamics_20.svg" width="90%"></div>
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    What does the company do with the remaining cash?
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Well, the company wants to grow and the only way to achieve significant growth is by hiring new staff; the amount of cash available to the PSF will determine the hiring rate. Any new staff coming on board create will create cost - I've illustrated this balancing loop in the diagram below.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    <div align="center"><img src="images/resource_allocation_dynamics_30.svg" width="90%"></div>
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    So far, we have investigated how the company will create revenue by delivering projects. Clearly the rate at which the staff can deliver projects doesn't only depend on the number of staff available, but also on the number of current projects. The faster the projects are delivered, the faster the current number of projects goes down - if no new projects come in, the PSF will go ot ouf business. I've added the negative feedback from the project delivery rate to the projects below.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    <div align="center"><img src="images/resource_allocation_dynamics_40.svg" width="90%"></div>
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    But where do new projects come from?
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Well, obviously the professional service staff can't just spend its time delivering projects, it also needs to spend some of its time acquiring new projects. The number of business development staff will determine the rate at which new business is developed, along with the effort to find prospective customers and with the prospecting success. The result of business development efforts are proposals, some of which are successful, some of which are not. Experience also shows that there is mostly a significant delay between generating a lead, writing a proposal and the time the new assignment starts. It is important to note that although these factors can be influenced by the company (after all, that is what marketing is all about), they are mainly determined by the market you are operating in.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    The actual ratio of business development time to project delivery time will depend on the staffing policy - some PSFs have teams dedicated to developing business, each team member spending all its time developing business and none delivering projects. In other companies, some of the staff both develop business and deliver projects, sharing their time between the two tasks. I will investigate the implications of these strategies a little later in this chapter, for now it is sufficent to add these facts to the sketch.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    <div align="center"><img src="images/resource_allocation_dynamics_50.svg" width="90%"></div>
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    The sketch is looking good now, it captures the main feedback loops that govern growth in a professional service firm. But as I noted at the beginning of this section, growth may have a negative effect on the productivity of the professional service team. I've added these negative feedbacks to the diagram below.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    <div align="center"><img src="images/resource_allocation_dynamics_60.svg" width="90%"></div>
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    This completes my investigation for today - it didn't take long to create the sketch, but nevertheless it captures some of the important feedback loops that determine the performance of a professional service firm. I will use the completed sketch below as a basis for investigating resource allocation policies in future posts.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    <div align="center"><img src="images/resource_allocation_dynamics.svg" width="90%"></div>
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    We now have a good understanding of what drives revenue and cash flow in a professional service firm. Now let's play a little game to see whether we can make our service firm grow.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # A Game To Test Our Strategic Skills
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    We have built a little game to test your entrepreneurial skills: every month you receive the current figures regarding your current project backlog, your headcount and the cash you have at your disposal. You have to decide how many new people to hire and how to allocate your current staff between business development and project delivery.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    The game used to run in a frame on this page, at `prototypes.transentis.com/psf`, and
    that host no longer answers. The case study it belongs to is on the transentis site:
    [Make Your PSF Grow](https://www.transentis.com/resources/make-your-psf-grow).
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    The challenge is to increase your cash and up with at least EUR 26 Mio. at the beginning of month 24.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Its not as easy as it sounds, in fact it is quite difficult to end up with more cash then if you had done nothing at all.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    And once you've reached your first cash target, try and reach EUR 42 Mio. of cash at the beginning of month 42 - you will probably find that the tactic you use to achieve the first cash target will not help you to reach the second target.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Here are the assumptions underlying the game - essentially we are just quantifying all the values in the conceptual diagrams we defined above:
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    1. __Project Volume.__ The average project volume is 16 person-months.
    2. __Project Duration.__ The average project duration is 2 months, i.e. 8 project delivery staff are involved for 2 months.
    3. __Prospecting Effort.__ The prospecting effort to generate a lead and write a proposal is 4 months.
    4. __Project Acquisition Duration.__ The project acquisition duration is 6 months, i.e. it takes 6 months between generating the initial lead before a newly acquired project starts.
    5. __Market Conditions.__ Market conditions are perfect, i.e. both the prospecting and acquisition success rates are at 100%.
    6. __Delivery Fee.__ The project delivery fee is EUR 17,600 per person-month, i.e. the daily rate per consultant is at EUR 880.
    7. __Billing Interval.__ Projects are charged on a monthly basis.
    8. __Collection Duration.__ The collection duration is 2 months, i.e. it takes 2 months after revenue is collected and arrives in the bank.
    9. __Workplace Cost.__ The workplace cost per staff member is at EUR 1000 per month (rent, laptop, software licenses and services, ...).
    10. __Overhead Cost.__ The company has overhead cost of EUR 306.000 per month (administrative cost, ...).
    11. __Staff Salary.__ The average salary per staff member is at EUR 80,000 per year.
    12. __Hiring Duration.__  The hiring duration for new staff is 3 months
    13. __Initial Cash.__ The initial cash is at EUR 1,000,000.
    14. __Initial Staff.__ The company initially has 200 professional staff members, 20% of which are assigned to business development. At this setting, the company is stable.
    15. __Initial Backlog.__ The initial backlog of project weeks is 320 person-months, and the initial number of prospective projects/proposals in the sales pipeline is also 320 person-months.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Before you read on, please try the challenge for yourself: first test the stable setting at 20% business development and zero hires and just "click the game through". Make sure you understand what the graphs mean. Then hire some people in the first months and see what happens to your staff level. Can you explain why the graphs change when they do? Can you see the dynamic we depicted in our conceptual model? Once you have understood the basic dynamics, start experimenting and try to solve the challenges - don't be ashamed to use pencil and paper to make a few calculations, you will most likely need too!
    """)
    return


if __name__ == "__main__":
    app.run()
