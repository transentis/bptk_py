mod common;

use bptk_rust_engine::json_parser::parse_json;
use bptk_rust_engine::json_parser::ParseError;
use bptk_rust_engine::model::*;
use common::load_error;

#[test]
fn test_parse_minimal_model() {
    let json = r#"{
        "name": "minimal",
        "specs": { "starttime": 0.0, "stoptime": 10.0, "dt": 1.0 },
        "entities": {
            "constants": [
                { "name": "x", "equation": { "type": "literal", "value": 42.0 } }
            ]
        }
    }"#;

    let model = parse_json(json).unwrap();
    assert_eq!(model.name, "minimal");
    assert_eq!(model.starttime, 0.0);
    assert_eq!(model.stoptime, 10.0);
    assert_eq!(model.dt, 1.0);
    assert_eq!(model.entities.len(), 1);
    assert_eq!(model.entities[0].name, "x");
    assert!(matches!(model.entities[0].kind, EntityKind::Constant));
    assert!(matches!(model.entities[0].equation, Expr::Literal(v) if v == 42.0));
}

#[test]
fn test_parse_sir_model() {
    let json = r#"{
        "name": "SIR",
        "specs": { "starttime": 0.0, "stoptime": 100.0, "dt": 1.0 },
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
    assert_eq!(model.name, "SIR");
    assert_eq!(model.entities.len(), 8); // 3 stocks + 2 flows + 3 constants

    // Verify entity index
    assert_eq!(*model.entity_index.get("susceptible").unwrap(), 0);
    assert_eq!(*model.entity_index.get("infected").unwrap(), 1);
    assert_eq!(*model.entity_index.get("recovered").unwrap(), 2);
    assert_eq!(*model.entity_index.get("infection").unwrap(), 3);
    assert_eq!(*model.entity_index.get("recovery").unwrap(), 4);

    // Verify stocks have proper initial values
    if let EntityKind::Stock { ref initial_value } = model.entities[0].kind {
        assert!(matches!(initial_value, Expr::Literal(v) if *v == 990.0));
    } else {
        panic!("Expected Stock");
    }

    // Verify eval_order contains all 5 non-stock entities
    assert_eq!(model.eval_order.len(), 5);
}

#[test]
fn test_parse_invalid_json() {
    let result = parse_json("not json");
    assert!(result.is_err());
}

#[test]
fn test_parse_unknown_entity_ref() {
    let json = r#"{
        "name": "bad",
        "specs": { "starttime": 0.0, "stoptime": 10.0, "dt": 1.0 },
        "entities": {
            "constants": [
                { "name": "x", "equation": { "type": "ref", "name": "nonexistent" } }
            ]
        }
    }"#;

    let result = parse_json(json);
    assert!(matches!(result, Err(ParseError::UnknownEntity(_))));
}

#[test]
fn test_parse_lookup_model() {
    let json = r#"{
        "name": "lookup_test",
        "specs": { "starttime": 0.0, "stoptime": 10.0, "dt": 1.0 },
        "entities": {
            "converters": [
                {
                    "name": "rate",
                    "equation": {
                        "type": "call",
                        "function": "lookup",
                        "args": [
                            { "type": "call", "function": "time", "args": [] },
                            { "type": "literal", "value": "rate_table" }
                        ]
                    }
                }
            ]
        },
        "graphical_functions": {
            "rate_table": {
                "points": [[0.0, 5.0], [50.0, 10.0], [100.0, 5.0]]
            }
        }
    }"#;

    let model = parse_json(json).unwrap();
    assert_eq!(model.entities.len(), 1);

    // Verify it parsed as Lookup builtin
    if let Expr::Call {
        ref function,
        ref args,
    } = model.entities[0].equation
    {
        assert!(matches!(function, BuiltinFn::Lookup(name) if name == "rate_table"));
        assert_eq!(args.len(), 1); // just the x-value arg
    } else {
        panic!("Expected Call expression");
    }

    // Verify graphical function
    assert!(model.graphical_functions.contains_key("rate_table"));
    assert_eq!(model.graphical_functions["rate_table"].points.len(), 3);
}

