use crate::model::{LookupKind, LookupStatistic, SdModel};

impl SdModel {
    /// A graphical function at `x`, by its kind: continuous holds the end values outside
    /// the table, extrapolate goes on along the first and the last segment, discrete takes
    /// the value of the next lower x.
    pub fn lookup(&self, table_name: &str, x: f64, kind: LookupKind) -> f64 {
        let table = match self.graphical_functions.get(table_name) {
            Some(gf) if !gf.points.is_empty() => &gf.points,
            _ => return 0.0,
        };
        if x.is_nan() {
            return f64::NAN;
        }
        let (first, last) = (table[0], table[table.len() - 1]);
        match kind {
            LookupKind::Discrete => table.iter().rev().find(|&&(px, _)| px <= x).unwrap_or(&first).1,
            LookupKind::Extrapolate if table.len() > 1 && x < first.0 => {
                let (x1, y1) = table[1];
                first.1 + (x - first.0) * (y1 - first.1) / (x1 - first.0)
            }
            LookupKind::Extrapolate if table.len() > 1 && x > last.0 => {
                let (x0, y0) = table[table.len() - 2];
                last.1 + (x - last.0) * (last.1 - y0) / (last.0 - x0)
            }
            _ => self.lookup_interpolate(table_name, x),
        }
    }

    /// Stella's LOOKUPINV: the x at which the table reaches `y`. Meant for a monotonic
    /// table; on a segment that reaches `y` the x is interpolated, the first such segment
    /// counts. A `y` outside what the table reaches gives the x of the end nearer to it -
    /// on a monotonic table; on one that is not, NaN, as in Stella. An extrapolate table
    /// goes on along that end's segment; a discrete one is read as continuous, as Stella does.
    pub fn lookup_inverse(&self, table_name: &str, y: f64, kind: LookupKind) -> f64 {
        let table = match self.graphical_functions.get(table_name) {
            Some(gf) if !gf.points.is_empty() => &gf.points,
            _ => return 0.0,
        };
        for pair in table.windows(2) {
            let ((x0, y0), (x1, y1)) = (pair[0], pair[1]);
            if y0.min(y1) <= y && y <= y0.max(y1) {
                return if y0 == y1 { x0 } else { x0 + (y - y0) * (x1 - x0) / (y1 - y0) };
            }
        }
        let rises = table.windows(2).all(|pair| pair[0].1 <= pair[1].1);
        let falls = table.windows(2).all(|pair| pair[0].1 >= pair[1].1);
        if !(rises || falls) {
            return f64::NAN;
        }
        let (first, last) = (table[0], table[table.len() - 1]);
        let nearer_first = (y - first.1).abs() <= (y - last.1).abs();
        if kind == LookupKind::Extrapolate && table.len() > 1 {
            let ((x0, y0), (x1, y1)) =
                if nearer_first { (table[0], table[1]) } else { (table[table.len() - 2], last) };
            if y0 != y1 {
                return x0 + (y - y0) * (x1 - x0) / (y1 - y0);
            }
        }
        if nearer_first { first.0 } else { last.0 }
    }

    /// Stella's LOOKUPAREA: the area under the table between `from` and `to`, an infinite
    /// bound standing for the table's end. As in Stella, nothing beyond the table's ends
    /// counts, though lookup holds the end values there - except on an extrapolate table,
    /// whose lines go on; a discrete table's steps are integrated as steps. `from` above
    /// `to` gives the area with its sign turned.
    pub fn lookup_area(&self, table_name: &str, from: f64, to: f64, kind: LookupKind) -> f64 {
        let table = match self.graphical_functions.get(table_name) {
            Some(gf) if !gf.points.is_empty() => &gf.points,
            _ => return 0.0,
        };
        if from.is_nan() || to.is_nan() {
            return f64::NAN;
        }
        let (lowest, highest) = (table[0].0, table[table.len() - 1].0);
        let from = if from == f64::NEG_INFINITY { lowest } else { from };
        let to = if to == f64::INFINITY { highest } else { to };
        if from > to {
            return -self.lookup_area(table_name, to, from, kind);
        }
        let (start, end) = if kind == LookupKind::Extrapolate {
            (from, to)
        } else {
            (from.max(lowest), to.min(highest))
        };
        if start >= end {
            return 0.0;
        }
        let mut xs = vec![start];
        xs.extend(table.iter().map(|&(x, _)| x).filter(|&x| start < x && x < end));
        xs.push(end);
        xs.windows(2)
            .map(|pair| {
                let (x0, x1) = (pair[0], pair[1]);
                let (y0, y1) = (self.lookup(table_name, x0, kind), self.lookup(table_name, x1, kind));
                if kind == LookupKind::Discrete { (x1 - x0) * y0 } else { (x1 - x0) * (y0 + y1) / 2.0 }
            })
            .sum()
    }

