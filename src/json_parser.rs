use std::collections::HashMap;

use serde::Deserialize;

use crate::model::*;

// ── Intermediate serde structs (pass 1: JSON → these) ──────────────────────

#[derive(Deserialize)]
pub struct JsonModel {
    pub name: Option<String>,
    pub specs: JsonSpecs,
    pub entities: JsonEntities,
    #[serde(default)]
    pub graphical_functions: HashMap<String, JsonGraphicalFunction>,
}

#[derive(Deserialize)]
pub struct JsonSpecs {
    pub starttime: f64,
    pub stoptime: f64,
    pub dt: f64,
}

#[derive(Deserialize)]
pub struct JsonEntities {
    #[serde(default)]
    pub stocks: Vec<JsonStock>,
    #[serde(default)]
    pub flows: Vec<JsonFlowOrConverter>,
    #[serde(default)]
    pub biflows: Vec<JsonFlowOrConverter>,
    #[serde(default)]
    pub converters: Vec<JsonFlowOrConverter>,
    #[serde(default)]
    pub constants: Vec<JsonFlowOrConverter>,
}

#[derive(Deserialize)]
pub struct JsonStock {
    pub name: String,
    pub initial_value: JsonExpr,
    pub equation: Option<JsonExpr>,
}

#[derive(Deserialize)]
pub struct JsonFlowOrConverter {
    pub name: String,
    pub equation: JsonExpr,
}

#[derive(Deserialize)]
#[serde(tag = "type")]
pub enum JsonExpr {
    #[serde(rename = "literal")]
    Literal { value: JsonLiteralValue },
    #[serde(rename = "ref")]
    Ref { name: String },
    #[serde(rename = "binary_op")]
    BinaryOp {
        op: String,
        left: Box<JsonExpr>,
        right: Box<JsonExpr>,
    },
    #[serde(rename = "unary_op")]
    UnaryOp { op: String, operand: Box<JsonExpr> },
    #[serde(rename = "call")]
    Call {
        function: String,
        args: Vec<JsonExpr>,
    },
    #[serde(rename = "if")]
    If {
        condition: Box<JsonExpr>,
        then: Box<JsonExpr>,
        #[serde(rename = "else")]
        else_: Box<JsonExpr>,
    },
    #[serde(rename = "py_callback")]
    PyCallback {
        name: String,
        args: Vec<JsonExpr>,
    },
}

/// Literal values can be either numbers or strings (for lookup table names).
#[derive(Deserialize)]
#[serde(untagged)]
pub enum JsonLiteralValue {
    Number(f64),
    String(String),
}

#[derive(Deserialize)]
pub struct JsonGraphicalFunction {
    pub points: Vec<(f64, f64)>,
}

// ── Parsing errors ──────────────────────────────────────────────────────────

#[derive(Debug)]
pub enum ParseError {
    Json(serde_json::Error),
    UnknownEntity(String),
    UnknownBinaryOp(String),
    UnknownUnaryOp(String),
    UnknownFunction(String),
    /// A `py_callback` node in a build without Python. Not a malformed model: the same
    /// JSON loads in the extension module, and the message says so.
    PythonCallbackUnsupported(String),
    /// Carries one readable path per cycle, e.g. `["a → b → a"]`. Empty when the
    /// cycle was detected but not described (the first, cheap sorting pass).
    CyclicDependency(Vec<String>),
    /// Starttime, stoptime and dt that cannot run; the message says which and why.
    InvalidRunSpecs(String),
    /// A function called with a number of arguments it does not take.
    WrongArgumentCount {
        function: String,
        expected: &'static str,
        got: usize,
    },
    /// `seeded` around something other than a random builtin's call.
    SeededWithoutDraw,
    /// A `bounded` whose last argument is not the call of a random function.
    BoundedWithoutDraw,
    /// `delay` and `irr` read the past of an element, so their first argument has to name
    /// one; the function's name.
    PastOfNoEntity(&'static str),
    /// Two entities of the same name; the second used to replace the first unnoticed.
    DuplicateEntity(String),
    /// A string where a number belongs - only a lookup's table name is a string.
    StringOutsideLookup(String),
    /// A lookup call without the name of a table where it belongs, or with the wrong
    /// number of arguments; the function's name.
    LookupWithoutTable(String),
    /// A `lookup` of a table the model does not have; it used to read 0.0.
    UnknownLookupTable(String),
    /// A kind of table XMILE does not have; the name given.
    UnknownLookupKind(String),
    /// Points that are no lookup table; the message says why.
    InvalidLookupPoints(String),
}

impl std::fmt::Display for ParseError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            ParseError::Json(e) => write!(f, "JSON parse error: {}", e),
            ParseError::UnknownEntity(name) => write!(f, "Unknown entity: '{}'", name),
            ParseError::UnknownBinaryOp(op) => write!(f, "Unknown binary operator: '{}'", op),
            ParseError::UnknownUnaryOp(op) => write!(f, "Unknown unary operator: '{}'", op),
            ParseError::UnknownFunction(name) => write!(f, "Unknown function: '{}'", name),
            ParseError::PythonCallbackUnsupported(name) => write!(
                f,
                "Model calls the Python function '{}', which this build cannot do: it was \
                 compiled without Python.",
                name
            ),
            ParseError::CyclicDependency(cycles) if cycles.is_empty() => {
                write!(f, "Cyclic dependency among non-stock entities")
            }
            ParseError::CyclicDependency(cycles) => write!(
                f,
                "Cyclic dependency among non-stock entities: {}",
                cycles.join("; ")
            ),
            ParseError::InvalidRunSpecs(message) => write!(f, "{}", message),
            ParseError::WrongArgumentCount { function, expected, got } => write!(
                f,
                "Function '{}' takes {} argument(s), and was given {}",
                function, expected, got
            ),
            ParseError::DuplicateEntity(name) => {
                write!(f, "The model has more than one entity named '{}'", name)
            }
            ParseError::StringOutsideLookup(text) => write!(
                f,
                "The string \"{}\" stands where a number belongs; only a lookup takes a \
                 string, the name of its table",
                text
            ),
            ParseError::LookupWithoutTable(function) => write!(
                f,
                "Function '{}' takes {}",
                function,
                if function == "lookuprandom" {
                    "the name of a table"
                } else if matches!(function.as_str(), "lookuparea" | "lookupmax" | "lookupmin" | "lookupmean") {
                    "the name of a table, a from and a to"
                } else {
                    "an input and the name of a table"
                }
            ),
            ParseError::UnknownLookupTable(name) => {
                write!(f, "Lookup of a table the model does not have: '{}'", name)
            }
            ParseError::UnknownLookupKind(kind) => write!(
                f,
                "A lookup table is continuous, extrapolate or discrete, not '{}'",
                kind
            ),
            ParseError::InvalidLookupPoints(message) => write!(f, "{}", message),
            ParseError::BoundedWithoutDraw => write!(
                f,
                "Function 'bounded' takes a minimum, a maximum and the call of a random function, last"
            ),
            ParseError::SeededWithoutDraw => write!(
                f,
                "Function 'seeded' takes a seed, the keys of a cell and the call of a random \
                 function, last"
            ),
            ParseError::PastOfNoEntity(function) => write!(
                f,
                "Function '{}' reads the past of an element, so its first argument has \
                 to be a reference to one",
                function
            ),
        }
    }
}

