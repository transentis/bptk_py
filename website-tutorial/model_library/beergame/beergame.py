# Front matter the .py format cannot carry; injected on export.
# keywords: agent-based modeling, system dynamics,abm, bptk, bptk-py, python, business simulation, reinforcement learning, q-learning
# description: Computational notebooks, System Dynamics Models, Agent-based Models and a Reinforcement Learning Algorithm
import marimo

__generated_with = "0.23.13"
app = marimo.App(app_title="The Beer Distribution Game")


@app.cell
def _():
    import marimo as mo

    return (mo,)




@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # The Beer Distribution Game
    **Computational notebooks, System Dynamics Models, Agent-based Models and a Reinforcement Learning Algorithm**

    The Beer Game was developed by Jay Forrester's group at MIT in the early years of System Dynamics, to illustrate how difficult it is to manage dynamic systems – in this case a supply chain that delivers beer from a brewery to the end consumer.

    Have a go at playing the Beer Game (on your own or – much more fun – in a group) before you read these pages: you can play it online at [beergame.transentis.com](https://beergame.transentis.com/). The companion blog posts are on the [transentis blog](https://www.transentis.com/blog).

    ## Contents

    * [Understanding the Beer Game](understanding_the_beergame.md). The best place to get started: the rules of the game, the dynamics governing it and how to improve on a typical game. It uses the SD DSL version of the model.
    * [Simulating the Beer Game](beergame_sd_dsl.md). The stock and flow model behind the game and its implementation in the SD DSL.
    * [The Beer Game in Stella](understanding_the_beergame_xmile.md). The same model built in Stella Architect, loaded from its XMILE file and run on both engines.
    * [An Agent-based Approach To Modeling the Beer Game](beergame_abm.md). An agent-based simulation of the Beer Game that can be used to test policies.
    * [Training AI to play the Beer Game – A Reinforcement Learning Approach](training_ai_beergame.md). Reinforcement learning, applied to training agents to play the Beer Game - from the training to the stored q-tables of 50,000 episodes.
    """)
    return


if __name__ == "__main__":
    app.run()