    /// Stella's LOOKUPMAX, LOOKUPMIN and LOOKUPMEAN between `from` and `to`, in either
    /// order, an infinite bound standing for the table's end. The largest and the smallest
    /// value read the table as lookup does, beyond its ends too. The mean is the mean x of
    /// the table read as a density - each segment uniform, weighted by its area, as
    /// LOOKUPRANDOM draws from it - so nothing beyond the ends counts but on an extrapolate
    /// table; a range without area gives NaN.
    pub fn lookup_statistic(
        &self,
        table_name: &str,
        statistic: LookupStatistic,
        from: f64,
        to: f64,
        kind: LookupKind,
    ) -> f64 {
        let table = match self.graphical_functions.get(table_name) {
            Some(gf) if !gf.points.is_empty() => &gf.points,
            _ => return 0.0,
        };
        if from.is_nan() || to.is_nan() {
            return f64::NAN;
        }
        let (lowest, highest) = (table[0].0, table[table.len() - 1].0);
        let from = if from == f64::NEG_INFINITY { lowest } else { from };
        let to = if to == f64::INFINITY { highest } else { to };
        let (mut start, mut end) = (from.min(to), from.max(to));
        if statistic == LookupStatistic::Mean && kind != LookupKind::Extrapolate {
            start = start.max(lowest);
            end = end.min(highest);
        }
        let mut xs = vec![start];
        xs.extend(table.iter().map(|&(x, _)| x).filter(|&x| start < x && x < end));
        if end > start {
            xs.push(end);
        }
        let ys: Vec<f64> = xs.iter().map(|&x| self.lookup(table_name, x, kind)).collect();
        match statistic {
            LookupStatistic::Max => ys.iter().cloned().fold(f64::NEG_INFINITY, f64::max),
            LookupStatistic::Min => ys.iter().cloned().fold(f64::INFINITY, f64::min),
            LookupStatistic::Mean => {
                let (mut total, mut moment) = (0.0, 0.0);
                for i in 1..xs.len() {
                    let (x0, x1, y0, y1) = (xs[i - 1], xs[i], ys[i - 1], ys[i]);
                    let area = (x1 - x0) * if kind == LookupKind::Discrete { y0 } else { (y0 + y1) / 2.0 };
                    total += area;
                    moment += area * (x0 + x1) / 2.0;
                }
                if total == 0.0 { f64::NAN } else { moment / total }
            }
        }
    }

    /// Linear interpolation from a graphical function's points.
    /// Clamps at boundaries (returns first/last y if x is outside range).
    pub fn lookup_interpolate(&self, table_name: &str, x: f64) -> f64 {
        let table = match self.graphical_functions.get(table_name) {
            Some(gf) => &gf.points,
            None => return 0.0,
        };

        if table.is_empty() {
            return 0.0;
        }
        // NaN falls through every comparison below and would read the last point
        if x.is_nan() {
            return f64::NAN;
        }

        // Clamp at boundaries
        if x <= table[0].0 {
            return table[0].1;
        }
        if x >= table[table.len() - 1].0 {
            return table[table.len() - 1].1;
        }

        // Find the two bounding points and interpolate
        for i in 0..table.len() - 1 {
            let (x0, y0) = table[i];
            let (x1, y1) = table[i + 1];
            if x >= x0 && x <= x1 {
                let fraction = (x - x0) / (x1 - x0);
                return y0 + fraction * (y1 - y0);
            }
        }

        // Shouldn't reach here if points are sorted, but just in case
        table[table.len() - 1].1
    }
}