impl From<serde_json::Error> for ParseError {
    fn from(e: serde_json::Error) -> Self {
        ParseError::Json(e)
    }
}

// ── Pass 2: resolve references, build SdModel ──────────────────────────────

pub fn parse_json(json: &str) -> Result<SdModel, ParseError> {
    let jm: JsonModel = serde_json::from_str(json)?;
    num_steps_for(jm.specs.starttime, jm.specs.stoptime, jm.specs.dt)
        .map_err(ParseError::InvalidRunSpecs)?;

    // Entities are indexed stocks first, then flows, biflows, converters and constants.
    // The evaluation order is a different thing: the topological sort below decides it.
    let non_stocks = [
        (&jm.entities.flows, EntityKind::Flow),
        (&jm.entities.biflows, EntityKind::Biflow),
        (&jm.entities.converters, EntityKind::Converter),
        (&jm.entities.constants, EntityKind::Constant),
    ];

    // Every name is registered before any expression is resolved, so that an equation
    // may refer to an entity declared after it.
    let mut entity_index: HashMap<String, usize> = HashMap::new();
    let mut entities: Vec<Entity> = Vec::new();
    // Callback names in the order they are first seen; the slot is the position.
    let mut callbacks = CallbackSlots::default();

    let declared = jm
        .entities
        .stocks
        .iter()
        .map(|s| (&s.name, EntityKind::Stock { initial_value: Expr::Literal(0.0) }))
        .chain(non_stocks.iter().flat_map(|(group, kind)| {
            group.iter().map(move |entity| (&entity.name, kind.clone()))
        }));
    for (name, kind) in declared {
        insert_entity(&mut entity_index, name, entities.len())?;
        entities.push(Entity {
            name: name.clone(),
            kind,
            equation: Expr::Literal(0.0),
        });
    }

    // Now resolve all expressions with the complete entity_index, in the same order.
    let (stock_entities, non_stock_entities) = entities.split_at_mut(jm.entities.stocks.len());
    for (entity, s) in stock_entities.iter_mut().zip(&jm.entities.stocks) {
        let initial_value = resolve_expr(&s.initial_value, &entity_index, &mut callbacks)?;
        entity.equation = match &s.equation {
            Some(eq) => resolve_expr(eq, &entity_index, &mut callbacks)?,
            None => Expr::Literal(0.0),
        };
        entity.kind = EntityKind::Stock { initial_value };
    }
    let non_stock_equations = non_stocks.iter().flat_map(|(group, _)| group.iter());
    for (entity, f) in non_stock_entities.iter_mut().zip(non_stock_equations) {
        entity.equation = resolve_expr(&f.equation, &entity_index, &mut callbacks)?;
    }

    // Parse graphical functions
    let mut graphical_functions: HashMap<String, GraphicalFunction> = HashMap::new();
    for (name, gf) in jm.graphical_functions {
        let points = sorted_points(&name, gf.points).map_err(ParseError::InvalidLookupPoints)?;
        graphical_functions.insert(name, GraphicalFunction { points });
    }
    for entity in &entities {
        let mut names = Vec::new();
        collect_lookup_tables(&entity.equation, &mut names);
        if let EntityKind::Stock { ref initial_value } = entity.kind {
            collect_lookup_tables(initial_value, &mut names);
        }
        if let Some(name) = names.into_iter().find(|name| !graphical_functions.contains_key(*name)) {
            return Err(ParseError::UnknownLookupTable(name.clone()));
        }
    }

    // Topological sort of non-stock entities, for every step; and of all entities, for
    // the start, where a stock is its initial value rather than its flows
    let eval_order = topological_sort(&entities, jm.specs.dt, false)?;
    let init_order = topological_sort(&entities, jm.specs.dt, true)?;

    Ok(SdModel {
        name: jm.name.unwrap_or_default(),
        starttime: jm.specs.starttime,
        stoptime: jm.specs.stoptime,
        dt: jm.specs.dt,
        entities,
        entity_index,
        graphical_functions,
        eval_order,
        init_order,
        #[cfg(feature = "python")]
        // `Py` is not `Clone`, so the empty slots are built rather than repeated.
        callbacks: callbacks.names.iter().map(|_| None).collect(),
        callback_names: callbacks.names,
    })
}

