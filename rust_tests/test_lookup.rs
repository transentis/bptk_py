use std::collections::HashMap;

use bptk_rust_engine::model::*;
use bptk_rust_engine::state::SimulationState;

fn model_with_lookup(table_name: &str, points: Vec<(f64, f64)>) -> SdModel {
    let mut graphical_functions = HashMap::new();
    graphical_functions.insert(
        table_name.to_string(),
        GraphicalFunction { points },
    );
    SdModel {
        name: String::new(),
        starttime: 0.0,
        stoptime: 10.0,
        dt: 1.0,
        entities: Vec::new(),
        entity_index: HashMap::new(),
        graphical_functions,
        eval_order: Vec::new(),
    }
}

#[test]
fn test_lookup_exact_point() {
    let model = model_with_lookup("table", vec![(0.0, 5.0), (50.0, 10.0), (100.0, 5.0)]);
    assert_eq!(model.lookup_interpolate("table", 0.0), 5.0);
    assert_eq!(model.lookup_interpolate("table", 50.0), 10.0);
    assert_eq!(model.lookup_interpolate("table", 100.0), 5.0);
}

#[test]
fn test_lookup_interpolation() {
    let model = model_with_lookup("table", vec![(0.0, 0.0), (10.0, 100.0)]);
    // Midpoint: x=5 → y=50
    assert!((model.lookup_interpolate("table", 5.0) - 50.0).abs() < 1e-10);
    // Quarter: x=2.5 → y=25
    assert!((model.lookup_interpolate("table", 2.5) - 25.0).abs() < 1e-10);
}

#[test]
fn test_lookup_clamp_below() {
    let model = model_with_lookup("table", vec![(10.0, 5.0), (20.0, 10.0)]);
    // x < first point → clamp to first y
    assert_eq!(model.lookup_interpolate("table", 0.0), 5.0);
    assert_eq!(model.lookup_interpolate("table", -100.0), 5.0);
}

#[test]
fn test_lookup_clamp_above() {
    let model = model_with_lookup("table", vec![(10.0, 5.0), (20.0, 10.0)]);
    // x > last point → clamp to last y
    assert_eq!(model.lookup_interpolate("table", 30.0), 10.0);
    assert_eq!(model.lookup_interpolate("table", 1000.0), 10.0);
}

#[test]
fn test_lookup_missing_table() {
    let model = model_with_lookup("table", vec![(0.0, 5.0)]);
    // Nonexistent table → 0.0
    assert_eq!(model.lookup_interpolate("nonexistent", 5.0), 0.0);
}

#[test]
fn test_lookup_multiple_segments() {
    let model = model_with_lookup(
        "table",
        vec![(0.0, 0.0), (10.0, 10.0), (20.0, 5.0), (30.0, 15.0)],
    );
    // In first segment: x=5 → y=5
    assert!((model.lookup_interpolate("table", 5.0) - 5.0).abs() < 1e-10);
    // In second segment: x=15 → y=7.5
    assert!((model.lookup_interpolate("table", 15.0) - 7.5).abs() < 1e-10);
    // In third segment: x=25 → y=10
    assert!((model.lookup_interpolate("table", 25.0) - 10.0).abs() < 1e-10);
}

#[test]
fn test_lookup_via_eval() {
    let model = model_with_lookup(
        "rate_table",
        vec![(0.0, 5.0), (50.0, 10.0), (100.0, 5.0)],
    );
    let state = SimulationState::new(0, 1, None);

    // lookup(25.0, "rate_table") → interpolate between (0,5) and (50,10) → 7.5
    let expr = Expr::Call {
        function: BuiltinFn::Lookup("rate_table".to_string()),
        args: vec![Expr::Literal(25.0)],
    };
    assert!((model.eval_expr(&expr, &state, 0) - 7.5).abs() < 1e-10);
}
