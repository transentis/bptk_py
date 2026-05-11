use std::collections::HashMap;

use bptk_rust_engine::model::*;
use bptk_rust_engine::state::SimulationState;

fn model_with_specs(starttime: f64, stoptime: f64, dt: f64) -> SdModel {
    SdModel {
        name: String::new(),
        starttime,
        stoptime,
        dt,
        entities: Vec::new(),
        entity_index: HashMap::new(),
        graphical_functions: HashMap::new(),
        eval_order: Vec::new(),
    }
}

// ── Temporal functions ──────────────────────────────────────────────────

#[test]
fn test_time() {
    let model = model_with_specs(0.0, 10.0, 1.0);
    let state = SimulationState::new(0, 11, None);
    let expr = Expr::Call {
        function: BuiltinFn::Time,
        args: vec![],
    };
    assert_eq!(model.eval_expr(&expr, &state, 0), 0.0);
    assert_eq!(model.eval_expr(&expr, &state, 5), 5.0);
    assert_eq!(model.eval_expr(&expr, &state, 10), 10.0);
}

#[test]
fn test_time_with_fractional_dt() {
    let model = model_with_specs(0.0, 10.0, 0.25);
    let state = SimulationState::new(0, 41, None);
    let expr = Expr::Call {
        function: BuiltinFn::Time,
        args: vec![],
    };
    assert_eq!(model.eval_expr(&expr, &state, 0), 0.0);
    assert_eq!(model.eval_expr(&expr, &state, 4), 1.0);
    assert_eq!(model.eval_expr(&expr, &state, 40), 10.0);
}

#[test]
fn test_time_with_nonzero_starttime() {
    let model = model_with_specs(5.0, 15.0, 1.0);
    let state = SimulationState::new(0, 11, None);
    let expr = Expr::Call {
        function: BuiltinFn::Time,
        args: vec![],
    };
    assert_eq!(model.eval_expr(&expr, &state, 0), 5.0);
    assert_eq!(model.eval_expr(&expr, &state, 5), 10.0);
}

#[test]
fn test_dt() {
    let model = model_with_specs(0.0, 10.0, 0.25);
    let state = SimulationState::new(0, 1, None);
    let expr = Expr::Call {
        function: BuiltinFn::Dt,
        args: vec![],
    };
    assert_eq!(model.eval_expr(&expr, &state, 0), 0.25);
}

#[test]
fn test_starttime_stoptime() {
    let model = model_with_specs(5.0, 100.0, 1.0);
    let state = SimulationState::new(0, 1, None);
    assert_eq!(
        model.eval_expr(
            &Expr::Call {
                function: BuiltinFn::Starttime,
                args: vec![]
            },
            &state,
            0
        ),
        5.0
    );
    assert_eq!(
        model.eval_expr(
            &Expr::Call {
                function: BuiltinFn::Stoptime,
                args: vec![]
            },
            &state,
            0
        ),
        100.0
    );
}

// ── Math functions ──────────────────────────────────────────────────────

#[test]
fn test_abs() {
    let model = model_with_specs(0.0, 10.0, 1.0);
    let state = SimulationState::new(0, 1, None);
    let expr = Expr::Call {
        function: BuiltinFn::Abs,
        args: vec![Expr::Literal(-5.0)],
    };
    assert_eq!(model.eval_expr(&expr, &state, 0), 5.0);
}

#[test]
fn test_sqrt() {
    let model = model_with_specs(0.0, 10.0, 1.0);
    let state = SimulationState::new(0, 1, None);
    let expr = Expr::Call {
        function: BuiltinFn::Sqrt,
        args: vec![Expr::Literal(16.0)],
    };
    assert_eq!(model.eval_expr(&expr, &state, 0), 4.0);
}

#[test]
fn test_exp_ln() {
    let model = model_with_specs(0.0, 10.0, 1.0);
    let state = SimulationState::new(0, 1, None);

    let exp_expr = Expr::Call {
        function: BuiltinFn::Exp,
        args: vec![Expr::Literal(1.0)],
    };
    assert!((model.eval_expr(&exp_expr, &state, 0) - std::f64::consts::E).abs() < 1e-10);

    let ln_expr = Expr::Call {
        function: BuiltinFn::Ln,
        args: vec![Expr::Literal(std::f64::consts::E)],
    };
    assert!((model.eval_expr(&ln_expr, &state, 0) - 1.0).abs() < 1e-10);
}

