# Front matter the .py format cannot carry; injected on export.
# keywords: agent-based modeling, system dynamics,abm, bptk, bptk-py, python, business simulation, reinforcement learning, q-learning
# description: Computational notebooks, System Dynamics Models, Agent-based Models and A Reinforcement Learning Algorithm
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

    The Beer Game was developed in the 1960s at MIT to illustrate how difficult it is to manage dynamic systems – in this case a supply chain that delivers beer from a brewery to the end consumer.

    This repository contains computational notebooks, simulation models and AI training algorithms that explore the game in depth.

    Please read the companion blog posts on the [transentis blog](https://www.transentis.com/blog).

    Have a go at playing the Beer Game (on your own or – much more fun – in a group) before you read the notebooks:

    You can play the online alone or in a group on our [beergame website](https://beergame.transentis.com/).

    ## Contents

    ### Notebooks

    The model library contains a number of pages. The key ones are:

    * [Understanding the Beer Game](understanding_the_beergame.md). This is the best place to get started - play the Beer Game in single player mode and learn about the dynamics governing the game. This version uses a SD DSL implementation of the Beer Game.
    * [Simulating the Beer Game](beergame_sd_dsl.md) This notebook introduces a stock and flow model for the Beer Game and discusses an implementation of that model using the SD DSL.
    * [An Agent-based Approach To Modeling the Beer Game](beergame_abm.md). An agent-based simulation of the Beer Game that can be used to test policies. It is also used as the basis for the reinforcement learning apporach described in the notebook [Training AI to play the Beer Game](training_ai_beergame.md)
    * [Training AI to play the Beer Game – A Reinforcement Learning Approach](training_ai_beergame.md). This notebook introduces the concept of reinforcement learning and then applies it to training intelligent agents to play the Beer Game.
    * [Understanding the Beer Game (XMILE)](understanding_the_beergame_xmile.md). The same introduction, but driven by the Stella Architect version of the model rather than the SD DSL one.
    * [Beer Distribution Game Reinforcement Learning](beergame_ql.md). Play against the agents that were trained in the notebook above, using a stored Q-table.

    ### Models

    This repository contains three simulation models of the Beer Game:

    * One version of the Beer Game model built in Python using the SD DSL provided by BPTK. This version is used in the [Understanding the Beer Game](understanding_the_beergame.md) notebook and is discussed in detail in the [Simulating the Beer Game](beergame_sd_dsl.md) notebook. The code for this version can be found in the _src/sd_dsl_ directory.
    * One version of the Beer Game model built using Stella Architect and then utilizing the XMILE transpiler that is part of BPTK. The Stella model can be found in the _simulation_models_ directory. This version of the simulation is used in the [Understanding the Beer Game (XMILE)](understanding_the_beergame_xmile.md) notebook.
    * One built using the Agent-based modeling framework that is part of BPTK-Py. The ABM version can be found in the  _src/abm_ directory.  This version is is used in the [An Agent-based Approach To Modeling the Beer Game](beergame_abm.md) and [Training AI to Play The Beer Game](training_ai_beergame.md) notebooks.
    """)
    return


if __name__ == "__main__":
    app.run()
