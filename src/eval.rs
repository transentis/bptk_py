use crate::model::*;
use crate::state::SimulationState;

impl SdModel {
    /// Evaluate a single expression at a given timestep.
    pub fn eval_expr(&self, expr: &Expr, state: &SimulationState, step: usize) -> f64 {
        match expr {
            Expr::Literal(v) => *v,
            Expr::Ref(idx) => state.memo[*idx][step],
            Expr::BinaryOp { op, left, right } => {
                let l = self.eval_expr(left, state, step);
                let r = self.eval_expr(right, state, step);
                eval_bin_op(*op, l, r)
            }
            Expr::UnaryOp { op, operand } => {
                let v = self.eval_expr(operand, state, step);
                eval_un_op(*op, v)
            }
            Expr::Call { function, args } => self.eval_builtin(function, args, state, step),
            Expr::If {
                condition,
                then,
                else_,
            } => {
                let cond = self.eval_expr(condition, state, step);
                if cond != 0.0 {
                    self.eval_expr(then, state, step)
                } else {
                    self.eval_expr(else_, state, step)
                }
            }
            #[cfg(feature = "python")]
            Expr::PyCallback { slot, args } => self.eval_callback(*slot, args, state, step),
        }
    }

    /// Call a registered Python function with the time and the evaluated arguments.
    ///
    /// The three ways this can go wrong - no callable for the slot, an exception inside
    /// the function, an answer that is not a number - are recorded on the state and end
    /// the step. The value returned here is NaN and is never read for anything but
    /// filling the memo cell of a run that is about to be abandoned.
    #[cfg(feature = "python")]
    fn eval_callback(
        &self,
        slot: usize,
        args: &[Expr],
        state: &SimulationState,
        step: usize,
    ) -> f64 {
        use pyo3::prelude::*;

        let name = self
            .callback_names
            .get(slot)
            .map(String::as_str)
            .unwrap_or("<unknown>");

        let callable = match self.callbacks.get(slot).and_then(Option::as_ref) {
            Some(callable) => callable,
            None => {
                state.record_error(format!(
                    "No Python function registered for '{}'. Register it before running.",
                    name
                ));
                return f64::NAN;
            }
        };

        // The engine counts steps; the function was written for a model that has a time.
        let t = self.starttime + step as f64 * self.dt;
        let values: Vec<f64> = args
            .iter()
            .map(|a| self.eval_expr(a, state, step))
            .collect();

        Python::attach(|py| {
            let mut call_args: Vec<f64> = Vec::with_capacity(values.len() + 1);
            call_args.push(t);
            call_args.extend(values);

            match callable
                .call1(py, pyo3::types::PyTuple::new(py, call_args)?)
                .and_then(|answer| answer.extract::<f64>(py))
            {
                Ok(value) => Ok(value),
                Err(error) => {
                    state.record_error(format!(
                        "Python function '{}' failed at t={}: {}",
                        name,
                        t,
                        describe(py, &error)
                    ));
                    Ok(f64::NAN)
                }
            }
        })
        .unwrap_or_else(|error: PyErr| {
            state.record_error(format!(
                "Python function '{}' could not be called at t={}: {}",
                name, t, error
            ));
            f64::NAN
        })
    }
}

/// A Python exception with its traceback, so that a failure inside a user's function is
/// readable rather than reduced to its type.
#[cfg(feature = "python")]
fn describe(py: pyo3::Python<'_>, error: &pyo3::PyErr) -> String {
    use pyo3::types::PyTracebackMethods;

    match error.traceback(py) {
        Some(traceback) => match traceback.format() {
            Ok(text) => format!("{}\n{}", error, text.trim_end()),
            Err(_) => error.to_string(),
        },
        None => error.to_string(),
    }
}

/// Boolean encoding: 0.0 = false, nonzero = true (SD convention).
fn to_bool(v: f64) -> f64 {
    if v != 0.0 { 1.0 } else { 0.0 }
}

fn eval_bin_op(op: BinOp, l: f64, r: f64) -> f64 {
    match op {
        BinOp::Add => l + r,
        BinOp::Sub => l - r,
        BinOp::Mul => l * r,
        BinOp::Div => {
            if r == 0.0 {
                f64::NAN
            } else {
                l / r
            }
        }
        BinOp::Pow => l.powf(r),
        BinOp::Mod => {
            if r == 0.0 {
                f64::NAN
            } else {
                l % r
            }
        }
        BinOp::Gt => to_bool(if l > r { 1.0 } else { 0.0 }),
        BinOp::Lt => to_bool(if l < r { 1.0 } else { 0.0 }),
        BinOp::Gte => to_bool(if l >= r { 1.0 } else { 0.0 }),
        BinOp::Lte => to_bool(if l <= r { 1.0 } else { 0.0 }),
        BinOp::Eq => to_bool(if l == r { 1.0 } else { 0.0 }),
        BinOp::Neq => to_bool(if l != r { 1.0 } else { 0.0 }),
        BinOp::And => to_bool(if l != 0.0 && r != 0.0 { 1.0 } else { 0.0 }),
        BinOp::Or => to_bool(if l != 0.0 || r != 0.0 { 1.0 } else { 0.0 }),
    }
}

fn eval_un_op(op: UnOp, v: f64) -> f64 {
    match op {
        UnOp::Neg => -v,
        UnOp::Not => {
            if v == 0.0 {
                1.0
            } else {
                0.0
            }
        }
    }
}
