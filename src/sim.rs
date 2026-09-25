use std::collections::HashMap;

use crate::model::*;
use crate::state::SimulationState;

/// Simulation results: entity name → { time → value }
pub type SimulationResults = HashMap<String, HashMap<String, f64>>;

/// Errors that can be returned from `SdModel::step()`.
#[derive(Debug)]
pub enum StepError {
    /// `step()` was called when `current_step` is already the last step.
    PastStoptime,
    /// A Python callback failed during the step. Carries the message the evaluator
    /// recorded, including the traceback where there is one.
    Callback(String),
}

impl std::fmt::Display for StepError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            StepError::PastStoptime => {
                write!(f, "PastStoptime: the simulation has already reached stoptime")
            }
            StepError::Callback(message) => write!(f, "{}", message),
        }
    }
}

impl SdModel {
    /// Allocate a fresh `SimulationState`, evaluate step 0, and integrate
    /// stocks into step 1 if the run has more than one step.
    ///
    /// Algorithm (matches Python behavior in stock.py:68-82):
    /// 1. Allocate memo table: entities.len() x num_steps
    /// 2. Pre-evaluate non-stock entities at step 0 (constants, converters, flows)
    /// 3. Initialise stocks at step 0 from their `initial_value` expression
    /// 4. Re-evaluate non-stocks at step 0 so that flows / converters that
    ///    reference stocks see the correct initial values
    /// 5. If `num_steps > 1`, Euler-integrate stocks into step 1
    ///
    /// On return `state.current_step == 0`.
    pub fn init(&self, seed: Option<u64>) -> Result<SimulationState, StepError> {
        let num_steps = ((self.stoptime - self.starttime) / self.dt).round() as usize + 1;
        let mut state = SimulationState::new(self.entities.len(), num_steps, seed);

        // Settle step 0. An initial value may read a converter that reads another
        // stock's initial value, so one pass in each direction is not enough: with a
        // single round the converter is corrected afterwards while the stock that read
        // it keeps the stale number - which is how the same model answered 50 in Python
        // and 0 here. Each round fixes one more link of such a chain, so the number of
        // stocks bounds it, and the loop stops as soon as nothing moves. The bound also
        // ends it when a value is NaN, which never compares equal to itself.
        let stock_count = self
            .entities
            .iter()
            .filter(|entity| matches!(entity.kind, EntityKind::Stock { .. }))
            .count();

        self.eval_step(&mut state, 0);
        for _ in 0..stock_count.max(1) {
            let mut settled = true;
            for (i, entity) in self.entities.iter().enumerate() {
                if let EntityKind::Stock { ref initial_value } = entity.kind {
                    let value = self.eval_expr(initial_value, &state, 0);
                    if value != state.memo[i][0] {
                        settled = false;
                    }
                    state.memo[i][0] = value;
                }
            }
            // Non-stocks read stocks, so they follow every correction.
            self.eval_step(&mut state, 0);
            if settled {
                break;
            }
        }

        // Euler integration into step 1 if present.
        if num_steps > 1 {
            self.integrate_stocks(&mut state, 0);
        }

        state.current_step = 0;
        match state.take_error() {
            Some(message) => Err(StepError::Callback(message)),
            None => Ok(state),
        }
    }

    /// Advance the simulation by one timestep. Evaluates all non-stock
    /// entities at the new step, then integrates stocks into the following
    /// step if one exists.
    ///
    /// Returns `Err(StepError::PastStoptime)` if `current_step` is already at
    /// the last step (i.e. there is nothing more to evaluate).
    pub fn step(&self, state: &mut SimulationState) -> Result<(), StepError> {
        let num_steps = state.memo[0].len();
        let next = state.current_step + 1;
        if next >= num_steps {
            return Err(StepError::PastStoptime);
        }
        self.eval_step(state, next);
        if next + 1 < num_steps {
            self.integrate_stocks(state, next);
        }
        state.current_step = next;
        match state.take_error() {
            Some(message) => Err(StepError::Callback(message)),
            None => Ok(()),
        }
    }

    /// Repeatedly call `step()` until the simulation has reached `stoptime`.
    pub fn run_to_end(&self, state: &mut SimulationState) -> Result<(), StepError> {
        let num_steps = state.memo[0].len();
        while state.current_step + 1 < num_steps {
            // The bound is checked above, so the only failure left is a callback's.
            self.step(state)?;
        }
        Ok(())
    }

    /// Build the output results dict from `state`'s memo table, for the
    /// requested equations only.
    pub fn extract_results(
        &self,
        state: &SimulationState,
        equations: &[String],
    ) -> SimulationResults {
        let num_steps = state.memo[0].len();
        let mut results: SimulationResults = HashMap::new();
        for eq_name in equations {
            if let Some(&idx) = self.entity_index.get(eq_name) {
                let mut time_series: HashMap<String, f64> = HashMap::new();
                for step in 0..num_steps {
                    let t = self.starttime + step as f64 * self.dt;
                    // Use rounded time string to avoid floating point display issues
                    let t_str = format_time(t);
                    time_series.insert(t_str, state.memo[idx][step]);
                }
                results.insert(eq_name.clone(), time_series);
            }
        }
        results
    }

    /// Full simulation: `init` → `run_to_end` → `extract_results`.
    pub fn simulate(
        &self,
        equations: &[String],
        seed: Option<u64>,
    ) -> Result<SimulationResults, StepError> {
        let mut state = self.init(seed)?;
        self.run_to_end(&mut state)?;
        Ok(self.extract_results(&state, equations))
    }

    /// Evaluate all non-stock entities at `step` in topological order,
    /// writing each result into `state.memo`. Flows are clamped to ≥ 0.
    fn eval_step(&self, state: &mut SimulationState, step: usize) {
        for &idx in &self.eval_order {
            let val = self.eval_expr(&self.entities[idx].equation, state, step);
            state.memo[idx][step] = if matches!(self.entities[idx].kind, EntityKind::Flow) {
                val.max(0.0)
            } else {
                val
            };
        }
    }

    /// Euler integration: `stock(step+1) = stock(step) + dt * net_flow(step)`.
    /// Caller guarantees `step + 1 < num_steps`.
    fn integrate_stocks(&self, state: &mut SimulationState, step: usize) {
        for (i, entity) in self.entities.iter().enumerate() {
            if matches!(entity.kind, EntityKind::Stock { .. }) {
                let flow_val = self.eval_expr(&entity.equation, state, step);
                state.memo[i][step + 1] = state.memo[i][step] + self.dt * flow_val;
            }
        }
    }
}

/// Format time as a clean string (avoid trailing zeros for whole numbers).
fn format_time(t: f64) -> String {
    if t == t.floor() {
        format!("{:.1}", t)
    } else {
        format!("{}", t)
    }
}
