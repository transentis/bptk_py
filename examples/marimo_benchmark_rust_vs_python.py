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
    # ⚡ Rust vs. Python — SD-Backend-Benchmark

    Dieses [marimo](https://marimo.io)-Notebook baut ein nicht-triviales
    **SIR-Modell mit Impfung und Krankenhaus-Kapazität** (5 Stocks, 5 Flows,
    10 Konverter/Konstanten) und führt es über **beide** BPTK-Py-Backends aus —
    einmal in reinem Python, einmal über den **Rust-Engine**.

    Wähle die Problemgröße, klicke **Benchmark starten** und vergleiche
    Laufzeit, Speedup und numerische Übereinstimmung.

    > Interaktive Portierung von `examples/benchmark_rust_vs_python.py`.
    """)
    return


@app.cell
def _():
    import time
    import numpy as np
    import pandas as pd
    import matplotlib.pyplot as plt

    import BPTK_Py
    from BPTK_Py import Model
    from BPTK_Py.sddsl import functions as sd

    return BPTK_Py, Model, plt, sd, time


@app.cell
def _(Model, sd):
    def build_sir_model(stoptime=100, dt=0.25):
        """SIR-Modell mit Impfung und Krankenhaus-Kapazitäts-Feedback.

        5 Stocks, 5 Flows, 10 Konverter/Konstanten — komplex genug, um einen
        aussagekräftigen Performance-Unterschied zu zeigen.
        """
        model = Model(starttime=0, stoptime=stoptime, dt=dt, name="sir_benchmark")

        susceptible = model.stock("susceptible")
        infected = model.stock("infected")
        recovered = model.stock("recovered")
        vaccinated = model.stock("vaccinated")
        deceased = model.stock("deceased")

        infection = model.flow("infection")
        recovery = model.flow("recovery")
        vaccination = model.flow("vaccination")
        death = model.flow("death")
        waning_immunity = model.flow("waning_immunity")

        total_population = model.converter("total_population")
        contact_rate = model.constant("contact_rate")
        transmission_prob = model.constant("transmission_prob")
        recovery_time = model.constant("recovery_time")
        mortality_rate = model.constant("mortality_rate")
        vaccination_rate = model.constant("vaccination_rate")
        immunity_duration = model.constant("immunity_duration")
        hospital_capacity = model.constant("hospital_capacity")
        capacity_pressure = model.converter("capacity_pressure")
        effective_mortality = model.converter("effective_mortality")

        susceptible.initial_value = 9990.0
        infected.initial_value = 10.0
        recovered.initial_value = 0.0
        vaccinated.initial_value = 0.0
        deceased.initial_value = 0.0

        total_population.equation = susceptible + infected + recovered + vaccinated

        infection.equation = sd.max(
            0,
            contact_rate * transmission_prob * susceptible * infected / total_population,
        )
        recovery.equation = sd.max(0, infected / recovery_time)
        vaccination.equation = sd.If(
            sd.time() > 10,
            sd.min(susceptible * vaccination_rate, susceptible / model.dt),
            0,
        )
        capacity_pressure.equation = sd.max(1, infected / hospital_capacity)
        effective_mortality.equation = mortality_rate * capacity_pressure
        death.equation = sd.max(0, infected * effective_mortality)
        waning_immunity.equation = sd.max(0, recovered / immunity_duration)

        susceptible.equation = -infection - vaccination + waning_immunity
        infected.equation = infection - recovery - death
        recovered.equation = recovery - waning_immunity
        vaccinated.equation = vaccination
        deceased.equation = death

        contact_rate.equation = 8.0
        transmission_prob.equation = 0.03
        recovery_time.equation = 14.0
        mortality_rate.equation = 0.001
        vaccination_rate.equation = 0.01
        immunity_duration.equation = 180.0
        hospital_capacity.equation = 200.0

        return model

    ALL_EQUATIONS = [
        "susceptible", "infected", "recovered", "vaccinated", "deceased",
        "infection", "recovery", "vaccination", "death", "waning_immunity",
        "total_population", "capacity_pressure", "effective_mortality",
    ]
    return ALL_EQUATIONS, build_sir_model


@app.cell
def _(mo):
    size = mo.ui.dropdown(
        options={
            "Small — 400 Schritte (stoptime 100)": 100,
            "Medium — 4.000 Schritte (stoptime 1.000)": 1000,
            "Large — 40.000 Schritte (stoptime 10.000)": 10000,
        },
        value="Medium — 4.000 Schritte (stoptime 1.000)",
        label="Problemgröße",
    )
    runs = mo.ui.slider(start=1, stop=9, step=2, value=3, label="Läufe (Median)")
    run_button = mo.ui.run_button(label="⚡ Benchmark starten")

    mo.vstack([size, runs, run_button])
    return run_button, runs, size


@app.cell
def _(
    ALL_EQUATIONS,
    BPTK_Py,
    build_sir_model,
    mo,
    run_button,
    runs,
    size,
    time,
):
    # Teuer -> nur auf Knopfdruck laufen lassen (nicht bei jeder Regler-Änderung).
    mo.stop(
        not run_button.value,
        mo.md("👆 Größe & Läufe wählen, dann **Benchmark starten** klicken."),
    )

    _model = build_sir_model(stoptime=size.value, dt=0.25)
    _bptk = BPTK_Py.bptk()
    _bptk.register_scenario_manager({"bench": {"model": _model}})
    _bptk.register_scenarios(scenarios={"base": {}}, scenario_manager="bench")

    def _run(backend):
        for _, _mgr in _bptk.scenario_manager_factory.scenario_managers.items():
            if getattr(_mgr, "model", None) is not None:
                _mgr.model.reset_cache()
        _t0 = time.perf_counter()
        _df = _bptk.run_scenarios(
            scenario_managers=["bench"],
            scenarios=["base"],
            equations=ALL_EQUATIONS,
            backend=backend,
        )
        return time.perf_counter() - _t0, _df

    _py_times, _rust_times = [], []
    _py_df = _rust_df = None
    for _ in range(runs.value):
        _tp, _py_df = _run("python")
        _tr, _rust_df = _run("rust")
        _py_times.append(_tp)
        _rust_times.append(_tr)

    _py_times.sort()
    _rust_times.sort()
    py_time = _py_times[len(_py_times) // 2]
    rust_time = _rust_times[len(_rust_times) // 2]

    # Numerische Parität zwischen den Backends.
    _common = [c for c in _py_df.columns if c in _rust_df.columns]
    max_abs_diff = float((_py_df[_common] - _rust_df[_common]).abs().to_numpy().max())

    steps = int(size.value / 0.25)
    rust_df = _rust_df
    return max_abs_diff, py_time, rust_df, rust_time, steps


@app.cell
def _(max_abs_diff, mo, py_time, rust_time, steps):
    _speedup = py_time / rust_time if rust_time else float("nan")
    _parity = "✅ identisch" if max_abs_diff < 1e-9 else f"⚠ Δ={max_abs_diff:.2e}"

    mo.hstack(
        [
            mo.stat(value=f"{py_time * 1000:,.1f} ms", label="Python", caption=f"{steps:,} Schritte", bordered=True),
            mo.stat(value=f"{rust_time * 1000:,.1f} ms", label="Rust", caption=f"{steps:,} Schritte", bordered=True),
            mo.stat(value=f"{_speedup:.1f}×", label="Speedup", caption="Python / Rust", bordered=True),
            mo.stat(value=_parity, label="Parität", caption=f"max |Δ| = {max_abs_diff:.1e}", bordered=True),
        ],
        justify="start",
        gap=1,
    )
    return


@app.cell
def _(plt, py_time, rust_time):
    _fig, _ax = plt.subplots(figsize=(7, 3.2))
    _bars = _ax.barh(
        ["Python", "Rust"],
        [py_time * 1000, rust_time * 1000],
        color=["#94a3b8", "#dc2626"],
    )
    _ax.bar_label(_bars, fmt="%.1f ms", padding=4)
    _ax.set_xlabel("Laufzeit (ms)")
    _ax.set_title("End-to-End-Laufzeit: run_scenarios")
    _ax.margins(x=0.15)
    _ax.grid(True, axis="x", alpha=0.2)
    _fig.tight_layout()
    _fig
    return


@app.cell
def _(plt, rust_df):
    # Kontrolle: So sieht der Modellverlauf aus (Rust-Ergebnis).
    _fig, _ax = plt.subplots(figsize=(9, 4))
    for _col, _color in [
        ("susceptible", "#2563eb"),
        ("infected", "#dc2626"),
        ("recovered", "#16a34a"),
        ("vaccinated", "#7c3aed"),
        ("deceased", "#475569"),
    ]:
        _ax.plot(rust_df.index, rust_df[_col], label=_col, color=_color, lw=1.8)
    _ax.set_xlabel("Zeit")
    _ax.set_ylabel("Personen")
    _ax.set_title("Modellverlauf (Rust-Ergebnis)")
    _ax.legend(ncol=3, fontsize=8)
    _ax.grid(True, alpha=0.2)
    _fig.tight_layout()
    _fig
    return


if __name__ == "__main__":
    app.run()
