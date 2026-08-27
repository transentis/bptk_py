# Front matter the .py format cannot carry; injected on export.
# keywords: system dynamics, causal loops, bptk, bptk-py, python, business simulation
# description: Simulation models and interactive dashboards of system archetypes
import marimo

__generated_with = "0.23.13"
app = marimo.App(app_title="System Archetypes")


@app.cell
def _():
    import marimo as mo

    return (mo,)




@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # System Archetypes

    System archetypes are basic patterns of behaviour of a system. They arise in different guises in socio-economic systems such as enterprises and their ecosystems. Being able to identify these patterns is often a first step in finding leverage points for systemic improvements.

    The model library provides System Dynamics models and dashboards that will provide you with a deeper understanding of the archetypes and of how to model them.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    * [Balancing Feedback](./balancing_feedback/balancing_feedback.md). Balancing, goal seeking feedback loops seek to close the gap between the current state of a system and its desired state (the goal state).
    * [Limits to Growth](./limits_to_growth/limits_to_growth.md). No system property can grow indefinitely without being destroyed, so any reinforcing feedback loop must be kept in check by balancing loops. The limits to growth pattern is thus the combination of a reinforcing loop with a balancing loop.
    """)
    return


if __name__ == "__main__":
    app.run()
