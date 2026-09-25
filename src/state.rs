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
    /// The first failure of a Python callback, kept until somebody asks for it.
    ///
    /// The evaluator answers with a number and has no channel of its own: every other
    /// operation it performs is total, and giving sixty infallible builtins a fallible
    /// signature to express the one that is not would be the wrong trade. So a failing
    /// callback records what went wrong, answers NaN, and the step that contains it ends
    /// as an error. A `Mutex` for the same reason as the RNG above.
    error: Mutex<Option<String>>,
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
            error: Mutex::new(None),
        }
    }

    /// Record a failure, keeping the first one: a later step evaluated with NaN can
    /// fail for a reason that is only a consequence of this one.
    pub fn record_error(&self, message: String) {
        let mut slot = self.error.lock().expect("simulation error mutex poisoned");
        if slot.is_none() {
            *slot = Some(message);
        }
    }

    /// Take the recorded failure, leaving the state usable again.
    pub fn take_error(&self) -> Option<String> {
        self.error
            .lock()
            .expect("simulation error mutex poisoned")
            .take()
    }

    pub fn rng(&self) -> std::sync::MutexGuard<'_, StdRng> {
        // No call site holds two guards at once, so this cannot deadlock; a poisoned
        // lock would mean a panic inside a distribution, which is a bug either way.
        self.rng.lock().expect("simulation RNG mutex poisoned")
    }
}