/// Register an entity's name, refusing one that is taken.
fn insert_entity(
    entity_index: &mut HashMap<String, usize>,
    name: &str,
    index: usize,
) -> Result<(), ParseError> {
    if entity_index.insert(name.to_string(), index).is_some() {
        return Err(ParseError::DuplicateEntity(name.to_string()));
    }
    Ok(())
}

/// The names of the lookup tables an expression reads.
fn collect_lookup_tables<'a>(expr: &'a Expr, names: &mut Vec<&'a String>) {
    match expr {
        Expr::Literal(_) | Expr::Ref(_) => {}
        Expr::BinaryOp { left, right, .. } => {
            collect_lookup_tables(left, names);
            collect_lookup_tables(right, names);
        }
        Expr::UnaryOp { operand, .. } => collect_lookup_tables(operand, names),
        Expr::Call { function, args } => {
            if let BuiltinFn::Lookup(name, _)
            | BuiltinFn::LookupInv(name, _)
            | BuiltinFn::LookupArea(name, _)
            | BuiltinFn::LookupMax(name, _)
            | BuiltinFn::LookupMin(name, _)
            | BuiltinFn::LookupMean(name, _)
            | BuiltinFn::LookupRandom(name, _) = function
            {
                names.push(name);
            }
            for arg in args {
                collect_lookup_tables(arg, names);
            }
        }
        Expr::If { condition, then, else_ } => {
            collect_lookup_tables(condition, names);
            collect_lookup_tables(then, names);
            collect_lookup_tables(else_, names);
        }
        #[cfg(feature = "python")]
        Expr::PyCallback { args, .. } => {
            for arg in args {
                collect_lookup_tables(arg, names);
            }
        }
    }
}

/// Callback names in first-seen order. The slot an expression carries is the position in
/// `names`, so a name mentioned twice resolves to the same slot and is registered once.
// Only the `py_callback` arm fills this, and that arm is Python-only - without the
// feature the registry is built, stays empty and is never asked anything.
#[cfg_attr(not(feature = "python"), allow(dead_code))]
#[derive(Default)]
struct CallbackSlots {
    names: Vec<String>,
    index: HashMap<String, usize>,
}

#[cfg_attr(not(feature = "python"), allow(dead_code))]
impl CallbackSlots {
    fn slot_for(&mut self, name: &str) -> usize {
        if let Some(&slot) = self.index.get(name) {
            return slot;
        }
        let slot = self.names.len();
        self.names.push(name.to_string());
        self.index.insert(name.to_string(), slot);
        slot
    }
}

