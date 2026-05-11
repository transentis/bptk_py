use crate::model::*;
use crate::state::SimulationState;
use statrs::function::gamma::ln_gamma;
use statrs::distribution::{Normal as StatrsNormal, ContinuousCDF};
use rand::Rng;
use rand_distr::{
    Distribution,
    Normal as NormalDist, Beta as BetaDist, Binomial as BinomialDist,
    Exp as ExpDist, Gamma as GammaDist, Geometric as GeometricDist,
    LogNormal as LogNormalDist, Poisson as PoissonDist,
    Triangular as TriangularDist, Weibull as WeibullDist, Pareto as ParetoDist,
};

impl SdModel {
    /// Evaluate a built-in function call.
    pub fn eval_builtin(
        &self,
        function: &BuiltinFn,
        args: &[Expr],
        state: &SimulationState,
        step: usize,
    ) -> f64 {
        match function {
            // Temporal
            BuiltinFn::Time => self.starttime + step as f64 * self.dt,
            BuiltinFn::Dt => self.dt,
            BuiltinFn::Starttime => self.starttime,
            BuiltinFn::Stoptime => self.stoptime,

            // Math — single argument
            BuiltinFn::Abs => {
                let v = self.eval_expr(&args[0], state, step);
                v.abs()
            }
            BuiltinFn::Sqrt => {
                let v = self.eval_expr(&args[0], state, step);
                v.sqrt()
            }
            BuiltinFn::Exp => {
                let v = self.eval_expr(&args[0], state, step);
                v.exp()
            }
            BuiltinFn::Ln => {
                let v = self.eval_expr(&args[0], state, step);
                v.ln()
            }
            BuiltinFn::Log10 => {
                let v = self.eval_expr(&args[0], state, step);
                v.log10()
            }
            BuiltinFn::Sin => {
                let v = self.eval_expr(&args[0], state, step);
                v.sin()
            }
            BuiltinFn::Cos => {
                let v = self.eval_expr(&args[0], state, step);
                v.cos()
            }
            BuiltinFn::Tan => {
                let v = self.eval_expr(&args[0], state, step);
                v.tan()
            }
            BuiltinFn::Arcsin => {
                let v = self.eval_expr(&args[0], state, step);
                v.asin()
            }
            BuiltinFn::Arccos => {
                let v = self.eval_expr(&args[0], state, step);
                v.acos()
            }
            BuiltinFn::Arctan => {
                let v = self.eval_expr(&args[0], state, step);
                v.atan()
            }
            BuiltinFn::Round => {
                let v = self.eval_expr(&args[0], state, step);
                if args.len() > 1 {
                    let digits = self.eval_expr(&args[1], state, step);
                    let factor = 10.0_f64.powf(digits);
                    (v * factor).round() / factor
                } else {
                    v.round()
                }
            }
            BuiltinFn::Floor => {
                let v = self.eval_expr(&args[0], state, step);
                v.floor()
            }
            BuiltinFn::Ceil => {
                let v = self.eval_expr(&args[0], state, step);
                v.ceil()
            }

            // Math — two arguments
            BuiltinFn::Max => {
                let a = self.eval_expr(&args[0], state, step);
                let b = self.eval_expr(&args[1], state, step);
                a.max(b)
            }
            BuiltinFn::Min => {
                let a = self.eval_expr(&args[0], state, step);
                let b = self.eval_expr(&args[1], state, step);
                a.min(b)
            }

            // Math — constant
            BuiltinFn::Pi => std::f64::consts::PI,

            // Sinwave: amplitude * sin(2π / period * (t - starttime))
            BuiltinFn::Sinwave => {
                let amplitude = self.eval_expr(&args[0], state, step);
                let period = self.eval_expr(&args[1], state, step);
                let t = self.starttime + step as f64 * self.dt;
                amplitude * (2.0 * std::f64::consts::PI / period * (t - self.starttime)).sin()
            }

            // Coswave: amplitude * cos(2π / period * (t - starttime))
            BuiltinFn::Coswave => {
                let amplitude = self.eval_expr(&args[0], state, step);
                let period = self.eval_expr(&args[1], state, step);
                let t = self.starttime + step as f64 * self.dt;
                amplitude * (2.0 * std::f64::consts::PI / period * (t - self.starttime)).cos()
            }

            // Control — step: returns height when t > timestep, else 0
            BuiltinFn::Step => {
                let height = self.eval_expr(&args[0], state, step);
                let timestep = self.eval_expr(&args[1], state, step);
                let t = self.starttime + step as f64 * self.dt;
                if t > timestep {
                    height
                } else {
                    0.0
                }
            }

            // Control — pulse: returns volume/dt at specified times
            // pulse(volume, first_pulse, [interval])
            BuiltinFn::Pulse => {
                let volume = self.eval_expr(&args[0], state, step);
                let first_pulse = if args.len() > 1 {
                    self.eval_expr(&args[1], state, step)
                } else {
                    0.0
                };
                let interval = if args.len() > 2 {
                    self.eval_expr(&args[2], state, step)
                } else {
                    0.0
                };
                let t = self.starttime + step as f64 * self.dt;

                if interval == 0.0 {
                    // Single pulse at first_pulse
                    if (t - first_pulse).abs() < 1e-10 {
                        volume / self.dt
                    } else {
                        0.0
                    }
                } else {
                    // Repeating pulse
                    let elapsed = t - first_pulse;
                    if elapsed >= -1e-10 && (elapsed % interval).abs() < 1e-10 {
                        volume / self.dt
                    } else {
                        0.0
                    }
                }
            }

            // Stateful — delay: look back in memo table
            // args[0] = Ref(entity_idx) — the input entity
            // args[1] = delay duration expression
            // args[2] = initial value expression
            BuiltinFn::Delay => {
                let entity_idx = match &args[0] {
                    Expr::Ref(idx) => *idx,
                    _ => panic!("delay: first argument must be an entity reference"),
                };
                let delay_duration = self.eval_expr(&args[1], state, step);
                let delay_steps = (delay_duration / self.dt).round() as usize;

                if step >= delay_steps {
                    state.memo[entity_idx][step - delay_steps]
                } else {
                    // Before enough time has elapsed, return initial value
                    self.eval_expr(&args[2], state, step)
                }
            }

            // Combinatorial & special
            BuiltinFn::Combinations => {
                let n = self.eval_expr(&args[0], state, step);
                let r = self.eval_expr(&args[1], state, step);
                if n < r { 0.0 } else {
                    (ln_gamma(n + 1.0) - ln_gamma(r + 1.0) - ln_gamma(n - r + 1.0)).exp()
                }
            }
            BuiltinFn::Permutations => {
                let n = self.eval_expr(&args[0], state, step);
                let r = self.eval_expr(&args[1], state, step);
                if n < r { 0.0 } else {
                    (ln_gamma(n + 1.0) - ln_gamma(n - r + 1.0)).exp()
                }
            }
            BuiltinFn::Factorial => {
                let n = self.eval_expr(&args[0], state, step);
                if n < 0.0 { 0.0 } else {
                    (ln_gamma(n + 1.0)).exp().round()
                }
            }
            BuiltinFn::GammaLN => {
                let n = self.eval_expr(&args[0], state, step);
                ln_gamma(n)
            }
            BuiltinFn::Inf => f64::INFINITY,
            BuiltinFn::Nan => f64::NAN,

            // Statistical functions
            BuiltinFn::Random => {
                let min_val = self.eval_expr(&args[0], state, step);
                let max_val = self.eval_expr(&args[1], state, step);
                state.rng().gen_range(min_val..=max_val)
            }
            BuiltinFn::Normal => {
                let mean = self.eval_expr(&args[0], state, step);
                let stddev = self.eval_expr(&args[1], state, step);
                if stddev < 0.0 {
                    f64::NAN
                } else {
                    let dist = NormalDist::new(mean, stddev).unwrap();
                    dist.sample(&mut *state.rng())
                }
            }
            BuiltinFn::Beta => {
                let a = self.eval_expr(&args[0], state, step);
                let b = self.eval_expr(&args[1], state, step);
                if a <= 0.0 || b <= 0.0 {
                    f64::NAN
                } else {
                    let dist = BetaDist::new(a, b).unwrap();
                    dist.sample(&mut *state.rng())
                }
            }
            BuiltinFn::Binomial => {
                let n = self.eval_expr(&args[0], state, step);
                let p = self.eval_expr(&args[1], state, step);
                if n < 0.0 || p < 0.0 || p > 1.0 {
                    f64::NAN
                } else {
                    let dist = BinomialDist::new(n as u64, p).unwrap();
                    dist.sample(&mut *state.rng()) as f64
                }
            }
            BuiltinFn::NegBinomial => {
                let n = self.eval_expr(&args[0], state, step);
                let p = self.eval_expr(&args[1], state, step);
                if n <= 0.0 || p < 0.0 || p > 1.0 {
                    f64::NAN
                } else if p == 0.0 {
                    // Negative binomial: number of failures before n successes
                    f64::INFINITY
                } else if p >= 1.0 {
                    0.0
                } else {
                    let n_int = n as u64;
                    let geom = GeometricDist::new(p).unwrap();
                    let mut total: u64 = 0;
                    for _ in 0..n_int {
                        total += geom.sample(&mut *state.rng());
                    }
                    total as f64
                }
            }
            BuiltinFn::Exprnd => {
                // Python: np.random.exponential(scale). scale = 1/rate.
                let scale = self.eval_expr(&args[0], state, step);
                if scale <= 0.0 {
                    f64::NAN
                } else {
                    let dist = ExpDist::new(1.0 / scale).unwrap();
                    dist.sample(&mut *state.rng())
                }
            }
            BuiltinFn::GammaDist => {
                let shape = self.eval_expr(&args[0], state, step);
                let scale = if args.len() > 1 {
                    self.eval_expr(&args[1], state, step)
                } else {
                    1.0
                };
                if shape <= 0.0 || scale <= 0.0 {
                    f64::NAN
                } else {
                    let dist = GammaDist::new(shape, scale).unwrap();
                    dist.sample(&mut *state.rng())
                }
            }
            BuiltinFn::Geometric => {
                let p = self.eval_expr(&args[0], state, step);
                if p <= 0.0 || p > 1.0 {
                    1.0
                } else {
                    // rand_distr::Geometric returns failures before first success (0-based).
                    // numpy.random.geometric returns trial count including success (1-based).
                    // Add 1 to match Python SD DSL behavior.
                    let dist = GeometricDist::new(p).unwrap();
                    dist.sample(&mut *state.rng()) as f64 + 1.0
                }
            }
            BuiltinFn::Lognormal => {
                let mean = self.eval_expr(&args[0], state, step);
                let stddev = self.eval_expr(&args[1], state, step);
                if stddev < 0.0 {
                    f64::NAN
                } else {
                    let dist = LogNormalDist::new(mean, stddev).unwrap();
                    dist.sample(&mut *state.rng())
                }
            }
            BuiltinFn::Logistic => {
                // Inverse CDF method: mean + scale * ln(u / (1 - u))
                let mean = self.eval_expr(&args[0], state, step);
                let scale = self.eval_expr(&args[1], state, step);
                if scale < 0.0 {
                    f64::NAN
                } else {
                    let u: f64 = state.rng().gen_range(0.0001..0.9999);
                    mean + scale * (u / (1.0 - u)).ln()
                }
            }
            BuiltinFn::Montecarlo => {
                let p = self.eval_expr(&args[0], state, step);
                let threshold = p * self.dt;
                let u: f64 = state.rng().gen_range(0.0..100.0);
                if u < threshold { 1.0 } else { 0.0 }
            }
            BuiltinFn::Poisson => {
                let mu = self.eval_expr(&args[0], state, step);
                if mu < 0.0 {
                    f64::NAN
                } else if mu == 0.0 {
                    0.0
                } else {
                    let dist = PoissonDist::new(mu).unwrap();
                    dist.sample(&mut *state.rng()) as f64
                }
            }
            BuiltinFn::Triangular => {
                let lower = self.eval_expr(&args[0], state, step);
                let mode = self.eval_expr(&args[1], state, step);
                let upper = self.eval_expr(&args[2], state, step);
                if lower == mode && mode == upper {
                    lower
                } else if lower > upper || mode < lower || mode > upper {
                    f64::NAN
                } else {
                    let dist = TriangularDist::new(lower, upper, mode).unwrap();
                    dist.sample(&mut *state.rng())
                }
            }
            BuiltinFn::Weibull => {
                // Python: np.random.weibull(shape) * scale
                // Rust: Weibull::new(scale, shape) — scale first, shape second
                let shape = self.eval_expr(&args[0], state, step);
                let scale = self.eval_expr(&args[1], state, step);
                if shape <= 0.0 || scale <= 0.0 {
                    f64::NAN
                } else {
                    let dist = WeibullDist::new(scale, shape).unwrap();
                    dist.sample(&mut *state.rng())
                }
            }
            BuiltinFn::Pareto => {
                let shape = self.eval_expr(&args[0], state, step);
                let scale = self.eval_expr(&args[1], state, step);
                if shape <= 0.0 || scale <= 0.0 {
                    f64::NAN
                } else {
                    // rand_distr::Pareto samples from Pareto(xm, alpha) with min=xm.
                    // numpy.random.pareto(a) * scale gives (X-1)*scale where X~Pareto(1,a).
                    // Subtract scale to match Python SD DSL: result = sample - scale.
                    let dist = ParetoDist::new(scale, shape).unwrap();
                    dist.sample(&mut *state.rng()) - scale
                }
            }
            BuiltinFn::Invnorm => {
                let p = self.eval_expr(&args[0], state, step);
                let (mean, stddev) = if args.len() >= 3 {
                    (self.eval_expr(&args[1], state, step),
                     self.eval_expr(&args[2], state, step))
                } else if args.len() == 2 {
                    (self.eval_expr(&args[1], state, step), 1.0)
                } else {
                    (0.0, 1.0)
                };
                if p < 0.0 || p > 1.0 || stddev <= 0.0 {
                    f64::NAN
                } else if p == 0.0 {
                    f64::NEG_INFINITY
                } else if p == 1.0 {
                    f64::INFINITY
                } else {
                    let dist = StatrsNormal::new(mean, stddev).unwrap();
                    dist.inverse_cdf(p)
                }
            }
            BuiltinFn::NormalCDF => {
                let left = self.eval_expr(&args[0], state, step);
                let right = self.eval_expr(&args[1], state, step);
                let mean = if args.len() > 2 { self.eval_expr(&args[2], state, step) } else { 0.0 };
                let stddev = if args.len() > 3 { self.eval_expr(&args[3], state, step) } else { 1.0 };
                if stddev <= 0.0 {
                    f64::NAN
                } else {
                    let dist = StatrsNormal::new(mean, stddev).unwrap();
                    dist.cdf(right) - dist.cdf(left)
                }
            }

            // Lookup — linear interpolation from graphical function
            BuiltinFn::Lookup(table_name) => {
                let x = self.eval_expr(&args[0], state, step);
                self.lookup_interpolate(table_name, x)
            }
        }
    }
}
