import marimo

__generated_with = "0.23.13"
app = marimo.App()


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Q-Table Tests
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Q Table
    """)
    return


@app.cell
def _():
    from src.q_learning_base.qtable import qTable
    qtable=qTable((10,10,10),-10)
    qtable.add_value((1,2),3,4)
    return qTable, qtable


@app.cell
def _(qtable):
    qtable.read_value((1,2),3)
    return


@app.cell
def _(qtable):
    qtable.max_action_value((1,2))
    return


@app.cell
def _(qtable):
    qtable.best_action((1,2))
    return


@app.cell
def _(qtable):
    qtable.add_value((1,2),5,7)
    return


@app.cell
def _(qtable):
    qtable.max_action_value((1,2))
    return


@app.cell
def _(qtable):
    qtable.best_action((1,2))
    return


@app.cell
def _(qtable):
    qtable.max_action_value((5,5))
    return


@app.cell
def _(qtable):
    qtable.best_action((5,5))
    return


@app.cell
def _(qtable):
    qtable.add_value((3,4),5,-3)
    return


@app.cell
def _(qtable):
    qtable.best_action((3,4))
    return


@app.cell
def _(qtable):
    qtable.max_action_value((3,4))
    return


@app.cell
def _(qtable):
    qtable.add_value((1,1),1,-12)
    return


@app.cell
def _(qtable):
    qtable.max_action_value((1,1))
    return


@app.cell
def _(qtable):
    qtable.best_action((1,1))
    return


@app.cell
def _(qtable):
    qtable.read_value((100,10),10)
    return


@app.cell
def _(qtable):
    qtable._within_bounds((100,10))
    return


@app.cell
def _(qtable):
    qtable._within_bounds((103,10))
    return


@app.cell
def _(qtable):
    qtable._within_bounds((5,3))
    return


@app.cell
def _(qTable):
    anotherQTable=qTable((100,100),0)
    anotherQTable.read_value((103,),0)
    return (anotherQTable,)


@app.cell
def _(anotherQTable):
    anotherQTable._within_bounds((103,0))
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Sparse QTable
    """)
    return


@app.cell
def _():
    from src.q_learning_base.sparseQTable import SparseQTable
    qtable_1 = SparseQTable(2, -10)
    qtable_1.add_value((1, 2), 3, 4)
    return (qtable_1,)


@app.cell
def _(qtable_1):
    qtable_1.read_value((1, 2), 3)
    return


@app.cell
def _(qtable_1):
    qtable_1.max_action_value((1, 2))
    return


@app.cell
def _(qtable_1):
    qtable_1.best_action((1, 2))
    return


@app.cell
def _(qtable_1):
    qtable_1.add_value((1, 2), 5, 7)
    return


@app.cell
def _(qtable_1):
    qtable_1.max_action_value((1, 2))
    return


@app.cell
def _(qtable_1):
    qtable_1.best_action((1, 2))
    return


@app.cell
def _(qtable_1):
    qtable_1.max_action_value((5, 5))
    return


@app.cell
def _(qtable_1):
    qtable_1.best_action((5, 5))
    return


@app.cell
def _(qtable_1):
    qtable_1.add_value((3, 4), 5, -3)
    return


@app.cell
def _(qtable_1):
    qtable_1.best_action((3, 4))
    return


@app.cell
def _(qtable_1):
    qtable_1.max_action_value((3, 4))
    return


@app.cell
def _(qtable_1):
    qtable_1.add_value((1, 1), 1, -12)
    return


@app.cell
def _(qtable_1):
    qtable_1.max_action_value((1, 1))
    return


@app.cell
def _(qtable_1):
    qtable_1.best_action((1, 1))
    return


@app.cell
def _(qtable_1):
    qtable_1.read_value((100, 10), 10)
    return


if __name__ == "__main__":
    app.run()
