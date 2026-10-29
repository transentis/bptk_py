//! The belt of a conveyor: what lies on it, and how one timestep moves it.
//!
//! A port of `BPTK_Py/sddsl/belt.py`, which is the reference: the same cohorts, the same
//! order of operations, the same tolerances - so that both engines move a belt alike. The
//! reasoning behind each rule is written down there.

/// Material at a position this close to the end of the belt has arrived.
const EPSILON: f64 = 1e-9;

/// The number of slats for a transit time: rounded half away from zero, at least 1.
pub fn slat_count(transit: f64, dt: f64) -> usize {
    let ratio = transit / dt;
    ((ratio.abs() + 0.5).floor() as usize).max(1)
}

/// The material that entered the belt in one timestep.
#[derive(Clone, Debug)]
pub struct Cohort {
    /// The time from which it lies on the belt.
    pub entered: f64,
    pub content: f64,
    /// Per linear leak: what one step of travel leaks per unit of fraction.
    pub basis: Vec<f64>,
    /// Per linear leak: what is still to leak per unit of fraction.
    pub window: Vec<f64>,
    /// Traditional: steps until it leaves.
    pub depth: usize,
    /// FIFO: the part of the unit belt it covers.
    pub low: f64,
    pub high: f64,
}

/// What lies on a conveyor at one moment.
#[derive(Clone, Debug)]
pub struct Belt {
    pub fifo: bool,
    pub exponential: bool,
    pub cohorts: Vec<Cohort>,
}

/// What one timestep moved: what left at the front, and what each leak took.
#[derive(Clone, Debug)]
pub struct Moves {
    pub exited: f64,
    pub leaked: Vec<f64>,
}

impl Belt {
    pub fn contents(&self) -> f64 {
        self.cohorts.iter().map(|cohort| cohort.content).sum()
    }

    /// The material that has been on the belt for at least `minimum` and less than
    /// `maximum` time units at time `t`.
    pub fn agecount(&self, t: f64, minimum: f64, maximum: f64) -> f64 {
        self.cohorts
            .iter()
            .filter(|cohort| {
                let age = t - cohort.entered;
                minimum - EPSILON <= age && age < maximum - EPSILON
            })
            .map(|cohort| cohort.content)
            .sum()
    }

    /// One timestep from `t`: what moved, and the belt at `t + dt`. `inflow` is the amount
    /// entering, `fractions` one per leak.
    pub fn advance(&self, t: f64, dt: f64, inflow: f64, transit: f64, fractions: &[f64]) -> (Moves, Belt) {
        let mut cohorts = self.cohorts.clone();
        let speed = dt / transit;
        let leaked = self.leak(&mut cohorts, dt, speed, fractions);
        let (exited, mut cohorts) = self.shift(cohorts, speed);
        if inflow != 0.0 {
            cohorts.push(self.enter(t + dt, inflow, transit, dt, fractions.len()));
        }
        (
            Moves { exited, leaked },
            Belt { fifo: self.fifo, exponential: self.exponential, cohorts },
        )
    }

    fn leak(&self, cohorts: &mut [Cohort], dt: f64, speed: f64, fractions: &[f64]) -> Vec<f64> {
        let mut leaked = vec![0.0; fractions.len()];
        for cohort in cohorts.iter_mut() {
            if self.exponential {
                let mut takes: Vec<f64> = fractions.iter().map(|fraction| cohort.content * fraction * dt).collect();
                let total: f64 = takes.iter().sum();
                if total > cohort.content && cohort.content > 0.0 {
                    let content = cohort.content;
                    takes = takes.iter().map(|take| take * content / total).collect();
                } else if cohort.content <= 0.0 {
                    takes = vec![0.0; fractions.len()];
                }
                for (k, take) in takes.iter().enumerate() {
                    leaked[k] += take;
                }
                cohort.content -= takes.iter().sum::<f64>();
            } else {
                for (k, fraction) in fractions.iter().enumerate() {
                    let step = cohort.basis[k] * if self.fifo { speed } else { 1.0 };
                    let used = python_min(step, cohort.window[k]);
                    let take = python_min(fraction * used, cohort.content);
                    cohort.window[k] -= used;
                    cohort.content -= take;
                    leaked[k] += take;
                }
            }
        }
        leaked
    }

