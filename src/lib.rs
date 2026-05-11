use std::collections::HashMap;

use pyo3::prelude::*;
use pyo3::exceptions::PyValueError;

pub mod model;
pub mod json_parser;
pub mod state;
pub mod eval;
pub mod builtins;
pub mod lookup;
pub mod sim;

/// Returns the version of the Rust SD engine.
#[pyfunction]
fn version() -> &'static str {
    "0.1.0"
}

#[pyclass]
pub struct RustSdEngine {}

#[pymethods]
impl RustSdEngine {
    #[new]
    fn new() -> Self {
        RustSdEngine {}
    }

    /// Parse a JSON string into an executable model.
    fn load_model(&self, json: &str) -> PyResult<RustSdModel> {
        let sd_model = json_parser::parse_json(json)
            .map_err(|e| PyValueError::new_err(e.to_string()))?;
        Ok(RustSdModel { model: sd_model })
    }
}

#[pyclass]
pub struct RustSdModel {
    model: model::SdModel,
}

#[pymethods]
impl RustSdModel {
    /// Run full simulation, return results for requested equations.
    /// Returns dict[str, dict[str, float]] — { entity_name: { time_str: value } }
    #[pyo3(signature = (equations, seed=None))]
    fn simulate(&self, equations: Vec<String>, seed: Option<u64>) -> PyResult<HashMap<String, HashMap<String, f64>>> {
        Ok(self.model.simulate(&equations, seed))
    }

    /// Override a constant's value.
    fn set_constant(&mut self, name: &str, value: f64) -> PyResult<()> {
        self.model
            .set_constant(name, value)
            .map_err(|e| PyValueError::new_err(e))
    }

    /// Override the simulation run specifications (starttime, stoptime, dt).
    fn set_runspecs(&mut self, starttime: f64, stoptime: f64, dt: f64) -> PyResult<()> {
        self.model.set_runspecs(starttime, stoptime, dt);
        Ok(())
    }

    /// Replace the points of a graphical function (lookup table).
    fn set_points(&mut self, name: &str, points: Vec<(f64, f64)>) -> PyResult<()> {
        self.model
            .set_points(name, points)
            .map_err(|e| PyValueError::new_err(e))
    }
}

/// The Rust engine Python module, installed at `BPTK_Py._rust_engine`.
#[pymodule]
fn _rust_engine(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(version, m)?)?;
    m.add_class::<RustSdEngine>()?;
    m.add_class::<RustSdModel>()?;
    Ok(())
}