/// Resolve a JSON expression tree into a typed Expr with usize references.
fn resolve_expr(
    json_expr: &JsonExpr,
    entity_index: &HashMap<String, usize>,
    // Written only by the `py_callback` arm, which a build without Python never takes.
    #[cfg_attr(not(feature = "python"), allow(unused_variables))] callbacks: &mut CallbackSlots,
) -> Result<Expr, ParseError> {
    match json_expr {
        JsonExpr::Literal { value } => match value {
            JsonLiteralValue::Number(n) => Ok(Expr::Literal(*n)),
            // A lookup's table name is taken before its arguments are resolved, so a
            // string that arrives here stands where a number belongs.
            JsonLiteralValue::String(text) => Err(ParseError::StringOutsideLookup(text.clone())),
        },
        JsonExpr::Ref { name } => {
            let idx = entity_index
                .get(name)
                .ok_or_else(|| ParseError::UnknownEntity(name.clone()))?;
            Ok(Expr::Ref(*idx))
        }
        JsonExpr::BinaryOp { op, left, right } => {
            let bin_op = parse_bin_op(op)?;
            Ok(Expr::BinaryOp {
                op: bin_op,
                left: Box::new(resolve_expr(left, entity_index, callbacks)?),
                right: Box::new(resolve_expr(right, entity_index, callbacks)?),
            })
        }
        JsonExpr::UnaryOp { op, operand } => {
            let un_op = parse_un_op(op)?;
            Ok(Expr::UnaryOp {
                op: un_op,
                operand: Box::new(resolve_expr(operand, entity_index, callbacks)?),
            })
        }
        JsonExpr::Call { function, args } => {
            // The lookups name their table in a string: `lookup` and `lookupinv` as their
            // second argument, after the input, `lookuparea`, `lookupmax`, `lookupmin` and
            // `lookupmean` as their first, before from and to.
            // A string after the other arguments names the kind of table; without it the
            // table is continuous
            let table_lookup: Option<(usize, usize, fn(String, LookupKind) -> BuiltinFn)> = match function.as_str() {
                "lookup" => Some((1, 2, BuiltinFn::Lookup)),
                "lookupinv" => Some((1, 2, BuiltinFn::LookupInv)),
                "lookuparea" => Some((0, 3, BuiltinFn::LookupArea)),
                "lookupmax" => Some((0, 3, BuiltinFn::LookupMax)),
                "lookuprandom" => Some((0, 1, BuiltinFn::LookupRandom)),
                "lookupmin" => Some((0, 3, BuiltinFn::LookupMin)),
                "lookupmean" => Some((0, 3, BuiltinFn::LookupMean)),
                _ => None,
            };
            if let Some((position, count, builtin)) = table_lookup {
                let (table_args, kind) = match args.get(count) {
                    Some(JsonExpr::Literal { value: JsonLiteralValue::String(name) }) if args.len() == count + 1 => (
                        &args[..count],
                        LookupKind::from_name(name).ok_or_else(|| ParseError::UnknownLookupKind(name.clone()))?,
                    ),
                    _ => (&args[..], LookupKind::Continuous),
                };
                if let (true, Some(JsonExpr::Literal { value: JsonLiteralValue::String(table_name) })) =
                    (table_args.len() == count, table_args.get(position))
                {
                    let resolved_args = table_args
                        .iter()
                        .enumerate()
                        .filter(|&(i, _)| i != position)
                        .map(|(_, a)| resolve_expr(a, entity_index, callbacks))
                        .collect::<Result<_, _>>()?;
                    return Ok(Expr::Call {
                        function: builtin(table_name.clone(), kind),
                        args: resolved_args,
                    });
                }
                return Err(ParseError::LookupWithoutTable(function.clone()));
            }
            let builtin = parse_builtin_fn(function)?;
            let (fewest, most, expected) = arity(&builtin);
            if args.len() < fewest || most.is_some_and(|most| args.len() > most) {
                return Err(ParseError::WrongArgumentCount {
                    function: function.clone(),
                    expected,
                    got: args.len(),
                });
            }
            // The values and their tiebreaks come in pairs, after the rank
            if matches!(builtin, BuiltinFn::ArrRank) && args.len() % 2 == 0 {
                return Err(ParseError::WrongArgumentCount {
                    function: function.clone(),
                    expected: "a rank, then values and as many tiebreak values, so an odd number of",
                    got: args.len(),
                });
            }
            // The values and their weights come in pairs, after the three numbers
            if matches!(builtin, BuiltinFn::ArrPercentile) && args.len() % 2 == 0 {
                return Err(ParseError::WrongArgumentCount {
                    function: function.clone(),
                    expected: "whether it weighs, a percentile, a lower one, then values and as many weights, so an odd number of",
                    got: args.len(),
                });
            }
            let resolved_args: Vec<Expr> = args
                .iter()
                .map(|a| resolve_expr(a, entity_index, callbacks))
                .collect::<Result<_, _>>()?;
            let past_of = match builtin {
                BuiltinFn::Delay => Some("delay"),
                BuiltinFn::Irr => Some("irr"),
                BuiltinFn::RunCum => Some("runcum"),
                BuiltinFn::RunMax => Some("runmax"),
                BuiltinFn::RunMin => Some("runmin"),
                BuiltinFn::RunMean => Some("runmean"),
                BuiltinFn::RunCumTarget => Some("runcumtarget"),
                BuiltinFn::ConveyorFlow => Some("conveyor_flow"),
                BuiltinFn::AgeCount => Some("agecount"),
                _ => None,
            };
            if let Some(function) = past_of {
                if !matches!(resolved_args[0], Expr::Ref(_)) {
                    return Err(ParseError::PastOfNoEntity(function));
                }
            }
            if matches!(builtin, BuiltinFn::Seeded) && resolved_args.last().and_then(draw_of).is_none() {
                return Err(ParseError::SeededWithoutDraw);
            }
            if matches!(builtin, BuiltinFn::Bounded)
                && !matches!(&resolved_args[2], Expr::Call { function, .. } if seeded_draw_name(function).is_some())
            {
                return Err(ParseError::BoundedWithoutDraw);
            }
            Ok(Expr::Call {
                function: builtin,
                args: resolved_args,
            })
        }
        JsonExpr::If {
            condition,
            then,
            else_,
        } => Ok(Expr::If {
            condition: Box::new(resolve_expr(condition, entity_index, callbacks)?),
            then: Box::new(resolve_expr(then, entity_index, callbacks)?),
            else_: Box::new(resolve_expr(else_, entity_index, callbacks)?),
        }),
        JsonExpr::PyCallback { name, args } => {
            #[cfg(feature = "python")]
            {
                let slot = callbacks.slot_for(name);
                let resolved: Result<Vec<Expr>, ParseError> = args
                    .iter()
                    .map(|a| resolve_expr(a, entity_index, callbacks))
                    .collect();
                Ok(Expr::PyCallback {
                    slot,
                    args: resolved?,
                })
            }
            #[cfg(not(feature = "python"))]
            {
                let _ = args;
                Err(ParseError::PythonCallbackUnsupported(name.clone()))
            }
        }
    }
}

/// How many arguments each builtin takes: the fewest, the most (`None` for no limit), and
/// the same in words for the error message. The evaluator indexes arguments directly, so
/// this is what keeps a short argument list from reaching it.
fn arity(function: &BuiltinFn) -> (usize, Option<usize>, &'static str) {
    use BuiltinFn::*;
    match function {
        Time | Dt | Starttime | Stoptime | Pi | Inf | Nan | ConveyorChange | LookupRandom(..) => (0, Some(0), "no"),
        Abs | Sqrt | Exp | Ln | Log10 | Sin | Cos | Tan | Arcsin | Arccos | Arctan | Floor
        | Ceil | Trunc | Factorial | GammaLN | Exprnd | Geometric | Montecarlo | Poisson
        | Lookup(..) | LookupInv(..) | Positive => (1, Some(1), "1"),
        Sinwave | Coswave | Max | Min | Step | Combinations | Permutations | Random | Normal
        | Beta | Binomial | NegBinomial | Lognormal | Logistic | Weibull | Pareto | LookupArea(..)
        | LookupMax(..) | LookupMin(..) | LookupMean(..)
        | Irr | CutOut | CutIn | RunCumTarget => {
            (2, Some(2), "2")
        }
        Delay | Triangular | AgeCount | RunCum | RunMax | RunMin | RunMean => (3, Some(3), "3"),
        ConveyorStart => (6, None, "at least 6"),
        ConveyorFlow => (4, None, "at least 4"),
        Round | GammaDist => (1, Some(2), "1 or 2"),
        Pulse | Invnorm => (1, Some(3), "1 to 3"),
        NormalCDF => (2, Some(4), "2 to 4"),
        ArrSum | ArrProd | ArrMean | ArrMedian | ArrStddev | ArrMax | ArrMin => {
            (0, None, "any number of")
        }
        ArrLargest => (2, None, "at least 2"),
        ArrRank | ArrInterpolate => (3, None, "at least 3"),
        ArrPercentile => (5, None, "at least 5"),
        Seeded => (2, None, "at least 2"),
        Sample => (2, Some(2), "2"),
        Bounded => (3, Some(3), "3"),
    }
}

