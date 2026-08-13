use std::collections::HashMap;

use pyo3::prelude::*;
use pyo3::exceptions::PyValueError;

pub mod model;
pub mod json_parser;
pub mod state;
pub mod eval;
pub mod builtins;
pub mod lookup;
pub mod sim;

/// Returns the version of the Rust SD engine.
#[pyfunction]
fn version() -> &'static str {
    "0.1.0"
}

#[pyclass]
pub struct RustSdEngine {}

#[pymethods]
impl RustSdEngine {
    #[new]
    fn new() -> Self {
        RustSdEngine {}
    }

    /// Parse a JSON string into an executable model.
    fn load_model(&self, json: &str) -> PyResult<RustSdModel> {
        let sd_model = json_parser::parse_json(json)
            .map_err(|e| PyValueError::new_err(e.to_string()))?;
        Ok(RustSdModel {
            model: sd_model,
            state: None,
            requested_equations: Vec::new(),
        })
    }
}

// Deliberately NOT `unsendable`: a threaded WSGI server (Flask's dev server, uwsgi
// with threads) serves consecutive requests on different threads, and the runner
// caches this handle on the Scenario across requests — so the handle really does
// travel between threads. PyO3 requires `Send` here, not `Sync`; `RefCell<StdRng>`
// is `Send` because `StdRng` is, so no lock is needed. The GIL still serializes
// access, and PyO3's borrow flags still prevent overlapping `&mut self`.
#[pyclass]
pub struct RustSdModel {
    model: model::SdModel,
    /// Step-by-step state. `None` before `init()`, `Some` after.
    /// `simulate()` and `reset()` both clear it back to `None`.
    state: Option<state::SimulationState>,
    /// Equations captured at `init()` time. `step()` returns this set on each call.
    requested_equations: Vec<String>,
}

#[pymethods]
impl RustSdModel {
    /// Run full simulation. Clears any stepping state so a follow-up `init()`
    /// starts from a fresh `SimulationState`.
    ///
    /// Returns `dict[str, dict[str, float]]` — `{ entity_name: { time_str: value } }`.
    #[pyo3(signature = (equations, seed=None))]
    fn simulate(
        &mut self,
        equations: Vec<String>,
        seed: Option<u64>,
    ) -> PyResult<HashMap<String, HashMap<String, f64>>> {
        self.state = None;
        self.requested_equations.clear();
        Ok(self.model.simulate(&equations, seed))
    }

    /// Initialise for step-by-step execution. Pre-allocates the memo table,
    /// evaluates step 0, and returns the values of `equations` at `t = starttime`.
    ///
    /// Calling `init()` again on the same model discards any prior stepping
    /// state and starts fresh.
    #[pyo3(signature = (equations, seed=None))]
    fn init(
        &mut self,
        equations: Vec<String>,
        seed: Option<u64>,
    ) -> PyResult<HashMap<String, f64>> {
        let state = self.model.init(seed);
        self.state = Some(state);
        self.requested_equations = equations;
        Ok(self.snapshot_current())
    }

    /// Advance one timestep. Returns the values of the equations passed to
    /// `init()` at the new `t`.
    ///
    /// Errors with `ValueError` if `init()` was never called, or if the
    /// simulation has already reached `stoptime`.
    fn step(&mut self) -> PyResult<HashMap<String, f64>> {
        // Scoped mutation so the &mut borrow of self.state ends before we
        // call the &self snapshot helper.
        {
            let state = self
                .state
                .as_mut()
                .ok_or_else(|| PyValueError::new_err("step() called without init()"))?;
            self.model
                .step(state)
                .map_err(|e| PyValueError::new_err(format!("{:?}", e)))?;
        }
        Ok(self.snapshot_current())
    }

    /// Current simulation time (the last evaluated step).
    fn current_time(&self) -> PyResult<f64> {
        let state = self
            .state
            .as_ref()
            .ok_or_else(|| PyValueError::new_err("current_time() called without init()"))?;
        Ok(self.model.starttime + (state.current_step as f64) * self.model.dt)
    }

    /// Number of timesteps remaining before `stoptime`.
    /// `0` means the next `step()` would error with `PastStoptime`.
    fn steps_remaining(&self) -> PyResult<usize> {
        let state = self
            .state
            .as_ref()
            .ok_or_else(|| PyValueError::new_err("steps_remaining() called without init()"))?;
        // memo is indexed [entity][step]; outer length matches num_entities,
        // and num_steps is the length of any inner vector (model must have ≥1 entity).
        let num_steps = state.memo[0].len();
        Ok(num_steps - 1 - state.current_step)
    }

    /// Discard the stepping state. After `reset()`, `simulate()` is safe again
    /// and `init()` will start from scratch.
    /// Does NOT reset constant / runspec / lookup overrides — those persist on the model.
    fn reset(&mut self) {
        self.state = None;
        self.requested_equations.clear();
    }

    /// Override a constant's value. Safe to call before or after `init()` —
    /// mid-simulation overrides take effect from the next `step()` forward.
    fn set_constant(&mut self, name: &str, value: f64) -> PyResult<()> {
        self.model
            .set_constant(name, value)
            .map_err(PyValueError::new_err)
    }