#[test]
fn test_parse_if_expression() {
    let json = r#"{
        "name": "if_test",
        "specs": { "starttime": 0.0, "stoptime": 10.0, "dt": 1.0 },
        "entities": {
            "constants": [
                { "name": "threshold", "equation": { "type": "literal", "value": 50.0 } },
                {
                    "name": "result",
                    "equation": {
                        "type": "if",
                        "condition": {
                            "type": "binary_op", "op": "gt",
                            "left": { "type": "ref", "name": "threshold" },
                            "right": { "type": "literal", "value": 25.0 }
                        },
                        "then": { "type": "literal", "value": 1.0 },
                        "else": { "type": "literal", "value": 0.0 }
                    }
                }
            ]
        }
    }"#;

    let model = parse_json(json).unwrap();
    assert_eq!(model.entities.len(), 2);

    if let Expr::If { .. } = &model.entities[1].equation {
        // ok
    } else {
        panic!("Expected If expression");
    }
}

#[test]
fn test_topological_sort_order() {
    // c depends on b, b depends on a. Correct order: a, b, c.
    let json = r#"{
        "name": "topo_test",
        "specs": { "starttime": 0.0, "stoptime": 10.0, "dt": 1.0 },
        "entities": {
            "constants": [
                { "name": "a", "equation": { "type": "literal", "value": 1.0 } },
                {
                    "name": "b",
                    "equation": {
                        "type": "binary_op", "op": "mul",
                        "left": { "type": "ref", "name": "a" },
                        "right": { "type": "literal", "value": 2.0 }
                    }
                },
                {
                    "name": "c",
                    "equation": {
                        "type": "binary_op", "op": "add",
                        "left": { "type": "ref", "name": "b" },
                        "right": { "type": "literal", "value": 3.0 }
                    }
                }
            ]
        }
    }"#;

    let model = parse_json(json).unwrap();
    // a must come before b, b must come before c
    let a_pos = model
        .eval_order
        .iter()
        .position(|&i| model.entities[i].name == "a")
        .unwrap();
    let b_pos = model
        .eval_order
        .iter()
        .position(|&i| model.entities[i].name == "b")
        .unwrap();
    let c_pos = model
        .eval_order
        .iter()
        .position(|&i| model.entities[i].name == "c")
        .unwrap();
    assert!(a_pos < b_pos);
    assert!(b_pos < c_pos);
}

// ── Feedback loops and the two-pass topological sort ────────────────────────
//
// Non-stock entities are evaluated eagerly once per timestep in a precomputed
// order, so a loop is only solvable if something in it reads a past value: a stock
// (integrated in the previous step) or a `delay` (reads memo[step - delay_steps]).

fn loop_model_json(delay_duration: &str) -> String {
    format!(r#"{{
        "name": "delay_loop",
        "specs": {{ "starttime": 1.0, "stoptime": 5.0, "dt": 1.0 }},
        "entities": {{
            "converters": [
                {{ "name": "a", "equation": {{ "type": "binary_op", "op": "add",
                     "left": {{ "type": "ref", "name": "d" }},
                     "right": {{ "type": "literal", "value": 1.0 }} }} }},
                {{ "name": "d", "equation": {{ "type": "call", "function": "delay", "args": [
                     {{ "type": "ref", "name": "a" }},
                     {},
                     {{ "type": "literal", "value": 0.0 }} ] }} }}
            ]
        }}
    }}"#, delay_duration)
}

#[test]
fn test_loop_closed_by_delay_parses() {
    let json = loop_model_json(r#"{ "type": "literal", "value": 1.0 }"#);
    let model = parse_json(&json).expect("a loop broken by a one-step delay must load");
    // a(1)=1, then a(t) = a(t-1) + 1
    let results = model.simulate(&["a".to_string()], None).unwrap();
    let a = &results["a"];
    assert_eq!(a["1.0"], 1.0);
    assert_eq!(a["2.0"], 2.0);
    assert_eq!(a["5.0"], 5.0);
}

#[test]
fn test_loop_closed_by_delay_with_entity_duration_parses() {
    // Duration is a reference, so its value is unknown at load time and the loop can
    // only be broken by assuming it is at least one dt.
    let json = r#"{
        "name": "delay_loop_dyn",
        "specs": { "starttime": 1.0, "stoptime": 4.0, "dt": 1.0 },
        "entities": {
            "constants": [
                { "name": "duration", "equation": { "type": "literal", "value": 1.0 } }
            ],
            "converters": [
                { "name": "a", "equation": { "type": "binary_op", "op": "add",
                    "left": { "type": "ref", "name": "d" },
                    "right": { "type": "literal", "value": 1.0 } } },
                { "name": "d", "equation": { "type": "call", "function": "delay", "args": [
                    { "type": "ref", "name": "a" },
                    { "type": "ref", "name": "duration" },
                    { "type": "literal", "value": 0.0 } ] } }
            ]
        }
    }"#;
    parse_json(json).expect("an entity-valued delay duration must not block the sort");
}