fn parse_bin_op(op: &str) -> Result<BinOp, ParseError> {
    match op {
        "add" => Ok(BinOp::Add),
        "sub" => Ok(BinOp::Sub),
        "mul" => Ok(BinOp::Mul),
        "div" => Ok(BinOp::Div),
        "pow" => Ok(BinOp::Pow),
        "mod" => Ok(BinOp::Mod),
        "gt" => Ok(BinOp::Gt),
        "lt" => Ok(BinOp::Lt),
        "gte" => Ok(BinOp::Gte),
        "lte" => Ok(BinOp::Lte),
        "eq" => Ok(BinOp::Eq),
        "neq" => Ok(BinOp::Neq),
        "and" => Ok(BinOp::And),
        "or" => Ok(BinOp::Or),
        _ => Err(ParseError::UnknownBinaryOp(op.to_string())),
    }
}

fn parse_un_op(op: &str) -> Result<UnOp, ParseError> {
    match op {
        "neg" => Ok(UnOp::Neg),
        "not" => Ok(UnOp::Not),
        _ => Err(ParseError::UnknownUnaryOp(op.to_string())),
    }
}

fn parse_builtin_fn(name: &str) -> Result<BuiltinFn, ParseError> {
    match name {
        "time" => Ok(BuiltinFn::Time),
        "dt" => Ok(BuiltinFn::Dt),
        "starttime" => Ok(BuiltinFn::Starttime),
        "stoptime" => Ok(BuiltinFn::Stoptime),
        "abs" => Ok(BuiltinFn::Abs),
        "sqrt" => Ok(BuiltinFn::Sqrt),
        "exp" => Ok(BuiltinFn::Exp),
        "ln" => Ok(BuiltinFn::Ln),
        "log10" => Ok(BuiltinFn::Log10),
        "sin" => Ok(BuiltinFn::Sin),
        "cos" => Ok(BuiltinFn::Cos),
        "tan" => Ok(BuiltinFn::Tan),
        "arcsin" => Ok(BuiltinFn::Arcsin),
        "arccos" => Ok(BuiltinFn::Arccos),
        "arctan" => Ok(BuiltinFn::Arctan),
        "sinwave" => Ok(BuiltinFn::Sinwave),
        "coswave" => Ok(BuiltinFn::Coswave),
        "max" => Ok(BuiltinFn::Max),
        "min" => Ok(BuiltinFn::Min),
        "round" => Ok(BuiltinFn::Round),
        "floor" => Ok(BuiltinFn::Floor),
        "ceil" => Ok(BuiltinFn::Ceil),
        "trunc" => Ok(BuiltinFn::Trunc),
        "pi" => Ok(BuiltinFn::Pi),
        "step" => Ok(BuiltinFn::Step),
        "pulse" => Ok(BuiltinFn::Pulse),
        "delay" => Ok(BuiltinFn::Delay),
        "irr" => Ok(BuiltinFn::Irr),
        "runcum" => Ok(BuiltinFn::RunCum),
        "runmax" => Ok(BuiltinFn::RunMax),
        "runmin" => Ok(BuiltinFn::RunMin),
        "runmean" => Ok(BuiltinFn::RunMean),
        "runcumtarget" => Ok(BuiltinFn::RunCumTarget),
        // Combinatorial & special
        "combinations" => Ok(BuiltinFn::Combinations),
        "permutations" => Ok(BuiltinFn::Permutations),
        "factorial" => Ok(BuiltinFn::Factorial),
        "gammaln" => Ok(BuiltinFn::GammaLN),
        "inf" => Ok(BuiltinFn::Inf),
        "nan" => Ok(BuiltinFn::Nan),
        // Statistical
        "random" => Ok(BuiltinFn::Random),
        "normal" => Ok(BuiltinFn::Normal),
        "beta" => Ok(BuiltinFn::Beta),
        "binomial" => Ok(BuiltinFn::Binomial),
        "negbinomial" => Ok(BuiltinFn::NegBinomial),
        "exprnd" => Ok(BuiltinFn::Exprnd),
        "gamma_dist" => Ok(BuiltinFn::GammaDist),
        "geometric" => Ok(BuiltinFn::Geometric),
        "lognormal" => Ok(BuiltinFn::Lognormal),
        "logistic" => Ok(BuiltinFn::Logistic),
        "montecarlo" => Ok(BuiltinFn::Montecarlo),
        "poisson" => Ok(BuiltinFn::Poisson),
        "triangular" => Ok(BuiltinFn::Triangular),
        "weibull" => Ok(BuiltinFn::Weibull),
        "pareto" => Ok(BuiltinFn::Pareto),
        "invnorm" => Ok(BuiltinFn::Invnorm),
        "normalcdf" => Ok(BuiltinFn::NormalCDF),
        // Array aggregations
        "arr_sum" => Ok(BuiltinFn::ArrSum),
        "arr_prod" => Ok(BuiltinFn::ArrProd),
        "arr_mean" => Ok(BuiltinFn::ArrMean),
        "arr_median" => Ok(BuiltinFn::ArrMedian),
        "arr_stddev" => Ok(BuiltinFn::ArrStddev),
        "seeded" => Ok(BuiltinFn::Seeded),
        "bounded" => Ok(BuiltinFn::Bounded),
        "sample" => Ok(BuiltinFn::Sample),
        "positive" => Ok(BuiltinFn::Positive),
        "cut_out" => Ok(BuiltinFn::CutOut),
        "cut_in" => Ok(BuiltinFn::CutIn),
        "conveyor_start" => Ok(BuiltinFn::ConveyorStart),
        "conveyor_flow" => Ok(BuiltinFn::ConveyorFlow),
        "conveyor_change" => Ok(BuiltinFn::ConveyorChange),
        "agecount" => Ok(BuiltinFn::AgeCount),
        "arr_largest" => Ok(BuiltinFn::ArrLargest),
        "arr_rank" => Ok(BuiltinFn::ArrRank),
        "arr_percentile" => Ok(BuiltinFn::ArrPercentile),
        "arr_interpolate" => Ok(BuiltinFn::ArrInterpolate),
        "arr_max" => Ok(BuiltinFn::ArrMax),
        "arr_min" => Ok(BuiltinFn::ArrMin),
        _ => Err(ParseError::UnknownFunction(name.to_string())),
    }
}

