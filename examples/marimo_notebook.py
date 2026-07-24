import marimo

__generated_with = "0.23.13"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell
def _(mo):
    mo.md(r"""
    # 🦠 SIR-Epidemiemodell — ausgeführt mit dem Rust-Engine

    Dieses [marimo](https://marimo.io)-Notebook baut ein klassisches
    **SIR-Modell** (Susceptible → Infected → Recovered) mit dem BPTK-Py
    System-Dynamics-DSL und führt es über den **Rust-Backend** aus.

    Alle Diagramme werden über die BPTK-Funktion `plot_scenarios(...)`
    erzeugt (`backend="rust"`, `format="axes"`).

    Es zeigt drei Dinge:

    1. **Einzelszenario** — Parameter per Regler ändern, das Notebook rechnet
       reaktiv neu.
    2. **Szenario-Vergleich** — mehrere Infektionsraten als eigene BPTK-Szenarien
       überlagern.
    3. **Progressives Aufdecken** — die fertige Kurve Schritt für Schritt sichtbar
       machen (`visualize_to_period`).
    """)
    return


@app.cell
def _():
    import BPTK_Py
    from BPTK_Py import Model
    import matplotlib.pyplot as plt

    return BPTK_Py, Model, plt


@app.cell
def _(Model):
    def build_sir_model(beta, gamma, i0, population, stoptime=120, dt=0.25):
        """Baut ein SIR-Modell im BPTK-Py SD-DSL.

        infection = beta * S * I / N        (Neuansteckungen)
        recovery  = gamma * I               (Genesungen)
        """
        model = Model(starttime=0, stoptime=stoptime, dt=dt, name="sir")

        S = model.stock("susceptible")
        I = model.stock("infected")
        R = model.stock("recovered")

        infection = model.flow("infection")
        recovery = model.flow("recovery")

        b = model.constant("beta")
        g = model.constant("gamma")
        N = model.constant("N")
        b.equation = beta
        g.equation = gamma
        N.equation = population

        S.initial_value = float(population - i0)
        I.initial_value = float(i0)
        R.initial_value = 0.0

        infection.equation = b * S * I / N
        recovery.equation = g * I

        S.equation = -infection
        I.equation = infection - recovery
        R.equation = recovery

        return model

    return (build_sir_model,)


@app.cell
def _(BPTK_Py):
    def make_bptk(model, scenarios):
        """Registriert ein Modell + Szenarien und liefert die bptk-Instanz.

        ``scenarios`` ist ein Dict wie es ``register_scenarios`` erwartet, z.B.
        ``{"base": {}}`` oder ``{"β=0.4": {"constants": {"beta": 0.4}}}``.
        """
        bptk = BPTK_Py.bptk()
        bptk.register_scenario_manager({"sir_mgr": {"model": model}})
        bptk.register_scenarios(scenario_manager="sir_mgr", scenarios=scenarios)
        return bptk

    return (make_bptk,)


@app.cell
def _(mo):
    mo.md(r"""
    ## 1 · Einzelszenario
    """)
    return


@app.cell
def _(mo):
    # --- Interaktive Parameter -------------------------------------------------
    beta = mo.ui.slider(
        start=0.05, stop=1.0, step=0.05, value=0.4, label="β  Infektionsrate"
    )
    gamma = mo.ui.slider(
        start=0.02, stop=0.5, step=0.02, value=0.1, label="γ  Genesungsrate"
    )
    i0 = mo.ui.slider(start=1, stop=100, step=1, value=10, label="I₀  Startinfizierte")
    population = mo.ui.slider(
        start=100, stop=10000, step=100, value=1000, label="N  Bevölkerung"
    )

    mo.vstack([mo.md("### Parameter"), beta, gamma, i0, population])
    return beta, gamma, i0, population