#[test]
fn test_loop_closed_by_zero_duration_delay_is_rejected() {
    // delay(x, 0) reads the current step, so it breaks no loop.
    let json = loop_model_json(r#"{ "type": "literal", "value": 0.0 }"#);
    assert!(parse_json(&json).is_err(),
            "a loop whose delay has a literal zero duration must stay rejected");
}

#[test]
fn test_algebraic_loop_is_rejected() {
    let json = r#"{
        "name": "algebraic_loop",
        "specs": { "starttime": 1.0, "stoptime": 5.0, "dt": 1.0 },
        "entities": {
            "converters": [
                { "name": "a", "equation": { "type": "binary_op", "op": "add",
                    "left": { "type": "ref", "name": "b" },
                    "right": { "type": "literal", "value": 1.0 } } },
                { "name": "b", "equation": { "type": "binary_op", "op": "mul",
                    "left": { "type": "ref", "name": "a" },
                    "right": { "type": "literal", "value": 2.0 } } }
            ]
        }
    }"#;
    assert!(parse_json(json).is_err(), "a loop with no time offset must be rejected");
}

// ── Thread safety of the handles the Python layer keeps alive ───────────────
//
// A threaded WSGI server serves consecutive requests on different threads while the
// runner caches the model handle on the Scenario, so these types must be Send+Sync.
// PyO3 0.24 enforces it for #[pyclass]; this pins it at the Rust level so a future
// RefCell cannot silently reintroduce the crash.

#[test]
fn test_model_and_state_are_send_and_sync() {
    fn assert_send_sync<T: Send + Sync>() {}
    assert_send_sync::<bptk_rust_engine::model::SdModel>();
    assert_send_sync::<bptk_rust_engine::state::SimulationState>();
}