// ── Topological sort ────────────────────────────────────────────────────────

/// Collect the entity references (Ref(idx)) of an expression.
///
/// With `break_delays`, the *input* of a `delay(...)` counts as a dependency on a past
/// timestep rather than the current one, so it contributes no ordering edge.
///
/// `delay` evaluates to `memo[input][step - delay_steps]` (see builtins.rs), a cell
/// written in an earlier step, so the input need not be evaluated before the delay
/// within a step. Skipping that edge lets feedback loops whose only time offset is a
/// delay be ordered at all — the standard System Dynamics ordering policy.
///
/// Exception: a delay whose duration is a *literal* rounding to 0 steps really does
/// read the current step, so its edge is kept and such a loop stays unsolvable. A
/// non-literal duration cannot be decided at load time; those are assumed to be at
/// least one dt.
fn collect_refs_inner(expr: &Expr, refs: &mut Vec<usize>, break_delays: bool, dt: f64) {
    match expr {
        Expr::Literal(_) => {}
        Expr::Ref(idx) => refs.push(*idx),
        Expr::BinaryOp { left, right, .. } => {
            collect_refs_inner(left, refs, break_delays, dt);
            collect_refs_inner(right, refs, break_delays, dt);
        }
        Expr::UnaryOp { operand, .. } => collect_refs_inner(operand, refs, break_delays, dt),
        Expr::Call { function, args } => {
            let skip_input = break_delays
                && matches!(function, BuiltinFn::Delay)
                && !delay_is_known_zero_steps(args, dt);
            for (i, a) in args.iter().enumerate() {
                if skip_input && i == 0 {
                    continue;
                }
                collect_refs_inner(a, refs, break_delays, dt);
            }
        }
        Expr::If {
            condition,
            then,
            else_,
        } => {
            collect_refs_inner(condition, refs, break_delays, dt);
            collect_refs_inner(then, refs, break_delays, dt);
            collect_refs_inner(else_, refs, break_delays, dt);
        }
        #[cfg(feature = "python")]
        Expr::PyCallback { args, .. } => {
            // A callback reads whatever its arguments read, so those edges have to be in
            // the ordering - otherwise the engine would call Python with a cell that has
            // not been evaluated at this step yet.
            for a in args {
                collect_refs_inner(a, refs, break_delays, dt);
            }
        }
    }
}

/// True when a delay's duration is a literal that rounds to zero timesteps, i.e. the
/// delay reads the current step and therefore breaks no dependency cycle.
fn delay_is_known_zero_steps(args: &[Expr], dt: f64) -> bool {
    match args.get(1) {
        Some(Expr::Literal(duration)) => (duration / dt).round() as i64 == 0,
        _ => false,
    }
}

/// Topological sort of non-stock entities so they can be eagerly evaluated
/// in dependency order. Returns indices into the entities vec.
///
/// With `at_start` it sorts every entity for the start time instead: there a stock holds
/// its initial value, so it comes after what that reads, and whatever reads a stock comes
/// after the stock. One pass in that order settles the start the way the Python engine
/// does by evaluating on demand.
///
/// Two passes: first with every reference treated as a same-step dependency, which
/// keeps the evaluation order of all models that already worked exactly as it was.
/// Only if that reports a cycle is the sort retried with the input edges of
/// `delay(...)` dropped — those read a past memo cell and so break loops (see
/// `collect_refs_inner`). A model that is cyclic under both passes is
/// genuinely unsolvable in a single pass per timestep and is rejected.
fn topological_sort(entities: &[Entity], dt: f64, at_start: bool) -> Result<Vec<usize>, ParseError> {
    if let Ok(order) = topological_sort_pass(entities, dt, false, at_start) {
        return Ok(order);
    }
    match topological_sort_pass(entities, dt, true, at_start) {
        Ok(order) => Ok(order),
        // Only now, on the definitive failure, is it worth naming the culprits.
        Err(_) => Err(ParseError::CyclicDependency(describe_cycles(entities, dt, at_start))),
    }
}

/// Whether `entity` takes part in the sort: every entity at the start, else the non-stocks.
fn is_sorted(entity: &Entity, at_start: bool) -> bool {
    at_start || !matches!(entity.kind, EntityKind::Stock { .. })
}

