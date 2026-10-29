mod common;

use bptk_rust_engine::model::*;
use bptk_rust_engine::state::SimulationState;
use common::model_with_specs;

fn model_with_lookup(table_name: &str, points: Vec<(f64, f64)>) -> SdModel {
    let mut model = model_with_specs(0.0, 10.0, 1.0);
    model
        .graphical_functions
        .insert(table_name.to_string(), GraphicalFunction { points });
    model
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
        function: BuiltinFn::Lookup("rate_table".to_string(), LookupKind::Continuous),
        args: vec![Expr::Literal(25.0)],
    };
    assert!((model.eval_expr(&expr, &state, 0) - 7.5).abs() < 1e-10);
}

#[test]
fn test_lookup_inverse_interpolates_on_the_first_segment_that_reaches_the_value() {
    let model = model_with_lookup("table", vec![(0.0, 1.0), (2.0, 3.0), (4.0, 6.0)]);
    assert!((model.lookup_inverse("table", 2.0, LookupKind::Continuous) - 1.0).abs() < 1e-12);
    assert!((model.lookup_inverse("table", 4.5, LookupKind::Continuous) - 3.0).abs() < 1e-12);
    // A flat segment gives its left end
    let flat = model_with_lookup("flat", vec![(0.0, 0.0), (1.0, 2.0), (3.0, 2.0), (4.0, 5.0)]);
    assert_eq!(flat.lookup_inverse("flat", 2.0, LookupKind::Continuous), 1.0);
}

#[test]
fn test_lookup_inverse_beyond_the_table_gives_the_nearer_end_or_nan() {
    let rising = model_with_lookup("table", vec![(0.0, 1.0), (2.0, 3.0), (4.0, 6.0)]);
    assert_eq!(rising.lookup_inverse("table", -3.0, LookupKind::Continuous), 0.0);
    assert_eq!(rising.lookup_inverse("table", 30.0, LookupKind::Continuous), 4.0);
    let falling = model_with_lookup("table", vec![(0.0, 10.0), (5.0, 0.0)]);
    assert_eq!(falling.lookup_inverse("table", 20.0, LookupKind::Continuous), 0.0);
    let not_monotonic = model_with_lookup("table", vec![(0.0, 0.0), (1.0, 5.0), (2.0, 1.0)]);
    assert!(not_monotonic.lookup_inverse("table", 9.0, LookupKind::Continuous).is_nan());
}

#[test]
fn test_lookup_area_counts_nothing_beyond_the_ends() {
    let model = model_with_lookup("table", vec![(0.0, 1.0), (2.0, 3.0), (4.0, 6.0)]);
    assert!((model.lookup_area("table", 0.0, 4.0, LookupKind::Continuous) - 13.0).abs() < 1e-12);
    assert!((model.lookup_area("table", -5.0, 50.0, LookupKind::Continuous) - 13.0).abs() < 1e-12);
    assert!((model.lookup_area("table", 1.0, 3.0, LookupKind::Continuous) - 6.25).abs() < 1e-12);
    assert_eq!(model.lookup_area("table", 5.0, 9.0, LookupKind::Continuous), 0.0);
}

#[test]
fn test_lookup_area_turns_its_sign_when_from_is_above_to() {
    let model = model_with_lookup("table", vec![(0.0, 1.0), (2.0, 3.0), (4.0, 6.0)]);
    assert!((model.lookup_area("table", 3.0, 1.0, LookupKind::Continuous) + 6.25).abs() < 1e-12);
    assert!(model.lookup_area("table", f64::NAN, 1.0, LookupKind::Continuous).is_nan());
}

#[test]
fn test_lookup_inverse_and_area_of_an_unknown_table_read_zero() {
    // The parser refuses an unknown table; built some other way, the model reads 0.0
    let model = model_with_lookup("table", vec![(0.0, 1.0)]);
    assert_eq!(model.lookup_inverse("missing", 1.0, LookupKind::Continuous), 0.0);
    assert_eq!(model.lookup_area("missing", 0.0, 1.0, LookupKind::Continuous), 0.0);
}

#[test]
fn test_lookup_inverse_and_area_via_eval() {
    let model = model_with_lookup("table", vec![(0.0, 0.0), (10.0, 100.0)]);
    let state = SimulationState::new(0, 1, None);
    let inverse = Expr::Call {
        function: BuiltinFn::LookupInv("table".to_string(), LookupKind::Continuous),
        args: vec![Expr::Literal(25.0)],
    };
    let area = Expr::Call {
        function: BuiltinFn::LookupArea("table".to_string(), LookupKind::Continuous),
        args: vec![Expr::Literal(0.0), Expr::Literal(10.0)],
    };
    assert!((model.eval_expr(&inverse, &state, 0) - 2.5).abs() < 1e-12);
    assert!((model.eval_expr(&area, &state, 0) - 500.0).abs() < 1e-12);
}

