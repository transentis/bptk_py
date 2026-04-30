"""
Benchmark: Rust vs Python SD simulation backend.

Builds a non-trivial System Dynamics model (SIR epidemic with vaccination
and hospital capacity) and runs it using both backends, measuring wall-clock
time for each.

Usage:
    python examples/benchmark_rust_vs_python.py

Sample results (Apple M1, median of 5 runs):

    Overall comparison
    ------------------------------------------------------------------------
    Configuration                 Python   Rust total    Speedup
    ------------------------------------------------------------------------
    Small   (400 steps)          24.9 ms       6.1 ms      4.1x
    Medium  (4,000 steps)       225.6 ms      59.9 ms      3.8x
    Large   (40,000 steps)     2295.5 ms     600.6 ms      3.8x
    XLarge  (400,000 steps)   23692.3 ms    7268.6 ms      3.3x

    Rust phase breakdown
    ------------------------------------------------------------------------
    Configuration              Serialize      Parse   Simulate    Convert
    ------------------------------------------------------------------------
    Small   (400 steps)           0.1 ms     0.3 ms     4.3 ms     1.3 ms
    Medium  (4,000 steps)         0.1 ms     0.3 ms    48.7 ms    10.8 ms
    Large   (40,000 steps)        0.1 ms     0.3 ms   481.6 ms   118.6 ms
    XLarge  (400,000 steps)       0.1 ms     0.3 ms  5174.7 ms  2092.3 ms

    Simulation-only speedup (excluding serialization & conversion)
    ------------------------------------------------------------------------
    Configuration                 Python   Rust sim    Speedup
    ------------------------------------------------------------------------
    Small   (400 steps)          24.9 ms     4.3 ms      5.7x
    Medium  (4,000 steps)       225.6 ms    48.7 ms      4.6x
    Large   (40,000 steps)     2295.5 ms   481.6 ms      4.8x
    XLarge  (400,000 steps)   23692.3 ms  5174.7 ms      4.6x

    Numerical parity: all configurations PASS (max abs diff: 0.00e+00)

    Key findings:
    - End-to-end speedup: ~3.3-4.1x (including serialization & DataFrame conversion)
    - Pure simulation speedup: ~4.6-5.7x
    - Serialization and JSON parsing are negligible (~0.1-0.3 ms)
    - DataFrame conversion accounts for ~20-29% of Rust total time
    - Results are bit-for-bit identical between backends
"""

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

    print()
    print("=" * 72)


if __name__ == "__main__":
    main()
