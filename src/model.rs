use std::collections::HashMap;

/// A compiled, ready-to-execute SD model.
#[derive(Debug)]
pub struct SdModel {
    pub name: String,
    pub starttime: f64,
    pub stoptime: f64,
    pub dt: f64,
    pub entities: Vec<Entity>,
    pub entity_index: HashMap<String, usize>,
    pub graphical_functions: HashMap<String, GraphicalFunction>,
    /// Evaluation order for non-stock entities (indices into `entities`).
    /// Computed via topological sort at load time.
    pub eval_order: Vec<usize>,
    /// Evaluation order for every entity at the start time, where a stock is its initial
    /// value: it follows what that reads, and whatever reads the stock follows it.
    pub init_order: Vec<usize>,
    /// The Python functions this model calls back into, by slot. A `PyCallback`
    /// expression carries the slot, never the name: the name is resolved once at load
    /// time, the way an entity reference becomes an index. Always empty in a build
    /// without Python, where such a node is a load error.
    pub callback_names: Vec<String>,
    /// What to call for each slot, `None` until it is registered. Parallel to
    /// `callback_names`.
    #[cfg(feature = "python")]
    pub callbacks: Vec<Option<pyo3::Py<pyo3::PyAny>>>,
}

#[derive(Debug)]
pub struct Entity {
    pub name: String,
    pub kind: EntityKind,
    pub equation: Expr,
}

#[derive(Debug, Clone, PartialEq)]
pub enum EntityKind {
    Stock { initial_value: Expr },
    Flow,
    Biflow,
    Converter,
    Constant,
}

/// Expression tree — the core of equation evaluation.
#[derive(Debug, Clone, PartialEq)]
pub enum Expr {
    Literal(f64),
    Ref(usize), // index into entities vec
    BinaryOp {
        op: BinOp,
        left: Box<Expr>,
        right: Box<Expr>,
    },
    UnaryOp {
        op: UnOp,
        operand: Box<Expr>,
    },
    Call {
        function: BuiltinFn,
        args: Vec<Expr>,
    },
    If {
        condition: Box<Expr>,
        then: Box<Expr>,
        else_: Box<Expr>,
    },
    /// A call into a Python function: the arguments are evaluated to numbers here and
    /// the answer is one number. The variant does not exist without Python - there is
    /// no interpreter to call, which is the whole reason the crate splits.
    #[cfg(feature = "python")]
    PyCallback { slot: usize, args: Vec<Expr> },
}

#[derive(Debug, Clone, Copy, PartialEq)]
pub enum BinOp {
    Add,
    Sub,
    Mul,
    Div,
    Pow,
    Mod,
    Gt,
    Lt,
    Gte,
    Lte,
    Eq,
    Neq,
    And,
    Or,
}

#[derive(Debug, Clone, Copy, PartialEq)]
pub enum UnOp {
    Neg,
    Not,
}

/// XMILE's three types of graphical function: `Continuous` holds the end values outside
/// the table, `Extrapolate` goes on along the first and the last segment, `Discrete` is a
/// step function - the value of the next lower x.
#[derive(Debug, Clone, Copy, PartialEq)]
pub enum LookupKind {
    Continuous,
    Extrapolate,
    Discrete,
}

impl LookupKind {
    pub fn from_name(name: &str) -> Option<LookupKind> {
        match name {
            "continuous" => Some(LookupKind::Continuous),
            "extrapolate" => Some(LookupKind::Extrapolate),
            "discrete" => Some(LookupKind::Discrete),
            _ => None,
        }
    }
}

/// What LOOKUPMAX, LOOKUPMIN and LOOKUPMEAN take of a table.
#[derive(Debug, Clone, Copy, PartialEq)]
pub enum LookupStatistic {
    Max,
    Min,
    Mean,
}