#[test]
fn test_lookup_of_nan_gives_nan() {
    let model = model_with_lookup("table", vec![(0.0, 1.0), (2.0, 3.0)]);
    assert!(model.lookup_interpolate("table", f64::NAN).is_nan());
}

#[test]
fn test_the_three_kinds_of_table_as_stella_computes_them() {
    // Stella's run of the same table (`test_models/lookups`)
    let model = model_with_lookup("peak", vec![(2.0, 0.0), (4.0, 5.0), (6.0, 20.0), (8.0, 10.0), (10.0, 0.0)]);
    for (x, continuous, extrapolate, discrete) in [
        (-3.0, 0.0, -12.5, 0.0),
        (3.0, 2.5, 2.5, 0.0),
        (4.0, 5.0, 5.0, 5.0),
        (5.0, 12.5, 12.5, 5.0),
        (11.0, 0.0, -5.0, 0.0),
    ] {
        assert!((model.lookup("peak", x, LookupKind::Continuous) - continuous).abs() < 1e-12);
        assert!((model.lookup("peak", x, LookupKind::Extrapolate) - extrapolate).abs() < 1e-12);
        assert!((model.lookup("peak", x, LookupKind::Discrete) - discrete).abs() < 1e-12);
    }
    assert!(model.lookup("peak", f64::NAN, LookupKind::Discrete).is_nan());
    assert_eq!(model.lookup("missing", 1.0, LookupKind::Discrete), 0.0);
    let single = model_with_lookup("one", vec![(3.0, 7.0)]);
    assert_eq!(single.lookup("one", 9.0, LookupKind::Extrapolate), 7.0);
}

#[test]
fn test_the_inverse_and_the_area_of_each_kind() {
    // Stella's run of the same tables (`test_models/lookup_kinds`)
    let rising = model_with_lookup("rising", vec![(0.0, 0.0), (2.0, 1.0), (4.0, 4.0), (6.0, 9.0), (8.0, 16.0)]);
    assert!((rising.lookup_inverse("rising", -2.0, LookupKind::Extrapolate) + 4.0).abs() < 1e-12);
    assert!((rising.lookup_inverse("rising", 20.0, LookupKind::Extrapolate) - 64.0 / 7.0).abs() < 1e-12);
    assert!((rising.lookup_area("rising", -2.0, 1.0, LookupKind::Extrapolate) + 0.75).abs() < 1e-12);
    assert!((rising.lookup_area("rising", f64::NEG_INFINITY, f64::INFINITY, LookupKind::Extrapolate) - 44.0).abs() < 1e-12);
    let steps = model_with_lookup("steps", vec![(0.0, 0.0), (2.0, 1.0), (4.0, 4.0), (6.0, 9.0), (8.0, 9.0)]);
    assert!((steps.lookup_inverse("steps", 2.0, LookupKind::Discrete) - 8.0 / 3.0).abs() < 1e-12);
    assert!((steps.lookup_area("steps", -2.0, 7.0, LookupKind::Discrete) - 19.0).abs() < 1e-12);
    assert!((steps.lookup_area("steps", 7.0, -2.0, LookupKind::Discrete) + 19.0).abs() < 1e-12);
    // A flat end segment cannot be followed: the inverse stays at the end
    let flat = model_with_lookup("flat", vec![(0.0, 0.0), (2.0, 4.0), (4.0, 4.0)]);
    assert_eq!(flat.lookup_inverse("flat", 9.0, LookupKind::Extrapolate), 4.0);
}

#[test]
fn test_lookup_statistics_as_stella_computes_them() {
    // Stella's runs of the same tables (`test_models/stella_extras`)
    let shape = model_with_lookup("shape", vec![(2.0, 0.0), (4.0, 5.0), (6.0, 20.0), (8.0, 10.0), (10.0, 0.0)]);
    let (all, low, high) = (f64::NEG_INFINITY, 3.0, 5.0);
    let at = |statistic, from, to| shape.lookup_statistic("shape", statistic, from, to, LookupKind::Continuous);
    assert_eq!(at(LookupStatistic::Max, all, f64::INFINITY), 20.0);
    assert_eq!(at(LookupStatistic::Min, all, f64::INFINITY), 0.0);
    // Either order, and the interpolated ends of the range
    assert_eq!(at(LookupStatistic::Max, high, low), 12.5);
    assert_eq!(at(LookupStatistic::Min, low, high), 2.5);
    assert!((at(LookupStatistic::Mean, all, f64::INFINITY) - 44.0 / 7.0).abs() < 1e-12);
    assert!((at(LookupStatistic::Mean, all, 8.0) - 35.0 / 6.0).abs() < 1e-12);
    assert!((at(LookupStatistic::Mean, 8.0, 4.0) - 67.0 / 11.0).abs() < 1e-12);
    // A range ending inside a segment takes that piece's own middle; Stella gives 2.45
    assert!((at(LookupStatistic::Mean, low, high) - 4.2).abs() < 1e-12);
}