#[test]
fn test_log10() {
    let model = model_with_specs(0.0, 10.0, 1.0);
    let state = SimulationState::new(0, 1, None);
    let expr = Expr::Call {
        function: BuiltinFn::Log10,
        args: vec![Expr::Literal(100.0)],
    };
    assert!((model.eval_expr(&expr, &state, 0) - 2.0).abs() < 1e-10);
}

#[test]
fn test_trig_functions() {
    let model = model_with_specs(0.0, 10.0, 1.0);
    let state = SimulationState::new(0, 1, None);

    // sin(0) = 0
    let sin_expr = Expr::Call {
        function: BuiltinFn::Sin,
        args: vec![Expr::Literal(0.0)],
    };
    assert!((model.eval_expr(&sin_expr, &state, 0)).abs() < 1e-10);

    // cos(0) = 1
    let cos_expr = Expr::Call {
        function: BuiltinFn::Cos,
        args: vec![Expr::Literal(0.0)],
    };
    assert!((model.eval_expr(&cos_expr, &state, 0) - 1.0).abs() < 1e-10);

    // tan(0) = 0
    let tan_expr = Expr::Call {
        function: BuiltinFn::Tan,
        args: vec![Expr::Literal(0.0)],
    };
    assert!((model.eval_expr(&tan_expr, &state, 0)).abs() < 1e-10);

    // arcsin(0) = 0
    let asin_expr = Expr::Call {
        function: BuiltinFn::Arcsin,
        args: vec![Expr::Literal(0.0)],
    };
    assert!((model.eval_expr(&asin_expr, &state, 0)).abs() < 1e-10);

    // arccos(1) = 0
    let acos_expr = Expr::Call {
        function: BuiltinFn::Arccos,
        args: vec![Expr::Literal(1.0)],
    };
    assert!((model.eval_expr(&acos_expr, &state, 0)).abs() < 1e-10);

    // arctan(0) = 0
    let atan_expr = Expr::Call {
        function: BuiltinFn::Arctan,
        args: vec![Expr::Literal(0.0)],
    };
    assert!((model.eval_expr(&atan_expr, &state, 0)).abs() < 1e-10);
}

#[test]
fn test_max_min() {
    let model = model_with_specs(0.0, 10.0, 1.0);
    let state = SimulationState::new(0, 1, None);

    let max_expr = Expr::Call {
        function: BuiltinFn::Max,
        args: vec![Expr::Literal(3.0), Expr::Literal(7.0)],
    };
    assert_eq!(model.eval_expr(&max_expr, &state, 0), 7.0);

    let min_expr = Expr::Call {
        function: BuiltinFn::Min,
        args: vec![Expr::Literal(3.0), Expr::Literal(7.0)],
    };
    assert_eq!(model.eval_expr(&min_expr, &state, 0), 3.0);
}

#[test]
fn test_round_floor_ceil() {
    let model = model_with_specs(0.0, 10.0, 1.0);
    let state = SimulationState::new(0, 1, None);

    let round_expr = Expr::Call {
        function: BuiltinFn::Round,
        args: vec![Expr::Literal(3.7)],
    };
    assert_eq!(model.eval_expr(&round_expr, &state, 0), 4.0);

    let floor_expr = Expr::Call {
        function: BuiltinFn::Floor,
        args: vec![Expr::Literal(3.7)],
    };
    assert_eq!(model.eval_expr(&floor_expr, &state, 0), 3.0);

    let ceil_expr = Expr::Call {
        function: BuiltinFn::Ceil,
        args: vec![Expr::Literal(3.2)],
    };
    assert_eq!(model.eval_expr(&ceil_expr, &state, 0), 4.0);
}

#[test]
fn test_pi() {
    let model = model_with_specs(0.0, 10.0, 1.0);
    let state = SimulationState::new(0, 1, None);
    let expr = Expr::Call {
        function: BuiltinFn::Pi,
        args: vec![],
    };
    assert_eq!(model.eval_expr(&expr, &state, 0), std::f64::consts::PI);
}

// ── Control functions ───────────────────────────────────────────────────

#[test]
fn test_step_function() {
    let model = model_with_specs(0.0, 10.0, 1.0);
    let state = SimulationState::new(0, 11, None);

    // step(height=100, timestep=5)
    let expr = Expr::Call {
        function: BuiltinFn::Step,
        args: vec![Expr::Literal(100.0), Expr::Literal(5.0)],
    };

    // t=0..5: should be 0 (t is not > 5)
    for step in 0..=5 {
        assert_eq!(model.eval_expr(&expr, &state, step), 0.0, "step={}", step);
    }
    // t=6..10: should be 100 (t > 5)
    for step in 6..=10 {
        assert_eq!(model.eval_expr(&expr, &state, step), 100.0, "step={}", step);
    }
}

