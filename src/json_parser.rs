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
    /// Carries one readable path per cycle, e.g. `["a → b → a"]`. Empty when the
    /// cycle was detected but not described (the first, cheap sorting pass).
    CyclicDependency(Vec<String>),
}

impl std::fmt::Display for ParseError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            ParseError::Json(e) => write!(f, "JSON parse error: {}", e),
            ParseError::UnknownEntity(name) => write!(f, "Unknown entity: '{}'", name),
            ParseError::UnknownBinaryOp(op) => write!(f, "Unknown binary operator: '{}'", op),
            ParseError::UnknownUnaryOp(op) => write!(f, "Unknown unary operator: '{}'", op),
            ParseError::UnknownFunction(name) => write!(f, "Unknown function: '{}'", name),
            ParseError::CyclicDependency(cycles) if cycles.is_empty() => {
                write!(f, "Cyclic dependency among non-stock entities")
            }
            ParseError::CyclicDependency(cycles) => write!(
                f,
                "Cyclic dependency among non-stock entities: {}",
                cycles.join("; ")
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
    let eval_order = topological_sort(&entities, jm.specs.dt)?;

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
    collect_refs_inner(expr, refs, false, 1.0)
}

/// Like `collect_refs`, but treats the *input* of a `delay(...)` as a dependency on
/// a past timestep rather than the current one, so it contributes no ordering edge.
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
fn collect_refs_breaking_delays(expr: &Expr, refs: &mut Vec<usize>, dt: f64) {
    collect_refs_inner(expr, refs, true, dt)
}

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
/// Two passes: first with every reference treated as a same-step dependency, which
/// keeps the evaluation order of all models that already worked exactly as it was.
/// Only if that reports a cycle is the sort retried with the input edges of
/// `delay(...)` dropped — those read a past memo cell and so break loops (see
/// `collect_refs_breaking_delays`). A model that is cyclic under both passes is
/// genuinely unsolvable in a single pass per timestep and is rejected.
fn topological_sort(entities: &[Entity], dt: f64) -> Result<Vec<usize>, ParseError> {
    if let Ok(order) = topological_sort_pass(entities, dt, false) {
        return Ok(order);
    }
    match topological_sort_pass(entities, dt, true) {
        Ok(order) => Ok(order),
        // Only now, on the definitive failure, is it worth naming the culprits.
        Err(_) => Err(ParseError::CyclicDependency(describe_cycles(entities, dt))),
    }
}

/// Adjacency list "entity → entities that must be evaluated before it", restricted to
/// non-stock entities and using the same edges the second sorting pass uses.
fn dependency_edges(entities: &[Entity], dt: f64) -> HashMap<usize, Vec<usize>> {
    let mut edges: HashMap<usize, Vec<usize>> = HashMap::new();
    for (idx, entity) in entities.iter().enumerate() {
        if matches!(entity.kind, EntityKind::Stock { .. }) {
            continue;
        }
        let mut refs = Vec::new();
        collect_refs_breaking_delays(&entity.equation, &mut refs, dt);
        refs.retain(|&dep| !matches!(entities[dep].kind, EntityKind::Stock { .. }));
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
fn describe_cycles(entities: &[Entity], dt: f64) -> Vec<String> {
    let edges = dependency_edges(entities, dt);
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
) -> Result<Vec<usize>, ParseError> {
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
        if break_delays {
            collect_refs_breaking_delays(&entities[idx].equation, &mut refs, dt);
        } else {
            collect_refs(&entities[idx].equation, &mut refs);
        }
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
        return Err(ParseError::CyclicDependency(Vec::new()));
    }

    Ok(sorted)
}
