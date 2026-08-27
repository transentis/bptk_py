# Front matter the .py format cannot carry; injected on export.
# keywords: agent-based modeling, abm, bptk, bptk-py, python, business simulation
# description: A small, but growing, collection of System Dynamics and Agent-based models built using the Business Prototyping Toolkit
import marimo

__generated_with = "0.23.13"
app = marimo.App(app_title="Model Library")


@app.cell
def _():
    import marimo as mo

    return (mo,)




@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Model Library

    A small, but growing, collection of System Dynamics and Agent-based models built using the _Business Prototyping Toolkit_.

    - [Bass Diffusion Model](./bass_diffusion/bass_diffusion.md). The classic [Bass Diffusion Model](https://en.wikipedia.org/wiki/Bass_diffusion_model) that is used to explain the dynamics of introductiong a new product or service into a market.
    - [Beer Distribution Game](./beergame/beergame.md). Computational notebooks, simulation models and AI training algorithms that explore the [beer distribution game](https://beergame.transentis.com) in depth.
    - [Competitive Pricing Dynamics](competitive_pricing/competitive_pricing_dynamics.md) A neat little model that can be used to understand pricing dynamics.
    - [Customer Acquisition](./customer_acquisition/customer_acquisition.md). A model that analyses the effects of referral marketing on customer acquisition.
    - [Enterprise Digital Twin](./enterprise_digital_twin/enterprise_digital_twin.md). A simulation of a professional service firm that forms part of the transentis Enterprise Digital Twin. This is work in progress; we report on it at our [events](https://academy.transentis.com/en/events)
    - [Make Your Professional Service Firm Grow](./make_your_psf_grow/make_your_psf_grow.md). A model that analyses growth strategies in professional service firms.
    - [System Archetypes](./system_archetypes/system_archetypes.md). Models and interactive dashboards that illustrate system archetypes. System archetypes are patterns of behavior of systems.
    """)
    return


if __name__ == "__main__":
    app.run()
