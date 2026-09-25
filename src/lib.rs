//! The BPTK SD execution engine.
//!
//! The crate builds with or without Python. `python` (on by default) adds the pyo3
//! binding in `python.rs`; without it no pyo3 enters the dependency graph at all.

pub mod model;
pub mod json_parser;
pub mod state;
pub mod eval;
pub mod builtins;
pub mod lookup;
pub mod sim;

#[cfg(feature = "python")]
pub mod python;
