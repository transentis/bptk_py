use std::cell::RefCell;
use rand::rngs::StdRng;
use rand::SeedableRng;

/// Simulation state: pre-allocated memo table for all entities across all timesteps.
pub struct SimulationState {
    /// memo[entity_index][timestep_index] = value
    pub memo: Vec<Vec<f64>>,
    /// Seeded RNG for stochastic functions (interior mutability).
    rng: RefCell<StdRng>,
}

impl SimulationState {
    pub fn new(num_entities: usize, num_steps: usize, seed: Option<u64>) -> Self {
        let rng = match seed {
            Some(s) => StdRng::seed_from_u64(s),
            None => StdRng::from_entropy(),
        };
        SimulationState {
            memo: vec![vec![0.0; num_steps]; num_entities],
            rng: RefCell::new(rng),
        }
    }

    pub fn rng(&self) -> std::cell::RefMut<'_, StdRng> {
        self.rng.borrow_mut()
    }
}
