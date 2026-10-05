# Front matter the .py format cannot carry; injected on export.
# description: A small arrayed SD DSL model from start to finish
# keywords: system dynamics, systemdynamics, sd dsl, arrays, bptk, bptk-py, python, business simulation
import marimo

__generated_with = "0.23.13"
app = marimo.App(app_title="A Simple Arrayed Model")


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # A Simple Arrayed Model
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    The examples on this page share one model, set up here:
    """)
    return


@app.cell
def _():
    from BPTK_Py import Model
    from BPTK_Py import sd_functions as sd
    from BPTK_Py.bptk import bptk

    model = Model(starttime=0.0, stoptime=15.0, dt=1.0, name="Arrays")
    return bptk, model, sd


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Lets have a look on a concrete example, how a multidimensional SD Model can look like.

    Consider an investment depot with two accounts:

    - bank account
    - depot account

    Both accounts will have different deposit rates and different interest rates each year.
    We want to investigate the value development of the bank account, the depot account and the whole investment depot.

    Lets set up the model:
    """)
    return

@app.cell
def _(model):
    account = model.stock('account')
    account.setup_named_vector({'bank': 0.0, 'depot': 0.0})
    accountInitialValues = model.constant('accountInitialValues')
    #define the initial values of the accounts
    accountInitialValues.setup_named_vector({'bank': 1000.0, 'depot': 500.0})
    account['bank'].initial_value = accountInitialValues['bank']
    account['depot'].initial_value = accountInitialValues['depot']
    interestRate = model.constant('interestRate')
    interestRate.setup_named_vector({'bank': 0.02, 'depot': 0.1})
    depositRate = model.constant('depositRate')
    #define the interest rates
    depositRate.setup_named_vector({'bank': 200.0, 'depot': 100.0})
    deposit = model.flow('deposit')
    deposit.equation = depositRate * 1
    #define the deposit rates
    interest = model.flow('interest')
    interest.equation = account * interestRate
    account.equation = deposit + interest
    #define the flows
    totalValue = model.converter('totalValue')
    #set the equation for the stock value
    #finally define a converter for the total value of the account
    totalValue.equation = account.arr_sum()
    return

@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    As always we define a scenario manager and scenarios:
    """)
    return

@app.cell
def _(bptk, model):
    arrays_bptk = bptk()
    arrays_bptk.register_model(model)
    scenario_manager = {'sm': {
        'model': model,
        'base_constants': {
            'interestRate[bank]': 0.02,
            'interestRate[depot]': 0.1,
            'depositRate[bank]': 200,
            'depositRate[depot]': 100,
            'accountInitialValues[bank]': 1000.0,
            'accountInitialValues[depot]': 500.0,
        },
    }}
    arrays_bptk.register_scenario_manager(scenario_manager)
    arrays_bptk.register_scenarios(
        scenario_manager='sm',
        scenarios={
            'base': {},
            'scenarioHighDepotInterestRate': {'constants': {'interestRate[depot]': 0.2}},
            'scenarioHighDepotDepositRate': {'constants': {'depositRate[depot]': 250.0}},
            'scenarioHighDepotInitialValue': {'constants': {'accountInitialValues[depot]': 750.0}},
        },
    )
    return (arrays_bptk,)

@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    And plot the results. Each cell is asked for by its own name, `account[bank]`: the array itself, `account`, has no values beside its cells, and asking for it logs an error that names them.
    """)
    return

@app.cell
def _(arrays_bptk):
    arrays_bptk.plot_scenarios(
        scenarios=['base'],
        scenario_managers='sm',
        equations=['account[bank]', 'account[depot]', 'totalValue'],
        series_names={},
        format="axes",
    )
    return

@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    As always we can compare different scenarios with each other by plotting them simultaneously:
    """)
    return

@app.cell
def _(arrays_bptk):
    arrays_bptk.plot_scenarios(
        scenarios=[
            'base',
            'scenarioHighDepotInterestRate',
            'scenarioHighDepotDepositRate',
            'scenarioHighDepotInitialValue',
        ],
        scenario_managers='sm',
        equations=['totalValue'],
        series_names={},
        format="axes",
    )
    return

if __name__ == "__main__":
    app.run()
