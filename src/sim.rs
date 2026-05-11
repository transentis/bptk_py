use std::collections::HashMap;

use crate::model::*;
use crate::state::SimulationState;

/// Simulation results: entity name → { time → value }
pub type SimulationResults = HashMap<String, HashMap<String, f64>>;

impl SdModel {
    /// Run full simulation, return results for requested equations.
    ///
    /// Algorithm (matches Python behavior in stock.py:68-82):
    /// 1. Allocate memo table: entities.len() x num_steps
    /// 2. Pre-evaluate non-stock entities at step 0 (constants, converters, flows)
    /// 3. Initialize stocks at step 0 from their initial_value expression
    /// 4. For each step 0..num_steps:
    ///    - Evaluate all non-stock entities (in topological order)
    ///    - Flows enforce max(0, val) (non-negativity)
    ///    - If step+1 < num_steps: integrate stocks via Euler method
    /// 4. Extract requested equations into results
    pub fn simulate(&self, equations: &[String], seed: Option<u64>) -> SimulationResults {
        let num_steps = ((self.stoptime - self.starttime) / self.dt).round() as usize + 1;
        let mut state = SimulationState::new(self.entities.len(), num_steps, seed);

        // Pre-evaluate non-stock entities at step 0 so that constants and
        // converters are available for stock initial_value expressions.
        for &idx in &self.eval_order {
            let val = self.eval_expr(&self.entities[idx].equation, &state, 0);
            state.memo[idx][0] = if matches!(self.entities[idx].kind, EntityKind::Flow) {
                val.max(0.0)
            } else {
                val
            };
        }

        // Initialize stocks at step 0 (can now reference evaluated constants)
        for (i, entity) in self.entities.iter().enumerate() {
            if let EntityKind::Stock { ref initial_value } = entity.kind {
                state.memo[i][0] = self.eval_expr(initial_value, &state, 0);
            }
        }

        // Main simulation loop (step 0 re-evaluates non-stocks with correct stock values)
        for step in 0..num_steps {
            // Evaluate all non-stock entities in topological order
            for &idx in &self.eval_order {
                let val = self.eval_expr(&self.entities[idx].equation, &state, step);
                // Flow non-negativity: max(0, val)
                state.memo[idx][step] = if matches!(self.entities[idx].kind, EntityKind::Flow) {
                    val.max(0.0)
                } else {
                    val
                };
            }

            // Euler integration: stock(t+dt) = stock(t) + dt * net_flow(t)
            if step + 1 < num_steps {
                for (i, entity) in self.entities.iter().enumerate() {
                    if matches!(entity.kind, EntityKind::Stock { .. }) {
                        let flow_val = self.eval_expr(&entity.equation, &state, step);
                        state.memo[i][step + 1] = state.memo[i][step] + self.dt * flow_val;
                    }
                }
            }
        }

        // Extract results for requested equations
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
}

/// Format time as a clean string (avoid trailing zeros for whole numbers).
fn format_time(t: f64) -> String {
    if t == t.floor() {
        format!("{:.1}", t)
    } else {
        format!("{}", t)
    }
}
