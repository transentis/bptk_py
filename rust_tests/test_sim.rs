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
