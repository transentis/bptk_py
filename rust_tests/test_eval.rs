use std::collections::HashMap;

use bptk_rust_engine::model::*;
use bptk_rust_engine::state::SimulationState;

/// Helper: build a minimal SdModel with no entities, just for eval testing.
fn empty_model() -> SdModel {
    SdModel {
        name: String::new(),
        starttime: 0.0,
        stoptime: 10.0,
        dt: 1.0,
        entities: Vec::new(),
        entity_index: HashMap::new(),
        graphical_functions: HashMap::new(),
        eval_order: Vec::new(),
    }
}

#[test]
fn test_eval_literal() {
    let model = empty_model();
    let state = SimulationState::new(0, 1, None);
    let expr = Expr::Literal(42.0);
    assert_eq!(model.eval_expr(&expr, &state, 0), 42.0);
}

#[test]
fn test_eval_ref() {
    let model = empty_model();
    let mut state = SimulationState::new(3, 5, None);
    state.memo[1][3] = 99.0;
    let expr = Expr::Ref(1);
    assert_eq!(model.eval_expr(&expr, &state, 3), 99.0);
}

#[test]
fn test_eval_arithmetic() {
    let model = empty_model();
    let state = SimulationState::new(0, 1, None);

    // 3 + 4 = 7
    let add = Expr::BinaryOp {
        op: BinOp::Add,
        left: Box::new(Expr::Literal(3.0)),
        right: Box::new(Expr::Literal(4.0)),
    };
    assert_eq!(model.eval_expr(&add, &state, 0), 7.0);

    // 10 - 3 = 7
    let sub = Expr::BinaryOp {
        op: BinOp::Sub,
        left: Box::new(Expr::Literal(10.0)),
        right: Box::new(Expr::Literal(3.0)),
    };
    assert_eq!(model.eval_expr(&sub, &state, 0), 7.0);

    // 5 * 6 = 30
    let mul = Expr::BinaryOp {
        op: BinOp::Mul,
        left: Box::new(Expr::Literal(5.0)),
        right: Box::new(Expr::Literal(6.0)),
    };
    assert_eq!(model.eval_expr(&mul, &state, 0), 30.0);

    // 15 / 3 = 5
    let div = Expr::BinaryOp {
        op: BinOp::Div,
        left: Box::new(Expr::Literal(15.0)),
        right: Box::new(Expr::Literal(3.0)),
    };
    assert_eq!(model.eval_expr(&div, &state, 0), 5.0);

    // 2 ^ 10 = 1024
    let pow = Expr::BinaryOp {
        op: BinOp::Pow,
        left: Box::new(Expr::Literal(2.0)),
        right: Box::new(Expr::Literal(10.0)),
    };
    assert_eq!(model.eval_expr(&pow, &state, 0), 1024.0);

    // 10 % 3 = 1
    let modulo = Expr::BinaryOp {
        op: BinOp::Mod,
        left: Box::new(Expr::Literal(10.0)),
        right: Box::new(Expr::Literal(3.0)),
    };
    assert_eq!(model.eval_expr(&modulo, &state, 0), 1.0);
}

#[test]
fn test_eval_division_by_zero() {
    let model = empty_model();
    let state = SimulationState::new(0, 1, None);
    let expr = Expr::BinaryOp {
        op: BinOp::Div,
        left: Box::new(Expr::Literal(1.0)),
        right: Box::new(Expr::Literal(0.0)),
    };
    assert!(model.eval_expr(&expr, &state, 0).is_nan());
}

#[test]
fn test_eval_comparisons() {
    let model = empty_model();
    let state = SimulationState::new(0, 1, None);

    let gt = Expr::BinaryOp {
        op: BinOp::Gt,
        left: Box::new(Expr::Literal(5.0)),
        right: Box::new(Expr::Literal(3.0)),
    };
    assert_eq!(model.eval_expr(&gt, &state, 0), 1.0);

    let gt_false = Expr::BinaryOp {
        op: BinOp::Gt,
        left: Box::new(Expr::Literal(3.0)),
        right: Box::new(Expr::Literal(5.0)),
    };
    assert_eq!(model.eval_expr(&gt_false, &state, 0), 0.0);

    let eq = Expr::BinaryOp {
        op: BinOp::Eq,
        left: Box::new(Expr::Literal(5.0)),
        right: Box::new(Expr::Literal(5.0)),
    };
    assert_eq!(model.eval_expr(&eq, &state, 0), 1.0);

    let neq = Expr::BinaryOp {
        op: BinOp::Neq,
        left: Box::new(Expr::Literal(5.0)),
        right: Box::new(Expr::Literal(3.0)),
    };
    assert_eq!(model.eval_expr(&neq, &state, 0), 1.0);

    let lte = Expr::BinaryOp {
        op: BinOp::Lte,
        left: Box::new(Expr::Literal(5.0)),
        right: Box::new(Expr::Literal(5.0)),
    };
    assert_eq!(model.eval_expr(&lte, &state, 0), 1.0);

    let gte = Expr::BinaryOp {
        op: BinOp::Gte,
        left: Box::new(Expr::Literal(3.0)),
        right: Box::new(Expr::Literal(5.0)),
    };
    assert_eq!(model.eval_expr(&gte, &state, 0), 0.0);

    let lt = Expr::BinaryOp {
        op: BinOp::Lt,
        left: Box::new(Expr::Literal(3.0)),
        right: Box::new(Expr::Literal(5.0)),
    };
    assert_eq!(model.eval_expr(&lt, &state, 0), 1.0);
}

