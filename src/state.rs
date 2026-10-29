use std::collections::{HashMap, HashSet};
use std::sync::atomic::{AtomicBool, AtomicUsize, Ordering};
use std::sync::Mutex;
use rand::rngs::StdRng;
use rand::SeedableRng;

/// A builtin was given arguments it does not accept, and answered NaN.
///
/// Only the facts: which builtin, where and with what. Why they are invalid, and the
/// wording of the report, come from the Python side's table of the same builtins, so that
/// both engines say the same thing in the same words.
#[derive(Debug, Clone, PartialEq)]
pub struct InvalidArgument {
    pub entity: usize,
    pub builtin: &'static str,
    pub step: usize,
    pub values: Vec<f64>,
}

/// Simulation state: pre-allocated memo table for all entities across all timesteps.
pub struct SimulationState {
    /// memo[entity_index][timestep_index] = value
    pub memo: Vec<Vec<f64>>,
    /// The number of timesteps, starttime and stoptime included. Kept here rather than
    /// read off `memo[0]`, which a model without entities does not have.
    pub num_steps: usize,
    /// Cursor into the memo table: the index of the last step whose
    /// non-stock entities have been evaluated. After `init()` returns this is
    /// `0`; each successful `step()` increments it by one.
    pub current_step: usize,
    /// Seeded RNG for stochastic functions (interior mutability).
    ///
    /// A `Mutex` rather than a `RefCell` so that `SimulationState` — and with it the
    /// `RustSdModel` pyclass that owns it — is `Sync` as well as `Send`, which PyO3
    /// requires of a class that may cross threads. A threaded WSGI server hands
    /// consecutive requests to different threads while the runner keeps the model handle
    /// on the Scenario, so the handle does cross threads. The lock is always uncontended
    /// (the GIL serializes access) and only taken by stochastic functions; deterministic
    /// models never touch it.
    rng: Mutex<StdRng>,
    /// The first failure of a Python callback, kept until somebody asks for it.
    ///
    /// The evaluator answers with a number and has no channel of its own: every other
    /// operation it performs is total, and giving sixty infallible builtins a fallible
    /// signature to express the one that is not would be the wrong trade. So a failing
    /// callback records what went wrong, answers NaN, and the step that contains it ends
    /// as an error. A `Mutex` for the same reason as the RNG above.
    error: Mutex<Option<String>>,
    /// The entity being evaluated, so that a builtin can say where it was called from.
    current_entity: AtomicUsize,
    /// Whether the start time is being evaluated, in the model's `init_order`.
    starting: AtomicBool,
    /// Invalid arguments not yet collected, and the entities already recorded: one record
    /// per entity and run, or a run of many steps would repeat the same one.
    invalid: Mutex<(Vec<InvalidArgument>, HashSet<usize>)>,
    /// Per conveyor entity: its belt at the step being evaluated and the next one, and
    /// what the step moved. Only the neighbourhood of the cursor is kept.
    pub conveyors: Mutex<HashMap<usize, ConveyorState>>,
    /// Per `sample` node: the step its sample began and the value drawn then, so that an
    /// unseeded draw holds until the next sample.
    held: Mutex<HashMap<usize, (usize, f64)>>,
}

/// The belts of one conveyor by step, and what each step moved.
#[derive(Default)]
pub struct ConveyorState {
    pub belts: HashMap<usize, crate::conveyor::Belt>,
    pub moves: HashMap<usize, crate::conveyor::Moves>,
}

impl SimulationState {
    pub fn new(num_entities: usize, num_steps: usize, seed: Option<u64>) -> Self {
        Self::try_new(num_entities, num_steps, seed).expect("memo table allocation failed")
    }

    /// Like `new`, but a memo table too large for memory is an error rather than an abort.
    pub fn try_new(num_entities: usize, num_steps: usize, seed: Option<u64>) -> Result<Self, String> {
        let mut memo = Vec::new();
        let too_large = || {
            format!(
                "Cannot allocate the results of {} entities over {} timesteps",
                num_entities, num_steps
            )
        };
        memo.try_reserve_exact(num_entities).map_err(|_| too_large())?;
        for _ in 0..num_entities {
            let mut row = Vec::new();
            row.try_reserve_exact(num_steps).map_err(|_| too_large())?;
            row.resize(num_steps, 0.0);
            memo.push(row);
        }
        let rng = match seed {
            Some(s) => StdRng::seed_from_u64(s),
            None => StdRng::from_entropy(),
        };
        Ok(SimulationState {
            memo,
            num_steps,
            current_step: 0,
            rng: Mutex::new(rng),
            error: Mutex::new(None),
            current_entity: AtomicUsize::new(0),
            starting: AtomicBool::new(false),
            invalid: Mutex::new((Vec::new(), HashSet::new())),
            conveyors: Mutex::new(HashMap::new()),
            held: Mutex::new(HashMap::new()),
        })
    }

    /// The value a `sample` node drew when the sample that began at `step` began, if it did.
    pub fn held(&self, node: usize, step: usize) -> Option<f64> {
        let held = self.held.lock().expect("held draws mutex poisoned");
        held.get(&node).filter(|&&(began, _)| began == step).map(|&(_, value)| value)
    }

    pub fn hold(&self, node: usize, step: usize, value: f64) {
        self.held.lock().expect("held draws mutex poisoned").insert(node, (step, value));
    }

    pub fn current_entity(&self) -> usize {
        self.current_entity.load(Ordering::Relaxed)
    }

    pub fn set_current_entity(&self, entity: usize) {
        self.current_entity.store(entity, Ordering::Relaxed);
    }

    pub fn starting(&self) -> bool {
        self.starting.load(Ordering::Relaxed)
    }

    pub fn set_starting(&self, starting: bool) {
        self.starting.store(starting, Ordering::Relaxed);
    }

    /// Record an invalid argument for the entity being evaluated, unless it has one.
    pub fn record_invalid(&self, builtin: &'static str, step: usize, values: &[f64]) {
        let entity = self.current_entity.load(Ordering::Relaxed);
        let mut invalid = self.invalid.lock().expect("invalid-argument mutex poisoned");
        if invalid.1.insert(entity) {
            invalid.0.push(InvalidArgument { entity, builtin, step, values: values.to_vec() });
        }
    }

    /// Take the invalid arguments recorded since the last call. An entity already recorded
    /// stays recorded, so a later step does not report it again.
    pub fn take_invalid(&self) -> Vec<InvalidArgument> {
        std::mem::take(&mut self.invalid.lock().expect("invalid-argument mutex poisoned").0)
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

    /// Put `rng` in place of the run's generator and return the one it replaces - so that
    /// a seeded draw takes its numbers from a generator of its own and gives it back.
    pub fn swap_rng(&self, rng: StdRng) -> StdRng {
        std::mem::replace(&mut *self.rng(), rng)
    }

    pub fn rng(&self) -> std::sync::MutexGuard<'_, StdRng> {
        // No call site holds two guards at once, so this cannot deadlock; a poisoned
        // lock would mean a panic inside a distribution, which is a bug either way.
        self.rng.lock().expect("simulation RNG mutex poisoned")
    }
}
