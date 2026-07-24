use bptk_rust_engine::json_parser::parse_json;

#[test]
fn test_constant_model() {
    let json = r#"{
        "name": "constant",
        "specs": { "starttime": 0.0, "stoptime": 5.0, "dt": 1.0 },
        "entities": {
            "constants": [
                { "name": "x", "equation": { "type": "literal", "value": 42.0 } }
            ]
        }
    }"#;

    let model = parse_json(json).unwrap();
    let results = model.simulate(&["x".to_string()], None);

    let x = &results["x"];
    // 6 timesteps: 0,1,2,3,4,5
    assert_eq!(x.len(), 6);
    for step in 0..=5 {
        let t = format!("{:.1}", step as f64);
        assert_eq!(x[&t], 42.0, "t={}", t);
    }
}

#[test]
fn test_linear_growth() {
    // Stock with constant inflow of 10 per timestep.
    // stock(0)=0, stock(t) = 0 + 10*t
    let json = r#"{
        "name": "linear",
        "specs": { "starttime": 0.0, "stoptime": 5.0, "dt": 1.0 },
        "entities": {
            "stocks": [
                {
                    "name": "level",
                    "initial_value": { "type": "literal", "value": 0.0 },
                    "equation": { "type": "ref", "name": "inflow" }
                }
            ],
            "flows": [
                {
                    "name": "inflow",
                    "equation": { "type": "literal", "value": 10.0 }
                }
            ]
        }
    }"#;

    let model = parse_json(json).unwrap();
    let results = model.simulate(&["level".to_string(), "inflow".to_string()], None);

    let level = &results["level"];
    // level(0)=0, level(1)=10, level(2)=20, ...
    for step in 0..=5 {
        let t = format!("{:.1}", step as f64);
        let expected = 10.0 * step as f64;
        assert!(
            (level[&t] - expected).abs() < 1e-10,
            "t={}: expected={}, got={}",
            t,
            expected,
            level[&t]
        );
    }
}

#[test]
fn test_exponential_growth() {
    // Stock grows by 10% each timestep.
    // stock(0)=100, flow = stock * 0.1
    // stock(t+1) = stock(t) + dt * stock(t) * 0.1 = stock(t) * 1.1
    let json = r#"{
        "name": "exponential",
        "specs": { "starttime": 0.0, "stoptime": 5.0, "dt": 1.0 },
        "entities": {
            "stocks": [
                {
                    "name": "population",
                    "initial_value": { "type": "literal", "value": 100.0 },
                    "equation": { "type": "ref", "name": "growth" }
                }
            ],
            "flows": [
                {
                    "name": "growth",
                    "equation": {
                        "type": "binary_op", "op": "mul",
                        "left": { "type": "ref", "name": "population" },
                        "right": { "type": "literal", "value": 0.1 }
                    }
                }
            ]
        }
    }"#;

    let model = parse_json(json).unwrap();
    let results = model.simulate(&["population".to_string()], None);

    let pop = &results["population"];
    let mut expected = 100.0;
    for step in 0..=5 {
        let t = format!("{:.1}", step as f64);
        assert!(
            (pop[&t] - expected).abs() < 1e-6,
            "t={}: expected={}, got={}",
            t,
            expected,
            pop[&t]
        );
        expected *= 1.1;
    }
}

#[test]
fn test_flow_non_negativity() {
    // Flow equation yields -10, but flows enforce max(0, val) → 0
    let json = r#"{
        "name": "non_neg",
        "specs": { "starttime": 0.0, "stoptime": 3.0, "dt": 1.0 },
        "entities": {
            "stocks": [
                {
                    "name": "level",
                    "initial_value": { "type": "literal", "value": 100.0 },
                    "equation": { "type": "ref", "name": "outflow" }
                }
            ],
            "flows": [
                {
                    "name": "outflow",
                    "equation": { "type": "literal", "value": -10.0 }
                }
            ]
        }
    }"#;

    let model = parse_json(json).unwrap();
    let results = model.simulate(&["level".to_string(), "outflow".to_string()], None);

    let outflow = &results["outflow"];
    // Flow should be clamped to 0
    for step in 0..=3 {
        let t = format!("{:.1}", step as f64);
        assert_eq!(outflow[&t], 0.0, "outflow at t={}", t);
    }

    let level = &results["level"];
    // Stock should remain at 100 since flow is 0
    for step in 0..=3 {
        let t = format!("{:.1}", step as f64);
        assert_eq!(level[&t], 100.0, "level at t={}", t);
    }
}