#[test]
fn test_pulse_single() {
    let model = model_with_specs(0.0, 10.0, 1.0);
    let state = SimulationState::new(0, 11, None);

    // pulse(volume=10, first_pulse=3) — single pulse at t=3
    let expr = Expr::Call {
        function: BuiltinFn::Pulse,
        args: vec![Expr::Literal(10.0), Expr::Literal(3.0)],
    };

    for step in 0..=10 {
        let expected = if step == 3 { 10.0 / 1.0 } else { 0.0 };
        assert_eq!(
            model.eval_expr(&expr, &state, step),
            expected,
            "step={}",
            step
        );
    }
}

#[test]
fn test_pulse_with_interval() {
    let model = model_with_specs(0.0, 10.0, 1.0);
    let state = SimulationState::new(0, 11, None);

    // pulse(volume=10, first_pulse=2, interval=3) — pulses at t=2,5,8
    let expr = Expr::Call {
        function: BuiltinFn::Pulse,
        args: vec![
            Expr::Literal(10.0),
            Expr::Literal(2.0),
            Expr::Literal(3.0),
        ],
    };

    for step in 0..=10 {
        let t = step as f64;
        let expected = if t == 2.0 || t == 5.0 || t == 8.0 {
            10.0 / 1.0
        } else {
            0.0
        };
        assert_eq!(
            model.eval_expr(&expr, &state, step),
            expected,
            "step={}",
            step
        );
    }
}

// ── Sinwave / Coswave ───────────────────────────────────────────────────

#[test]
fn test_sinwave() {
    let model = model_with_specs(0.0, 10.0, 1.0);
    let state = SimulationState::new(0, 11, None);

    // sinwave(amplitude=5, period=10)
    // At t=0: sin(0) = 0 → 5*0 = 0
    // At t=2.5: sin(2π/10 * 2.5) = sin(π/2) = 1 → 5*1 = 5
    let expr = Expr::Call {
        function: BuiltinFn::Sinwave,
        args: vec![Expr::Literal(5.0), Expr::Literal(10.0)],
    };

    assert!((model.eval_expr(&expr, &state, 0)).abs() < 1e-10);
}

#[test]
fn test_coswave() {
    let model = model_with_specs(0.0, 10.0, 1.0);
    let state = SimulationState::new(0, 11, None);

    // coswave(amplitude=5, period=10)
    // At t=0: cos(0) = 1 → 5*1 = 5
    let expr = Expr::Call {
        function: BuiltinFn::Coswave,
        args: vec![Expr::Literal(5.0), Expr::Literal(10.0)],
    };

    assert!((model.eval_expr(&expr, &state, 0) - 5.0).abs() < 1e-10);
}

// ── Combinatorial & special functions ──────────────────────────────────

#[test]
fn test_factorial() {
    let model = model_with_specs(0.0, 10.0, 1.0);
    let state = SimulationState::new(0, 1, None);

    // factorial(5) = 120
    let expr = Expr::Call {
        function: BuiltinFn::Factorial,
        args: vec![Expr::Literal(5.0)],
    };
    assert_eq!(model.eval_expr(&expr, &state, 0), 120.0);

    // factorial(0) = 1
    let expr_zero = Expr::Call {
        function: BuiltinFn::Factorial,
        args: vec![Expr::Literal(0.0)],
    };
    assert_eq!(model.eval_expr(&expr_zero, &state, 0), 1.0);
}

#[test]
fn test_factorial_negative() {
    let model = model_with_specs(0.0, 10.0, 1.0);
    let state = SimulationState::new(0, 1, None);

    // factorial(-5) = 0 (guard for invalid input)
    let expr = Expr::Call {
        function: BuiltinFn::Factorial,
        args: vec![Expr::Literal(-5.0)],
    };
    assert_eq!(model.eval_expr(&expr, &state, 0), 0.0);
}

#[test]
fn test_combinations() {
    let model = model_with_specs(0.0, 10.0, 1.0);
    let state = SimulationState::new(0, 1, None);

    // C(10, 3) = 120
    let expr = Expr::Call {
        function: BuiltinFn::Combinations,
        args: vec![Expr::Literal(10.0), Expr::Literal(3.0)],
    };
    assert!((model.eval_expr(&expr, &state, 0) - 120.0).abs() < 1e-6);

    // C(5, 0) = 1
    let expr_zero = Expr::Call {
        function: BuiltinFn::Combinations,
        args: vec![Expr::Literal(5.0), Expr::Literal(0.0)],
    };
    assert!((model.eval_expr(&expr_zero, &state, 0) - 1.0).abs() < 1e-6);
}

