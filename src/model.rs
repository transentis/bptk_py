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
    Pi,
    // Control
    Step,
    Pulse,
    // Stateful
    Delay,
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
    // Lookup
    Lookup(String), // graphical function table name
}

#[derive(Debug, Clone)]
pub struct GraphicalFunction {
    pub points: Vec<(f64, f64)>, // sorted by x
}

impl SdModel {
    /// Override a constant's equation to a new literal value.
    pub fn set_constant(&mut self, name: &str, value: f64) -> Result<(), String> {
        let idx = self
            .entity_index
            .get(name)
            .ok_or_else(|| format!("Unknown entity: '{}'", name))?;
        self.entities[*idx].equation = Expr::Literal(value);
        Ok(())
    }

    /// Override the simulation run specifications.
    pub fn set_runspecs(&mut self, starttime: f64, stoptime: f64, dt: f64) {
        self.starttime = starttime;
        self.stoptime = stoptime;
        self.dt = dt;
    }

    /// Replace the points of a graphical function.
    pub fn set_points(&mut self, name: &str, points: Vec<(f64, f64)>) -> Result<(), String> {
        let gf = self
            .graphical_functions
            .get_mut(name)
            .ok_or_else(|| format!("Unknown graphical function: '{}'", name))?;
        gf.points = points;
        Ok(())
    }
}