#[test]
fn test_state_can_be_stepped_from_another_thread() {
    let json = loop_model_json(r#"{ "type": "literal", "value": 1.0 }"#);
    let model = parse_json(&json).unwrap();
    let mut state = model.init(None).unwrap();

    // Move model and state into a second thread and continue stepping there.
    let handle = std::thread::spawn(move || {
        model.step(&mut state).unwrap();
        model.step(&mut state).unwrap();
        state.memo[0][state.current_step]
    });
    let value = handle.join().expect("stepping in another thread must not panic");
    assert!(value.is_finite());
}

// ── Edge cases of the two-pass sort ─────────────────────────────────────────

#[test]
fn test_loop_delay_duration_rounding_to_zero_is_rejected() {
    // 0.4 / dt 1.0 rounds to 0 steps, so this delay reads the current step and
    // breaks no loop, even though the literal is not exactly 0.
    let json = loop_model_json(r#"{ "type": "literal", "value": 0.4 }"#);
    assert!(parse_json(&json).is_err(),
            "a duration rounding to zero steps must not be treated as a loop breaker");
}

#[test]
fn test_loop_delay_duration_rounding_to_one_parses() {
    // 0.6 / dt 1.0 rounds to 1 step.
    let json = loop_model_json(r#"{ "type": "literal", "value": 0.6 }"#);
    parse_json(&json).expect("a duration rounding to one step breaks the loop");
}

#[test]
fn test_loop_with_delay_nested_in_expression_parses() {
    // The delay does not sit at the root of the equation: it is nested inside an
    // `if` inside a binary op, so the edge-skipping has to work at any depth.
    let json = r#"{
        "name": "nested_delay_loop",
        "specs": { "starttime": 1.0, "stoptime": 5.0, "dt": 1.0 },
        "entities": {
            "converters": [
                { "name": "a", "equation": { "type": "binary_op", "op": "add",
                    "left": { "type": "ref", "name": "d" },
                    "right": { "type": "literal", "value": 1.0 } } },
                { "name": "d", "equation": { "type": "binary_op", "op": "mul",
                    "left": { "type": "literal", "value": 1.0 },
                    "right": { "type": "if",
                        "condition": { "type": "binary_op", "op": "gt",
                            "left": { "type": "call", "function": "time", "args": [] },
                            "right": { "type": "literal", "value": 0.0 } },
                        "then": { "type": "call", "function": "delay", "args": [
                            { "type": "ref", "name": "a" },
                            { "type": "literal", "value": 1.0 },
                            { "type": "literal", "value": 0.0 } ] },
                        "else": { "type": "literal", "value": 0.0 } } } }
            ]
        }
    }"#;
    let model = parse_json(json).expect("a nested delay must still break the loop");
    let results = model.simulate(&["a".to_string()], None).unwrap();
    assert_eq!(results["a"]["1.0"], 1.0);
    assert_eq!(results["a"]["3.0"], 3.0);
}

#[test]
fn test_two_independent_delay_loops_parse() {
    // The beergame has one such loop per supply chain stage (wholesaler and
    // distributor), so more than one broken cycle must be orderable at once.
    let json = r#"{
        "name": "two_delay_loops",
        "specs": { "starttime": 1.0, "stoptime": 4.0, "dt": 1.0 },
        "entities": {
            "converters": [
                { "name": "a1", "equation": { "type": "binary_op", "op": "add",
                    "left": { "type": "ref", "name": "d1" },
                    "right": { "type": "literal", "value": 1.0 } } },
                { "name": "d1", "equation": { "type": "call", "function": "delay", "args": [
                    { "type": "ref", "name": "a1" },
                    { "type": "literal", "value": 1.0 },
                    { "type": "literal", "value": 0.0 } ] } },
                { "name": "a2", "equation": { "type": "binary_op", "op": "add",
                    "left": { "type": "ref", "name": "d2" },
                    "right": { "type": "literal", "value": 10.0 } } },
                { "name": "d2", "equation": { "type": "call", "function": "delay", "args": [
                    { "type": "ref", "name": "a2" },
                    { "type": "literal", "value": 1.0 },
                    { "type": "literal", "value": 0.0 } ] } }
            ]
        }
    }"#;
    let model = parse_json(json).expect("two delay-broken loops must both be ordered");
    let results = model.simulate(&["a1".to_string(), "a2".to_string()], None).unwrap();
    assert_eq!(results["a1"]["4.0"], 4.0);
    assert_eq!(results["a2"]["4.0"], 40.0);
}

#[test]
fn test_delay_loop_plus_algebraic_loop_is_rejected() {
    // The second pass must not turn a genuine algebraic loop into a valid order
    // just because some other loop in the model is delay-broken.
    let json = r#"{
        "name": "mixed_loops",
        "specs": { "starttime": 1.0, "stoptime": 4.0, "dt": 1.0 },
        "entities": {
            "converters": [
                { "name": "a", "equation": { "type": "binary_op", "op": "add",
                    "left": { "type": "ref", "name": "d" },
                    "right": { "type": "literal", "value": 1.0 } } },
                { "name": "d", "equation": { "type": "call", "function": "delay", "args": [
                    { "type": "ref", "name": "a" },
                    { "type": "literal", "value": 1.0 },
                    { "type": "literal", "value": 0.0 } ] } },
                { "name": "x", "equation": { "type": "binary_op", "op": "add",
                    "left": { "type": "ref", "name": "y" },
                    "right": { "type": "literal", "value": 1.0 } } },
                { "name": "y", "equation": { "type": "binary_op", "op": "mul",
                    "left": { "type": "ref", "name": "x" },
                    "right": { "type": "literal", "value": 2.0 } } }
            ]
        }
    }"#;
    assert!(parse_json(json).is_err(),
            "an algebraic loop must still be rejected next to a delay-broken one");
}