#[test]
fn test_combinations_n_less_than_r() {
    let model = model_with_specs(0.0, 10.0, 1.0);
    let state = SimulationState::new(0, 1, None);

    // C(2, 5) = 0 (n < r)
    let expr = Expr::Call {
        function: BuiltinFn::Combinations,
        args: vec![Expr::Literal(2.0), Expr::Literal(5.0)],
    };
    assert_eq!(model.eval_expr(&expr, &state, 0), 0.0);
}

#[test]
fn test_permutations() {
    let model = model_with_specs(0.0, 10.0, 1.0);
    let state = SimulationState::new(0, 1, None);

    // P(5, 2) = 20
    let expr = Expr::Call {
        function: BuiltinFn::Permutations,
        args: vec![Expr::Literal(5.0), Expr::Literal(2.0)],
    };
    assert!((model.eval_expr(&expr, &state, 0) - 20.0).abs() < 1e-6);
}

#[test]
fn test_permutations_n_less_than_r() {
    let model = model_with_specs(0.0, 10.0, 1.0);
    let state = SimulationState::new(0, 1, None);

    // P(2, 5) = 0 (n < r)
    let expr = Expr::Call {
        function: BuiltinFn::Permutations,
        args: vec![Expr::Literal(2.0), Expr::Literal(5.0)],
    };
    assert_eq!(model.eval_expr(&expr, &state, 0), 0.0);
}

#[test]
fn test_gammaln() {
    let model = model_with_specs(0.0, 10.0, 1.0);
    let state = SimulationState::new(0, 1, None);

    // gammaln(5) = ln(Gamma(5)) = ln(24) ≈ 3.178
    let expr = Expr::Call {
        function: BuiltinFn::GammaLN,
        args: vec![Expr::Literal(5.0)],
    };
    assert!((model.eval_expr(&expr, &state, 0) - 3.178054).abs() < 1e-4);

    // gammaln(1) = 0
    let expr_one = Expr::Call {
        function: BuiltinFn::GammaLN,
        args: vec![Expr::Literal(1.0)],
    };
    assert!((model.eval_expr(&expr_one, &state, 0)).abs() < 1e-10);
}

#[test]
fn test_inf_nan() {
    let model = model_with_specs(0.0, 10.0, 1.0);
    let state = SimulationState::new(0, 1, None);

    let inf_expr = Expr::Call {
        function: BuiltinFn::Inf,
        args: vec![],
    };
    assert!(model.eval_expr(&inf_expr, &state, 0).is_infinite());

    let nan_expr = Expr::Call {
        function: BuiltinFn::Nan,
        args: vec![],
    };
    assert!(model.eval_expr(&nan_expr, &state, 0).is_nan());
}

// ── Stochastic function guards ─────────────────────────────────────────

#[test]
fn test_normal_negative_stddev() {
    let model = model_with_specs(0.0, 10.0, 1.0);
    let state = SimulationState::new(0, 1, Some(42));
    let expr = Expr::Call {
        function: BuiltinFn::Normal,
        args: vec![Expr::Literal(0.0), Expr::Literal(-1.0)],
    };
    assert!(model.eval_expr(&expr, &state, 0).is_nan());
}

#[test]
fn test_beta_negative_params() {
    let model = model_with_specs(0.0, 10.0, 1.0);
    let state = SimulationState::new(0, 1, Some(42));
    let expr = Expr::Call {
        function: BuiltinFn::Beta,
        args: vec![Expr::Literal(-1.0), Expr::Literal(2.0)],
    };
    assert!(model.eval_expr(&expr, &state, 0).is_nan());

    let expr2 = Expr::Call {
        function: BuiltinFn::Beta,
        args: vec![Expr::Literal(2.0), Expr::Literal(0.0)],
    };
    assert!(model.eval_expr(&expr2, &state, 0).is_nan());
}

#[test]
fn test_binomial_negative_n() {
    let model = model_with_specs(0.0, 10.0, 1.0);
    let state = SimulationState::new(0, 1, Some(42));
    let expr = Expr::Call {
        function: BuiltinFn::Binomial,
        args: vec![Expr::Literal(-5.0), Expr::Literal(0.5)],
    };
    assert!(model.eval_expr(&expr, &state, 0).is_nan());
}

#[test]
fn test_negbinomial_negative_n() {
    let model = model_with_specs(0.0, 10.0, 1.0);
    let state = SimulationState::new(0, 1, Some(42));
    let expr = Expr::Call {
        function: BuiltinFn::NegBinomial,
        args: vec![Expr::Literal(-5.0), Expr::Literal(0.5)],
    };
    assert!(model.eval_expr(&expr, &state, 0).is_nan());
}

