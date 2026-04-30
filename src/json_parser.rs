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
    CyclicDependency,
}

impl std::fmt::Display for ParseError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            ParseError::Json(e) => write!(f, "JSON parse error: {}", e),
            ParseError::UnknownEntity(name) => write!(f, "Unknown entity: '{}'", name),
            ParseError::UnknownBinaryOp(op) => write!(f, "Unknown binary operator: '{}'", op),
            ParseError::UnknownUnaryOp(op) => write!(f, "Unknown unary operator: '{}'", op),
            ParseError::UnknownFunction(name) => write!(f, "Unknown function: '{}'", name),
            ParseError::CyclicDependency => write!(f, "Cyclic dependency among non-stock entities"),
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

    // Build entity_index: name → index
    // Order: stocks first, then flows, converters, constants
    let mut entity_index: HashMap<String, usize> = HashMap::new();
    let mut entities: Vec<Entity> = Vec::new();

    // Stocks
    for s in &jm.entities.stocks {
        entity_index.insert(s.name.clone(), entities.len());
        entities.push(Entity {
            name: s.name.clone(),
            kind: EntityKind::Stock {
                initial_value: Expr::Literal(0.0),
            },
            equation: Expr::Literal(0.0),
        });
    }

    // Flows
    for f in &jm.entities.flows {
        entity_index.insert(f.name.clone(), entities.len());
        entities.push(Entity {
            name: f.name.clone(),
            kind: EntityKind::Flow,
            equation: Expr::Literal(0.0),
        });
    }

    // Biflows
    for f in &jm.entities.biflows {
        entity_index.insert(f.name.clone(), entities.len());
        entities.push(Entity {
            name: f.name.clone(),
            kind: EntityKind::Biflow,
            equation: Expr::Literal(0.0),
        });
    }

    // Converters
    for c in &jm.entities.converters {
        entity_index.insert(c.name.clone(), entities.len());
        entities.push(Entity {
            name: c.name.clone(),
            kind: EntityKind::Converter,
            equation: Expr::Literal(0.0),
        });
    }

    // Constants
    for c in &jm.entities.constants {
        entity_index.insert(c.name.clone(), entities.len());
        entities.push(Entity {
            name: c.name.clone(),
            kind: EntityKind::Constant,
            equation: Expr::Literal(0.0),
        });
    }

    // Now resolve all expressions with the complete entity_index

    // Stocks: resolve initial_value and equation
    let mut idx = 0;
    for s in &jm.entities.stocks {
        let initial_value = resolve_expr(&s.initial_value, &entity_index)?;
        let equation = match &s.equation {
            Some(eq) => resolve_expr(eq, &entity_index)?,
            None => Expr::Literal(0.0),
        };
        entities[idx].kind = EntityKind::Stock { initial_value };
        entities[idx].equation = equation;
        idx += 1;
    }

    // Flows
    for f in &jm.entities.flows {
        entities[idx].equation = resolve_expr(&f.equation, &entity_index)?;
        idx += 1;
    }

    // Biflows
    for f in &jm.entities.biflows {
        entities[idx].equation = resolve_expr(&f.equation, &entity_index)?;
        idx += 1;
    }

    // Converters
    for c in &jm.entities.converters {
        entities[idx].equation = resolve_expr(&c.equation, &entity_index)?;
        idx += 1;
    }

    // Constants
    for c in &jm.entities.constants {
        entities[idx].equation = resolve_expr(&c.equation, &entity_index)?;
        idx += 1;
    }

    // Parse graphical functions
    let graphical_functions: HashMap<String, GraphicalFunction> = jm
        .graphical_functions
        .into_iter()
        .map(|(name, gf)| (name, GraphicalFunction { points: gf.points }))
        .collect();

    // Topological sort of non-stock entities
    let eval_order = topological_sort(&entities)?;

    Ok(SdModel {
        name: jm.name.unwrap_or_default(),
        starttime: jm.specs.starttime,
        stoptime: jm.specs.stoptime,
        dt: jm.specs.dt,
        entities,
        entity_index,
        graphical_functions,
        eval_order,
    })
}