#[test]
fn test_loop_with_unary_op_in_the_cycle_parses() {
    // The second pass walks unary operators too — without that arm the ref to `d`
    // inside the negation would be missed and the ordering would be wrong.
    let json = r#"{
        "name": "unary_delay_loop",
        "specs": { "starttime": 1.0, "stoptime": 4.0, "dt": 1.0 },
        "entities": {
            "converters": [
                { "name": "a", "equation": { "type": "binary_op", "op": "add",
                    "left": { "type": "unary_op", "op": "neg",
                        "operand": { "type": "ref", "name": "d" } },
                    "right": { "type": "literal", "value": 1.0 } } },
                { "name": "d", "equation": { "type": "call", "function": "delay", "args": [
                    { "type": "ref", "name": "a" },
                    { "type": "literal", "value": 1.0 },
                    { "type": "literal", "value": 2.0 } ] } }
            ]
        }
    }"#;
    let model = parse_json(json).expect("a cycle through a unary op must be orderable");
    let results = model.simulate(&["a".to_string(), "d".to_string()], None).unwrap();
    // t=1: d = initial 2 -> a = -2 + 1 = -1 ; t=2: d = a(1) = -1 -> a = 1 + 1 = 2
    assert_eq!(results["a"]["1.0"], -1.0);
    assert_eq!(results["a"]["2.0"], 2.0);
}

// ── Naming the cycle in the error message ───────────────────────────────────
//
// A rejected model should say *which* equations form the loop. Finding that out by
// hand cost real time during the beergame integration, and the engine has the graph
// in its hands anyway. Only computed on the definitive failure, so healthy models
// never pay for it.

#[test]
fn test_error_names_a_simple_cycle() {
    let json = r#"{
        "name": "simple_cycle",
        "specs": { "starttime": 1.0, "stoptime": 4.0, "dt": 1.0 },
        "entities": { "converters": [
            { "name": "a", "equation": { "type": "binary_op", "op": "add",
                "left": { "type": "ref", "name": "b" },
                "right": { "type": "literal", "value": 1.0 } } },
            { "name": "b", "equation": { "type": "binary_op", "op": "mul",
                "left": { "type": "ref", "name": "a" },
                "right": { "type": "literal", "value": 2.0 } } }
        ] }
    }"#;
    assert_eq!(
        load_error(json),
        "Cyclic dependency among non-stock entities: a → b → a");
}

#[test]
fn test_error_names_a_self_reference() {
    let json = r#"{
        "name": "self_cycle",
        "specs": { "starttime": 1.0, "stoptime": 4.0, "dt": 1.0 },
        "entities": { "converters": [
            { "name": "a", "equation": { "type": "binary_op", "op": "add",
                "left": { "type": "ref", "name": "a" },
                "right": { "type": "literal", "value": 1.0 } } }
        ] }
    }"#;
    assert_eq!(
        load_error(json),
        "Cyclic dependency among non-stock entities: a → a");
}

#[test]
fn test_error_keeps_the_order_of_a_longer_cycle() {
    // a ← c ← b ← a, so the path has to read a → c → b → a
    let json = r#"{
        "name": "long_cycle",
        "specs": { "starttime": 1.0, "stoptime": 4.0, "dt": 1.0 },
        "entities": { "converters": [
            { "name": "a", "equation": { "type": "binary_op", "op": "add",
                "left": { "type": "ref", "name": "c" },
                "right": { "type": "literal", "value": 1.0 } } },
            { "name": "b", "equation": { "type": "binary_op", "op": "mul",
                "left": { "type": "ref", "name": "a" },
                "right": { "type": "literal", "value": 2.0 } } },
            { "name": "c", "equation": { "type": "binary_op", "op": "add",
                "left": { "type": "ref", "name": "b" },
                "right": { "type": "literal", "value": 3.0 } } }
        ] }
    }"#;
    assert_eq!(
        load_error(json),
        "Cyclic dependency among non-stock entities: a → c → b → a");
}

#[test]
fn test_error_names_every_independent_cycle() {
    let json = r#"{
        "name": "two_cycles",
        "specs": { "starttime": 1.0, "stoptime": 4.0, "dt": 1.0 },
        "entities": { "converters": [
            { "name": "a", "equation": { "type": "binary_op", "op": "add",
                "left": { "type": "ref", "name": "b" },
                "right": { "type": "literal", "value": 1.0 } } },
            { "name": "b", "equation": { "type": "binary_op", "op": "mul",
                "left": { "type": "ref", "name": "a" },
                "right": { "type": "literal", "value": 2.0 } } },
            { "name": "c", "equation": { "type": "binary_op", "op": "add",
                "left": { "type": "ref", "name": "d" },
                "right": { "type": "literal", "value": 1.0 } } },
            { "name": "d", "equation": { "type": "binary_op", "op": "mul",
                "left": { "type": "ref", "name": "c" },
                "right": { "type": "literal", "value": 2.0 } } }
        ] }
    }"#;
    assert_eq!(
        load_error(json),
        "Cyclic dependency among non-stock entities: a → b → a; c → d → c");
}