#[test]
fn test_poisson_negative_mu() {
    let model = model_with_specs(0.0, 10.0, 1.0);
    let state = SimulationState::new(0, 1, Some(42));
    let expr = Expr::Call {
        function: BuiltinFn::Poisson,
        args: vec![Expr::Literal(-5.0)],
    };
    assert!(model.eval_expr(&expr, &state, 0).is_nan());
}

#[test]
fn test_gamma_negative_params() {
    let model = model_with_specs(0.0, 10.0, 1.0);
    let state = SimulationState::new(0, 1, Some(42));
    let expr = Expr::Call {
        function: BuiltinFn::GammaDist,
        args: vec![Expr::Literal(-1.0), Expr::Literal(2.0)],
    };
    assert!(model.eval_expr(&expr, &state, 0).is_nan());

    let expr2 = Expr::Call {
        function: BuiltinFn::GammaDist,
        args: vec![Expr::Literal(2.0), Expr::Literal(0.0)],
    };
    assert!(model.eval_expr(&expr2, &state, 0).is_nan());
}

#[test]
fn test_exprnd_negative_scale() {
    let model = model_with_specs(0.0, 10.0, 1.0);
    let state = SimulationState::new(0, 1, Some(42));
    let expr = Expr::Call {
        function: BuiltinFn::Exprnd,
        args: vec![Expr::Literal(-1.0)],
    };
    assert!(model.eval_expr(&expr, &state, 0).is_nan());

    let expr_zero = Expr::Call {
        function: BuiltinFn::Exprnd,
        args: vec![Expr::Literal(0.0)],
    };
    assert!(model.eval_expr(&expr_zero, &state, 0).is_nan());
}

#[test]
fn test_lognormal_negative_stddev() {
    let model = model_with_specs(0.0, 10.0, 1.0);
    let state = SimulationState::new(0, 1, Some(42));
    let expr = Expr::Call {
        function: BuiltinFn::Lognormal,
        args: vec![Expr::Literal(0.0), Expr::Literal(-1.0)],
    };
    assert!(model.eval_expr(&expr, &state, 0).is_nan());
}

#[test]
fn test_logistic_negative_scale() {
    let model = model_with_specs(0.0, 10.0, 1.0);
    let state = SimulationState::new(0, 1, Some(42));
    let expr = Expr::Call {
        function: BuiltinFn::Logistic,
        args: vec![Expr::Literal(0.0), Expr::Literal(-1.0)],
    };
    assert!(model.eval_expr(&expr, &state, 0).is_nan());
}

#[test]
fn test_triangular_invalid_ordering() {
    let model = model_with_specs(0.0, 10.0, 1.0);
    let state = SimulationState::new(0, 1, Some(42));
    // lower > upper
    let expr = Expr::Call {
        function: BuiltinFn::Triangular,
        args: vec![Expr::Literal(10.0), Expr::Literal(5.0), Expr::Literal(1.0)],
    };
    assert!(model.eval_expr(&expr, &state, 0).is_nan());

    // mode > upper
    let expr2 = Expr::Call {
        function: BuiltinFn::Triangular,
        args: vec![Expr::Literal(0.0), Expr::Literal(15.0), Expr::Literal(10.0)],
    };
    assert!(model.eval_expr(&expr2, &state, 0).is_nan());

    // mode < lower
    let expr3 = Expr::Call {
        function: BuiltinFn::Triangular,
        args: vec![Expr::Literal(5.0), Expr::Literal(2.0), Expr::Literal(10.0)],
    };
    assert!(model.eval_expr(&expr3, &state, 0).is_nan());
}

#[test]
fn test_weibull_negative_params() {
    let model = model_with_specs(0.0, 10.0, 1.0);
    let state = SimulationState::new(0, 1, Some(42));
    let expr = Expr::Call {
        function: BuiltinFn::Weibull,
        args: vec![Expr::Literal(-1.0), Expr::Literal(2.0)],
    };
    assert!(model.eval_expr(&expr, &state, 0).is_nan());

    let expr2 = Expr::Call {
        function: BuiltinFn::Weibull,
        args: vec![Expr::Literal(2.0), Expr::Literal(0.0)],
    };
    assert!(model.eval_expr(&expr2, &state, 0).is_nan());
}

// ── Stochastic function boundary tests ─────────────────────────────────

