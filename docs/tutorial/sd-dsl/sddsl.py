# Front matter the .py format cannot carry; injected on export.
# keywords: system dynamics, systemdynamics, sd dsl, bptk, bptk-py, python, business simulation
# description: Introduction to building models using the domain specific language for System Dynamics (SD DSL) that is part of the BPTK-Py business simulation framework.
import marimo

__generated_with = "0.23.13"
app = marimo.App(app_title="System Dynamics")


@app.cell
def _():
    import marimo as mo

    return (mo,)




@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # System Dynamics

    This section explains how to use BPTK for System Dynamics modeling, both in pure Python using the domain specific language for System Dynamics (SD DSL) and also using XMILE.

    ## Contents

    - [A Simple Python Library For System Dynamics](./simple_python_library_sd_dsl/simple_python_library_sd_dsl.md)
    - [SD DSL Functions](./sd_dsl_functions/sd_dsl_functions.md)
    - [Creating User-defined Functions in SD Models](./sd_user_defined_functions/sd_user_defined_functions.md)
    - [SD DSL: Under The Hood](./sd_dsl_under_the_hood/sd_dsl_under_the_hood.md)
    - [Multidimensional SD DSL](./sd_dsl_multidimensional/sd_dsl_multidimensional.md)
    - [The Mathematics Underlying the SD DSL](./sd_dsl_mathematics/sd_dsl_mathematics.md)
    - [Working with XMILE](../xmile/xmile.md)
    """)
    return


if __name__ == "__main__":
    app.run()