#[test]
fn test_error_names_the_shortest_path_and_the_group_size() {
    // A cycle a → b → a, plus e and f hanging in the same strongly connected group
    // via a second route a → e → f → b. The message shows the short path and says how
    // many entities the group has.
    let json = r#"{
        "name": "wide_cycle",
        "specs": { "starttime": 1.0, "stoptime": 4.0, "dt": 1.0 },
        "entities": { "converters": [
            { "name": "a", "equation": { "type": "binary_op", "op": "add",
                "left": { "type": "ref", "name": "b" },
                "right": { "type": "ref", "name": "f" } } },
            { "name": "b", "equation": { "type": "binary_op", "op": "mul",
                "left": { "type": "ref", "name": "a" },
                "right": { "type": "literal", "value": 2.0 } } },
            { "name": "e", "equation": { "type": "ref", "name": "b" } },
            { "name": "f", "equation": { "type": "ref", "name": "e" } }
        ] }
    }"#;
    let message = load_error(json);
    assert!(message.contains("a → b → a"), "{}", message);
    assert!(message.contains("4 entities involved"), "{}", message);
}

#[test]
fn test_delay_broken_loop_produces_no_cycle_error() {
    // The naming must not fire for models that are fine.
    let json = loop_model_json(r#"{ "type": "literal", "value": 1.0 }"#);
    assert!(parse_json(&json).is_ok());
}

// An arrayed element reaches the engine as one entity per sub-element, so the sort sees
// `a[0]` and `a[1]` as two nodes. That is what makes a loop between two of them an
// error while one of them reading the other is an ordinary dependency.

#[test]
fn test_error_names_a_cycle_between_sub_elements_of_one_array() {
    let json = r#"{
        "name": "array_cycle",
        "specs": { "starttime": 0.0, "stoptime": 3.0, "dt": 1.0 },
        "entities": { "converters": [
            { "name": "a[0]", "equation": { "type": "binary_op", "op": "add",
                "left": { "type": "ref", "name": "a[1]" },
                "right": { "type": "literal", "value": 1.0 } } },
            { "name": "a[1]", "equation": { "type": "binary_op", "op": "mul",
                "left": { "type": "ref", "name": "a[0]" },
                "right": { "type": "literal", "value": 2.0 } } }
        ] }
    }"#;
    assert_eq!(
        load_error(json),
        "Cyclic dependency among non-stock entities: a[0] → a[1] → a[0]");
}

#[test]
fn test_a_sub_element_reading_its_neighbour_is_no_cycle() {
    let json = r#"{
        "name": "array_chain",
        "specs": { "starttime": 0.0, "stoptime": 3.0, "dt": 1.0 },
        "entities": { "converters": [
            { "name": "a[0]", "equation": { "type": "literal", "value": 5.0 } },
            { "name": "a[1]", "equation": { "type": "binary_op", "op": "add",
                "left": { "type": "ref", "name": "a[0]" },
                "right": { "type": "literal", "value": 1.0 } } }
        ] }
    }"#;
    let model = parse_json(json).expect("a sub-element reading another is no cycle");
    let results = model.simulate(&["a[1]".to_string()], None).unwrap();
    for step in 0..=3 {
        let t = format!("{:.1}", step as f64);
        assert_eq!(results["a[1]"][&t], 6.0, "t={}", t);
    }
}

// ── Python callbacks ────────────────────────────────────────────────────────

fn callback_model_json() -> String {
    r#"{
        "name": "callback",
        "specs": { "starttime": 0.0, "stoptime": 3.0, "dt": 1.0 },
        "entities": { "converters": [
            { "name": "source", "equation": { "type": "literal", "value": 2.0 } },
            { "name": "scaled", "equation": {
                "type": "py_callback", "name": "scale",
                "args": [ { "type": "ref", "name": "source" } ] } }
        ] }
    }"#
    .to_string()
}

