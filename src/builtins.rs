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

/// The largest count a counting distribution is asked for: numpy refuses a Poisson rate
/// above about 9.22e18, and a count beyond it no longer fits the integers it is drawn as.
/// The Python side uses the same bound.
const LARGEST_COUNT: f64 = 9.2e18;

impl SdModel {
    /// Whether `entity` already holds its value for the step being evaluated: a stock
    /// does from the step before, anything else if it comes before the entity being
    /// evaluated now.
    fn computed_at_this_step(&self, entity: usize, state: &SimulationState) -> bool {
        if matches!(self.entities[entity].kind, EntityKind::Stock { .. }) {
            return true;
        }
        let position = |idx| self.eval_order.iter().position(|&e| e == idx);
        match (position(entity), position(state.current_entity())) {
            (Some(input), Some(current)) => input < current,
            _ => false,
        }
    }

    /// NaN for arguments it does not accept, recorded so that it can be reported.
    fn rejected(&self, state: &SimulationState, step: usize, builtin: &'static str, values: &[f64]) -> f64 {
        state.record_invalid(builtin, step, values);
        f64::NAN
    }

    /// Evaluate a built-in function call.
    pub fn eval_builtin(
        &self,
        function: &BuiltinFn,
        args: &[Expr],
        state: &SimulationState,
        step: usize,
    ) -> f64 {
        // A function of its one argument and nothing else.
        let unary = |math: fn(f64) -> f64| math(self.eval_expr(&args[0], state, step));
        match function {
            // Temporal
            BuiltinFn::Time => self.time_at(step),
            BuiltinFn::Dt => self.dt,
            BuiltinFn::Starttime => self.starttime,
            BuiltinFn::Stoptime => self.stoptime,

            // Math — single argument
            BuiltinFn::Abs => unary(f64::abs),
            BuiltinFn::Sqrt => unary(f64::sqrt),
            BuiltinFn::Exp => unary(f64::exp),
            BuiltinFn::Ln => unary(f64::ln),
            BuiltinFn::Log10 => unary(f64::log10),
            BuiltinFn::Sin => unary(f64::sin),
            BuiltinFn::Cos => unary(f64::cos),
            BuiltinFn::Tan => unary(f64::tan),
            BuiltinFn::Arcsin => unary(f64::asin),
            BuiltinFn::Arccos => unary(f64::acos),
            BuiltinFn::Arctan => unary(f64::atan),
            BuiltinFn::Floor => unary(f64::floor),
            BuiltinFn::Ceil => unary(f64::ceil),
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
                let t = self.time_at(step);
                amplitude * (2.0 * std::f64::consts::PI / period * (t - self.starttime)).sin()
            }

            // Coswave: amplitude * cos(2π / period * (t - starttime))
            BuiltinFn::Coswave => {
                let amplitude = self.eval_expr(&args[0], state, step);
                let period = self.eval_expr(&args[1], state, step);
                let t = self.time_at(step);
                amplitude * (2.0 * std::f64::consts::PI / period * (t - self.starttime)).cos()
            }

            // Control — step: returns height from the timestep on, as XMILE's STEP does
            BuiltinFn::Step => {
                let height = self.eval_expr(&args[0], state, step);
                let timestep = self.eval_expr(&args[1], state, step);
                let t = self.time_at(step);
                if t >= timestep {
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
                let t = self.time_at(step);

                if interval == 0.0 {
                    // Single pulse at first_pulse
                    if (t - first_pulse).abs() < 1e-10 {
                        volume / self.dt
                    } else {
                        0.0
                    }
                } else {
                    // Repeating pulse: a whole number of intervals since the first one,
                    // within a tolerance - a remainder just below the interval counts too
                    let elapsed = t - first_pulse;
                    let intervals = elapsed / interval;
                    if elapsed >= -1e-10 && (intervals - intervals.round()).abs() < 1e-9 {
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
                // The parser refuses any other first argument; NaN rather than a panic
                // for an expression built some other way.
                let entity_idx = match &args[0] {
                    Expr::Ref(idx) => *idx,
                    _ => return f64::NAN,
                };
                let delay_duration = self.eval_expr(&args[1], state, step);
                let delay_steps = (delay_duration / self.dt).round() as usize;

                // Shorter than half a step, the delay reads its input at this very step.
                // That is only there if the input came earlier in the evaluation order;
                // a delay that closes a loop does not order its input first, and would
                // read what the cell held before. The Python engine meets the same case
                // as a cycle, at the same step.
                if delay_steps == 0 && !self.computed_at_this_step(entity_idx, state) {
                    let current = state.current_entity();
                    state.record_error(format!(
                        "Cyclic dependency among non-stock entities at t={:?}: the delay in \
                         '{}' has a duration of {:?}, less than half of dt={:?}, so it reads \
                         '{}' at the same step, which the loop it closes has not computed yet",
                        self.time_at(step),
                        self.entities[current].name,
                        delay_duration,
                        self.dt,
                        self.entities[entity_idx].name
                    ));
                    return f64::NAN;
                }

                if step >= delay_steps {
                    state.memo[entity_idx][step - delay_steps]
                } else {
                    // Before enough time has elapsed, the initial value - taken at the start
                    // time, as the Python engine and XMILE's DELAY take it. Without an
                    // initial value it is the input itself, and read at the current step
                    // that gave the input of the moment instead of the one at the start.
                    self.eval_expr(&args[2], state, 0)
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
            //
            // Each one: a NaN or infinite argument gives NaN and nothing else - it comes
            // from upstream, a division by zero or an overflow.
            // An argument the builtin does not accept gives NaN and is recorded for the
            // report (`rejected`). The rules are the Python engine's, in
            // `BPTK_Py/sddsl/distributions.py`, and have to stay the same. A distribution
            // constructor that still refuses what the rules let through answers NaN rather
            // than a panic.
            BuiltinFn::Random => {
                let lo = self.eval_expr(&args[0], state, step);
                let hi = self.eval_expr(&args[1], state, step);
                if !lo.is_finite() || !hi.is_finite() {
                    f64::NAN
                } else if lo > hi {
                    self.rejected(state, step, "uniform", &[lo, hi])
                } else if lo.is_finite() && hi.is_finite() {
                    state.rng().gen_range(lo..=hi)
                } else {
                    lo + (hi - lo) * state.rng().gen::<f64>()
                }
            }
            BuiltinFn::Normal => {
                let mean = self.eval_expr(&args[0], state, step);
                let stddev = self.eval_expr(&args[1], state, step);
                if !mean.is_finite() || !stddev.is_finite() {
                    f64::NAN
                } else if stddev < 0.0 {
                    self.rejected(state, step, "normal", &[mean, stddev])
                } else {
                    NormalDist::new(mean, stddev).map_or(f64::NAN, |d| d.sample(&mut *state.rng()))
                }
            }
            BuiltinFn::Beta => {
                let a = self.eval_expr(&args[0], state, step);
                let b = self.eval_expr(&args[1], state, step);
                if !a.is_finite() || !b.is_finite() {
                    f64::NAN
                } else if a <= 0.0 || b <= 0.0 {
                    self.rejected(state, step, "beta", &[a, b])
                } else {
                    BetaDist::new(a, b).map_or(f64::NAN, |d| d.sample(&mut *state.rng()))
                }
            }
            BuiltinFn::Binomial => {
                let n = self.eval_expr(&args[0], state, step);
                let p = self.eval_expr(&args[1], state, step);
                if !n.is_finite() || !p.is_finite() {
                    f64::NAN
                } else if n < 0.0 || n > LARGEST_COUNT || p < 0.0 || p > 1.0 {
                    self.rejected(state, step, "binomial", &[n, p])
                } else {
                    BinomialDist::new(n as u64, p)
                        .map_or(f64::NAN, |d| d.sample(&mut *state.rng()) as f64)
                }
            }
            BuiltinFn::NegBinomial => {
                let n = self.eval_expr(&args[0], state, step);
                let p = self.eval_expr(&args[1], state, step);
                if !n.is_finite() || !p.is_finite() {
                    f64::NAN
                } else if n <= 0.0 || n > LARGEST_COUNT || p <= 0.0 || p > 1.0 {
                    self.rejected(state, step, "negbinomial", &[n, p])
                } else if p >= 1.0 {
                    0.0
                } else {
                    // Failures before n successes, drawn as a Poisson whose rate is
                    // Gamma-distributed - the standard mixture, and constant in n where
                    // adding up n geometric draws took as long as n is large.
                    match GammaDist::new(n, (1.0 - p) / p) {
                        Ok(gamma) => {
                            let rate = gamma.sample(&mut *state.rng());
                            if rate <= 0.0 {
                                0.0
                            } else {
                                PoissonDist::new(rate)
                                    .map_or(f64::NAN, |d| d.sample(&mut *state.rng()))
                            }
                        }
                        Err(_) => f64::NAN,
                    }
                }
            }
            BuiltinFn::Exprnd => {
                // Python: np.random.exponential(scale). scale = 1/rate.
                let scale = self.eval_expr(&args[0], state, step);
                if !scale.is_finite() {
                    f64::NAN
                } else if scale <= 0.0 {
                    self.rejected(state, step, "exprnd", &[scale])
                } else {
                    ExpDist::new(1.0 / scale).map_or(f64::NAN, |d| d.sample(&mut *state.rng()))
                }
            }
            BuiltinFn::GammaDist => {
                let shape = self.eval_expr(&args[0], state, step);
                let scale = if args.len() > 1 {
                    self.eval_expr(&args[1], state, step)
                } else {
                    1.0
                };
                if !shape.is_finite() || !scale.is_finite() {
                    f64::NAN
                } else if shape <= 0.0 || scale <= 0.0 {
                    self.rejected(state, step, "gamma", &[shape, scale])
                } else {
                    GammaDist::new(shape, scale).map_or(f64::NAN, |d| d.sample(&mut *state.rng()))
                }
            }
            BuiltinFn::Geometric => {
                let p = self.eval_expr(&args[0], state, step);
                if !p.is_finite() {
                    f64::NAN
                } else if p <= 0.0 || p > 1.0 {
                    self.rejected(state, step, "geometric", &[p])
                } else {
                    // rand_distr::Geometric returns failures before first success (0-based).
                    // numpy.random.geometric returns trial count including success (1-based).
                    // Add 1 to match Python SD DSL behavior.
                    GeometricDist::new(p)
                        .map_or(f64::NAN, |d| d.sample(&mut *state.rng()) as f64 + 1.0)
                }
            }
            BuiltinFn::Lognormal => {
                let mean = self.eval_expr(&args[0], state, step);
                let stddev = self.eval_expr(&args[1], state, step);
                if !mean.is_finite() || !stddev.is_finite() {
                    f64::NAN
                } else if stddev < 0.0 {
                    self.rejected(state, step, "lognormal", &[mean, stddev])
                } else {
                    LogNormalDist::new(mean, stddev)
                        .map_or(f64::NAN, |d| d.sample(&mut *state.rng()))
                }
            }
            BuiltinFn::Logistic => {
                // Inverse CDF method: mean + scale * ln(u / (1 - u))
                let mean = self.eval_expr(&args[0], state, step);
                let scale = self.eval_expr(&args[1], state, step);
                if !mean.is_finite() || !scale.is_finite() {
                    f64::NAN
                } else if scale < 0.0 {
                    self.rejected(state, step, "logistic", &[mean, scale])
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
                if !mu.is_finite() {
                    f64::NAN
                } else if mu < 0.0 || mu > LARGEST_COUNT {
                    self.rejected(state, step, "poisson", &[mu])
                } else if mu == 0.0 {
                    0.0
                } else {
                    PoissonDist::new(mu).map_or(f64::NAN, |d| d.sample(&mut *state.rng()) as f64)
                }
            }
            BuiltinFn::Triangular => {
                let lower = self.eval_expr(&args[0], state, step);
                let mode = self.eval_expr(&args[1], state, step);
                let upper = self.eval_expr(&args[2], state, step);
                if !lower.is_finite() || !mode.is_finite() || !upper.is_finite() {
                    f64::NAN
                } else if lower == mode && mode == upper {
                    lower
                } else if lower > upper || mode < lower || mode > upper {
                    self.rejected(state, step, "triangular", &[lower, mode, upper])
                } else {
                    TriangularDist::new(lower, upper, mode)
                        .map_or(f64::NAN, |d| d.sample(&mut *state.rng()))
                }
            }
            BuiltinFn::Weibull => {
                // Python: np.random.weibull(shape) * scale
                // Rust: Weibull::new(scale, shape) — scale first, shape second
                let shape = self.eval_expr(&args[0], state, step);
                let scale = self.eval_expr(&args[1], state, step);
                if !shape.is_finite() || !scale.is_finite() {
                    f64::NAN
                } else if shape <= 0.0 || scale <= 0.0 {
                    self.rejected(state, step, "weibull", &[shape, scale])
                } else {
                    WeibullDist::new(scale, shape).map_or(f64::NAN, |d| d.sample(&mut *state.rng()))
                }
            }
            BuiltinFn::Pareto => {
                let shape = self.eval_expr(&args[0], state, step);
                let scale = self.eval_expr(&args[1], state, step);
                if !shape.is_finite() || !scale.is_finite() {
                    f64::NAN
                } else if shape <= 0.0 || scale <= 0.0 {
                    self.rejected(state, step, "pareto", &[shape, scale])
                } else {
                    // rand_distr::Pareto samples from Pareto(xm, alpha) with min=xm.
                    // numpy.random.pareto(a) * scale gives (X-1)*scale where X~Pareto(1,a).
                    // Subtract scale to match Python SD DSL: result = sample - scale.
                    ParetoDist::new(scale, shape)
                        .map_or(f64::NAN, |d| d.sample(&mut *state.rng()) - scale)
                }
            }
            BuiltinFn::Invnorm => {
                // The serializer sends all three, filling in a mean of 0 and a stddev of
                // 1 for whichever was left out; the defaults here are for older JSON.
                let p = self.eval_expr(&args[0], state, step);
                let mean = args.get(1).map_or(0.0, |a| self.eval_expr(a, state, step));
                let stddev = args.get(2).map_or(1.0, |a| self.eval_expr(a, state, step));
                if !p.is_finite() || !mean.is_finite() || !stddev.is_finite() {
                    f64::NAN
                } else if p < 0.0 || p > 1.0 || stddev <= 0.0 {
                    self.rejected(state, step, "invnorm", &[p, mean, stddev])
                } else if p == 0.0 {
                    f64::NEG_INFINITY
                } else if p == 1.0 {
                    f64::INFINITY
                } else {
                    StatrsNormal::new(mean, stddev).map_or(f64::NAN, |d| d.inverse_cdf(p))
                }
            }
            BuiltinFn::NormalCDF => {
                let left = self.eval_expr(&args[0], state, step);
                let right = self.eval_expr(&args[1], state, step);
                let mean = if args.len() > 2 { self.eval_expr(&args[2], state, step) } else { 0.0 };
                let stddev = if args.len() > 3 { self.eval_expr(&args[3], state, step) } else { 1.0 };
                if !left.is_finite() || !right.is_finite() || !mean.is_finite() || !stddev.is_finite() {
                    f64::NAN
                } else if stddev <= 0.0 {
                    self.rejected(state, step, "normalcdf", &[left, right, mean, stddev])
                } else {
                    StatrsNormal::new(mean, stddev)
                        .map_or(f64::NAN, |d| d.cdf(right) - d.cdf(left))
                }
            }

            // ── Array aggregations ──────────────────────────────────────────
            //
            // An arrayed element is flattened into scalar entities, so an aggregation
            // arrives as one variadic call over its leaves, in the order the array
            // declares them. The semantics follow numpy, which is what the Python
            // operators evaluate: the mean is sum/len, the median averages the two
            // middle values on an even count, and the deviation is the population one
            // (numpy's ddof=0 default), not the sample one.
            BuiltinFn::ArrSum => self.eval_args(args, state, step).iter().sum(),

            BuiltinFn::ArrProd => self
                .eval_args(args, state, step)
                .iter()
                .product(),

            BuiltinFn::ArrMean => {
                let values = self.eval_args(args, state, step);
                if values.is_empty() {
                    0.0
                } else {
                    values.iter().sum::<f64>() / values.len() as f64
                }
            }

            BuiltinFn::ArrMedian => {
                let mut values = self.eval_args(args, state, step);
                if values.is_empty() {
                    return 0.0;
                }
                values.sort_by(|a, b| a.partial_cmp(b).unwrap_or(std::cmp::Ordering::Equal));
                let middle = values.len() / 2;
                if values.len() % 2 == 0 {
                    (values[middle - 1] + values[middle]) / 2.0
                } else {
                    values[middle]
                }
            }

            BuiltinFn::ArrStddev => {
                let values = self.eval_args(args, state, step);
                if values.is_empty() {
                    return 0.0;
                }
                let count = values.len() as f64;
                let mean = values.iter().sum::<f64>() / count;
                let variance =
                    values.iter().map(|v| (v - mean) * (v - mean)).sum::<f64>() / count;
                variance.sqrt()
            }

            BuiltinFn::ArrMax => self
                .eval_args(args, state, step)
                .iter()
                .copied()
                .fold(f64::NAN, f64::max),

            BuiltinFn::ArrMin => self
                .eval_args(args, state, step)
                .iter()
                .copied()
                .fold(f64::NAN, f64::min),

            // arr_rank sorts descending and returns the rank-th value, counting from
            // one. A rank outside 1..=count - including zero and negative ranks -
            // gives the *minimum*, which is what the Python operator does: it indexes
            // with `count - 1` when the rank is out of range, and a rank of zero
            // becomes the Python index -1, the last element of the descending sort.
            BuiltinFn::ArrRank => {
                if args.len() < 2 {
                    return 0.0;
                }
                let (rank_arg, value_args) = args.split_last().unwrap();
                let mut values = self.eval_args(value_args, state, step);
                if values.is_empty() {
                    return 0.0;
                }
                values.sort_by(|a, b| b.partial_cmp(a).unwrap_or(std::cmp::Ordering::Equal));

                let count = values.len();
                let rank = self.eval_expr(rank_arg, state, step);
                let position = if rank < 1.0 || rank > count as f64 {
                    count - 1
                } else {
                    rank as usize - 1
                };
                values[position]
            }

            // Lookup — linear interpolation from graphical function
            BuiltinFn::Lookup(table_name) => {
                let x = self.eval_expr(&args[0], state, step);
                self.lookup_interpolate(table_name, x)
            }
        }
    }

    /// Evaluate every argument of a variadic call.
    fn eval_args(&self, args: &[Expr], state: &SimulationState, step: usize) -> Vec<f64> {
        args.iter()
            .map(|arg| self.eval_expr(arg, state, step))
            .collect()
    }
}