@app.cell
def _(beta, build_sir_model, gamma, i0, make_bptk, population):
    # --- plot_scenarios über den Rust-Backend ----------------------------------
    _model = build_sir_model(
        beta=beta.value, gamma=gamma.value, i0=i0.value, population=population.value
    )
    _bptk = make_bptk(_model, {"base": {}})

    _bptk.plot_scenarios(
        scenario_managers="sir_mgr",
        scenarios=["base"],
        equations=["susceptible", "infected", "recovered"],
        backend="rust",
        format="axes",
        title="SIR-Verlauf (Rust-Engine)",
        x_label="Zeit (Tage)",
        y_label="Personen"
    )
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## 2 · Szenario-Vergleich

    Jede gewählte Infektionsrate β wird als **eigenes BPTK-Szenario**
    (`constants`-Override) registriert. `plot_scenarios` legt die
    Infizierten-Kurven aller Szenarien in einem Diagramm übereinander.
    (γ, I₀ und N bleiben fest: 0.1 / 10 / 1000.)
    """)
    return


@app.cell
def _(mo):
    beta_choices = mo.ui.multiselect(
        options=[0.15, 0.25, 0.40, 0.60, 0.90],
        value=[0.25, 0.40, 0.60],
        label="β-Werte zum Vergleich",
    )
    beta_choices
    return (beta_choices,)


@app.cell
def _(beta_choices, build_sir_model, make_bptk, mo):
    # --- Ein Szenario je gewähltem β, gemeinsam über plot_scenarios ------------
    mo.stop(
        len(beta_choices.value) == 0,
        mo.md("👆 Bitte mindestens einen β-Wert auswählen."),
    )

    _model = build_sir_model(beta=0.4, gamma=0.1, i0=10, population=1000)
    _scenarios = {
        f"β={_b:.2f}": {"constants": {"beta": _b}}
        for _b in sorted(beta_choices.value)
    }
    _bptk = make_bptk(_model, _scenarios)

    _bptk.plot_scenarios(
        scenario_managers="sir_mgr",
        scenarios=list(_scenarios.keys()),
        equations=["infected"],
        backend="rust",
        format="axes",
        title="Infektionsverlauf je Infektionsrate β (Rust-Engine)",
        x_label="Zeit (Tage)",
        y_label="Infizierte"
    )
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## 3 · Step-by-Step

    Hier treiben wir die Simulation **schrittweise** über `begin_session` +
    `run_step` voran. Der Rust-Backend hält dabei einen zustandsbehafteten
    Cursor, der pro Klick genau einen Zeitschritt weiterrückt.

    > Anders als in den Abschnitten oben wird hier **nicht** `plot_scenarios`
    > genutzt: das rechnet stets die volle Simulation und passt nicht zum
    > echten schrittweisen Vorrücken des Cursors.
    """)
    return


@app.cell
def _(mo):
    # Schritt-Zähler als reaktiver State (überlebt Button-Klicks).
    get_step, set_step = mo.state(0)
    return get_step, set_step


@app.cell
def _(mo, set_step):
    step_btn = mo.ui.button(
        label="▶ Nächster Schritt", on_click=lambda _: set_step(lambda v: v + 1)
    )
    step5_btn = mo.ui.button(
        label="⏭ 5 Schritte", on_click=lambda _: set_step(lambda v: v + 5)
    )
    reset_btn = mo.ui.button(label="⟲ Reset", on_click=lambda _: set_step(lambda _v: 0))

    mo.hstack([step_btn, step5_btn, reset_btn], justify="start")
    return


@app.cell
def _(build_sir_model, get_step, make_bptk, mo, plt):
    # --- Session bis zum aktuellen Schritt vorspulen und Verlauf zeichnen ------
    STOP = 120
    _n = min(get_step(), STOP)

    _model = build_sir_model(beta=0.4, gamma=0.1, i0=10, population=1000, stoptime=STOP)
    _bptk = make_bptk(_model, {"base": {}})
    _bptk.begin_session(
        scenario_managers=["sir_mgr"],
        scenarios=["base"],
        equations=["infected", "recovered"],
        backend="rust",
    )

    _inf, _rec = {}, {}
    for _ in range(_n + 1):  # +1: erster run_step liefert den Startzustand (t=0)
        _res = _bptk.run_step()
        if _res is None or "msg" in _res:
            break
        _step = _res["sir_mgr"]["base"]
        for _t, _v in _step["infected"].items():
            _inf[float(_t)] = _v
        for _t, _v in _step["recovered"].items():
            _rec[float(_t)] = _v

    _ts = sorted(_inf)
    _fig, _ax = plt.subplots(figsize=(9, 4.5))
    _ax.plot(_ts, [_inf[t] for t in _ts], "-o", label="Infected", color="#dc2626", lw=2, ms=4)
    _ax.plot(_ts, [_rec[t] for t in _ts], "-o", label="Recovered", color="#16a34a", lw=2, ms=4)
    _ax.set_xlim(0, STOP)
    _ax.set_xlabel("Zeit (Schritte)")
    _ax.set_ylabel("Personen")
    _ax.set_title(f"Step-by-Step über Rust — Schritt {_n} / {STOP}")
    _ax.legend(loc="center right")
    _ax.grid(True, alpha=0.2)
    _fig.tight_layout()

    mo.vstack([mo.md(f"**Aktueller Schritt: {_n} / {STOP}**"), _fig])
    return


if __name__ == "__main__":
    app.run()
