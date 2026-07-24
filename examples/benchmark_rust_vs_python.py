"""
Benchmark: Rust vs Python SD simulation backend.

Builds a non-trivial System Dynamics model (SIR epidemic with vaccination
and hospital capacity) and runs it using both backends, measuring wall-clock
time for each.

Usage:
    python examples/benchmark_rust_vs_python.py

Sample results (median of 5 runs for the full-simulate tables, 3 for
step-by-step and /execute):

    Overall comparison
    ------------------------------------------------------------------------
    Configuration                 Python   Rust total    Speedup
    ------------------------------------------------------------------------
    Small   (400 steps)          24.6 ms       2.5 ms      9.8x
    Medium  (4,000 steps)       232.1 ms      22.7 ms     10.2x
    Large   (40,000 steps)     2369.7 ms     245.2 ms      9.7x
    XLarge  (400,000 steps)   24519.9 ms    3685.2 ms      6.7x

    Rust phase breakdown
    ------------------------------------------------------------------------
    Configuration              Serialize      Parse   Simulate    Convert
    ------------------------------------------------------------------------
    Small   (400 steps)           0.1 ms     0.0 ms     1.2 ms     1.2 ms
    Medium  (4,000 steps)         0.1 ms     0.1 ms    11.5 ms    10.9 ms
    Large   (40,000 steps)        0.1 ms     0.1 ms   122.3 ms   122.4 ms
    XLarge  (400,000 steps)       0.1 ms     0.1 ms  1610.1 ms  2073.9 ms

    Simulation-only speedup (excluding serialization & conversion)
    ------------------------------------------------------------------------
    Configuration                 Python   Rust sim    Speedup
    ------------------------------------------------------------------------
    Small   (400 steps)          24.6 ms     1.2 ms     21.1x
    Medium  (4,000 steps)       232.1 ms    11.5 ms     20.1x
    Large   (40,000 steps)     2369.7 ms   122.3 ms     19.4x
    XLarge  (400,000 steps)   24519.9 ms  1610.1 ms     15.2x

    Numerical parity: all configurations PASS (max abs diff: 0.00e+00)

    Step-by-step Rust (init + step loop) vs full Rust simulate
    ------------------------------------------------------------------------
    Configuration               Rust full        Step  Step+const Step parity
    ------------------------------------------------------------------------
    Small   (400 steps)            2.5 ms      2.1 ms      2.0 ms        PASS
    Medium  (4,000 steps)         22.7 ms     18.6 ms     17.8 ms        PASS
    Large   (40,000 steps)       245.2 ms    196.8 ms    197.7 ms        PASS
    XLarge  (400,000 steps)     3685.2 ms   2798.9 ms   2796.8 ms        PASS

    POST /execute round-trip latency (Flask test client)
    ------------------------------------------------------------------------
    Configuration                Rust sim  Round-trip   HTTP+JSON
    ------------------------------------------------------------------------
    Small   (400 steps)            1.2 ms      4.6 ms      3.4 ms
    Medium  (4,000 steps)         11.5 ms     40.3 ms     28.8 ms
    Large   (40,000 steps)       122.3 ms    528.8 ms    406.5 ms
    XLarge  (400,000 steps)     1610.1 ms   6512.5 ms   4902.4 ms

    Key findings:
    - End-to-end full-simulate speedup: ~6.7-10.2x (incl. serialize & convert)
    - Pure simulation speedup: ~15-21x
    - Serialization and JSON parsing are negligible (~0.1 ms)
    - DataFrame conversion is ~half of Rust total time at scale
    - Results are bit-for-bit identical between backends (full and step-by-step)
    - Step-by-step is within (in fact slightly under) full-simulate time — the
      memo is pre-allocated at init(), so per-step cost is one PyO3 call + a small
      dict; the step path also skips the full-run's time-keyed convert. The design
      doc's "<20% over full simulate" target is met with margin.
    - A per-step set_constant (the server's per-round override case) adds no
      measurable overhead.
    - /execute round-trip is dominated by JSON (de)serialization of the response
      time series, which grows with row count — not Flask routing.
"""

