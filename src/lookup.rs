use crate::model::SdModel;

impl SdModel {
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
