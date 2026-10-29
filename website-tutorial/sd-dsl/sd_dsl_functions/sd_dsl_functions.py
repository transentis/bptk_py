# Front matter the .py format cannot carry; injected on export.
# description: Overview of the SD DSL functions that are part of the BPTK-Py business simulation framework.
# keywords: system dynamics, systemdynamics, sd dsl, bptk, bptk-py, python, business simulation
#
# A section overview: prose and nothing else, so it is not run in the browser.
# interactive: false
import marimo

__generated_with = "0.23.13"
app = marimo.App(app_title="SD DSL Functions")


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # SD DSL Functions

    The SD DSL comes with the builtins of XMILE and Stella as Python functions in `sd_functions`. Import them beside the `Model` class:

    ```python
    from BPTK_Py import Model
    from BPTK_Py import sd_functions as sd
    ```

    The functions are on two pages, each sorted from A to Z:

    - [Deterministic Functions](./sd_dsl_functions_deterministic.md) - everything that gives the same result on every run: time, delays and smoothing, finance, lookups, rounding and mathematics
    - [Random Functions](./sd_dsl_functions_random.md) - drawing numbers from statistical distributions

    The statistical functions - the random distributions, INVNORM and NORMALCDF - check their arguments, and so do SQRT, LN, LOG10, ARCSIN, ARCCOS, FACTORIAL, COMBINATIONS, PERMUTATIONS and DELAY. An argument a function does not accept, such as a negative ``stddev``, gives NaN, and one ``[ERROR]`` names the element, the time and the values; it is printed as well as written to the log file, once per element and run. A NaN or an infinity that arrives as an argument gives NaN without a message: it comes from further up the model.

    Three operations divide by zero: `a / 0`, `a % 0` and `0 ** -n`, which is 1 / 0ⁿ. All yield NaN plus one ``[ERROR]`` in the log per element, naming the time it first happens. The run goes on.
    """)
    return


if __name__ == "__main__":
    app.run()
