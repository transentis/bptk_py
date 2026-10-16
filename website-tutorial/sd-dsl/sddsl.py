# Front matter the .py format cannot carry; injected on export.
# keywords: system dynamics, systemdynamics, sd dsl, bptk, bptk-py, python, business simulation
# description: Introduction to building models using the domain specific language for System Dynamics (SD DSL) that is part of the BPTK-Py business simulation framework.
#
# A section overview: prose and nothing else - not one chart, and no cell that offers
# a decision to take. Left reactive it booted Pyodide, some 8 MB, to display text, and
# it is the page a reader arrives on first.
# interactive: false
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
        - [Deterministic Functions](./sd_dsl_functions/sd_dsl_functions_deterministic.md)
        - [Random Functions](./sd_dsl_functions/sd_dsl_functions_random.md)
    - [Non-Negative Stocks, Biflows and Conveyors](./sd_dsl_stocks_and_flows/sd_dsl_stocks_and_flows.md)
    - [Creating User-defined Functions in SD Models](./sd_user_defined_functions/sd_user_defined_functions.md)
    - [SD DSL: Under The Hood](./sd_dsl_under_the_hood/sd_dsl_under_the_hood.md)
    - [Multidimensional SD DSL](./sd_dsl_multidimensional/sd_dsl_multidimensional.md)
        - [Defining Arrayed Components](./sd_dsl_multidimensional/sd_dsl_arrays_defining.md)
        - [Operations on Arrayed Components](./sd_dsl_multidimensional/sd_dsl_arrays_operations.md)
        - [Array Functions](./sd_dsl_multidimensional/sd_dsl_arrays_functions.md)
        - [A Simple Arrayed Model](./sd_dsl_multidimensional/sd_dsl_arrays_example.md)
    - [The Mathematics Underlying the SD DSL](./sd_dsl_mathematics/sd_dsl_mathematics.md)
    - [Working with XMILE](../xmile/xmile.md)
        - [XMILE Step by Step](../xmile/xmile_step_by_step/xmile_step_by_step.md)
        - [Working with Arrayed Variables in XMILE Models](../xmile/xmile_arrays/XMILE_arrays.md)
        - [Exporting Simulation Results](../xmile/exporting_simulation_results/exporting_simulation_results.md)
        - [Writing Computational Essays Based on Simulation Models](../xmile/writing_computational_essays/writing_computational_essays.md)
        - [Using the XMILE Compiler Standalone](../xmile/use_sd_compiler_standalone/use_sd_compiler_standalone.md)
        - [XMILE in the SD DSL](../xmile/xmile_in_the_sd_dsl/xmile_in_the_sd_dsl.md)
            - [Builtins Side by Side](../xmile/xmile_in_the_sd_dsl/builtins_side_by_side.md)
            - [Built from Other Functions](../xmile/xmile_in_the_sd_dsl/built_from_other_functions.md)
            - [Model Structure](../xmile/xmile_in_the_sd_dsl/model_structure.md)
    """)
    return


if __name__ == "__main__":
    app.run()
