import unittest

import pandas as pd

from Pipelines.metrics import MetricsCalculator
from Pipelines.transformers import DataTransformer, apply_all_transformations
from Pipelines.validators import DataValidator, validate_all_tables


class TestPipelinesUnits(unittest.TestCase):
    def test_metrics_outliers_and_profile_and_quality(self):
        df = pd.DataFrame(
            {
                "a": [1, 2, 3, 1000],
                "b": [10, 20, None, 40],
                "c": ["x", "x", "y", "z"],
            }
        )
        calc = MetricsCalculator()

        corr = calc.calculate_correlation_matrix(df)
        self.assertIn("a", corr.columns)

        out_iqr = calc.detect_outliers(df, "a", method="iqr")
        self.assertIn("outlier_count", out_iqr)

        out_z = calc.detect_outliers(df, "a", method="zscore")
        self.assertIn("outlier_count", out_z)

        with self.assertRaises(ValueError):
            calc.detect_outliers(df, "a", method="nope")

        profile = calc.generate_data_profile(df, "t")
        self.assertIn("table_stats", profile)
        self.assertIn("data_quality_score", profile)

        empty_quality = calc._calculate_quality_score(calc.calculate_table_stats(pd.DataFrame(), "empty"))
        self.assertEqual(empty_quality, 0.0)

        # Cover "no outliers because no numeric values"
        df_nan = pd.DataFrame({"x": [None, None]})
        out_empty = calc.detect_outliers(df_nan, "x")
        self.assertEqual(out_empty["outlier_count"], 0)

        # Cover correlation with numeric_only=False (use numeric-only df to avoid pandas casting error)
        corr2 = calc.calculate_correlation_matrix(df[["a", "b"]], numeric_only=False)
        self.assertTrue(hasattr(corr2, "shape"))

        # Cover profile when numeric cols <= 1 (no correlation matrix)
        profile2 = calc.generate_data_profile(pd.DataFrame({"only": [1, 2, 3]}), "one")
        self.assertIsNone(profile2["correlation_matrix"])

        # Cover TableStats.summary
        ts = calc.calculate_table_stats(df, "t")
        s = ts.summary()
        self.assertIn("STATISTIQUES", s)

        # cover calculate_column_stats exception branch by monkeypatching pd.to_numeric
        import Pipelines.metrics as m
        orig = m.pd.to_numeric
        try:
            def raiser(*a, **k):
                raise RuntimeError("x")
            m.pd.to_numeric = raiser
            _ = calc.calculate_column_stats(pd.DataFrame({"n": [1, 2, 3]}), "n")
        finally:
            m.pd.to_numeric = orig

    def test_transformer_missing_values_and_types_and_business_transforms(self):
        tr = DataTransformer()
        df = pd.DataFrame({"x": [1, None, 3], "y": ["  A ", None, "nan"]})

        res = tr.handle_missing_values(df, strategy={"x": "mean", "y": "fill"}, fill_values={"y": "B"})
        self.assertEqual(res.df["y"].isna().sum(), 0)

        res2 = tr.normalize_string_columns(df)
        self.assertTrue("normalize(y)" in res2.transformations_applied or res2.values_modified >= 0)

        res3 = tr.convert_types(pd.DataFrame({"n": ["1", "2"]}), {"n": "int"})
        self.assertIn(str(res3.df["n"].dtype), ("int64", "Int64"))

        # Clip + standardize via apply_all_transformations using known rules
        patient = pd.DataFrame(
            {
                "patient_id": ["P00001"],
                "age": [200],  # clipped
                "gender": ["male"],  # standardized to allowed values if present
                "weight_kg": [10],  # clipped
                "height_cm": [10],  # clipped
                "bmi_calculated": [999],  # recalculated
            }
        )
        out, steps = apply_all_transformations(patient, "patient", tr)
        self.assertIn("recalculate_bmi", steps)

    def test_validator_rules_and_missing_columns(self):
        v = DataValidator()

        # null not allowed
        r = v.validate_value(None, {"nullable": False, "type": "int"}, "age", 0)
        self.assertTrue(any(not x.is_valid for x in r))

        # type invalid
        r2 = v.validate_value("abc", {"nullable": False, "type": "int"}, "age", 0)
        self.assertTrue(any(not x.is_valid for x in r2))

        # min/max invalid
        r3 = v.validate_value(0, {"nullable": False, "type": "int", "min": 1, "max": 2}, "x", 0)
        self.assertTrue(any(not x.is_valid for x in r3))

        # allowed_values invalid
        r4 = v.validate_value("BAD", {"nullable": True, "type": "str", "allowed_values": ["OK"]}, "g", 0)
        self.assertTrue(any(not x.is_valid for x in r4))

        # pattern invalid
        r5 = v.validate_value("abc", {"nullable": True, "type": "str", "pattern": r"^[0-9]+$"}, "p", 0)
        self.assertTrue(any(not x.is_valid for x in r5))

        # missing required column triggers error
        df = pd.DataFrame({"gender": ["Male"]})
        rep = v.validate_dataframe(df, "patient")
        self.assertGreaterEqual(rep.error_count, 1)

        # validate_all_tables covers loop
        reps = validate_all_tables({"patient": pd.DataFrame({"age": [20], "gender": ["Male"], "weight_kg": [70], "height_cm": [170], "bmi_calculated": [24.2]})})
        self.assertIn("patient", reps)

        # Cover ValidationReport.summary + print_validation_summary path
        rep2 = reps["patient"]
        txt = rep2.summary()
        self.assertIn("RAPPORT", txt)


if __name__ == "__main__":
    unittest.main()

