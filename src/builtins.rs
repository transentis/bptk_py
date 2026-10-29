use crate::model::*;
use crate::state::SimulationState;

/// Stella draws again until a value lies within its bounds, and gives up after 100 draws.
const DRAWS_WITHIN_BOUNDS: usize = 100;
use statrs::function::gamma::ln_gamma;
use statrs::distribution::{Normal as StatrsNormal, ContinuousCDF};
use rand::Rng;
use rand::SeedableRng;
use rand::rngs::StdRng;
use crate::json_parser::{bounds_report, draw_of, seeded_draw_name};
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
    /// A mathematical function of one argument: NaN, recorded, for a finite argument outside
    /// its domain - as the Python engine reports it. An infinite one is left to the function.
    fn in_domain(
        &self,
        args: &[Expr],
        state: &SimulationState,
        step: usize,
        name: &'static str,
        math: fn(f64) -> f64,
        outside: fn(f64) -> bool,
    ) -> f64 {
        let x = self.eval_expr(&args[0], state, step);
        if x.is_finite() && outside(x) {
            return self.rejected(state, step, name, &[x]);
        }
        math(x)
    }

    /// A conveyor's transit time at `step`, or the recorded error the Python engine raises.
    fn conveyor_transit(&self, conveyor: usize, transit: f64, state: &SimulationState, step: usize) -> Option<f64> {
        if transit.is_finite() && transit > 0.0 {
            return Some(transit);
        }
        state.record_error(format!(
            "The transit time of conveyor '{}' is {} at t={}. It has to be greater than zero.",
            self.entities[conveyor].name,
            python_float(transit),
            python_float(self.time_at(step))
        ));
        None
    }

    /// A conveyor's leak fractions at `step`, or the recorded error the Python engine raises.
    fn conveyor_fractions(&self, conveyor: usize, args: &[Expr], state: &SimulationState, step: usize) -> Option<Vec<f64>> {
        let fractions = self.eval_args(args, state, step);
        for (k, &fraction) in fractions.iter().enumerate() {
            if !(fraction.is_finite() && fraction >= 0.0) {
                // The leak's name: the flow whose equation drives leak k of this conveyor
                let leak = self
                    .entities
                    .iter()
                    .find(|entity| match &entity.equation {
                        Expr::Call { function: BuiltinFn::ConveyorFlow, args } => {
                            matches!(args[0], Expr::Ref(idx) if idx == conveyor)
                                && matches!(args[1], Expr::Literal(which) if which == k as f64)
                        }
                        _ => false,
                    })
                    .map_or("?", |entity| entity.name.as_str());
                state.record_error(format!(
                    "The leak fraction of '{}' on conveyor '{}' is {} at t={}. It has to be zero or more.",
                    leak,
                    self.entities[conveyor].name,
                    python_float(fraction),
                    python_float(self.time_at(step))
                ));
                return None;
            }
        }
        Some(fractions)
    }

    /// The belt at the start: `ConveyorStart`'s arguments are fifo, exponential, transit,
    /// the number of fractions and the fractions, then the length of the initial list (0
    /// for a total) and the total or the list.
    fn conveyor_start(&self, args: &[Expr], state: &SimulationState, step: usize) -> f64 {
        let conveyor = state.current_entity();
        let fifo = self.eval_expr(&args[0], state, step) != 0.0;
        let exponential = self.eval_expr(&args[1], state, step) != 0.0;
        let count = self.eval_expr(&args[3], state, step) as usize;
        let (fraction_args, rest) = args[4..].split_at(count);
        let length = self.eval_expr(&rest[0], state, step) as usize;
        let transit = self.eval_expr(&args[2], state, step);
        let Some(transit) = self.conveyor_transit(conveyor, transit, state, step) else { return f64::NAN };
        let Some(fractions) = self.conveyor_fractions(conveyor, fraction_args, state, step) else { return f64::NAN };
        let initial = if length == 0 {
            crate::conveyor::Initial::Total(self.eval_expr(&rest[1], state, step))
        } else {
            crate::conveyor::Initial::List(self.eval_args(&rest[1..=length], state, step))
        };
        let belt = crate::conveyor::filled(fifo, exponential, self.time_at(step), self.dt, transit, &fractions, &initial);
        let contents = belt.contents();
        let mut conveyors = state.conveyors.lock().expect("conveyor mutex poisoned");
        let belts = conveyors.entry(conveyor).or_default();
        // A start computed again - step 0 is settled in rounds - begins afresh
        belts.belts.clear();
        belts.moves.clear();
        belts.belts.insert(step, belt);
        contents
    }

    /// The outflow (`which` = -1) or leak `which` of a conveyor at `step`. The first of its
    /// flows asked moves the belt; the others read what it moved.
    fn conveyor_flow(&self, args: &[Expr], state: &SimulationState, step: usize) -> f64 {
        let conveyor = match &args[0] {
            Expr::Ref(idx) => *idx,
            _ => return f64::NAN,
        };
        let which = self.eval_expr(&args[1], state, step);
        let read = |moves: &crate::conveyor::Moves| {
            if which < 0.0 { moves.exited / self.dt } else { moves.leaked[which as usize] / self.dt }
        };
        {
            let conveyors = state.conveyors.lock().expect("conveyor mutex poisoned");
            match conveyors.get(&conveyor) {
                Some(belts) => {
                    if let Some(moves) = belts.moves.get(&step) {
                        return read(moves);
                    }
                    // Before the start is computed - the first pass over step 0 - there is
                    // no belt yet; the pass after the start reads it
                    if !belts.belts.contains_key(&step) {
                        return 0.0;
                    }
                }
                None => return 0.0,
            }
        }
        let transit = self.eval_expr(&args[2], state, step);
        let Some(transit) = self.conveyor_transit(conveyor, transit, state, step) else { return f64::NAN };
        let inflow = self.eval_expr(&args[3], state, step) * self.dt;
        let Some(fractions) = self.conveyor_fractions(conveyor, &args[4..], state, step) else { return f64::NAN };
        let mut conveyors = state.conveyors.lock().expect("conveyor mutex poisoned");
        let belts = conveyors.get_mut(&conveyor).expect("checked above");
        let (moves, following) = belts.belts[&step].advance(self.time_at(step), self.dt, inflow, transit, &fractions);
        let value = read(&moves);
        belts.moves.insert(step, moves);
        belts.belts.insert(step + 1, following);
        belts.belts.retain(|&kept, _| kept + 1 >= step);
        belts.moves.retain(|&kept, _| kept + 1 >= step);
        value
    }

    /// Whether `entity` already holds its value for the step being evaluated: at the start
    /// if it comes before the entity being evaluated now in the start's order; later a
    /// stock does from the step before, anything else if it comes before in the step's.
    fn computed_at_this_step(&self, entity: usize, state: &SimulationState) -> bool {
        let before = |order: &[usize]| {
            let position = |idx| order.iter().position(|&e| e == idx);
            match (position(entity), position(state.current_entity())) {
                (Some(input), Some(current)) => input < current,
                _ => false,
            }
        };
        if state.starting() {
            return before(&self.init_order);
        }
        if matches!(self.entities[entity].kind, EntityKind::Stock { .. }) {
            return true;
        }
        // A stock's equation is evaluated after every non-stock of the step
        if matches!(self.entities[state.current_entity()].kind, EntityKind::Stock { .. }) {
            return true;
        }
        before(&self.eval_order)
    }

    /// NaN for arguments it does not accept, recorded so that it can be reported.
    /// An argument as its value at `step` - a draw inside `bounded` stays a call, with its own
    /// arguments as values, so that it can be drawn again.
    fn literal(&self, arg: &Expr, state: &SimulationState, step: usize) -> Expr {
        match arg {
            Expr::Call { function, args } if seeded_draw_name(function).is_some() => Expr::Call {
                function: function.clone(),
                args: args.iter().map(|a| Expr::Literal(self.eval_expr(a, state, step))).collect(),
            },
            _ => Expr::Literal(self.eval_expr(arg, state, step)),
        }
    }

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
            BuiltinFn::Sqrt => self.in_domain(args, state, step, "sqrt", f64::sqrt, |x| x < 0.0),
            BuiltinFn::Exp => unary(f64::exp),
            BuiltinFn::Ln => self.in_domain(args, state, step, "ln", f64::ln, |x| x < 0.0),
            BuiltinFn::Log10 => self.in_domain(args, state, step, "log10", f64::log10, |x| x < 0.0),
            BuiltinFn::Sin => unary(f64::sin),
            BuiltinFn::Cos => unary(f64::cos),
            BuiltinFn::Tan => unary(f64::tan),
            BuiltinFn::Arcsin => self.in_domain(args, state, step, "arcsin", f64::asin, |x| x.abs() > 1.0),
            BuiltinFn::Arccos => self.in_domain(args, state, step, "arccos", f64::acos, |x| x.abs() > 1.0),
            BuiltinFn::Arctan => unary(f64::atan),
            BuiltinFn::Floor => unary(f64::floor),
            BuiltinFn::Ceil => unary(f64::ceil),
            BuiltinFn::Trunc => unary(f64::trunc),
            BuiltinFn::Round => {
                let v = self.eval_expr(&args[0], state, step);
                if args.len() > 1 {
                    // As the Python engine: digits beyond a float leave the value, below it 0
                    let digits = self.eval_expr(&args[1], state, step);
                    if !digits.is_finite() {
                        return f64::NAN;
                    }
                    if !v.is_finite() || digits > 308.0 {
                        return v;
                    }
                    if digits < -308.0 {
                        return 0.0;
                    }
                    let factor = 10.0_f64.powf(digits);
                    if (v.abs() * factor).is_infinite() {
                        return v;
                    }
                    (v * factor).round() / factor
                } else {
                    v.round()
                }
            }

            // Math — two arguments
            BuiltinFn::Max => {
                let a = self.eval_expr(&args[0], state, step);
                let b = self.eval_expr(&args[1], state, step);
                // NaN in either gives NaN: f64::max returns the other operand
                if a.is_nan() || b.is_nan() { f64::NAN } else { a.max(b) }
            }
            BuiltinFn::Min => {
                let a = self.eval_expr(&args[0], state, step);
                let b = self.eval_expr(&args[1], state, step);
                if a.is_nan() || b.is_nan() { f64::NAN } else { a.min(b) }
            }

            // Math — constant
            BuiltinFn::Pi => std::f64::consts::PI,

            // Sinwave: amplitude * sin(2π / period * (t - starttime))
            BuiltinFn::Sinwave => {
                let amplitude = self.eval_expr(&args[0], state, step);
                let period = self.eval_expr(&args[1], state, step);
                // 2π over the period: a period of 0 divides by zero
                if period == 0.0 {
                    state.record_invalid("division", step, &[]);
                    return f64::NAN;
                }
                let t = self.time_at(step);
                amplitude * (2.0 * std::f64::consts::PI / period * (t - self.starttime)).sin()
            }

            // Coswave: amplitude * cos(2π / period * (t - starttime))
            BuiltinFn::Coswave => {
                let amplitude = self.eval_expr(&args[0], state, step);
                let period = self.eval_expr(&args[1], state, step);
                // 2π over the period: a period of 0 divides by zero
                if period == 0.0 {
                    state.record_invalid("division", step, &[]);
                    return f64::NAN;
                }
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
            // pulse(volume, [first_pulse], [interval]); the first pulse defaults to the start
            BuiltinFn::Pulse => {
                let volume = self.eval_expr(&args[0], state, step);
                let first_pulse = if args.len() > 1 {
                    self.eval_expr(&args[1], state, step)
                } else {
                    self.starttime
                };
                let interval = if args.len() > 2 {
                    self.eval_expr(&args[2], state, step)
                } else {
                    0.0
                };
                let t = self.time_at(step);

                // A pulse fires in the first step that reaches its time, as in Stella: a
                // step fires when a pulse time lies in (t - dt, t], within a tolerance
                let elapsed = t - first_pulse;
                let before = elapsed - self.dt;
                let fires = if interval == 0.0 {
                    elapsed >= -1e-10 && before < -1e-10
                } else {
                    // The index of the last pulse up to a time since the first one, -1 before it
                    let passed = |x: f64| {
                        if x >= -1e-10 {
                            (x / interval + 1e-9).floor()
                        } else {
                            -1.0
                        }
                    };
                    passed(elapsed) > passed(before)
                };
                if fires {
                    volume / self.dt
                } else {
                    0.0
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
                if delay_duration.is_nan() {
                    return f64::NAN;
                }
                // A negative duration would read the future
                if delay_duration < 0.0 {
                    return self.rejected(state, step, "delay", &[delay_duration]);
                }
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

            // Stella's IRR over the stream's values from STARTTIME up to this step
            BuiltinFn::Irr => {
                let entity_idx = match &args[0] {
                    Expr::Ref(idx) => *idx,
                    _ => return f64::NAN,
                };
                let flows: Vec<(f64, f64)> = (0..=step)
                    .map(|i| (state.memo[entity_idx][i], self.time_at(i) - self.starttime))
                    .collect();
                match internal_rate_of_return(&flows) {
                    Some(rate) => rate,
                    None => self.eval_expr(&args[1], state, step),
                }
            }

            // Stella's RUNCUM, RUNMAX, RUNMIN and RUNMEAN over the steps from `from` to `to`,
            // the current one included; a window without a step gives NaN
            BuiltinFn::RunCum | BuiltinFn::RunMax | BuiltinFn::RunMin | BuiltinFn::RunMean => {
                let entity_idx = match &args[0] {
                    Expr::Ref(idx) => *idx,
                    _ => return f64::NAN,
                };
                let from = self.eval_expr(&args[1], state, step);
                let to = self.eval_expr(&args[2], state, step);
                if from.is_nan() || to.is_nan() {
                    return f64::NAN;
                }
                let Some((first, last)) = self.run_steps(step, from, to) else {
                    return f64::NAN;
                };
                let values = &state.memo[entity_idx][first..=last];
                match function {
                    BuiltinFn::RunCum => {
                        let mut total = 0.0;
                        for value in values {
                            total += value * self.dt;
                        }
                        total
                    }
                    BuiltinFn::RunMax => values.iter().cloned().fold(f64::NEG_INFINITY, f64::max),
                    BuiltinFn::RunMin => values.iter().cloned().fold(f64::INFINITY, f64::min),
                    _ => {
                        let mut total = 0.0;
                        for value in values {
                            total += value;
                        }
                        total / values.len() as f64
                    }
                }
            }

            // Stella's RUNCUMTARGET: at the first step where the running sum of the
            // stream's magnitude times DT reaches the target, that step's time plus the
            // share of the step the rest takes; NaN before. Stella sums the magnitude.
            BuiltinFn::RunCumTarget => {
                let entity_idx = match &args[0] {
                    Expr::Ref(idx) => *idx,
                    _ => return f64::NAN,
                };
                let target = self.eval_expr(&args[1], state, step);
                if target.is_nan() {
                    return f64::NAN;
                }
                let mut total = 0.0;
                for i in 0..=step {
                    let time = self.time_at(i);
                    let rate = state.memo[entity_idx][i].abs();
                    let before = total;
                    total += rate * self.dt;
                    if total >= target {
                        return if rate > 0.0 { time + (target - before) / rate } else { time };
                    }
                }
                f64::NAN
            }

            // Combinatorial & special
            // Whole numbers of at least 0 only; a NaN or an infinite argument gives NaN
            // without a report, as for the statistical functions. The products are
            // multiplied in the order the Python engine multiplies them.
            BuiltinFn::Combinations => {
                let n = self.eval_expr(&args[0], state, step);
                let r = self.eval_expr(&args[1], state, step);
                if !n.is_finite() || !r.is_finite() {
                    f64::NAN
                } else if !(is_whole(n) && is_whole(r)) {
                    self.rejected(state, step, "combinations", &[n, r])
                } else if r > n {
                    0.0
                } else {
                    choose(n, r)
                }
            }
            BuiltinFn::Permutations => {
                let n = self.eval_expr(&args[0], state, step);
                let r = self.eval_expr(&args[1], state, step);
                if !n.is_finite() || !r.is_finite() {
                    f64::NAN
                } else if !(is_whole(n) && is_whole(r)) {
                    self.rejected(state, step, "permutations", &[n, r])
                } else if r > n {
                    0.0
                } else {
                    falling_product(n, r)
                }
            }
            BuiltinFn::Factorial => {
                let n = self.eval_expr(&args[0], state, step);
                if !n.is_finite() {
                    f64::NAN
                } else if !is_whole(n) {
                    self.rejected(state, step, "factorial", &[n])
                } else {
                    falling_product(n, n)
                }
            }
            BuiltinFn::GammaLN => gamma_ln(self.eval_expr(&args[0], state, step)),
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
                } else if mean <= 0.0 || stddev < 0.0 {
                    self.rejected(state, step, "lognormal", &[mean, stddev])
                } else {
                    // XMILE's mean and stddev are those of the distribution itself; the
                    // sampler takes the normal distribution underneath.
                    let variance = (stddev / mean).powi(2).ln_1p();
                    LogNormalDist::new(mean.ln() - variance / 2.0, variance.sqrt())
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
                // The mean is per time unit, as in XMILE and Stella: a step draws with mu * dt
                let mu = self.eval_expr(&args[0], state, step) * self.dt;
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
                    // The classic Pareto of Stella's help, starting at scale with exponent
                    // shape - rand_distr::Pareto(xm, alpha) with min = xm
                    ParetoDist::new(scale, shape)
                        .map_or(f64::NAN, |d| d.sample(&mut *state.rng()))
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
            BuiltinFn::ArrLargest => {
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
                // `as usize` makes NaN 0, and 0 - 1 underflows
                if rank.is_nan() {
                    return f64::NAN;
                }
                let position = if rank < 1.0 || rank > count as f64 {
                    count - 1
                } else {
                    rank as usize - 1
                };
                values[position]
            }

            // XMILE's RANK: the position, counting from 1, of the rank-th smallest value.
            // Equal values are ordered by their tiebreak values, then by position.
            BuiltinFn::ArrRank => {
                let rank = self.eval_expr(&args[0], state, step);
                let count = (args.len() - 1) / 2;
                let values = self.eval_args(&args[1..=count], state, step);
                let breaks = self.eval_args(&args[count + 1..], state, step);
                if !(rank.is_finite() && rank == rank.trunc() && rank >= 1.0 && rank <= count as f64) {
                    return self.rejected(state, step, "arr_rank", &[rank, count as f64]);
                }
                let mut order: Vec<usize> = (0..count).collect();
                order.sort_by(|&a, &b| {
                    values[a]
                        .partial_cmp(&values[b])
                        .unwrap_or(std::cmp::Ordering::Equal)
                        .then(breaks[a].partial_cmp(&breaks[b]).unwrap_or(std::cmp::Ordering::Equal))
                        .then(a.cmp(&b))
                });
                (order[rank as usize - 1] + 1) as f64
            }

            // Stella's PERCENTILE, with or without weights; a lower percentile above 0 is
            // taken off the result
            BuiltinFn::ArrPercentile => {
                let weighted = self.eval_expr(&args[0], state, step) != 0.0;
                let percentile = self.eval_expr(&args[1], state, step);
                let lower = self.eval_expr(&args[2], state, step);
                let count = (args.len() - 3) / 2;
                let values = self.eval_args(&args[3..3 + count], state, step);
                let weights = self.eval_args(&args[3 + count..], state, step);
                if values.iter().any(|v| v.is_nan()) || percentile.is_nan() || lower.is_nan() {
                    return f64::NAN;
                }
                let (smallest, total) = if weighted {
                    (weights.iter().cloned().fold(f64::INFINITY, f64::min), weights.iter().sum::<f64>())
                } else {
                    (1.0, 1.0)
                };
                if !((0.0..=100.0).contains(&percentile) && (0.0..=100.0).contains(&lower))
                    || smallest < 0.0
                    || total <= 0.0
                {
                    return self.rejected(state, step, "arr_percentile", &[percentile, lower, smallest, total]);
                }
                let mut order: Vec<usize> = (0..count).collect();
                order.sort_by(|&a, &b| values[a].partial_cmp(&values[b]).unwrap_or(std::cmp::Ordering::Equal).then(a.cmp(&b)));
                let sorted: Vec<f64> = order.iter().map(|&i| values[i]).collect();
                let sorted_weights: Option<Vec<f64>> =
                    if weighted { Some(order.iter().map(|&i| weights[i]).collect()) } else { None };
                let mut result = percentile_at(&sorted, sorted_weights.as_deref(), percentile);
                if lower > 0.0 {
                    result -= percentile_at(&sorted, sorted_weights.as_deref(), lower);
                }
                result
            }

            // Stella's INTERPOLATE: multilinear between the values of a vector or a matrix,
            // each weight in [0, 1] - 0 is the first value of its dimension, 1 the last
            BuiltinFn::ArrInterpolate => {
                let columns = self.eval_expr(&args[0], state, step).max(0.0) as usize;
                let depth = if columns == 0 { 1 } else { 2 };
                let weights = self.eval_args(&args[1..=depth], state, step);
                let values = self.eval_args(&args[depth + 1..], state, step);
                if values.is_empty() || !weights.iter().all(|weight| weight.is_finite()) {
                    return f64::NAN;
                }
                let weights: Vec<f64> = weights.iter().map(|weight| weight.clamp(0.0, 1.0)).collect();
                let along = |line: &[f64], weight: f64| -> f64 {
                    if line.len() == 1 {
                        return line[0];
                    }
                    let position = weight * (line.len() - 1) as f64;
                    let lower = (position.floor() as usize).min(line.len() - 2);
                    let share = position - lower as f64;
                    line[lower] + share * (line[lower + 1] - line[lower])
                };
                if columns == 0 {
                    along(&values, weights[0])
                } else {
                    let rows: Vec<f64> = values.chunks(columns).map(|row| along(row, weights[1])).collect();
                    along(&rows, weights[0])
                }
            }

            // A draw with a seed, from a generator of its own made from the seed, the step and
            // the cell - so it does not depend on the order of evaluation or on the draws
            // before it, and a resumed run draws what an uninterrupted one does. The draw's
            // arguments are evaluated first, from the run's generator if they draw themselves.
            BuiltinFn::Seeded => {
                let (draw, keys) = args[1..].split_last().expect("the parser checks the arity");
                let (function, draw_args) = match draw {
                    Expr::Call { function, args } => (function, args),
                    _ => return f64::NAN,
                };
                let name = match draw_of(draw).and_then(seeded_draw_name) {
                    Some(name) => name,
                    None => return f64::NAN,
                };
                let seed = self.eval_expr(&args[0], state, step);
                if !(seed.is_finite() && seed >= 0.0 && seed == seed.trunc()) {
                    return self.rejected(state, step, name, &[seed]);
                }
                let values: Vec<Expr> = draw_args.iter().map(|arg| self.literal(arg, state, step)).collect();
                let mut hash = splitmix64(seed as u64);
                hash = splitmix64(hash ^ step as u64);
                hash = splitmix64(hash ^ keys.len() as u64);
                for key in keys {
                    hash = splitmix64(hash ^ self.eval_expr(key, state, step) as u64);
                }
                let run = state.swap_rng(StdRng::seed_from_u64(hash));
                let value = self.eval_builtin(function, &values, state, step);
                state.swap_rng(run);
                value
            }

            // A draw within bounds: drawn again until it lies within them, both included; NaN
            // and a report when no draw of 100 does, as when the minimum is above the maximum.
            // Equal bounds give that value, a NaN bound is none. The draw's arguments are read
            // once, so that every try draws with the same ones.
            BuiltinFn::Bounded => {
                let minimum = self.eval_expr(&args[0], state, step);
                let maximum = self.eval_expr(&args[1], state, step);
                let draw = self.literal(&args[2], state, step);
                let function = match &draw {
                    Expr::Call { function, .. } => function,
                    _ => return f64::NAN,
                };
                let lower = if minimum.is_nan() { f64::NEG_INFINITY } else { minimum };
                let upper = if maximum.is_nan() { f64::INFINITY } else { maximum };
                if lower > upper {
                    return self.rejected(state, step, bounds_report(function, true), &[minimum, maximum]);
                }
                if lower == upper {
                    return lower;
                }
                for _ in 0..DRAWS_WITHIN_BOUNDS {
                    let value = self.eval_expr(&draw, state, step);
                    if value.is_nan() {
                        return value;
                    }
                    if lower <= value && value <= upper {
                        return value;
                    }
                }
                self.rejected(state, step, bounds_report(function, false), &[minimum, maximum])
            }

            // A draw read when its sample began: the sample cut down to whole steps, counted
            // from the start, one under a step for every step. An unseeded draw is kept for the
            // sample; a seeded one would give the same value again anyway.
            BuiltinFn::Sample => {
                let sample = self.eval_expr(&args[0], state, step);
                let steps = if sample.is_finite() { (sample / self.dt + 1e-9).floor() } else { 0.0 };
                let began = if steps <= 1.0 { step } else { step - step % steps as usize };
                let node = &args[1] as *const Expr as usize;
                if let Some(value) = state.held(node, began) {
                    return value;
                }
                let value = self.eval_expr(&args[1], state, began);
                state.hold(node, began, value);
                value
            }

            // A non-negative stock's flows, written out by the serializer: what is available
            // is the stock over dt, the inflows it may count, less what was served before.
            // The comparisons are those of Python's max and min, so NaN goes where it goes
            // on the Python engine.
            BuiltinFn::Positive => python_max(0.0, self.eval_expr(&args[0], state, step)),
            BuiltinFn::CutOut => {
                let wanted = self.eval_expr(&args[0], state, step);
                if wanted <= 0.0 {
                    return wanted;
                }
                let available = self.eval_expr(&args[1], state, step);
                python_max(0.0, python_min(wanted, available))
            }
            BuiltinFn::CutIn => {
                let wanted = self.eval_expr(&args[0], state, step);
                if wanted >= 0.0 {
                    return wanted;
                }
                let available = self.eval_expr(&args[1], state, step);
                -python_max(0.0, python_min(-wanted, available))
            }

            // A conveyor's belt lives in the state, one step at a time
            BuiltinFn::ConveyorStart => self.conveyor_start(args, state, step),
            BuiltinFn::ConveyorFlow => self.conveyor_flow(args, state, step),
            BuiltinFn::ConveyorChange => {
                let conveyor = state.current_entity();
                let next = state
                    .conveyors
                    .lock()
                    .expect("conveyor mutex poisoned")
                    .get(&conveyor)
                    .and_then(|belts| belts.belts.get(&(step + 1)).map(|belt| belt.contents()));
                match next {
                    Some(contents) => (contents - state.memo[conveyor][step]) / self.dt,
                    None => 0.0,
                }
            }
            BuiltinFn::AgeCount => {
                let conveyor = match &args[0] {
                    Expr::Ref(idx) => *idx,
                    _ => return f64::NAN,
                };
                let minimum = self.eval_expr(&args[1], state, step);
                let given = self.eval_expr(&args[2], state, step);
                // As Stella: no maximum counts everything from minimum on, and a maximum
                // equal to minimum the one step of material of that age rather than nothing
                let maximum = if given.is_nan() {
                    f64::INFINITY
                } else if (given - minimum).abs() < 1e-9 {
                    minimum + self.dt
                } else {
                    given
                };
                let t = self.time_at(step);
                state
                    .conveyors
                    .lock()
                    .expect("conveyor mutex poisoned")
                    .get(&conveyor)
                    .and_then(|belts| belts.belts.get(&step).map(|belt| belt.agecount(t, minimum, maximum)))
                    .unwrap_or(0.0)
            }

            // Lookup — from a graphical function, by its kind
            BuiltinFn::Lookup(table_name, kind) => {
                let x = self.eval_expr(&args[0], state, step);
                self.lookup(table_name, x, *kind)
            }
            BuiltinFn::LookupInv(table_name, kind) => {
                let y = self.eval_expr(&args[0], state, step);
                self.lookup_inverse(table_name, y, *kind)
            }
            BuiltinFn::LookupArea(table_name, kind) => {
                let from = self.eval_expr(&args[0], state, step);
                let to = self.eval_expr(&args[1], state, step);
                self.lookup_area(table_name, from, to, *kind)
            }
            // Stella's LOOKUPRANDOM: a segment chosen by its area, then a point uniformly
            // within it - one uniform draw does both, by walking the areas until it is used up
            BuiltinFn::LookupRandom(table_name, _) => {
                let table = match self.graphical_functions.get(table_name) {
                    Some(gf) => gf.points.clone(),
                    None => return 0.0,
                };
                let areas: Vec<f64> = table
                    .windows(2)
                    .map(|pair| (pair[1].0 - pair[0].0) * (pair[0].1 + pair[1].1) / 2.0)
                    .collect();
                let total: f64 = areas.iter().sum();
                if table.iter().any(|&(_, y)| y < 0.0) || !(total > 0.0) {
                    return self.rejected(state, step, "lookuprandom", &[]);
                }
                let mut rest = state.rng().gen::<f64>() * total;
                for (pair, &area) in table.windows(2).zip(areas.iter()) {
                    if area > 0.0 && rest < area {
                        return pair[0].0 + rest / area * (pair[1].0 - pair[0].0);
                    }
                    rest -= area;
                }
                table[table.len() - 1].0
            }
            BuiltinFn::LookupMax(table_name, kind)
            | BuiltinFn::LookupMin(table_name, kind)
            | BuiltinFn::LookupMean(table_name, kind) => {
                let from = self.eval_expr(&args[0], state, step);
                let to = self.eval_expr(&args[1], state, step);
                let statistic = match function {
                    BuiltinFn::LookupMax(..) => LookupStatistic::Max,
                    BuiltinFn::LookupMin(..) => LookupStatistic::Min,
                    _ => LookupStatistic::Mean,
                };
                self.lookup_statistic(table_name, statistic, from, to, *kind)
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

/// The rate r at which the values, each discounted by (1 + r)^exponent, sum to zero - the one
/// nearest zero when there are several, `None` when there is none or fewer than two values.
///
/// As the Python engine finds it: a sign change of the net present value on the same grid of
/// rates, each one refined by Brent's method with scipy's `brentq` tolerances.
pub fn internal_rate_of_return(flows: &[(f64, f64)]) -> Option<f64> {
    if flows.len() < 2 {
        return None;
    }
    let npv = |rate: f64| -> f64 {
        flows.iter().map(|&(value, exponent)| value / (1.0 + rate).powf(exponent)).sum()
    };
    // numpy's linspace(-0.99, 1.0, 400), then linspace(1.0, 10.0, 91) without its first point
    let mut candidates: Vec<f64> = (0..400).map(|i| i as f64 * ((1.0 - -0.99) / 399.0) - 0.99).collect();
    candidates[399] = 1.0;
    candidates.extend((1..91).map(|i| i as f64 * ((10.0 - 1.0) / 90.0) + 1.0));
    candidates[489] = 10.0;
    let npvs: Vec<f64> = candidates.iter().map(|&rate| npv(rate)).collect();

    let mut nearest: Option<f64> = None;
    for i in 0..candidates.len() - 1 {
        let (a, b) = (npvs[i], npvs[i + 1]);
        // A root inside the interval or on one of its ends; a stream of zeros has none
        if a.is_finite() && b.is_finite() && a * b <= 0.0 && (a != 0.0 || b != 0.0) {
            let root = brentq(&npv, candidates[i], candidates[i + 1]);
            if nearest.is_none_or(|best| root.abs() < best.abs()) {
                nearest = Some(root);
            }
        }
    }
    nearest
}

/// scipy's `brentq` (`scipy/optimize/Zeros/brentq.c`) with its default tolerances, so that
/// both engines refine a bracket to the same root. The caller makes sure the bracket holds
/// a sign change.
fn brentq(f: &dyn Fn(f64) -> f64, xa: f64, xb: f64) -> f64 {
    const XTOL: f64 = 2e-12;
    const RTOL: f64 = 4.0 * f64::EPSILON;
    const MAXITER: usize = 100;
    let (mut xpre, mut xcur) = (xa, xb);
    let (mut xblk, mut fblk, mut spre, mut scur) = (0.0, 0.0, 0.0, 0.0);
    let mut fpre = f(xpre);
    let mut fcur = f(xcur);
    if fpre == 0.0 {
        return xpre;
    }
    if fcur == 0.0 {
        return xcur;
    }
    for _ in 0..MAXITER {
        if fpre != 0.0 && fcur != 0.0 && fpre.is_sign_negative() != fcur.is_sign_negative() {
            xblk = xpre;
            fblk = fpre;
            spre = xcur - xpre;
            scur = spre;
        }
        if fblk.abs() < fcur.abs() {
            xpre = xcur;
            xcur = xblk;
            xblk = xpre;
            fpre = fcur;
            fcur = fblk;
            fblk = fpre;
        }
        let delta = (XTOL + RTOL * xcur.abs()) / 2.0;
        let sbis = (xblk - xcur) / 2.0;
        if fcur == 0.0 || sbis.abs() < delta {
            return xcur;
        }
        if spre.abs() > delta && fcur.abs() < fpre.abs() {
            let stry = if xpre == xblk {
                // interpolate
                -fcur * (xcur - xpre) / (fcur - fpre)
            } else {
                // extrapolate
                let dpre = (fpre - fcur) / (xpre - xcur);
                let dblk = (fblk - fcur) / (xblk - xcur);
                -fcur * (fblk * dblk - fpre * dpre) / (dblk * dpre * (fblk - fpre))
            };
            if 2.0 * stry.abs() < spre.abs().min(3.0 * sbis.abs() - delta) {
                spre = scur;
                scur = stry;
            } else {
                spre = sbis;
                scur = sbis;
            }
        } else {
            spre = sbis;
            scur = sbis;
        }
        xpre = xcur;
        fpre = fcur;
        if scur.abs() > delta {
            xcur += scur;
        } else {
            xcur += if sbis > 0.0 { delta } else { -delta };
        }
        fcur = f(xcur);
    }
    xcur
}

/// One round of SplitMix64: mixes the seed, the step and the cell into the seed of a draw's
/// generator, so that neighbouring steps and cells start far apart.
fn splitmix64(value: u64) -> u64 {
    let mut z = value.wrapping_add(0x9E37_79B9_7F4A_7C15);
    z = (z ^ (z >> 30)).wrapping_mul(0xBF58_476D_1CE4_E5B9);
    z = (z ^ (z >> 27)).wrapping_mul(0x94D0_49BB_1331_11EB);
    z ^ (z >> 31)
}

/// Python's max of two: the second when it is greater, else the first - so a NaN second
/// gives the first, and a NaN first stays.
fn python_max(a: f64, b: f64) -> f64 {
    if b > a { b } else { a }
}

/// Python's min of two: the second when it is smaller, else the first.
fn python_min(a: f64, b: f64) -> f64 {
    if b < a { b } else { a }
}

/// A number as Python prints it in a message: `nan` and `inf` rather than Rust's spelling.
fn python_float(value: f64) -> String {
    if value.is_nan() {
        "nan".to_string()
    } else if value.is_infinite() {
        if value > 0.0 { "inf".to_string() } else { "-inf".to_string() }
    } else {
        format!("{:?}", value)
    }
}

fn is_whole(value: f64) -> bool {
    value >= 0.0 && value == value.trunc()
}

/// n * (n - 1) * ... over `count` factors, in this order - as the Python engine multiplies.
/// Past the range of a float the product is infinity, and the loop ends there.
fn falling_product(n: f64, count: f64) -> f64 {
    let mut result = 1.0;
    for i in 0..count as u64 {
        result *= n - i as f64;
        if result.is_infinite() {
            break;
        }
    }
    result
}

/// n over r, factor by factor as the Python engine builds it: exact while it fits.
fn choose(n: f64, r: f64) -> f64 {
    let k = r.min(n - r);
    let mut result = 1.0;
    for i in 1..=k as u64 {
        result = result * (n - k + i as f64) / i as f64;
        if result.is_infinite() {
            break;
        }
    }
    result
}

/// The natural log of Γ(x), as Stella and the Python engine: NaN for every argument of 0
/// and below, where Γ has poles and changes sign.
fn gamma_ln(x: f64) -> f64 {
    if x.is_nan() || x <= 0.0 {
        return f64::NAN;
    }
    if x.is_infinite() {
        return x;
    }
    ln_gamma(x)
}

/// Stella's two rules for PERCENTILE. Without weights: the rank percentile * (n - 1) / 100,
/// a whole rank giving its value, any other the mean of its two neighbours - a staircase.
/// With weights: each value at the middle of its weight, the mean of two neighbours at the
/// border between them, a straight line in between, held beyond the outer middles.
fn percentile_at(sorted: &[f64], weights: Option<&[f64]>, percentile: f64) -> f64 {
    let count = sorted.len();
    let Some(weights) = weights else {
        let rank = percentile / 100.0 * (count - 1) as f64;
        let (lower, upper) = (rank.floor() as usize, rank.ceil() as usize);
        return if lower == upper { sorted[lower] } else { (sorted[lower] + sorted[upper]) / 2.0 };
    };
    let total: f64 = weights.iter().sum();
    let mut points = Vec::with_capacity(2 * count);
    let mut below = 0.0;
    for position in 0..count {
        points.push(((below + weights[position] / 2.0) / total * 100.0, sorted[position]));
        below += weights[position];
        if position < count - 1 {
            points.push((below / total * 100.0, (sorted[position] + sorted[position + 1]) / 2.0));
        }
    }
    if percentile <= points[0].0 {
        return points[0].1;
    }
    for pair in points.windows(2) {
        let ((x0, y0), (x1, y1)) = (pair[0], pair[1]);
        if percentile <= x1 {
            return if x1 == x0 { y0 } else { y0 + (percentile - x0) / (x1 - x0) * (y1 - y0) };
        }
    }
    points[points.len() - 1].1
}