import json
import time
import numpy as np
import pandas as pd
import BPTK_Py
from BPTK_Py import Model
from BPTK_Py.sddsl import functions as sd
from BPTK_Py._rust_engine import RustSdEngine


# ---------------------------------------------------------------------------
# Model builder
# ---------------------------------------------------------------------------

def build_sir_model(stoptime=100, dt=0.25):
    """Build an SIR model with vaccination and hospital capacity feedback.

    This model has 5 stocks, 5 flows, and 10 converters/constants —
    enough complexity to show a meaningful performance difference.
    """
    model = Model(starttime=0, stoptime=stoptime, dt=dt, name="sir_benchmark")

    # --- Stocks ---
    susceptible = model.stock("susceptible")
    infected = model.stock("infected")
    recovered = model.stock("recovered")
    vaccinated = model.stock("vaccinated")
    deceased = model.stock("deceased")

    # --- Flows ---
    infection = model.flow("infection")
    recovery = model.flow("recovery")
    vaccination = model.flow("vaccination")
    death = model.flow("death")
    waning_immunity = model.flow("waning_immunity")

    # --- Constants and converters ---
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

    # --- Initial values ---
    susceptible.initial_value = 9990.0
    infected.initial_value = 10.0
    recovered.initial_value = 0.0
    vaccinated.initial_value = 0.0
    deceased.initial_value = 0.0

    # --- Equations ---
    total_population.equation = susceptible + infected + recovered + vaccinated

    # Infection: standard SIR with density-dependent transmission
    infection.equation = sd.max(
        0,
        contact_rate * transmission_prob * susceptible * infected / total_population,
    )

    # Recovery
    recovery.equation = sd.max(0, infected / recovery_time)

    # Vaccination: vaccinate susceptible at a fixed rate (starts after t=10)
    vaccination.equation = sd.If(
        sd.time() > 10,
        sd.min(susceptible * vaccination_rate, susceptible / model.dt),
        0,
    )

    # Death: mortality increases when hospitals are overwhelmed
    capacity_pressure.equation = sd.max(1, infected / hospital_capacity)
    effective_mortality.equation = mortality_rate * capacity_pressure
    death.equation = sd.max(0, infected * effective_mortality)

    # Waning immunity: recovered lose immunity over time
    waning_immunity.equation = sd.max(0, recovered / immunity_duration)

    # --- Stock equations (net flows) ---
    susceptible.equation = -infection - vaccination + waning_immunity
    infected.equation = infection - recovery - death
    recovered.equation = recovery - waning_immunity
    vaccinated.equation = vaccination
    deceased.equation = death

    # --- Parameters ---
    contact_rate.equation = 8.0
    transmission_prob.equation = 0.03
    recovery_time.equation = 14.0
    mortality_rate.equation = 0.001
    vaccination_rate.equation = 0.01
    immunity_duration.equation = 180.0
    hospital_capacity.equation = 200.0

    return model


# ---------------------------------------------------------------------------
# Benchmark runner
# ---------------------------------------------------------------------------

ALL_EQUATIONS = [
    "susceptible", "infected", "recovered", "vaccinated", "deceased",
    "infection", "recovery", "vaccination", "death", "waning_immunity",
    "total_population", "capacity_pressure", "effective_mortality",
]