#[derive(Debug, Clone, PartialEq)]
pub enum BuiltinFn {
    // Temporal
    Time,
    Dt,
    Starttime,
    Stoptime,
    // Math
    Abs,
    Sqrt,
    Exp,
    Ln,
    Log10,
    Sin,
    Cos,
    Tan,
    Arcsin,
    Arccos,
    Arctan,
    Sinwave,
    Coswave,
    Max,
    Min,
    Round,
    Floor,
    Ceil,
    Trunc,
    Pi,
    // Control
    Step,
    Pulse,
    // Stateful
    Delay,
    Irr, // the stream, then the value without a rate
    // Combinatorial & special
    Combinations,
    Permutations,
    Factorial,
    GammaLN,
    Inf,
    Nan,
    // Statistical
    Random,
    Normal,
    Beta,
    Binomial,
    NegBinomial,
    Exprnd,
    GammaDist,
    Geometric,
    Lognormal,
    Logistic,
    Montecarlo,
    Poisson,
    Triangular,
    Weibull,
    Pareto,
    Invnorm,
    NormalCDF,
    Seeded, // the seed, the cell's keys, then the draw - a random builtin's call
    Bounded, // minimum, maximum (NaN for none), then the draw
    Sample, // the sample, then the draw - seeded or bounded or neither
    // A non-negative stock's outflows, cut back as the Python engine cuts them
    Positive, // max(0, x), with Python's max: NaN gives 0
    CutOut,   // what an outflow takes: what it wants, at most what is available
    CutIn,    // what a biflow among the inflows takes while it runs backwards
    // A conveyor - see `src/conveyor.rs`
    ConveyorStart,  // fifo, exponential, transit, n, n fractions, m, then the total (m = 0) or m values
    ConveyorFlow,   // the conveyor, -1 for its outflow or the leak's index, transit, inflow, fractions
    ConveyorChange, // the conveyor's change over the step, for the integration
    AgeCount,       // the conveyor, minimum, maximum (NaN for none)
    // Array aggregations - variadic over the leaves of a flattened arrayed element
    ArrSum,
    ArrProd,
    ArrMean,
    ArrMedian,
    ArrStddev,
    ArrLargest, // the rank is the last argument
    ArrRank, // the rank, then the values, then as many tiebreak values
    ArrPercentile, // 1 with weights, 0 without; the percentile, the lower one, the values, as many weights
    ArrInterpolate, // the number of columns (0 for a vector), one weight per dimension, the values
    ArrMax,
    ArrMin,
    // Lookup - each names a graphical function table and says what kind it is
    Lookup(String, LookupKind),
    LookupInv(String, LookupKind),
    LookupArea(String, LookupKind), // the arguments are from and to
    RunCum, // the stream, then from and to
    RunMax,
    RunMin,
    RunMean,
    RunCumTarget, // the stream, then the target
    LookupRandom(String, LookupKind), // a draw: no arguments but the table
    LookupMax(String, LookupKind), // the arguments are from and to, in either order
    LookupMin(String, LookupKind),
    LookupMean(String, LookupKind),
}

/// The number of timesteps a run over these specs has, starttime and stoptime included,
/// or why the specs cannot run at all.
///
/// Checked where specs come in - the model JSON and `set_runspecs` - so that a dt of 0 is
/// named there instead of turning into a step count too large to allocate.
pub fn num_steps_for(starttime: f64, stoptime: f64, dt: f64) -> Result<usize, String> {
    if !(starttime.is_finite() && stoptime.is_finite() && dt.is_finite()) {
        return Err(format!(
            "Invalid run specs: starttime, stoptime and dt must be finite numbers \
             (starttime={:?}, stoptime={:?}, dt={:?})",
            starttime, stoptime, dt
        ));
    }
    if dt <= 0.0 {
        return Err(format!("Invalid run specs: dt must be positive (dt={:?})", dt));
    }
    if stoptime < starttime {
        return Err(format!(
            "Invalid run specs: stoptime must not be before starttime \
             (starttime={:?}, stoptime={:?})",
            starttime, stoptime
        ));
    }
    let steps = ((stoptime - starttime) / dt).round();
    // One f64 per entity and step: beyond this the memo table cannot even be addressed.
    if steps >= (isize::MAX as f64) / 8.0 {
        return Err(format!(
            "Invalid run specs: {:?} timesteps from starttime={:?} to stoptime={:?} with \
             dt={:?} are more than a run can hold",
            steps, starttime, stoptime, dt
        ));
    }
    Ok(steps as usize + 1)
}