/// Resolve a JSON expression tree into a typed Expr with usize references.
fn resolve_expr(
    json_expr: &JsonExpr,
    entity_index: &HashMap<String, usize>,
) -> Result<Expr, ParseError> {
    match json_expr {
        JsonExpr::Literal { value } => match value {
            JsonLiteralValue::Number(n) => Ok(Expr::Literal(*n)),
            JsonLiteralValue::String(_) => {
                // String literals are only used as lookup table name args —
                // they shouldn't appear as standalone expressions.
                // If they do, treat as 0.0 (the Call/Lookup resolution handles the name).
                Ok(Expr::Literal(0.0))
            }
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
                left: Box::new(resolve_expr(left, entity_index)?),
                right: Box::new(resolve_expr(right, entity_index)?),
            })
        }
        JsonExpr::UnaryOp { op, operand } => {
            let un_op = parse_un_op(op)?;
            Ok(Expr::UnaryOp {
                op: un_op,
                operand: Box::new(resolve_expr(operand, entity_index)?),
            })
        }
        JsonExpr::Call { function, args } => {
            // Special case: lookup function — second arg is the table name
            if function == "lookup" && args.len() == 2 {
                if let JsonExpr::Literal {
                    value: JsonLiteralValue::String(table_name),
                } = &args[1]
                {
                    let resolved_args = vec![resolve_expr(&args[0], entity_index)?];
                    return Ok(Expr::Call {
                        function: BuiltinFn::Lookup(table_name.clone()),
                        args: resolved_args,
                    });
                }
            }

            let builtin = parse_builtin_fn(function)?;
            let resolved_args: Result<Vec<Expr>, ParseError> = args
                .iter()
                .map(|a| resolve_expr(a, entity_index))
                .collect();
            Ok(Expr::Call {
                function: builtin,
                args: resolved_args?,
            })
        }
        JsonExpr::If {
            condition,
            then,
            else_,
        } => Ok(Expr::If {
            condition: Box::new(resolve_expr(condition, entity_index)?),
            then: Box::new(resolve_expr(then, entity_index)?),
            else_: Box::new(resolve_expr(else_, entity_index)?),
        }),
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
        "pi" => Ok(BuiltinFn::Pi),
        "step" => Ok(BuiltinFn::Step),
        "pulse" => Ok(BuiltinFn::Pulse),
        "delay" => Ok(BuiltinFn::Delay),
        // Combinatorial & special
        "combinations" => Ok(BuiltinFn::Combinations),
        "permutations" => Ok(BuiltinFn::Permutations),
        "factorial" => Ok(BuiltinFn::Factorial),
        "gammaln" => Ok(BuiltinFn::GammaLN),
        "inf" => Ok(BuiltinFn::Inf),
        "nan" => Ok(BuiltinFn::Nan),
        // Statistical
        "random" | "uniform" => Ok(BuiltinFn::Random),
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
        _ => Err(ParseError::UnknownFunction(name.to_string())),
    }
}

// ── Topological sort ────────────────────────────────────────────────────────

/// Collect direct entity references (Ref(idx)) from an expression.
fn collect_refs(expr: &Expr, refs: &mut Vec<usize>) {
    match expr {
        Expr::Literal(_) => {}
        Expr::Ref(idx) => refs.push(*idx),
        Expr::BinaryOp { left, right, .. } => {
            collect_refs(left, refs);
            collect_refs(right, refs);
        }
        Expr::UnaryOp { operand, .. } => collect_refs(operand, refs),
        Expr::Call { args, .. } => {
            for a in args {
                collect_refs(a, refs);
            }
        }
        Expr::If {
            condition,
            then,
            else_,
        } => {
            collect_refs(condition, refs);
            collect_refs(then, refs);
            collect_refs(else_, refs);
        }
    }
}

/// Topological sort of non-stock entities so they can be eagerly evaluated
/// in dependency order. Returns indices into the entities vec.
fn topological_sort(entities: &[Entity]) -> Result<Vec<usize>, ParseError> {
    let n = entities.len();

    let non_stock_indices: Vec<usize> = (0..n)
        .filter(|i| !matches!(entities[*i].kind, EntityKind::Stock { .. }))
        .collect();

    let is_non_stock: Vec<bool> = (0..n)
        .map(|i| !matches!(entities[i].kind, EntityKind::Stock { .. }))
        .collect();

    // Map entity index → position in non_stock_indices
    let mut idx_to_pos: HashMap<usize, usize> = HashMap::new();
    for (pos, &idx) in non_stock_indices.iter().enumerate() {
        idx_to_pos.insert(idx, pos);
    }

    let ns_count = non_stock_indices.len();
    let mut in_degree = vec![0usize; ns_count];
    let mut dependents: Vec<Vec<usize>> = vec![Vec::new(); ns_count];

    for (pos, &idx) in non_stock_indices.iter().enumerate() {
        let mut refs = Vec::new();
        collect_refs(&entities[idx].equation, &mut refs);
        for dep_idx in refs {
            if is_non_stock[dep_idx] {
                if let Some(&dep_pos) = idx_to_pos.get(&dep_idx) {
                    in_degree[pos] += 1;
                    dependents[dep_pos].push(pos);
                }
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
        sorted.push(non_stock_indices[pos]);
        for &dep_pos in &dependents[pos] {
            in_degree[dep_pos] -= 1;
            if in_degree[dep_pos] == 0 {
                queue.push(dep_pos);
            }
        }
    }

    if sorted.len() != ns_count {
        return Err(ParseError::CyclicDependency);
    }

    Ok(sorted)
}