/// What `entity` reads: a stock at the start its initial value, anything else its equation.
fn references(entity: &Entity, break_delays: bool, dt: f64) -> Vec<usize> {
    let expr = match entity.kind {
        EntityKind::Stock { ref initial_value } => initial_value,
        _ => &entity.equation,
    };
    let mut refs = Vec::new();
    collect_refs_inner(expr, &mut refs, break_delays, dt);
    refs
}

/// Adjacency list "entity → entities that must be evaluated before it", restricted to
/// the entities the sort orders and using the same edges the second sorting pass uses.
fn dependency_edges(entities: &[Entity], dt: f64, at_start: bool) -> HashMap<usize, Vec<usize>> {
    let mut edges: HashMap<usize, Vec<usize>> = HashMap::new();
    for (idx, entity) in entities.iter().enumerate() {
        if !is_sorted(entity, at_start) {
            continue;
        }
        let mut refs = references(entity, true, dt);
        refs.retain(|&dep| is_sorted(&entities[dep], at_start));
        refs.sort_unstable();
        refs.dedup();
        edges.insert(idx, refs);
    }
    edges
}

/// Human-readable paths for every cycle in the dependency graph, e.g. `"a → b → a"`.
///
/// Runs only when a model is definitively rejected, so its cost never touches a healthy
/// model. Groups the entities with Tarjan's algorithm and then reports, per group, the
/// shortest cycle through its lowest-numbered member — a short path reads better than a
/// dump of everything involved, and the group size is appended when it is larger.
fn describe_cycles(entities: &[Entity], dt: f64, at_start: bool) -> Vec<String> {
    let edges = dependency_edges(entities, dt, at_start);
    let mut descriptions = Vec::new();

    for group in strongly_connected_components(&edges) {
        let members: std::collections::HashSet<usize> = group.iter().copied().collect();
        let start = *group.iter().min().expect("a component is never empty");

        let is_self_loop = edges.get(&start).is_some_and(|deps| deps.contains(&start));
        if members.len() < 2 && !is_self_loop {
            continue; // a single entity without a self-reference is not a cycle
        }

        let mut path = shortest_cycle_through(start, &members, &edges)
            .into_iter()
            .map(|idx| entities[idx].name.clone())
            .collect::<Vec<_>>()
            .join(" → ");
        if members.len() > 1 && members.len() > path.matches('→').count() {
            path.push_str(&format!(" ({} entities involved)", members.len()));
        }
        descriptions.push(path);
    }

    descriptions.sort();
    if descriptions.len() > 3 {
        let extra = descriptions.len() - 3;
        descriptions.truncate(3);
        descriptions.push(format!("and {} further cycle(s)", extra));
    }
    descriptions
}

/// Shortest cycle from `start` back to `start`, staying inside `members`. Returned as
/// the node sequence with `start` repeated at the end.
fn shortest_cycle_through(
    start: usize,
    members: &std::collections::HashSet<usize>,
    edges: &HashMap<usize, Vec<usize>>,
) -> Vec<usize> {
    let mut predecessor: HashMap<usize, usize> = HashMap::new();
    let mut queue = std::collections::VecDeque::from(vec![start]);
    let mut seen = std::collections::HashSet::from([start]);

    while let Some(current) = queue.pop_front() {
        for &next in edges.get(&current).into_iter().flatten() {
            if next == start {
                let mut path = vec![start];
                let mut node = current;
                while node != start {
                    path.push(node);
                    node = predecessor[&node];
                }
                path.push(start);
                path.reverse();
                return path;
            }
            if members.contains(&next) && seen.insert(next) {
                predecessor.insert(next, current);
                queue.push_back(next);
            }
        }
    }
    vec![start] // unreachable for a real component, but never panic while reporting
}

/// Tarjan's algorithm, iterative so that a deeply nested model cannot blow the stack.
fn strongly_connected_components(edges: &HashMap<usize, Vec<usize>>) -> Vec<Vec<usize>> {
    let mut nodes: Vec<usize> = edges.keys().copied().collect();
    nodes.sort_unstable();

    let mut index_of: HashMap<usize, usize> = HashMap::new();
    let mut lowlink: HashMap<usize, usize> = HashMap::new();
    let mut on_stack: std::collections::HashSet<usize> = std::collections::HashSet::new();
    let mut stack: Vec<usize> = Vec::new();
    let mut next_index = 0usize;
    let mut components = Vec::new();

    for &root in &nodes {
        if index_of.contains_key(&root) {
            continue;
        }
        // (node, position in its successor list)
        let mut call_stack: Vec<(usize, usize)> = vec![(root, 0)];
        index_of.insert(root, next_index);
        lowlink.insert(root, next_index);
        next_index += 1;
        stack.push(root);
        on_stack.insert(root);

        while let Some((node, successor)) = call_stack.pop() {
            let successors = edges.get(&node).map(Vec::as_slice).unwrap_or(&[]);
            if successor < successors.len() {
                call_stack.push((node, successor + 1));
                let next = successors[successor];
                if !index_of.contains_key(&next) {
                    index_of.insert(next, next_index);
                    lowlink.insert(next, next_index);
                    next_index += 1;
                    stack.push(next);
                    on_stack.insert(next);
                    call_stack.push((next, 0));
                } else if on_stack.contains(&next) {
                    let candidate = index_of[&next];
                    let current = lowlink[&node];
                    lowlink.insert(node, current.min(candidate));
                }
                continue;
            }

            if lowlink[&node] == index_of[&node] {
                let mut component = Vec::new();
                while let Some(member) = stack.pop() {
                    on_stack.remove(&member);
                    component.push(member);
                    if member == node {
                        break;
                    }
                }
                components.push(component);
            }
            if let Some(&(parent, _)) = call_stack.last() {
                let child = lowlink[&node];
                let current = lowlink[&parent];
                lowlink.insert(parent, current.min(child));
            }
        }
    }
    components
}