#[test]
fn test_sir_model() {
    let json = r#"{
        "name": "SIR",
        "specs": { "starttime": 0.0, "stoptime": 3.0, "dt": 1.0 },
        "entities": {
            "stocks": [
                {
                    "name": "susceptible",
                    "initial_value": { "type": "literal", "value": 990.0 },
                    "equation": {
                        "type": "unary_op", "op": "neg",
                        "operand": { "type": "ref", "name": "infection" }
                    }
                },
                {
                    "name": "infected",
                    "initial_value": { "type": "literal", "value": 10.0 },
                    "equation": {
                        "type": "binary_op", "op": "sub",
                        "left": { "type": "ref", "name": "infection" },
                        "right": { "type": "ref", "name": "recovery" }
                    }
                },
                {
                    "name": "recovered",
                    "initial_value": { "type": "literal", "value": 0.0 },
                    "equation": { "type": "ref", "name": "recovery" }
                }
            ],
            "flows": [
                {
                    "name": "infection",
                    "equation": {
                        "type": "binary_op", "op": "mul",
                        "left": {
                            "type": "binary_op", "op": "mul",
                            "left": { "type": "ref", "name": "contact_rate" },
                            "right": { "type": "ref", "name": "transmission_prob" }
                        },
                        "right": {
                            "type": "binary_op", "op": "mul",
                            "left": { "type": "ref", "name": "susceptible" },
                            "right": { "type": "ref", "name": "infected" }
                        }
                    }
                },
                {
                    "name": "recovery",
                    "equation": {
                        "type": "binary_op", "op": "div",
                        "left": { "type": "ref", "name": "infected" },
                        "right": { "type": "ref", "name": "duration" }
                    }
                }
            ],
            "constants": [
                { "name": "contact_rate", "equation": { "type": "literal", "value": 10.0 } },
                { "name": "transmission_prob", "equation": { "type": "literal", "value": 0.001 } },
                { "name": "duration", "equation": { "type": "literal", "value": 5.0 } }
            ]
        }
    }"#;

    let model = parse_json(json).unwrap();
    let results = model.simulate(&[
        "susceptible".to_string(),
        "infected".to_string(),
        "recovered".to_string(),
    ], None);

    let s = &results["susceptible"];
    let i = &results["infected"];
    let r = &results["recovered"];

    // t=0: initial values
    assert_eq!(s["0.0"], 990.0);
    assert_eq!(i["0.0"], 10.0);
    assert_eq!(r["0.0"], 0.0);

    // Conservation: S + I + R should always equal 1000
    for step in 0..=3 {
        let t = format!("{:.1}", step as f64);
        let total = s[&t] + i[&t] + r[&t];
        assert!(
            (total - 1000.0).abs() < 1e-6,
            "t={}: S+I+R={} (should be 1000)",
            t,
            total
        );
    }

    // Susceptible should decrease (infection happens)
    assert!(s["1.0"] < s["0.0"]);
}

#[test]
fn test_fractional_dt() {
    // Stock with inflow=10, dt=0.25
    // stock(t) = 0 + 10 * t (each step adds 10 * 0.25 = 2.5)
    let json = r#"{
        "name": "fractional_dt",
        "specs": { "starttime": 0.0, "stoptime": 2.0, "dt": 0.25 },
        "entities": {
            "stocks": [
                {
                    "name": "level",
                    "initial_value": { "type": "literal", "value": 0.0 },
                    "equation": { "type": "ref", "name": "inflow" }
                }
            ],
            "flows": [
                {
                    "name": "inflow",
                    "equation": { "type": "literal", "value": 10.0 }
                }
            ]
        }
    }"#;

    let model = parse_json(json).unwrap();
    let results = model.simulate(&["level".to_string()], None);

    let level = &results["level"];
    // 9 timesteps: 0.0, 0.25, 0.5, ..., 2.0
    assert_eq!(level.len(), 9);
    assert_eq!(level["0.0"], 0.0);
    assert!((level["0.5"] - 5.0).abs() < 1e-10);
    assert!((level["1.0"] - 10.0).abs() < 1e-10);
    assert!((level["2.0"] - 20.0).abs() < 1e-10);
}

