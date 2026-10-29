//! The belt port against the reference values of `tests/unittests/test_belt.py`.

use bptk_rust_engine::conveyor::{filled, slat_count, Belt, Cohort, Initial};

const DT: f64 = 0.25;

/// (contents, outflow rate, leak rates) per step, as test_belt.py's `run`.
fn run(fifo: bool, exponential: bool, fractions: &[f64], initial: Initial, steps: usize) -> Vec<(f64, f64, Vec<f64>)> {
    let mut belt = filled(fifo, exponential, 0.0, DT, 4.0, fractions, &initial);
    let mut rows = Vec::new();
    for step in 0..steps {
        let t = step as f64 * DT;
        let (moves, following) = belt.advance(t, DT, 250.0 * DT, 4.0, fractions);
        let leaks = moves.leaked.iter().map(|amount| amount / DT).collect();
        rows.push((belt.contents(), moves.exited / DT, leaks));
        assert!((250.0 * DT - moves.exited - moves.leaked.iter().sum::<f64>()
            - (following.contents() - belt.contents())).abs() < 1e-6);
        belt = following;
    }
    rows
}

#[test]
fn test_the_reference_scenarios_on_both_belts() {
    for fifo in [false, true] {
        let steady = run(fifo, false, &[], Initial::Total(1000.0), 200);
        assert_eq!((steady[0].0, steady[0].1), (1000.0, 250.0));
        let linear = run(fifo, false, &[0.2], Initial::Total(1000.0), 200);
        let last = linear.last().unwrap();
        assert!((last.0 - 906.25).abs() < 1e-6 && (last.1 - 200.0).abs() < 1e-6 && (last.2[0] - 50.0).abs() < 1e-6);
        let exponential = run(fifo, true, &[0.1], Initial::Total(1000.0), 200);
        let last = exponential.last().unwrap();
        assert!((last.0 - 832.699579).abs() < 1e-6 && (last.1 - 166.730042).abs() < 1e-6);
    }
}

#[test]
fn test_slats_round_half_away_from_zero() {
    assert_eq!(slat_count(4.1, DT), 16);
    assert_eq!(slat_count(4.125, DT), 17);
    assert_eq!(slat_count(0.01, DT), 1);
}

#[test]
fn test_leaks_beyond_the_content() {
    let linear = run(false, false, &[0.7, 0.7], Initial::Total(1000.0), 200);
    let last = linear.last().unwrap();
    assert!(last.2[0] > last.2[1] && (last.2[0] + last.2[1] - 250.0).abs() < 1e-6 && last.1.abs() < 1e-9);
    let exponential = run(false, true, &[5.0, 5.0], Initial::Total(1000.0), 200);
    let last = exponential.last().unwrap();
    assert!((last.2[0] - last.2[1]).abs() < 1e-9 && last.1.abs() < 1e-9);
    let empty = Belt { fifo: false, exponential: true,
        cohorts: vec![Cohort { entered: 0.0, content: 0.0, basis: vec![0.0], window: vec![0.0], depth: 2, low: 0.0, high: 0.0 }] };
    let (moves, _) = empty.advance(0.0, 1.0, 0.0, 2.0, &[0.5]);
    assert_eq!(moves.leaked, vec![0.0]);
}

#[test]
fn test_filling_from_lists() {
    assert_eq!(filled(false, false, 0.0, DT, 4.0, &[], &Initial::List(vec![])).contents(), 0.0);
    let per_unit = filled(false, false, 0.0, DT, 4.0, &[], &Initial::List(vec![1.0, 2.0, 3.0, 4.0]));
    assert_eq!(per_unit.cohorts.len(), 16);
    assert!((per_unit.contents() - 10.0).abs() < 1e-12);
    let long = filled(false, false, 0.0, DT, 4.0, &[], &Initial::List(vec![1.0, 2.0, 3.0, 4.0, 5.0]));
    assert!((long.contents() - 10.0).abs() < 1e-12);
    let emptied = filled(false, false, 0.0, DT, 4.0, &[1.0, 1.0], &Initial::Total(100.0));
    assert!((emptied.contents() - 100.0).abs() < 1e-9);
    assert_eq!(emptied.cohorts.len(), 8);
}

#[test]
fn test_agecount_by_time_on_the_belt() {
    let belt = filled(false, false, 0.0, 1.0, 4.0, &[], &Initial::List(vec![1.0, 2.0, 3.0, 4.0]));
    assert_eq!(belt.agecount(0.0, 0.0, 1.0), 4.0);
    assert_eq!(belt.agecount(0.0, 0.0, 2.0), 7.0);
    assert_eq!(belt.agecount(0.0, 3.0, 4.0), 1.0);
    let (_, later) = belt.advance(0.0, 1.0, 9.0, 4.0, &[]);
    assert_eq!(later.agecount(1.0, 0.0, 1.0), 9.0);
    assert_eq!(later.agecount(1.0, 1.0, 2.0), 4.0);
}