#[test]
#[cfg(not(feature = "python"))]
fn test_a_callback_node_is_a_load_error_without_python() {
    // The same JSON loads in the extension module, so the message says what is missing
    // rather than calling the model invalid.
    let error = parse_json(&callback_model_json()).unwrap_err();
    let message = error.to_string();
    assert!(message.contains("scale"), "{}", message);
    assert!(message.contains("without Python"), "{}", message);
}

#[test]
#[cfg(feature = "python")]
fn test_a_callback_name_resolves_to_a_slot() {
    let model = parse_json(&callback_model_json()).unwrap();
    assert_eq!(model.callback_names, vec!["scale".to_string()]);
    // Unregistered until somebody registers it.
    assert!(model.callbacks.iter().all(Option::is_none));
}

#[test]
#[cfg(feature = "python")]
fn test_a_callback_argument_is_ordered_before_it() {
    // Without the argument's edge the engine would call Python with a cell that has not
    // been evaluated at this step yet.
    let model = parse_json(&callback_model_json()).unwrap();
    let source = model.entity_index["source"];
    let scaled = model.entity_index["scaled"];
    let position = |idx: usize| model.eval_order.iter().position(|&i| i == idx).unwrap();
    assert!(position(source) < position(scaled));
}

// ── Argument counts ─────────────────────────────────────────────────────────

fn call_model(call: &str) -> String {
    format!(
        r#"{{
        "name": "arity",
        "specs": {{ "starttime": 0.0, "stoptime": 3.0, "dt": 1.0 }},
        "entities": {{ "converters": [
            {{ "name": "src", "equation": {{ "type": "literal", "value": 1.0 }} }},
            {{ "name": "x", "equation": {} }}
        ] }}
    }}"#,
        call
    )
}

