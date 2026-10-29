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
    /// The run specs cannot run, or their results do not fit in memory.
    Specs(String),
}

impl std::fmt::Display for StepError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            StepError::PastStoptime => {
                write!(f, "PastStoptime: the simulation has already reached stoptime")
            }
            StepError::Callback(message) | StepError::Specs(message) => write!(f, "{}", message),
        }
    }
}

impl SdModel {
    /// Allocate a fresh `SimulationState`, evaluate step 0, and integrate
    /// stocks into step 1 if the run has more than one step.
    ///
    /// Algorithm (matches how the Python engine starts a stock, `Stock` in
    /// `BPTK_Py/sddsl/stock.py`):
    /// 1. Allocate memo table: entities.len() x num_steps
    /// 2. Evaluate every entity at step 0 in `init_order`: a stock from its
    ///    `initial_value`, anything else from its equation. That order puts each
    ///    entity after what it reads, so nothing is evaluated with a stock that has
    ///    not been started yet
    /// 3. If `num_steps > 1`, Euler-integrate stocks into step 1
    ///
    /// On return `state.current_step == 0`.
    pub fn init(&self, seed: Option<u64>) -> Result<SimulationState, StepError> {
        let num_steps =
            num_steps_for(self.starttime, self.stoptime, self.dt).map_err(StepError::Specs)?;
        let mut state = SimulationState::try_new(self.entities.len(), num_steps, seed)
            .map_err(StepError::Specs)?;

        state.set_starting(true);
        for &idx in &self.init_order {
            state.set_current_entity(idx);
            let entity = &self.entities[idx];
            state.memo[idx][0] = match entity.kind {
                EntityKind::Stock { ref initial_value } => self.eval_expr(initial_value, &state, 0),
                EntityKind::Flow => self.eval_expr(&entity.equation, &state, 0).max(0.0),
                _ => self.eval_expr(&entity.equation, &state, 0),
            };
        }
        state.set_starting(false);

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
        let num_steps = state.num_steps;
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
        let num_steps = state.num_steps;
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
        let num_steps = state.num_steps;
        let mut results: SimulationResults = HashMap::new();
        for eq_name in equations {
            if let Some(&idx) = self.entity_index.get(eq_name) {
                let mut time_series: HashMap<String, f64> = HashMap::new();
                for step in 0..num_steps {
                    let t = self.time_at(step);
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
            state.set_current_entity(idx);
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
                state.set_current_entity(i);
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
