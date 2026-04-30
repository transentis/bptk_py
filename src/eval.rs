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
        }
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