fn lit(value: f64) -> String {
    format!(r#"{{ "type": "literal", "value": {:?} }}"#, value)
}

fn call_of(function: &str, args: &[String]) -> String {
    format!(r#"{{ "type": "call", "function": "{}", "args": [{}] }}"#, function, args.join(", "))
}

#[test]
fn test_a_call_with_too_few_arguments_is_refused_at_load() {
    // The evaluator indexes its arguments; a short list used to panic mid-run.
    for (function, given, expected) in [
        ("normal", 1, "Function 'normal' takes 2 argument(s), and was given 1"),
        ("triangular", 2, "Function 'triangular' takes 3 argument(s), and was given 2"),
        ("sqrt", 0, "Function 'sqrt' takes 1 argument(s), and was given 0"),
        ("normalcdf", 1, "Function 'normalcdf' takes 2 to 4 argument(s), and was given 1"),
        ("arr_rank", 1, "Function 'arr_rank' takes at least 2 argument(s), and was given 1"),
    ] {
        let args: Vec<String> = (0..given).map(|_| lit(1.0)).collect();
        let message = match parse_json(&call_model(&call_of(function, &args))) {
            Ok(_) => panic!("{} with {} arguments loaded", function, given),
            Err(e) => e.to_string(),
        };
        assert_eq!(message, expected);
    }
}

#[test]
fn test_a_call_with_too_many_arguments_is_refused_at_load() {
    let message = match parse_json(&call_model(&call_of("time", &[lit(1.0)]))) {
        Ok(_) => panic!("time with an argument loaded"),
        Err(e) => e.to_string(),
    };
    assert_eq!(message, "Function 'time' takes no argument(s), and was given 1");
}

#[test]
fn test_optional_arguments_may_be_left_out() {
    for (function, given) in [("round", 1), ("gamma_dist", 1), ("pulse", 1), ("invnorm", 1),
                              ("normalcdf", 2), ("arr_sum", 0), ("arr_max", 5)] {
        let args: Vec<String> = (0..given).map(|_| lit(1.0)).collect();
        assert!(parse_json(&call_model(&call_of(function, &args))).is_ok(),
                "{} with {} arguments", function, given);
    }
}

#[test]
fn test_delay_of_something_other_than_an_element_is_refused_at_load() {
    // The first argument names whose past is read; a literal used to panic mid-run.
    let delay = call_of("delay", &[lit(1.0), lit(1.0), lit(0.0)]);
    let message = match parse_json(&call_model(&delay)) {
        Ok(_) => panic!("a delay of a literal loaded"),
        Err(e) => e.to_string(),
    };
    assert!(message.contains("first argument has to be a reference"), "{}", message);
    let delay = call_of("delay", &[r#"{ "type": "ref", "name": "src" }"#.to_string(),
                                   lit(1.0), lit(0.0)]);
    assert!(parse_json(&call_model(&delay)).is_ok());
}

// ── Names, strings and lookup tables ─────────────────────────────────────────

#[test]
fn test_two_entities_of_one_name_are_refused() {
    // The second used to replace the first in the index without a word.
    let message = load_error(r#"{
        "name": "twice",
        "specs": { "starttime": 0.0, "stoptime": 1.0, "dt": 1.0 },
        "entities": {
            "stocks": [ { "name": "a", "initial_value": { "type": "literal", "value": 0.0 } } ],
            "converters": [ { "name": "a", "equation": { "type": "literal", "value": 1.0 } } ]
        }
    }"#);
    assert_eq!(message, "The model has more than one entity named 'a'");
}

#[test]
fn test_a_string_where_a_number_belongs_is_refused() {
    // It used to be read as 0.0.
    let message = load_error(&call_model(r#"{ "type": "literal", "value": "ten" }"#));
    assert!(message.contains("\"ten\" stands where a number belongs"), "{}", message);
}

fn lookup_model(points: &str, table: &str) -> String {
    format!(
        r#"{{
        "name": "lookup",
        "specs": {{ "starttime": 0.0, "stoptime": 1.0, "dt": 1.0 }},
        "entities": {{ "converters": [
            {{ "name": "x", "equation": {{ "type": "call", "function": "lookup", "args": [
                {{ "type": "literal", "value": 2.5 }},
                {{ "type": "literal", "value": "{}" }} ] }} }}
        ] }},
        "graphical_functions": {{ "tab": {{ "points": {} }} }}
    }}"#,
        table, points
    )
}

#[test]
fn test_a_lookup_of_a_table_the_model_does_not_have_is_refused() {
    // It used to read 0.0 at every step.
    let message = load_error(&lookup_model("[[0.0, 0.0], [10.0, 100.0]]", "missing"));
    assert_eq!(message, "Lookup of a table the model does not have: 'missing'");
}

#[test]
fn test_a_lookup_without_a_table_name_is_refused() {
    let message = load_error(&call_model(&call_of("lookup", &[lit(1.0), lit(2.0)])));
    assert_eq!(message, "Function 'lookup' takes an input and the name of a table");
}

#[test]
fn test_lookup_points_in_any_order_describe_the_same_curve() {
    let model = parse_json(&lookup_model("[[10.0, 100.0], [0.0, 0.0], [5.0, 50.0]]", "tab")).unwrap();
    assert_eq!(model.graphical_functions["tab"].points, vec![(0.0, 0.0), (5.0, 50.0), (10.0, 100.0)]);
    assert_eq!(model.simulate(&["x".to_string()], None).unwrap()["x"]["0.0"], 25.0);
}

#[test]
fn test_lookup_points_that_are_no_table_are_refused() {
    for (points, expected) in [
        ("[[0.0, 0.0], [5.0, 10.0], [5.0, 90.0]]", "Lookup table 'tab' has two points at x=5.0"),
        ("[]", "Lookup table 'tab' has no points"),
    ] {
        assert_eq!(load_error(&lookup_model(points, "tab")), expected);
    }
}

#[test]
fn test_set_points_sorts_and_refuses_the_same_way() {
    let mut model = parse_json(&lookup_model("[[0.0, 0.0], [10.0, 100.0]]", "tab")).unwrap();
    model.set_points("tab", vec![(10.0, 0.0), (0.0, 100.0)]).unwrap();
    assert_eq!(model.graphical_functions["tab"].points, vec![(0.0, 100.0), (10.0, 0.0)]);
    let error = model.set_points("tab", vec![(1.0, 0.0), (1.0, 1.0)]).unwrap_err();
    assert_eq!(error, "Lookup table 'tab' has two points at x=1.0");
    let error = model.set_points("tab", vec![(f64::NAN, 0.0)]).unwrap_err();
    assert!(error.contains("x must be a finite number"), "{}", error);
    // A refused table leaves the one before in place.
    assert_eq!(model.graphical_functions["tab"].points, vec![(0.0, 100.0), (10.0, 0.0)]);
}