#[test]
fn test_normal_zero_stddev() {
    // stddev=0 is valid — returns mean deterministically
    let model = model_with_specs(0.0, 10.0, 1.0);
    let state = SimulationState::new(0, 1, Some(42));
    let expr = Expr::Call {
        function: BuiltinFn::Normal,
        args: vec![Expr::Literal(5.0), Expr::Literal(0.0)],
    };
    assert_eq!(model.eval_expr(&expr, &state, 0), 5.0);
}

#[test]
fn test_lognormal_zero_stddev() {
    // stddev=0 is valid — returns exp(mean) deterministically
    let model = model_with_specs(0.0, 10.0, 1.0);
    let state = SimulationState::new(0, 1, Some(42));
    let expr = Expr::Call {
        function: BuiltinFn::Lognormal,
        args: vec![Expr::Literal(0.0), Expr::Literal(0.0)],
    };
    assert!((model.eval_expr(&expr, &state, 0) - 1.0).abs() < 1e-10);
}

#[test]
fn test_logistic_zero_scale() {
    // scale=0 is valid — returns mean deterministically
    let model = model_with_specs(0.0, 10.0, 1.0);
    let state = SimulationState::new(0, 1, Some(42));
    let expr = Expr::Call {
        function: BuiltinFn::Logistic,
        args: vec![Expr::Literal(5.0), Expr::Literal(0.0)],
    };
    assert_eq!(model.eval_expr(&expr, &state, 0), 5.0);
}

#[test]
fn test_binomial_zero_n() {
    // n=0 is valid — always returns 0
    let model = model_with_specs(0.0, 10.0, 1.0);
    let state = SimulationState::new(0, 1, Some(42));
    let expr = Expr::Call {
        function: BuiltinFn::Binomial,
        args: vec![Expr::Literal(0.0), Expr::Literal(0.5)],
    };
    assert_eq!(model.eval_expr(&expr, &state, 0), 0.0);
}

#[test]
fn test_binomial_p_zero() {
    // p=0 is valid — always returns 0
    let model = model_with_specs(0.0, 10.0, 1.0);
    let state = SimulationState::new(0, 1, Some(42));
    let expr = Expr::Call {
        function: BuiltinFn::Binomial,
        args: vec![Expr::Literal(10.0), Expr::Literal(0.0)],
    };
    assert_eq!(model.eval_expr(&expr, &state, 0), 0.0);
}

#[test]
fn test_binomial_p_one() {
    // p=1 is valid — always returns n
    let model = model_with_specs(0.0, 10.0, 1.0);
    let state = SimulationState::new(0, 1, Some(42));
    let expr = Expr::Call {
        function: BuiltinFn::Binomial,
        args: vec![Expr::Literal(10.0), Expr::Literal(1.0)],
    };
    assert_eq!(model.eval_expr(&expr, &state, 0), 10.0);
}

#[test]
fn test_binomial_p_out_of_range() {
    // p < 0 or p > 1 → NaN
    let model = model_with_specs(0.0, 10.0, 1.0);
    let state = SimulationState::new(0, 1, Some(42));
    let expr = Expr::Call {
        function: BuiltinFn::Binomial,
        args: vec![Expr::Literal(10.0), Expr::Literal(-0.1)],
    };
    assert!(model.eval_expr(&expr, &state, 0).is_nan());

    let expr2 = Expr::Call {
        function: BuiltinFn::Binomial,
        args: vec![Expr::Literal(10.0), Expr::Literal(1.1)],
    };
    assert!(model.eval_expr(&expr2, &state, 0).is_nan());
}

#[test]
fn test_negbinomial_zero_n() {
    // n=0 → NaN (need at least 1 success)
    let model = model_with_specs(0.0, 10.0, 1.0);
    let state = SimulationState::new(0, 1, Some(42));
    let expr = Expr::Call {
        function: BuiltinFn::NegBinomial,
        args: vec![Expr::Literal(0.0), Expr::Literal(0.5)],
    };
    assert!(model.eval_expr(&expr, &state, 0).is_nan());
}

#[test]
fn test_negbinomial_p_out_of_range() {
    // p < 0 or p > 1 → NaN
    let model = model_with_specs(0.0, 10.0, 1.0);
    let state = SimulationState::new(0, 1, Some(42));
    let expr = Expr::Call {
        function: BuiltinFn::NegBinomial,
        args: vec![Expr::Literal(5.0), Expr::Literal(-0.1)],
    };
    assert!(model.eval_expr(&expr, &state, 0).is_nan());

    let expr2 = Expr::Call {
        function: BuiltinFn::NegBinomial,
        args: vec![Expr::Literal(5.0), Expr::Literal(1.1)],
    };
    assert!(model.eval_expr(&expr2, &state, 0).is_nan());
}

