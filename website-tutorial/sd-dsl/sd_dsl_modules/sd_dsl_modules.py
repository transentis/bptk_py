# Front matter the .py format cannot carry; injected on export.
# description: Structuring an SD DSL model into modules - named parts of a model whose elements carry the module's name, and how modules that read each other are set up
# keywords: system dynamics, systemdynamics, sd dsl, module, namespace, fully qualified name, bptk, bptk-py, python, business simulation
import marimo

__generated_with = "0.23.13"
app = marimo.App(app_title="Modules")


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Modules

    A model of a supply chain has an inventory at the shop and one at the factory; a model of
    a firm has a headcount in every department. Written as one flat model, every element needs
    a name of its own, and the names soon read like `shopInventory`, `factoryInventory`,
    `salesHeadcount`.

    A **module** is a named part of a model. Every element created through it carries the
    module's name in front of its own - `shop.inventory`, `factory.inventory` - and the module
    is a Python class, so the same structure can be built several times. The [Beer
    Game](../../model_library/beergame/beergame_sd_dsl.md) builds its four players from one
    module class this way.

    ## Elements in a Module

    A `Module` takes the model and a name. Its `stock`, `flow`, `biflow`, `conveyor`,
    `converter` and `constant` create the element in the model, under the module's name:
    """)
    return


@app.cell
def _():
    from BPTK_Py import Model, Module
    from BPTK_Py import sd_functions as sd

    sketch = Model(starttime=0, stoptime=10, dt=1, name="sketch")
    shop_part = Module(sketch, "shop")
    shop_part.stock("inventory")
    list(sketch.stocks)
    return Model, Module, sd


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    The model knows the stock as `shop.inventory`, and that is the name to use everywhere
    outside the module: in `plot_scenarios`, in `run_scenarios` and in a scenario's
    constants. Asking the module for `inventory` again returns the same stock.

    A module can sit inside another one, given as `parent`; the names then nest:
    """)
    return


@app.cell
def _(Model, Module):
    _model = Model(starttime=0, stoptime=10, dt=1, name="nested")
    _supply_chain = Module(_model, "supply_chain")
    _retailer = Module(_model, "retailer", parent=_supply_chain)
    _retailer.fqn("inventory")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    `fqn` gives the fully qualified name of an element, the name the model knows it by.

    ## Modules That Read Each Other

    Modules are rarely independent: the shop's inventory fills with what the factory ships.
    A module class therefore splits its work in two:

    - **`__init__` creates the elements other modules read** - the module's exports. It calls
      `super().__init__` first.
    - **`initialize` creates everything else and writes every equation.** It takes the
      modules it reads as arguments.

    The two steps keep the order simple: first every module is created, so every export
    exists; then each one is initialized, and may refer to any export, whichever module
    was created first.
    """)
    return


@app.cell
def _(Module, sd):
    class Factory(Module):
        def __init__(self, model, name):
            super().__init__(model, name)
            self.shipments = self.flow("shipments")

        def initialize(self):
            production_rate = self.constant("production_rate")
            production_rate.equation = 20.0
            self.shipments.equation = production_rate


    class Shop(Module):
        def __init__(self, model, name):
            super().__init__(model, name)
            self.inventory = self.stock("inventory")

        def initialize(self, factory):
            sales = self.flow("sales")
            demand = self.constant("demand")
            demand.equation = 15.0
            self.inventory.initial_value = 100.0
            self.inventory.inflows = [factory.shipments]
            self.inventory.outflows = [sales]
            sales.equation = sd.min(demand, self.inventory)
    return Factory, Shop


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Building the model is then two lines per module - create, then initialize:
    """)
    return


@app.cell
def _(Factory, Model, Shop):
    from BPTK_Py import bptk

    shop_model = Model(starttime=0, stoptime=20, dt=1, name="Shop")
    factory = Factory(shop_model, "factory")
    shop = Shop(shop_model, "shop")
    factory.initialize()
    shop.initialize(factory)

    shop_bptk = bptk()
    shop_bptk.register_model(shop_model)
    shop_bptk.register_scenarios(scenario_manager="smShop", scenarios={"interactive": {}})
    sorted(list(shop_model.stocks) + list(shop_model.flows) + list(shop_model.constants))
    return (shop_bptk,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    A scenario sets a module's constant by its full name, here `shop.demand`. The factory
    ships 20 units a day; move the demand above that and the shop's inventory drains:
    """)
    return


@app.cell
def _(mo):
    demand_slider = mo.ui.slider(start=0, stop=40, step=5, value=15, show_value=True, label="shop.demand")
    demand_slider
    return (demand_slider,)


@app.cell
def _(demand_slider, shop_bptk):
    shop_bptk.get_scenario("smShop", "interactive").constants["shop.demand"] = demand_slider.value
    shop_bptk.reset_scenario_cache(scenario_manager="smShop", scenario="interactive")
    shop_bptk.plot_scenarios(
        scenario_managers=["smShop"],
        scenarios=["interactive"],
        equations=["shop.inventory", "shop.sales"],
        series_names={
            "smShop_interactive_shop.inventory": "Inventory",
            "smShop_interactive_shop.sales": "Sales",
        },
        title="The shop",
        x_label="Day",
        format="axes",
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Things to Watch Out For

    - **A name is a name in the model.** Two modules called `shop` share their elements:
      the second one's `inventory` is the first one's stock.
    - **A module is a way of naming, not a separate model.** The model the modules write into
      is one model, and it runs on either engine like any other.
    - **An XMILE model with modules** becomes a model with the same names: the transpiler
      writes `cash.cash` for the stock `cash` of the module `cash`, as [The Same Model in
      Stella](../../model_library/make_your_psf_grow/xmile/make_your_psf_grow_intro.md) shows.

    Every method of the class is on the [Module](../../api/api_module.md) API page.
    """)
    return


if __name__ == "__main__":
    app.run()