#[test]
fn test_lookup_statistics_at_the_edges() {
    let model = model_with_lookup("table", vec![(0.0, 1.0), (2.0, 3.0), (4.0, 0.0)]);
    let stat = |statistic, from, to, kind| model.lookup_statistic("table", statistic, from, to, kind);
    // Beyond the ends max and min read the table as lookup does; the mean counts nothing there
    assert_eq!(stat(LookupStatistic::Max, 5.0, 9.0, LookupKind::Continuous), 0.0);
    assert_eq!(stat(LookupStatistic::Min, -9.0, -5.0, LookupKind::Extrapolate), -8.0);
    assert!(stat(LookupStatistic::Mean, 5.0, 9.0, LookupKind::Continuous).is_nan());
    assert_eq!(stat(LookupStatistic::Max, 1.0, 1.0, LookupKind::Continuous), 2.0);
    // A discrete table's steps are steps: on 0 to 2 its value is 1, on 2 to 4 it is 3
    assert!((stat(LookupStatistic::Mean, 0.0, 4.0, LookupKind::Discrete) - 2.5).abs() < 1e-12);
    assert_eq!(stat(LookupStatistic::Max, 0.0, 1.9, LookupKind::Discrete), 1.0);
    assert!(stat(LookupStatistic::Max, f64::NAN, 1.0, LookupKind::Continuous).is_nan());
    assert_eq!(stat(LookupStatistic::Max, 0.0, 1.0, LookupKind::Continuous), 2.0);
    assert_eq!(model.lookup_statistic("missing", LookupStatistic::Mean, 0.0, 1.0, LookupKind::Continuous), 0.0);
}

#[test]
fn test_lookup_statistics_via_eval() {
    let model = model_with_lookup("table", vec![(0.0, 0.0), (10.0, 100.0)]);
    let state = SimulationState::new(0, 1, None);
    for (function, expected) in [
        (BuiltinFn::LookupMax("table".to_string(), LookupKind::Continuous), 50.0),
        (BuiltinFn::LookupMin("table".to_string(), LookupKind::Continuous), 0.0),
        // One segment, uniform within itself: its middle, whatever its slope
        (BuiltinFn::LookupMean("table".to_string(), LookupKind::Continuous), 2.5),
    ] {
        let call = Expr::Call { function, args: vec![Expr::Literal(0.0), Expr::Literal(5.0)] };
        assert!((model.eval_expr(&call, &state, 0) - expected).abs() < 1e-12);
    }
}

#[test]
fn test_lookuprandom_draws_each_segment_by_its_area_and_uniformly_within_it() {
    // A triangle: the four segments hold 1/8, 3/8, 3/8 and 1/8, each uniform within itself
    let model = model_with_lookup("pdf", vec![(0.0, 0.0), (1.0, 1.0), (2.0, 2.0), (3.0, 1.0), (4.0, 0.0)]);
    let state = SimulationState::new(0, 1, Some(11));
    let draw = Expr::Call { function: BuiltinFn::LookupRandom("pdf".to_string(), LookupKind::Continuous), args: vec![] };
    let draws: Vec<f64> = (0..20000).map(|_| model.eval_expr(&draw, &state, 0)).collect();
    assert!(draws.iter().all(|&x| (0.0..=4.0).contains(&x)));
    let first = draws.iter().filter(|&&x| x < 1.0).count() as f64 / draws.len() as f64;
    let mean = draws.iter().sum::<f64>() / draws.len() as f64;
    assert!((first - 0.125).abs() < 0.01, "{}", first);
    assert!((mean - 2.0).abs() < 0.03, "{}", mean);
}

#[test]
fn test_lookuprandom_refuses_a_table_below_zero_or_without_area() {
    let state = SimulationState::new(0, 1, Some(1));
    let draw = |name: &str| Expr::Call { function: BuiltinFn::LookupRandom(name.to_string(), LookupKind::Continuous), args: vec![] };
    let negative = model_with_lookup("negative", vec![(0.0, 1.0), (1.0, -1.0), (2.0, 1.0)]);
    assert!(negative.eval_expr(&draw("negative"), &state, 0).is_nan());
    let flat = model_with_lookup("flat", vec![(0.0, 0.0), (1.0, 0.0)]);
    assert!(flat.eval_expr(&draw("flat"), &state, 0).is_nan());
    assert_eq!(flat.eval_expr(&draw("missing"), &state, 0), 0.0);
    assert_eq!(state.take_invalid().len(), 1, "one record per entity");
}