#[test]
fn test_poisson_zero_mu() {
    // mu=0 is valid — always returns 0
    let model = model_with_specs(0.0, 10.0, 1.0);
    let state = SimulationState::new(0, 1, Some(42));
    let expr = Expr::Call {
        function: BuiltinFn::Poisson,
        args: vec![Expr::Literal(0.0)],
    };
    assert_eq!(model.eval_expr(&expr, &state, 0), 0.0);
}

#[test]
fn test_triangular_all_equal() {
    // l == m == u → returns constant
    let model = model_with_specs(0.0, 10.0, 1.0);
    let state = SimulationState::new(0, 1, Some(42));
    let expr = Expr::Call {
        function: BuiltinFn::Triangular,
        args: vec![Expr::Literal(5.0), Expr::Literal(5.0), Expr::Literal(5.0)],
    };
    assert_eq!(model.eval_expr(&expr, &state, 0), 5.0);
}

#[test]
fn test_triangular_lower_eq_upper_mode_differs() {
    // l == u but m != l → NaN
    let model = model_with_specs(0.0, 10.0, 1.0);
    let state = SimulationState::new(0, 1, Some(42));
    let expr = Expr::Call {
        function: BuiltinFn::Triangular,
        args: vec![Expr::Literal(5.0), Expr::Literal(3.0), Expr::Literal(5.0)],
    };
    assert!(model.eval_expr(&expr, &state, 0).is_nan());
}

#[test]
fn test_triangular_mode_at_bounds() {
    // mode == lower is valid
    let model = model_with_specs(0.0, 10.0, 1.0);
    let state = SimulationState::new(0, 1, Some(42));
    let expr = Expr::Call {
        function: BuiltinFn::Triangular,
        args: vec![Expr::Literal(0.0), Expr::Literal(0.0), Expr::Literal(10.0)],
    };
    let val = model.eval_expr(&expr, &state, 0);
    assert!(val >= 0.0 && val <= 10.0);

    // mode == upper is valid
    let expr2 = Expr::Call {
        function: BuiltinFn::Triangular,
        args: vec![Expr::Literal(0.0), Expr::Literal(10.0), Expr::Literal(10.0)],
    };
    let val2 = model.eval_expr(&expr2, &state, 0);
    assert!(val2 >= 0.0 && val2 <= 10.0);
}

#[test]
fn test_pareto_negative_shape() {
    let model = model_with_specs(0.0, 10.0, 1.0);
    let state = SimulationState::new(0, 1, Some(42));
    let expr = Expr::Call {
        function: BuiltinFn::Pareto,
        args: vec![Expr::Literal(-1.0), Expr::Literal(1.0)],
    };
    assert!(model.eval_expr(&expr, &state, 0).is_nan());
}

#[test]
fn test_pareto_zero_shape() {
    let model = model_with_specs(0.0, 10.0, 1.0);
    let state = SimulationState::new(0, 1, Some(42));
    let expr = Expr::Call {
        function: BuiltinFn::Pareto,
        args: vec![Expr::Literal(0.0), Expr::Literal(1.0)],
    };
    assert!(model.eval_expr(&expr, &state, 0).is_nan());
}

#[test]
fn test_pareto_negative_scale() {
    let model = model_with_specs(0.0, 10.0, 1.0);
    let state = SimulationState::new(0, 1, Some(42));
    let expr = Expr::Call {
        function: BuiltinFn::Pareto,
        args: vec![Expr::Literal(1.0), Expr::Literal(-1.0)],
    };
    assert!(model.eval_expr(&expr, &state, 0).is_nan());
}

#[test]
fn test_pareto_zero_scale() {
    let model = model_with_specs(0.0, 10.0, 1.0);
    let state = SimulationState::new(0, 1, Some(42));
    let expr = Expr::Call {
        function: BuiltinFn::Pareto,
        args: vec![Expr::Literal(1.0), Expr::Literal(0.0)],
    };
    assert!(model.eval_expr(&expr, &state, 0).is_nan());
}

// ── Invnorm edge cases ─────────────────────────────────────────────────

#[test]
fn test_invnorm_p_negative() {
    let model = model_with_specs(0.0, 10.0, 1.0);
    let state = SimulationState::new(0, 1, Some(42));
    let expr = Expr::Call {
        function: BuiltinFn::Invnorm,
        args: vec![Expr::Literal(-0.5), Expr::Literal(0.0), Expr::Literal(1.0)],
    };
    assert!(model.eval_expr(&expr, &state, 0).is_nan());
}