    /// Override the simulation run specifications (starttime, stoptime, dt).
    /// Rejected with `ValueError` if `init()` has been called — changing the
    /// runspecs would invalidate the pre-allocated memo. Call `reset()` first.
    fn set_runspecs(&mut self, starttime: f64, stoptime: f64, dt: f64) -> PyResult<()> {
        if self.state.is_some() {
            return Err(PyValueError::new_err(
                "set_runspecs() not allowed after init() — call reset() first",
            ));
        }
        self.model.set_runspecs(starttime, stoptime, dt);
        Ok(())
    }

    /// Replace the points of a graphical function (lookup table).
    fn set_points(&mut self, name: &str, points: Vec<(f64, f64)>) -> PyResult<()> {
        self.model
            .set_points(name, points)
            .map_err(PyValueError::new_err)
    }

    /// Export the computed memo grid so a session can be resumed WITHOUT replay.
    ///
    /// Returns `(current_step, { entity_name: [value_0, .., value_current_step] })`
    /// covering every entity (not just the requested equations — future steps read
    /// past values of stocks / delay inputs that may not have been requested), or
    /// `None` if `init()` was never called.
    ///
    /// This captures two of the three pieces of simulation state: the memo values
    /// and the cursor. It does NOT capture the RNG position (see `import_state`) —
    /// for a stochastic model the resumed run therefore takes a different random
    /// path from the point of export onward. Past (already-computed) values are
    /// always preserved exactly.
    fn export_state(&self) -> Option<(usize, HashMap<String, Vec<f64>>)> {
        let state = self.state.as_ref()?;
        let step = state.current_step;
        // Include one column PAST the cursor: `step()` integrates each stock's next
        // value ahead of the cursor (stock[C+1] is written while landing on C), and
        // the following step reads it. Non-stock columns at C+1 are stale but get
        // overwritten by the next `eval_step` before they are read, so exporting
        // them is harmless. Capped at the last step for the end-of-run case.
        let num_steps = state.memo[0].len();
        let hi = (step + 1).min(num_steps - 1);
        let mut memo = HashMap::with_capacity(self.model.entities.len());
        for (idx, entity) in self.model.entities.iter().enumerate() {
            memo.insert(entity.name.clone(), state.memo[idx][..=hi].to_vec());
        }
        Some((step, memo))
    }

    /// Rebuild the stepping state from an exported grid — the fast alternative to
    /// replaying the whole settings_log. Allocates a fresh `SimulationState`, copies
    /// the exported values into the memo by entity name, and positions the cursor at
    /// `current_step`, so the next `step()` continues from `current_step + 1`.
    ///
    /// Runspecs and constant/points overrides must already be applied on the model
    /// (the caller re-applies them before `import_state`, exactly as replay would),
    /// so future steps evaluate with the correct equations. The RNG is seeded fresh
    /// from `seed`; the mid-stream RNG position is NOT restored (deliberate — see
    /// `export_state`). Deterministic models are unaffected.
    #[pyo3(signature = (current_step, memo, equations, seed=None))]
    fn import_state(
        &mut self,
        current_step: usize,
        memo: HashMap<String, Vec<f64>>,
        equations: Vec<String>,
        seed: Option<u64>,
    ) -> PyResult<()> {
        let num_steps =
            ((self.model.stoptime - self.model.starttime) / self.model.dt).round() as usize + 1;
        if current_step >= num_steps {
            return Err(PyValueError::new_err(format!(
                "import_state: current_step {} out of range for {} steps",
                current_step, num_steps
            )));
        }

        // Re-seed per cursor position, NOT with the raw seed. On a stateless
        // per-round resume the RNG position cannot be recovered (StdRng is opaque),
        // so a fresh SimulationState always starts its stream at position 0. Seeding
        // every round with the same raw seed would therefore draw the SAME "first"
        // random number every round — the stochastic term would collapse to a
        // constant. Deriving the seed from current_step gives each resume a distinct,
        // yet deterministic (given the persisted seed), stream. Deterministic models
        // never touch the RNG, so this is a no-op for them.
        let derived_seed = seed.map(|s| s.wrapping_add(current_step as u64).wrapping_add(1));
        let mut state = state::SimulationState::new(self.model.entities.len(), num_steps, derived_seed);
        for (name, values) in memo {
            let idx = self.model.entity_index.get(&name).ok_or_else(|| {
                PyValueError::new_err(format!("import_state: unknown entity '{}'", name))
            })?;
            let n = values.len().min(num_steps);
            state.memo[*idx][..n].copy_from_slice(&values[..n]);
        }
        state.current_step = current_step;

        self.state = Some(state);
        self.requested_equations = equations;
        Ok(())
    }
}

impl RustSdModel {
    /// Read the current step's values for `self.requested_equations` out of
    /// the memo table. Used by both `init()` (after the new state lands) and
    /// `step()` (after the cursor advances).
    fn snapshot_current(&self) -> HashMap<String, f64> {
        let state = self
            .state
            .as_ref()
            .expect("snapshot_current called without state");
        let step = state.current_step;
        self.requested_equations
            .iter()
            .filter_map(|name| {
                self.model
                    .entity_index
                    .get(name)
                    .map(|&idx| (name.clone(), state.memo[idx][step]))
            })
            .collect()
    }
}

/// The Rust engine Python module, installed at `BPTK_Py._rust_engine`.
#[pymodule]
fn _rust_engine(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(version, m)?)?;
    m.add_class::<RustSdEngine>()?;
    m.add_class::<RustSdModel>()?;
    Ok(())
}
