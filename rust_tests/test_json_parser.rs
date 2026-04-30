use bptk_rust_engine::json_parser::parse_json;
use bptk_rust_engine::json_parser::ParseError;
use bptk_rust_engine::model::*;

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