def benchmark(stoptime, dt, num_runs=5):
    """Run the model on both backends and return median times with phase breakdown."""
    model = build_sir_model(stoptime=stoptime, dt=dt)

    bptk = BPTK_Py.bptk()
    bptk.register_scenario_manager({"bench": {"model": model}})
    bptk.register_scenarios(scenarios={"base": {}}, scenario_manager="bench")

    python_times = []
    # Rust phase timings: (total, serialize, load, simulate, convert)
    rust_phase_times = []

    py_result = None
    rust_result = None

    for _ in range(num_runs):
        # --- Python ---
        for _, mgr in bptk.scenario_manager_factory.scenario_managers.items():
            if hasattr(mgr, "model") and mgr.model is not None:
                mgr.model.reset_cache()

        t0 = time.perf_counter()
        py_result = bptk.run_scenarios(
            scenario_managers=["bench"],
            scenarios=["base"],
            equations=ALL_EQUATIONS,
            backend="python",
        )
        python_times.append(time.perf_counter() - t0)

        # --- Rust (phase-by-phase) ---
        for _, mgr in bptk.scenario_manager_factory.scenario_managers.items():
            if hasattr(mgr, "model") and mgr.model is not None:
                mgr.model.reset_cache()

        # Phase 1: Serialize model to JSON
        t_total = time.perf_counter()
        t0 = time.perf_counter()
        json_str = model.to_json()
        t_serialize = time.perf_counter() - t0

        # Phase 2: Load/parse model in Rust engine
        t0 = time.perf_counter()
        engine = RustSdEngine()
        rust_model = engine.load_model(json_str)
        t_load = time.perf_counter() - t0

        # Phase 3: Pure simulation
        t0 = time.perf_counter()
        raw = rust_model.simulate(ALL_EQUATIONS)
        t_simulate = time.perf_counter() - t0

        # Phase 4: Convert results to DataFrame
        t0 = time.perf_counter()
        converted = {eq: {float(t): v for t, v in ts.items()} for eq, ts in raw.items()}
        df = pd.DataFrame(converted)
        df.index.name = "t"
        df = df.sort_index()
        t_convert = time.perf_counter() - t0

        rust_result = df
        t_total = time.perf_counter() - t_total
        rust_phase_times.append((t_total, t_serialize, t_load, t_simulate, t_convert))

    python_times.sort()
    # Sort by total time and pick median
    rust_phase_times.sort(key=lambda x: x[0])

    py_median = python_times[num_runs // 2]
    rust_median = rust_phase_times[num_runs // 2]  # (total, serialize, load, simulate, convert)

    return py_median, rust_median, py_result, rust_result


# ---------------------------------------------------------------------------
# Step-by-step benchmark
# ---------------------------------------------------------------------------

def benchmark_step(stoptime, dt, num_runs=3, with_overrides=False):
    """Step-by-step Rust execution: load + init() + a step() loop to stoptime.

    Mirrors how the BPTK server drives a stateful session (one step() per
    timestep). When `with_overrides` is True, a `set_constant` is issued before
    every step — the realistic server case, where each round injects per-step
    parameter changes — so the table can show the PyO3 call overhead it adds.

    Returns (median_total, median_loop, result_df):
      * median_total — serialize + load + init + step-loop + DataFrame convert,
        directly comparable to benchmark()'s "Rust total".
      * median_loop  — init + step-loop only, comparable to "Rust sim".
      * result_df    — the assembled trajectory, for numerical parity checks.
    """
    model = build_sir_model(stoptime=stoptime, dt=dt)

    totals = []
    loops = []
    result_df = None

    for _ in range(num_runs):
        t_total = time.perf_counter()
        json_str = model.to_json()
        engine = RustSdEngine()
        rust_model = engine.load_model(json_str)

        # init() evaluates step 0 and returns the values at t = starttime.
        t_loop = time.perf_counter()
        collected = {float(model.starttime): rust_model.init(ALL_EQUATIONS)}
        while rust_model.steps_remaining() > 0:
            if with_overrides:
                # Re-assert the baseline value: a no-op numerically, but it
                # exercises the same per-step set_constant path the server uses.
                rust_model.set_constant("transmission_prob", 0.03)
            values = rust_model.step()
            collected[rust_model.current_time()] = values
        loop_elapsed = time.perf_counter() - t_loop

        df = pd.DataFrame.from_dict(collected, orient="index")
        df.index.name = "t"
        df = df.sort_index()
        total_elapsed = time.perf_counter() - t_total

        totals.append(total_elapsed)
        loops.append(loop_elapsed)
        result_df = df

    totals.sort()
    loops.sort()
    return totals[num_runs // 2], loops[num_runs // 2], result_df


# ---------------------------------------------------------------------------
# /execute endpoint round-trip benchmark
# ---------------------------------------------------------------------------

def benchmark_execute(stoptime, dt, num_runs=3):
    """Round-trip latency of `POST /execute` through a Flask test client.

    The endpoint is stateless: the request body carries the full JSON model.
    Reported time is end-to-end (request serialize → Flask routing → Rust
    simulate → JSON response → parse), so subtracting the raw Rust-simulate
    number from benchmark() reveals what HTTP + JSON handling adds.

    `bearer_token=None` disables auth, so no Authorization header is needed.
    """
    from BPTK_Py.server import BptkServer

    model = build_sir_model(stoptime=stoptime, dt=dt)
    payload = json.dumps({
        "model": json.loads(model.to_json()),
        "scenarios": {"baseline": {}},
        "equations": ALL_EQUATIONS,
    })

    server = BptkServer(__name__, lambda: BPTK_Py.bptk(), None, None)
    client = server.test_client()

    times = []
    for _ in range(num_runs):
        t0 = time.perf_counter()
        resp = client.post('/execute', data=payload,
                            content_type='application/json')
        assert resp.status_code == 200, resp.data
        _ = resp.get_json()  # include JSON parse in the round-trip cost
        times.append(time.perf_counter() - t0)

    times.sort()
    return times[num_runs // 2]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def fmt_ms(seconds):
    """Format seconds as milliseconds string."""
    return f"{seconds * 1000:.1f} ms"


def main():
    print("=" * 72)
    print("  BPTK-Py Benchmark: Rust vs Python SD Backend")
    print("=" * 72)
    print()

    configs = [
        # (stoptime, dt, label)
        (100, 0.25, "Small   (400 steps)"),
        (1_000, 0.25, "Medium  (4,000 steps)"),
        (10_000, 0.25, "Large   (40,000 steps)"),
        (100_000, 0.25, "XLarge  (400,000 steps)"),
    ]

    print("Model: SIR epidemic with vaccination & hospital capacity feedback")
    print("Elements: 5 stocks, 5 flows, 3 converters, 5 constants")
    print(f"Equations tracked: {len(ALL_EQUATIONS)}")
    print("Runs per config: 5 (median reported)")

    # --- Summary table ---
    print()
    print("Overall comparison")
    print("-" * 72)
    print(f"{'Configuration':<25} {'Python':>10} {'Rust total':>12} {'Speedup':>10}")
    print("-" * 72)

    results = []
    for stoptime, dt, label in configs:
        py_time, rust, py_df, rust_df = benchmark(stoptime, dt)
        results.append((label, py_time, rust, py_df, rust_df))
        rust_total = rust[0]
        speedup = py_time / rust_total if rust_total > 0 else float("inf")
        print(f"{label:<25} {fmt_ms(py_time):>10} {fmt_ms(rust_total):>12} {speedup:.1f}x")

    # --- Phase breakdown table ---
    print()
    print("Rust phase breakdown")
    print("-" * 72)
    print(f"{'Configuration':<25} {'Serialize':>10} {'Parse':>10} {'Simulate':>10} {'Convert':>10}")
    print("-" * 72)

    for label, py_time, rust, _, _ in results:
        _, t_ser, t_load, t_sim, t_conv = rust
        print(f"{label:<25} {fmt_ms(t_ser):>10} {fmt_ms(t_load):>10} {fmt_ms(t_sim):>10} {fmt_ms(t_conv):>10}")

    # --- Simulation-only speedup ---
    print()
    print("Simulation-only speedup (excluding serialization & conversion)")
    print("-" * 72)
    print(f"{'Configuration':<25} {'Python':>10} {'Rust sim':>10} {'Speedup':>10}")
    print("-" * 72)

    for label, py_time, rust, _, _ in results:
        t_sim = rust[3]
        speedup = py_time / t_sim if t_sim > 0 else float("inf")
        print(f"{label:<25} {fmt_ms(py_time):>10} {fmt_ms(t_sim):>10} {speedup:.1f}x")

    # --- Numerical parity verification ---
    print()
    print("Numerical parity verification")
    print("-" * 72)

    all_passed = True
    for label, _, _, py_df, rust_df in results:
        # The Python backend prefixes column names with "bench_base_",
        # the Rust direct-call does not — align column names for comparison.
        py_cols = {c: c.replace("bench_base_", "") for c in py_df.columns}
        py_aligned = py_df.rename(columns=py_cols)

        # Keep only the equations present in both
        common_cols = sorted(set(py_aligned.columns) & set(rust_df.columns))
        py_vals = py_aligned[common_cols].sort_index()
        rust_vals = rust_df[common_cols].sort_index()

        max_abs_diff = np.abs(py_vals.values - rust_vals.values).max()
        max_rel_diff = np.abs(
            (py_vals.values - rust_vals.values)
            / np.where(py_vals.values == 0, 1.0, py_vals.values)
        ).max()

        passed = max_abs_diff < 1e-9
        status = "PASS" if passed else "FAIL"
        if not passed:
            all_passed = False

        print(f"{label:<25} {status}  max abs diff: {max_abs_diff:.2e}  max rel diff: {max_rel_diff:.2e}")

    print()
    if all_passed:
        print("All configurations: results are numerically identical.")
    else:
        print("WARNING: numerical differences detected!")

    # --- Step-by-step Rust vs full simulate ---
    print()
    print("Step-by-step Rust (init + step loop) vs full Rust simulate")
    print("-" * 72)
    print(f"{'Configuration':<25} {'Rust full':>11} {'Step':>11} {'Step+const':>11} {'Step parity':>11}")
    print("-" * 72)

    # Map label → (rust_total, python_df) from the full-simulate pass above.
    rust_total_by_label = {label: rust[0] for label, _, rust, _, _ in results}
    py_df_by_label = {label: py_df for label, _, _, py_df, _ in results}

    for stoptime, dt, label in configs:
        step_total, _, step_df = benchmark_step(stoptime, dt)
        step_ovr_total, _, _ = benchmark_step(stoptime, dt, with_overrides=True)

        # Parity: step-by-step trajectory vs the Python backend.
        py_df = py_df_by_label[label]
        py_aligned = py_df.rename(
            columns={c: c.replace("bench_base_", "") for c in py_df.columns}
        )
        common = sorted(set(py_aligned.columns) & set(step_df.columns))
        step_diff = np.abs(
            py_aligned[common].sort_index().values
            - step_df[common].sort_index().values
        ).max()
        parity = "PASS" if step_diff < 1e-9 else "FAIL ({:.1e})".format(step_diff)

        rust_full = rust_total_by_label[label]
        print(f"{label:<25} {fmt_ms(rust_full):>11} {fmt_ms(step_total):>11} "
              f"{fmt_ms(step_ovr_total):>11} {parity:>11}")

    print()
    print("(Step total includes serialize+load+convert, same as 'Rust total'.")
    print(" Step+const issues one set_constant per timestep — the server case.)")

    # --- /execute endpoint round-trip latency ---
    print()
    print("POST /execute round-trip latency (Flask test client)")
    print("-" * 72)
    print(f"{'Configuration':<25} {'Rust sim':>11} {'Round-trip':>11} {'HTTP+JSON':>11}")
    print("-" * 72)

    rust_sim_by_label = {label: rust[3] for label, _, rust, _, _ in results}
    for stoptime, dt, label in configs:
        rt = benchmark_execute(stoptime, dt)
        rust_sim = rust_sim_by_label[label]
        overhead = rt - rust_sim
        print(f"{label:<25} {fmt_ms(rust_sim):>11} {fmt_ms(rt):>11} {fmt_ms(overhead):>11}")

    print()
    print("(HTTP+JSON = round-trip minus raw Rust simulate: request/response")
    print(" (de)serialization + Flask routing overhead.)")

    print()
    print("=" * 72)


if __name__ == "__main__":
    main()