    fn shift(&self, cohorts: Vec<Cohort>, speed: f64) -> (f64, Vec<Cohort>) {
        let mut exited = 0.0;
        let mut remaining = Vec::with_capacity(cohorts.len());
        for mut cohort in cohorts {
            if !self.fifo {
                if cohort.depth <= 1 {
                    exited += cohort.content;
                    continue;
                }
                cohort.depth -= 1;
                remaining.push(cohort);
                continue;
            }
            cohort.low += speed;
            cohort.high += speed;
            if cohort.low >= 1.0 - EPSILON {
                exited += cohort.content;
                continue;
            }
            if cohort.high > 1.0 + EPSILON {
                let share = (cohort.high - 1.0) / (cohort.high - cohort.low);
                exited += cohort.content * share;
                cohort.content *= 1.0 - share;
                cohort.basis = cohort.basis.iter().map(|value| value * (1.0 - share)).collect();
                cohort.window = cohort.window.iter().map(|value| value * (1.0 - share)).collect();
                cohort.high = 1.0;
            }
            remaining.push(cohort);
        }
        (exited, remaining)
    }

    fn enter(&self, entered: f64, amount: f64, transit: f64, dt: f64, leaks: usize) -> Cohort {
        if self.fifo {
            return Cohort {
                entered,
                content: amount,
                basis: vec![amount; leaks],
                window: vec![amount; leaks],
                depth: 0,
                low: 0.0,
                high: dt / transit,
            };
        }
        let depth = slat_count(transit, dt);
        Cohort {
            entered,
            content: amount,
            basis: vec![amount / depth as f64; leaks],
            window: vec![amount; leaks],
            depth,
            low: 0.0,
            high: 0.0,
        }
    }
}

/// What a conveyor starts with: a total spread in the equilibrium its leakage implies, or
/// a list - one value per slat, or one per time unit.
pub enum Initial {
    Total(f64),
    List(Vec<f64>),
}

/// The belt at the start of a run.
pub fn filled(
    fifo: bool,
    exponential: bool,
    start: f64,
    dt: f64,
    transit: f64,
    fractions: &[f64],
    initial: &Initial,
) -> Belt {
    let slats = slat_count(transit, dt);
    let retained = retained_profile(exponential, slats, dt, fractions);
    let contents: Vec<f64> = match initial {
        Initial::List(values) => from_list(values, slats, dt),
        Initial::Total(total) => {
            // The profile starts at 1 at the back of the belt, so it never sums to zero.
            let scale = total / retained.iter().sum::<f64>();
            retained.iter().map(|share| scale * share).collect()
        }
    };

    let leaks = fractions.len();
    let mut cohorts = Vec::new();
    for (index, &content) in contents.iter().enumerate() {
        let depth = index + 1;
        let travelled = slats - depth;
        let entering = if retained[index] > 0.0 { content / retained[index] } else { content };
        let entered = start - travelled as f64 * dt;
        let cohort = if fifo {
            Cohort {
                entered,
                content,
                basis: vec![entering; leaks],
                window: vec![entering * depth as f64 / slats as f64; leaks],
                depth: 0,
                low: 1.0 - depth as f64 / slats as f64,
                high: 1.0 - (depth - 1) as f64 / slats as f64,
            }
        } else {
            Cohort {
                entered,
                content,
                basis: vec![entering / slats as f64; leaks],
                window: vec![entering / slats as f64 * depth as f64; leaks],
                depth,
                low: 0.0,
                high: 0.0,
            }
        };
        if content != 0.0 {
            cohorts.push(cohort);
        }
    }
    Belt { fifo, exponential, cohorts }
}

/// What one unit entering at the back still holds at each slat, front first.
fn retained_profile(exponential: bool, slats: usize, dt: f64, fractions: &[f64]) -> Vec<f64> {
    let total: f64 = fractions.iter().sum();
    let mut profile = vec![1.0];
    for _ in 0..slats - 1 {
        let last = *profile.last().unwrap();
        let next = if exponential { last * (1.0 - total * dt) } else { last - total / slats as f64 };
        profile.push(python_max(0.0, next));
    }
    profile.reverse();
    profile
}

fn from_list(values: &[f64], slats: usize, dt: f64) -> Vec<f64> {
    if values.len() == slats {
        return values.to_vec();
    }
    let units = ((slats - 1) as f64 * dt + EPSILON).floor() as usize + 1;
    let values: Vec<f64> = if values.is_empty() {
        vec![0.0; units]
    } else {
        let last = *values.last().unwrap();
        values.iter().copied().chain(std::iter::repeat(last)).take(units).collect()
    };
    let blocks: Vec<usize> = (0..slats).map(|index| (index as f64 * dt + EPSILON).floor() as usize).collect();
    let sizes: Vec<usize> = (0..units).map(|unit| blocks.iter().filter(|&&block| block == unit).count()).collect();
    blocks.iter().map(|&block| values[block] / sizes[block] as f64).collect()
}

/// Python's max and min of two, as belt.py computes with them.
fn python_max(a: f64, b: f64) -> f64 {
    if b > a { b } else { a }
}

fn python_min(a: f64, b: f64) -> f64 {
    if b < a { b } else { a }
}