#[test]
fn test_eval_logical() {
    let model = empty_model();
    let state = SimulationState::new(0, 1, None);

    // true AND true = true
    let and_tt = Expr::BinaryOp {
        op: BinOp::And,
        left: Box::new(Expr::Literal(1.0)),
        right: Box::new(Expr::Literal(1.0)),
    };
    assert_eq!(model.eval_expr(&and_tt, &state, 0), 1.0);

    // true AND false = false
    let and_tf = Expr::BinaryOp {
        op: BinOp::And,
        left: Box::new(Expr::Literal(1.0)),
        right: Box::new(Expr::Literal(0.0)),
    };
    assert_eq!(model.eval_expr(&and_tf, &state, 0), 0.0);

    // false OR true = true
    let or_ft = Expr::BinaryOp {
        op: BinOp::Or,
        left: Box::new(Expr::Literal(0.0)),
        right: Box::new(Expr::Literal(1.0)),
    };
    assert_eq!(model.eval_expr(&or_ft, &state, 0), 1.0);

    // false OR false = false
    let or_ff = Expr::BinaryOp {
        op: BinOp::Or,
        left: Box::new(Expr::Literal(0.0)),
        right: Box::new(Expr::Literal(0.0)),
    };
    assert_eq!(model.eval_expr(&or_ff, &state, 0), 0.0);
}

#[test]
fn test_eval_unary() {
    let model = empty_model();
    let state = SimulationState::new(0, 1, None);

    let neg = Expr::UnaryOp {
        op: UnOp::Neg,
        operand: Box::new(Expr::Literal(5.0)),
    };
    assert_eq!(model.eval_expr(&neg, &state, 0), -5.0);

    let not_true = Expr::UnaryOp {
        op: UnOp::Not,
        operand: Box::new(Expr::Literal(1.0)),
    };
    assert_eq!(model.eval_expr(&not_true, &state, 0), 0.0);

    let not_false = Expr::UnaryOp {
        op: UnOp::Not,
        operand: Box::new(Expr::Literal(0.0)),
    };
    assert_eq!(model.eval_expr(&not_false, &state, 0), 1.0);
}

#[test]
fn test_eval_if() {
    let model = empty_model();
    let state = SimulationState::new(0, 1, None);

    // if (1.0) then 10.0 else 20.0 → 10.0
    let if_true = Expr::If {
        condition: Box::new(Expr::Literal(1.0)),
        then: Box::new(Expr::Literal(10.0)),
        else_: Box::new(Expr::Literal(20.0)),
    };
    assert_eq!(model.eval_expr(&if_true, &state, 0), 10.0);

    // if (0.0) then 10.0 else 20.0 → 20.0
    let if_false = Expr::If {
        condition: Box::new(Expr::Literal(0.0)),
        then: Box::new(Expr::Literal(10.0)),
        else_: Box::new(Expr::Literal(20.0)),
    };
    assert_eq!(model.eval_expr(&if_false, &state, 0), 20.0);
}

#[test]
fn test_eval_nested_expression() {
    let model = empty_model();
    let mut state = SimulationState::new(2, 1, None);
    state.memo[0][0] = 10.0; // entity 0 = "a"
    state.memo[1][0] = 3.0; // entity 1 = "b"

    // (a * b) + 5.0 = (10 * 3) + 5 = 35
    let expr = Expr::BinaryOp {
        op: BinOp::Add,
        left: Box::new(Expr::BinaryOp {
            op: BinOp::Mul,
            left: Box::new(Expr::Ref(0)),
            right: Box::new(Expr::Ref(1)),
        }),
        right: Box::new(Expr::Literal(5.0)),
    };
    assert_eq!(model.eval_expr(&expr, &state, 0), 35.0);
}