#[test]
fn test_set_runspecs() {
    // Load model with starttime=0, stoptime=5, dt=1, then override to starttime=0, stoptime=3, dt=0.5
    let json = r#"{
        "name": "runspecs_test",
        "specs": { "starttime": 0.0, "stoptime": 5.0, "dt": 1.0 },
        "entities": {
            "stocks": [
                {
                    "name": "level",
                    "initial_value": { "type": "literal", "value": 100.0 },
                    "equation": { "type": "ref", "name": "inflow" }
                }
            ],
            "flows": [
                {
                    "name": "inflow",
                    "equation": { "type": "literal", "value": 10.0 }
                }
            ]
        }
    }"#;

    let mut model = parse_json(json).unwrap();

    // Override runspecs
    model.set_runspecs(0.0, 3.0, 0.5);

    let results = model.simulate(&["level".to_string()], None);
    let level = &results["level"];

    // With dt=0.5 and stoptime=3.0: 7 timesteps (0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0)
    assert_eq!(level.len(), 7);
    assert_eq!(level["0.0"], 100.0);
    // Each step adds 10 * 0.5 = 5.0
    assert!((level["0.5"] - 105.0).abs() < 1e-10);
    assert!((level["1.0"] - 110.0).abs() < 1e-10);
    assert!((level["3.0"] - 130.0).abs() < 1e-10);
}

#[test]
fn test_nonzero_starttime() {
    let json = r#"{
        "name": "nonzero_start",
        "specs": { "starttime": 5.0, "stoptime": 8.0, "dt": 1.0 },
        "entities": {
            "stocks": [
                {
                    "name": "level",
                    "initial_value": { "type": "literal", "value": 100.0 },
                    "equation": { "type": "ref", "name": "inflow" }
                }
            ],
            "flows": [
                {
                    "name": "inflow",
                    "equation": { "type": "literal", "value": 5.0 }
                }
            ]
        }
    }"#;

    let model = parse_json(json).unwrap();
    let results = model.simulate(&["level".to_string()], None);

    let level = &results["level"];
    assert_eq!(level.len(), 4); // t=5,6,7,8
    assert_eq!(level["5.0"], 100.0);
    assert_eq!(level["6.0"], 105.0);
    assert_eq!(level["7.0"], 110.0);
    assert_eq!(level["8.0"], 115.0);
}

// ---------------------------------------------------------------------------
// Substep 4a: tests targeting the new init / step / run_to_end / extract_results
// decomposition. simulate() composes all of these — these tests pin down each
// piece independently so a regression in any one surfaces with a clear cause.
// ---------------------------------------------------------------------------

use bptk_rust_engine::sim::StepError;

/// Helper: parse a small "linear growth" model (stock with constant inflow 10)
/// used by the cursor-mechanics tests below.
fn linear_growth_model() -> bptk_rust_engine::model::SdModel {
    let json = r#"{
        "name": "linear",
        "specs": { "starttime": 0.0, "stoptime": 5.0, "dt": 1.0 },
        "entities": {
            "stocks": [
                {
                    "name": "level",
                    "initial_value": { "type": "literal", "value": 0.0 },
                    "equation": { "type": "ref", "name": "inflow" }
                }
            ],
            "flows": [
                { "name": "inflow", "equation": { "type": "literal", "value": 10.0 } }
            ]
        }
    }"#;
    parse_json(json).unwrap()
}

#[test]
fn test_init_returns_at_step_zero() {
    // After init(), current_step must be 0, step 0 must be evaluated (level=0,
    // inflow=10), and step 1's stock must be pre-integrated (level=10).
    let model = linear_growth_model();
    let state = model.init(None);

    assert_eq!(state.current_step, 0);

    let level_idx = model.entity_index["level"];
    let inflow_idx = model.entity_index["inflow"];

    // Step 0 values
    assert_eq!(state.memo[level_idx][0], 0.0);
    assert_eq!(state.memo[inflow_idx][0], 10.0);

    // Stock for step 1 must already be Euler-integrated (level(1) = 0 + 1*10 = 10).
    assert_eq!(state.memo[level_idx][1], 10.0);
}