/// The points of a lookup table in the order interpolation needs, or why they are no table.
///
/// Sorted by x, because the order a list was written in carries no meaning and the
/// interpolation reads the first point as the left edge. Two points at the same x are
/// refused: the table would have two values there, and the engines used to pick different
/// ones. The same rule holds on the Python side (`BPTK_Py/util/lookup_data.py`).
pub fn sorted_points(name: &str, mut points: Vec<(f64, f64)>) -> Result<Vec<(f64, f64)>, String> {
    if points.is_empty() {
        return Err(format!("Lookup table '{}' has no points", name));
    }
    if let Some(&(x, _)) = points.iter().find(|(x, _)| !x.is_finite()) {
        return Err(format!("Lookup table '{}' has a point at x={:?}; x must be a finite number", name, x));
    }
    points.sort_by(|a, b| a.0.total_cmp(&b.0));
    if let Some(pair) = points.windows(2).find(|pair| pair[0].0 == pair[1].0) {
        return Err(format!("Lookup table '{}' has two points at x={:?}", name, pair[0].0));
    }
    Ok(points)
}

#[derive(Debug, Clone)]
pub struct GraphicalFunction {
    pub points: Vec<(f64, f64)>, // sorted by x
}

impl SdModel {
    /// The time of a step, on the grid the Python engine uses: `starttime + step * dt`
    /// rounded to ten decimals. Unrounded, dt = 0.3 gives 0.8999999999999999 for the
    /// fourth step, and a comparison with 0.9 - `step`, `pulse`, an `If` on the time -
    /// switches one step later than the Python engine does.
    pub fn time_at(&self, step: usize) -> f64 {
        let t = self.starttime + step as f64 * self.dt;
        (t * 1e10).round() / 1e10
    }

    /// The steps from `from` to `to`, both included and none after `step`, or None for a
    /// window without one. An infinite bound is the start or the current step. The bounds
    /// are read in steps, a millionth of a step to spare, so that TIME - 2 meets the step
    /// it means - as the Python engine reads them.
    pub fn run_steps(&self, step: usize, from: f64, to: f64) -> Option<(usize, usize)> {
        let first = if from == f64::NEG_INFINITY {
            0.0
        } else {
            ((from - self.starttime) / self.dt - 1e-6).ceil().max(0.0)
        };
        let last = if to == f64::INFINITY {
            step as f64
        } else {
            ((to - self.starttime) / self.dt + 1e-6).floor().min(step as f64)
        };
        if first > last { None } else { Some((first as usize, last as usize)) }
    }

    /// Override a constant's equation to a new literal value.
    pub fn set_constant(&mut self, name: &str, value: f64) -> Result<(), String> {
        let idx = self
            .entity_index
            .get(name)
            .ok_or_else(|| format!("Unknown entity: '{}'", name))?;
        self.entities[*idx].equation = Expr::Literal(value);
        Ok(())
    }

    /// Override the simulation run specifications, refusing specs that cannot run.
    pub fn set_runspecs(&mut self, starttime: f64, stoptime: f64, dt: f64) -> Result<(), String> {
        num_steps_for(starttime, stoptime, dt)?;
        self.starttime = starttime;
        self.stoptime = stoptime;
        self.dt = dt;
        Ok(())
    }

    /// Replace the points of a graphical function, sorted by x.
    pub fn set_points(&mut self, name: &str, points: Vec<(f64, f64)>) -> Result<(), String> {
        let gf = self
            .graphical_functions
            .get_mut(name)
            .ok_or_else(|| format!("Unknown graphical function: '{}'", name))?;
        gf.points = sorted_points(name, points)?;
        Ok(())
    }
}