#[test]
fn test_invnorm_p_gt_one() {
    let model = model_with_specs(0.0, 10.0, 1.0);
    let state = SimulationState::new(0, 1, Some(42));
    let expr = Expr::Call {
        function: BuiltinFn::Invnorm,
        args: vec![Expr::Literal(1.5), Expr::Literal(0.0), Expr::Literal(1.0)],
    };
    assert!(model.eval_expr(&expr, &state, 0).is_nan());
}

#[test]
fn test_invnorm_negative_stddev() {
    let model = model_with_specs(0.0, 10.0, 1.0);
    let state = SimulationState::new(0, 1, Some(42));
    let expr = Expr::Call {
        function: BuiltinFn::Invnorm,
        args: vec![Expr::Literal(0.5), Expr::Literal(0.0), Expr::Literal(-1.0)],
    };
    assert!(model.eval_expr(&expr, &state, 0).is_nan());
}

#[test]
fn test_invnorm_p_zero() {
    // p=0 → -inf
    let model = model_with_specs(0.0, 10.0, 1.0);
    let state = SimulationState::new(0, 1, Some(42));
    let expr = Expr::Call {
        function: BuiltinFn::Invnorm,
        args: vec![Expr::Literal(0.0), Expr::Literal(0.0), Expr::Literal(1.0)],
    };
    assert_eq!(model.eval_expr(&expr, &state, 0), f64::NEG_INFINITY);
}

#[test]
fn test_invnorm_p_one() {
    // p=1 → +inf
    let model = model_with_specs(0.0, 10.0, 1.0);
    let state = SimulationState::new(0, 1, Some(42));
    let expr = Expr::Call {
        function: BuiltinFn::Invnorm,
        args: vec![Expr::Literal(1.0), Expr::Literal(0.0), Expr::Literal(1.0)],
    };
    assert_eq!(model.eval_expr(&expr, &state, 0), f64::INFINITY);
}

#[test]
fn test_invnorm_zero_stddev() {
    // stddev=0 → NaN (matches scipy behavior)
    let model = model_with_specs(0.0, 10.0, 1.0);
    let state = SimulationState::new(0, 1, Some(42));
    let expr = Expr::Call {
        function: BuiltinFn::Invnorm,
        args: vec![Expr::Literal(0.5), Expr::Literal(7.0), Expr::Literal(0.0)],
    };
    assert!(model.eval_expr(&expr, &state, 0).is_nan());
}

#[test]
fn test_invnorm_valid() {
    // invnorm(0.5, 0, 1) = 0.0 (median of standard normal)
    let model = model_with_specs(0.0, 10.0, 1.0);
    let state = SimulationState::new(0, 1, Some(42));
    let expr = Expr::Call {
        function: BuiltinFn::Invnorm,
        args: vec![Expr::Literal(0.5), Expr::Literal(0.0), Expr::Literal(1.0)],
    };
    assert!((model.eval_expr(&expr, &state, 0)).abs() < 1e-10);
}

// ── NormalCDF edge cases ────────────────────────────────────────────────

#[test]
fn test_normalcdf_negative_stddev() {
    let model = model_with_specs(0.0, 10.0, 1.0);
    let state = SimulationState::new(0, 1, Some(42));
    let expr = Expr::Call {
        function: BuiltinFn::NormalCDF,
        args: vec![Expr::Literal(-1.0), Expr::Literal(1.0), Expr::Literal(0.0), Expr::Literal(-1.0)],
    };
    assert!(model.eval_expr(&expr, &state, 0).is_nan());
}

#[test]
fn test_normalcdf_zero_stddev() {
    let model = model_with_specs(0.0, 10.0, 1.0);
    let state = SimulationState::new(0, 1, Some(42));
    let expr = Expr::Call {
        function: BuiltinFn::NormalCDF,
        args: vec![Expr::Literal(-1.0), Expr::Literal(1.0), Expr::Literal(0.0), Expr::Literal(0.0)],
    };
    assert!(model.eval_expr(&expr, &state, 0).is_nan());
}

#[test]
fn test_normalcdf_valid() {
    // normalcdf(-1, 1, 0, 1) ≈ 0.6827
    let model = model_with_specs(0.0, 10.0, 1.0);
    let state = SimulationState::new(0, 1, Some(42));
    let expr = Expr::Call {
        function: BuiltinFn::NormalCDF,
        args: vec![Expr::Literal(-1.0), Expr::Literal(1.0), Expr::Literal(0.0), Expr::Literal(1.0)],
    };
    let val = model.eval_expr(&expr, &state, 0);
    assert!((val - 0.6826894921370859).abs() < 1e-6);
}