#[test]
fn test_step_advances_cursor_by_one() {
    let model = linear_growth_model();
    let mut state = model.init(None);
    assert_eq!(state.current_step, 0);

    model.step(&mut state).expect("step 1 should succeed");
    assert_eq!(state.current_step, 1);

    let level_idx = model.entity_index["level"];
    // After step() we've evaluated non-stocks at step 1 (inflow=10) and
    // integrated stocks into step 2 (level(2) = 10 + 10 = 20).
    assert_eq!(state.memo[level_idx][1], 10.0);
    assert_eq!(state.memo[level_idx][2], 20.0);
}

#[test]
fn test_step_past_stoptime_returns_error() {
    // num_steps = 6 (t = 0..5). After init() we're at cursor 0; 5 more step()
    // calls bring us to cursor 5; the sixth must return PastStoptime.
    let model = linear_growth_model();
    let mut state = model.init(None);

    for _ in 0..5 {
        model.step(&mut state).expect("within bounds");
    }
    assert_eq!(state.current_step, 5);

    let err = model.step(&mut state).expect_err("past stoptime");
    assert!(matches!(err, StepError::PastStoptime));
    // Cursor stays put on error.
    assert_eq!(state.current_step, 5);
}

#[test]
fn test_manual_stepping_matches_simulate() {
    // The defining safety net for the decomposition: walking init() + step()
    // by hand must produce a memo identical to the one simulate() composes.
    let model = linear_growth_model();

    let mut hand = model.init(None);
    while hand.current_step + 1 < hand.memo[0].len() {
        model.step(&mut hand).expect("within bounds");
    }

    // Build the reference state by re-running simulate() via the same primitives.
    let mut auto = model.init(None);
    model.run_to_end(&mut auto);

    assert_eq!(hand.memo, auto.memo);
    assert_eq!(hand.current_step, auto.current_step);

    // And both must agree with simulate()'s extracted results.
    let extracted = model.extract_results(&hand, &["level".to_string(), "inflow".to_string()]);
    let from_simulate = model.simulate(&["level".to_string(), "inflow".to_string()], None);
    assert_eq!(extracted, from_simulate);
}

#[test]
fn test_run_to_end_after_init() {
    let model = linear_growth_model();
    let mut state = model.init(None);
    assert_eq!(state.current_step, 0);

    model.run_to_end(&mut state);
    assert_eq!(state.current_step, 5);

    let level_idx = model.entity_index["level"];
    assert_eq!(state.memo[level_idx][0], 0.0);
    assert_eq!(state.memo[level_idx][5], 50.0);
}

#[test]
fn test_extract_results_filters_requested_equations() {
    // Only requested equations should appear in the output; unknown names are
    // silently dropped (matches simulate()'s pre-refactor behaviour).
    let model = linear_growth_model();
    let mut state = model.init(None);
    model.run_to_end(&mut state);

    let only_level = model.extract_results(&state, &["level".to_string()]);
    assert_eq!(only_level.len(), 1);
    assert!(only_level.contains_key("level"));
    assert!(!only_level.contains_key("inflow"));

    let unknown = model.extract_results(&state, &["does_not_exist".to_string()]);
    assert!(unknown.is_empty());

    let both = model.extract_results(
        &state,
        &["level".to_string(), "inflow".to_string()],
    );
    assert_eq!(both.len(), 2);
    // Series length matches num_steps for the requested equations.
    assert_eq!(both["level"].len(), 6);
    assert_eq!(both["inflow"].len(), 6);
}

#[test]
fn test_single_step_run_handles_no_integration() {
    // starttime == stoptime: num_steps = 1. init() must NOT try to integrate
    // (there is no step 1 to integrate into), and the very first step() must
    // immediately return PastStoptime.
    let json = r#"{
        "name": "single",
        "specs": { "starttime": 0.0, "stoptime": 0.0, "dt": 1.0 },
        "entities": {
            "stocks": [
                {
                    "name": "level",
                    "initial_value": { "type": "literal", "value": 7.0 },
                    "equation": { "type": "literal", "value": 99.0 }
                }
            ]
        }
    }"#;
    let model = parse_json(json).unwrap();
    let mut state = model.init(None);

    assert_eq!(state.memo[0].len(), 1);
    assert_eq!(state.current_step, 0);

    let level_idx = model.entity_index["level"];
    assert_eq!(state.memo[level_idx][0], 7.0);

    let err = model.step(&mut state).expect_err("past stoptime");
    assert!(matches!(err, StepError::PastStoptime));
}
