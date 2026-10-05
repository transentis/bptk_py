//! Helpers shared by the engine's integration tests.

// Each test binary compiles this module and uses only some of it.
#![allow(dead_code)]

use std::collections::HashMap;

use bptk_rust_engine::json_parser::parse_json;
use bptk_rust_engine::model::SdModel;

/// A model with these run specs and nothing in it, for evaluating expressions directly.
pub fn model_with_specs(starttime: f64, stoptime: f64, dt: f64) -> SdModel {
    SdModel {
        name: String::new(),
        starttime,
        stoptime,
        dt,
        entities: Vec::new(),
        entity_index: HashMap::new(),
        graphical_functions: HashMap::new(),
        eval_order: Vec::new(),
        callback_names: Vec::new(),
        #[cfg(feature = "python")]
        callbacks: Vec::new(),
    }
}

/// The message a model that must not load is refused with.
pub fn load_error(json: &str) -> String {
    match parse_json(json) {
        Ok(_) => panic!("expected the model to be rejected"),
        Err(e) => e.to_string(),
    }
}