fn topological_sort_pass(
    entities: &[Entity],
    dt: f64,
    break_delays: bool,
    at_start: bool,
) -> Result<Vec<usize>, ParseError> {
    let n = entities.len();

    let sorted_indices: Vec<usize> = (0..n).filter(|&i| is_sorted(&entities[i], at_start)).collect();

    // Map entity index → position in sorted_indices
    let mut idx_to_pos: HashMap<usize, usize> = HashMap::new();
    for (pos, &idx) in sorted_indices.iter().enumerate() {
        idx_to_pos.insert(idx, pos);
    }

    let ns_count = sorted_indices.len();
    let mut in_degree = vec![0usize; ns_count];
    let mut dependents: Vec<Vec<usize>> = vec![Vec::new(); ns_count];

    for (pos, &idx) in sorted_indices.iter().enumerate() {
        for dep_idx in references(&entities[idx], break_delays, dt) {
            if let Some(&dep_pos) = idx_to_pos.get(&dep_idx) {
                in_degree[pos] += 1;
                dependents[dep_pos].push(pos);
            }
        }
    }

    // Kahn's algorithm
    let mut queue: Vec<usize> = Vec::new();
    for pos in 0..ns_count {
        if in_degree[pos] == 0 {
            queue.push(pos);
        }
    }

    let mut sorted: Vec<usize> = Vec::with_capacity(ns_count);
    while let Some(pos) = queue.pop() {
        sorted.push(sorted_indices[pos]);
        for &dep_pos in &dependents[pos] {
            in_degree[dep_pos] -= 1;
            if in_degree[dep_pos] == 0 {
                queue.push(dep_pos);
            }
        }
    }

    if sorted.len() != ns_count {
        return Err(ParseError::CyclicDependency(Vec::new()));
    }

    Ok(sorted)
}

/// The name a seeded draw is reported under - `seed:` and the Python engine's name of the
/// distribution - or `None` for a builtin that draws nothing.
/// The random function a `seeded` node draws from: its last argument, or the draw inside the
/// `bounded` that is its last argument.
pub fn draw_of(expr: &Expr) -> Option<&BuiltinFn> {
    match expr {
        Expr::Call { function: BuiltinFn::Bounded, args } => draw_of(&args[2]),
        Expr::Call { function, .. } if seeded_draw_name(function).is_some() => Some(function),
        _ => None,
    }
}

/// What a draw with bounds reports: bounds the draw never met in its tries, or a minimum
/// above the maximum.
pub fn bounds_report(function: &BuiltinFn, reversed: bool) -> &'static str {
    use BuiltinFn::*;
    match (function, reversed) {
        (Random, false) => "bounds:uniform:missed",
        (Random, true) => "bounds:uniform:reversed",
        (Normal, false) => "bounds:normal:missed",
        (Normal, true) => "bounds:normal:reversed",
        (Beta, false) => "bounds:beta:missed",
        (Beta, true) => "bounds:beta:reversed",
        (Binomial, false) => "bounds:binomial:missed",
        (Binomial, true) => "bounds:binomial:reversed",
        (NegBinomial, false) => "bounds:negbinomial:missed",
        (NegBinomial, true) => "bounds:negbinomial:reversed",
        (Exprnd, false) => "bounds:exprnd:missed",
        (Exprnd, true) => "bounds:exprnd:reversed",
        (GammaDist, false) => "bounds:gamma:missed",
        (GammaDist, true) => "bounds:gamma:reversed",
        (Geometric, false) => "bounds:geometric:missed",
        (Geometric, true) => "bounds:geometric:reversed",
        (Lognormal, false) => "bounds:lognormal:missed",
        (Lognormal, true) => "bounds:lognormal:reversed",
        (Logistic, false) => "bounds:logistic:missed",
        (Logistic, true) => "bounds:logistic:reversed",
        (Montecarlo, false) => "bounds:montecarlo:missed",
        (Montecarlo, true) => "bounds:montecarlo:reversed",
        (Poisson, false) => "bounds:poisson:missed",
        (Poisson, true) => "bounds:poisson:reversed",
        (Triangular, false) => "bounds:triangular:missed",
        (Triangular, true) => "bounds:triangular:reversed",
        (Weibull, false) => "bounds:weibull:missed",
        (Weibull, true) => "bounds:weibull:reversed",
        (Pareto, false) => "bounds:pareto:missed",
        (Pareto, true) => "bounds:pareto:reversed",
        (LookupRandom(..), false) => "bounds:lookuprandom:missed",
        (LookupRandom(..), true) => "bounds:lookuprandom:reversed",
        _ => "bounds:unknown:missed",
    }
}

pub fn seeded_draw_name(function: &BuiltinFn) -> Option<&'static str> {
    use BuiltinFn::*;
    Some(match function {
        Random => "seed:uniform",
        Normal => "seed:normal",
        Beta => "seed:beta",
        Binomial => "seed:binomial",
        NegBinomial => "seed:negbinomial",
        Exprnd => "seed:exprnd",
        GammaDist => "seed:gamma",
        Geometric => "seed:geometric",
        Lognormal => "seed:lognormal",
        Logistic => "seed:logistic",
        Montecarlo => "seed:montecarlo",
        Poisson => "seed:poisson",
        Triangular => "seed:triangular",
        Weibull => "seed:weibull",
        Pareto => "seed:pareto",
        LookupRandom(..) => "seed:lookuprandom",
        _ => return None,
    })
}
