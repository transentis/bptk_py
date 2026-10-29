# Front matter the .py format cannot carry; injected on export.
# description: Training agents over many episodes with train_scenarios - the episode hooks, what survives from one episode to the next, and where learned knowledge has to be kept
# keywords: agent-based modeling, abm, training, episodes, reinforcement learning, q-learning, bptk, bptk-py, python
import marimo

__generated_with = "0.23.13"
app = marimo.App(app_title="Training Agents")


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Training Agents

    An agent that learns has to play the same game many times: try something, see what it
    earned, and do better the next time. Each of these games is an **episode**, and
    `bptk.train_scenarios` runs a scenario for as many episodes as you ask for. It works for
    agent-based and hybrid models.

    The library supplies the episodes. What an agent learns, and how, is up to you: this page
    builds the simplest learner there is, and [Training AI to Play the Beer
    Game](../../model_library/beergame/training_ai_beergame.md) applies Q-learning to a supply
    chain.

    ## The Episode Hooks

    In every episode, `train_scenarios` calls

    1. `begin_episode(episode_no)` on the model, which calls it on every agent,
    2. runs the scenario from its start to its stop time - with `begin_round` and `end_round`
       on the model in every round, and `act` on every agent,
    3. `end_episode(episode_no)` on the model, which calls it on every agent.

    `begin_episode` is the place to choose what to try, `end_episode` the place to learn from
    the result, and `end_round` the place for a reward that comes during the game.

    ## Two Things to Know Before You Start

    **Nothing is reset between episodes.** The model and its agents are the same from one
    episode to the next, and so are their properties: a profit that is added up in `act`
    goes on adding up across episodes. What has to start afresh, `begin_episode` sets back
    itself.

    **Learned knowledge must not live on the model instance.** The scenario manager builds
    the model again when training starts, and the scenario you run afterwards is a model of
    its own: an attribute set on the instance during training is no longer there. Keep what
    the agents learn somewhere that survives - as an attribute of the class, as the beer game
    keeps its q-tables, or in a module of its own.

    ## A Seller Learns Its Price

    A seller can charge 4, 6, 8 or 10 per unit. Demand falls with the price, each unit costs
    2, and the seller does not know which price earns most. In every episode it picks a
    price - usually the best one so far, sometimes one at random - plays five rounds and
    remembers what that price earned on average:
    """)
    return


@app.cell
def _():
    import random

    from BPTK_Py import Agent, DataCollector, Model, bptk

    PRICES = [4.0, 6.0, 8.0, 10.0]


    class Seller(Agent):
        def initialize(self):
            self.agent_type = "seller"
            self.state = "active"
            self.set_property("price", {"type": "Double", "value": 0.0})
            self.set_property("profit", {"type": "Double", "value": 0.0})

        def begin_episode(self, episode_no):
            self.profit = 0.0
            if self.model.random.random() < self.model.epsilon:
                self.price = self.model.random.choice(PRICES)
            else:
                self.price = max(PRICES, key=lambda price: Market.value[price])

        def act(self, time, round_no, step_no):
            demand = 100.0 - 8.0 * self.price
            self.profit += (self.price - 2.0) * demand

        def end_episode(self, episode_no):
            Market.tries[self.price] += 1
            Market.value[self.price] += (self.profit - Market.value[self.price]) / Market.tries[self.price]


    class Market(Model):
        # What the seller has learned, kept on the class, which outlives every instance
        value = {price: 0.0 for price in PRICES}
        tries = {price: 0 for price in PRICES}

        def instantiate_model(self):
            super().instantiate_model()
            self.register_agent_factory(
                "seller", lambda agent_id, model, properties: Seller(agent_id, model, properties))
            self.random = random.Random(1)
            self.epsilon = 0.2
    return DataCollector, Market, PRICES, bptk


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    The scenario is an ordinary agent-based one, with one seller:
    """)
    return


@app.cell
def _(DataCollector, Market, bptk):
    market_bptk = bptk()
    market_bptk.register_scenario_manager({
        "smMarket": {
            "type": "abm",
            "name": "market",
            "model": Market(1, 5, dt=1, name="market", data_collector=DataCollector()),
            "scenarios": {
                "train": {
                    "runspecs": {"starttime": 1, "stoptime": 5, "dt": 1.0},
                    "properties": {},
                    "agents": [{"name": "seller", "count": 1, "properties": {}}],
                }
            },
        }
    })
    return (market_bptk,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Training

    `train_scenarios` takes the scenario, the number of episodes and the agent properties to
    report - one row per episode, the value at the end of it. Choose how long the seller
    trains:
    """)
    return


@app.cell
def _(mo):
    episodes_slider = mo.ui.slider(start=5, stop=100, step=5, value=60, show_value=True, label="Episodes")
    episodes_slider
    return (episodes_slider,)


@app.cell
def _(Market, PRICES, episodes_slider, market_bptk):
    import BPTK_Py
    from BPTK_Py.visualizations import bptk_style

    for _price in PRICES:
        Market.value[_price] = 0.0
        Market.tries[_price] = 0

    training = market_bptk.train_scenarios(
        scenario_managers=["smMarket"],
        scenarios=["train"],
        episodes=episodes_slider.value,
        agents=["seller"],
        agent_states=["active"],
        agent_properties=["price", "profit"],
        agent_property_types=["total"],
        return_df=True,
    )
    with bptk_style():
        prices = training["seller_active_price_total"].plot(
            title="The price the seller charged in each episode", xlabel="Episode", ylabel="Price",
            drawstyle="steps-post", color=BPTK_Py.plotting_config.settings["colors"][0])
    prices.figure
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    For the first episodes the seller sticks to 4, the first price it tried; once a random
    choice has found 8, it keeps to that, apart from the odd excursion. What it has learned is
    on the class - the average profit of each price, and how often it was tried:
    """)
    return


@app.cell
def _(Market, episodes_slider):
    _ = episodes_slider.value
    {price: (round(Market.value[price]), Market.tries[price]) for price in Market.value}
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Keeping What Was Learned

    Training can take hours, so what the agents learned is worth keeping. That is ordinary
    Python - `json` or `pickle` on the learned structure. The beer game writes its q-tables
    with `dump_q_tables` and reads them back with `load_q_tables`, so that its pages can use
    agents trained for 50,000 episodes.

    `progress_bar=True` shows how far the training has got; in the browser there are no
    progress bars - see [Limitations](../../usage/limitations.md#running-the-documentation-in-a-browser).
    Every parameter of the method is on [bptk.train_scenarios](../../api/api_bptk.md#bptk.train_scenarios).
    """)
    return


if __name__ == "__main__":
    app.run()
