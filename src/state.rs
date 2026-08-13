use std::sync::Mutex;
use rand::rngs::StdRng;
use rand::SeedableRng;

/// Simulation state: pre-allocated memo table for all entities across all timesteps.
pub struct SimulationState {
    /// memo[entity_index][timestep_index] = value
    pub memo: Vec<Vec<f64>>,
    /// Cursor into the memo table: the index of the last step whose
    /// non-stock entities have been evaluated. After `init()` returns this is
    /// `0`; each successful `step()` increments it by one.
    pub current_step: usize,
    /// Seeded RNG for stochastic functions (interior mutability).
    ///
    /// A `Mutex` rather than a `RefCell` so that `SimulationState` — and with it the
    /// `RustSdModel` pyclass that owns it — is `Sync`, which PyO3 requires. A threaded
    /// WSGI server hands consecutive requests to different threads while the runner
    /// keeps the model handle on the Scenario, so the handle does cross threads. The
    /// lock is always uncontended (the GIL serializes access) and only taken by
    /// stochastic functions; deterministic models never touch it.
    rng: Mutex<StdRng>,
}

impl SimulationState {
    pub fn new(num_entities: usize, num_steps: usize, seed: Option<u64>) -> Self {
        let rng = match seed {
            Some(s) => StdRng::seed_from_u64(s),
            None => StdRng::from_entropy(),
        };
        SimulationState {
            memo: vec![vec![0.0; num_steps]; num_entities],
            current_step: 0,
            rng: Mutex::new(rng),
        }
    }

    pub fn rng(&self) -> std::sync::MutexGuard<'_, StdRng> {
        // No call site holds two guards at once, so this cannot deadlock; a poisoned
        // lock would mean a panic inside a distribution, which is a bug either way.
        self.rng.lock().expect("simulation RNG mutex poisoned")
    }
}
