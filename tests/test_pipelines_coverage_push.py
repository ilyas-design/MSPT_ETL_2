import json
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from Pipelines.pipeline import ETLPipeline, run_etl
from Pipelines.transformers import DataTransformer
from Pipelines.validators import DataValidator, print_validation_summary
from Pipelines.metrics import print_metrics_summary, calculate_all_metrics
from Pipelines.metrics import ColumnStats, TableStats


class TestCoveragePush(unittest.TestCase):
    def test_transformer_branches(self):
        tr = DataTransformer()

        df = pd.DataFrame({"a": [1, 1, None, 3], "b": [" x ", " x ", None, "Nan"]})
        # remove_duplicates subset
        tr.remove_duplicates(df, subset=["a", "b"])

        # handle_missing_values branches
        tr.handle_missing_values(df, strategy={"a": "drop"})
        tr.handle_missing_values(df, strategy={"a": "median"})
        tr.handle_missing_values(df, strategy={"b": "mode"})
        tr.handle_missing_values(df, strategy={"b": "fill"}, fill_values={"b": "y"})

        # normalize explicit columns + missing col skip
        tr.normalize_string_columns(df, columns=["b", "missing"])

        # convert_types branches
        tr.convert_types(pd.DataFrame({"i": ["1", "2"]}), {"i": "int"})
        tr.convert_types(pd.DataFrame({"f": ["1.5", "2.5"]}), {"f": "float"})
        tr.convert_types(pd.DataFrame({"s": [1, 2]}), {"s": "str"})
        tr.convert_types(pd.DataFrame({"d": ["2024-01-01"]}), {"d": "datetime"})
        # invalid dtype falls back (should not crash)
        tr.convert_types(pd.DataFrame({"x": ["a"]}), {"x": "nope"})

        # clip_numeric_values / standardize_categorical_values
        rules = {"a": {"min": 0, "max": 2}, "b": {"allowed_values": ["x", None]}}
        tr.clip_numeric_values(pd.DataFrame({"a": [-1, 1, 3]}), rules)
        tr.standardize_categorical_values(pd.DataFrame({"b": ["x", "bad"]}), rules)

        # cover TransformationResult.summary
        tr.remove_duplicates(pd.DataFrame({"x": [1, 1]})).summary()

        # cover handle_missing_values mode branch when mode is empty
        tr.handle_missing_values(pd.DataFrame({"m": [None, None]}), strategy={"m": "mode"})

    def test_validator_branches_and_summaries(self):
        v = DataValidator()

        # float type check branch
        self.assertTrue(v._check_type("1.0", "float"))
        self.assertFalse(v._check_type("x", "float"))

        # str type check branch
        self.assertTrue(v._check_type("x", "str"))

        # validate_dataframe with missing required cols to create errors
        bad_patient = pd.DataFrame({"gender": ["BAD"]})
        rep = v.validate_dataframe(bad_patient, "patient")
        self.assertGreater(rep.error_count, 0)
        _ = rep.summary()  # includes errors block

        # create warnings via coherence (BMI)
        df = pd.DataFrame(
            {"weight_kg": [80], "height_cm": [180], "bmi_calculated": [10], "age": [30], "gender": ["Male"]}
        )
        rep2 = v.validate_dataframe(df, "patient")
        rep2.warnings.extend(v.validate_coherence(df, "patient"))
        _ = rep2.summary()

        print_validation_summary({"patient": rep2})

        # validation_rate branch when total_rows == 0
        from Pipelines.validators import ValidationReport

        empty_report = ValidationReport(table_name="t", total_rows=0, valid_rows=0, invalid_rows=0)
        self.assertEqual(empty_report.validation_rate, 100.0)

        # validate_value null but nullable=True (returns empty)
        self.assertEqual(v.validate_value(None, {"nullable": True, "type": "int"}, "x", 0), [])

    def test_pipeline_error_and_optional_sources_and_report(self):
        repo = Path(__file__).resolve().parents[1]
        tmp = Path(tempfile.mkdtemp(prefix="mspr_cov_"))
        # minimal required CSVs
        pd.read_csv(repo / "diet_recommendations.csv").head(5).to_csv(tmp / "diet_recommendations.csv", index=False)
        pd.read_csv(repo / "gym_members_exercise.csv").head(5).to_csv(tmp / "gym_members_exercise.csv", index=False)
        pd.read_csv(repo / "daily_food_nutrition.csv").head(5).to_csv(tmp / "daily_food_nutrition.csv", index=False)

        # valid json branch
        (tmp / "exercises.json").write_text(json.dumps([{"id": 1, "name": "t"}]), encoding="utf-8")
        # excel branch will raise (no engine), but should be caught as WARNING if optional
        (tmp / "optional.xlsx").write_bytes(b"not-a-real-xlsx")

        db_path = tmp / "db.sqlite"
        report_dir = tmp / "reports"

        pipeline = ETLPipeline(data_dir=str(tmp), db_path=str(db_path), report_dir=str(report_dir))

        # custom file mappings to hit branches + optional warning path
        pipeline.extract(
            file_mappings={
                "diet": "diet_recommendations.csv",
                "gym": "gym_members_exercise.csv",
                "food_log": "daily_food_nutrition.csv",
                "exercise": "exercises.json",
                "optional": "optional.xlsx",
            }
        )
        pipeline.clean()
        pipeline.transform()
        pipeline.validate()
        self.assertTrue(pipeline.load())
        pipeline.calculate_metrics()

        # report generation branch
        report = pipeline.generate_report()
        self.assertIn("summary", report)
        self.assertTrue(any(p.name.startswith("etl_report_") for p in report_dir.glob("etl_report_*.json")))

        # log_operation branches
        pipeline.log_operation("X", "warn", "WARNING")
        pipeline.log_operation("X", "err", "ERROR")

        # exercise load path exists
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {r[0] for r in cur.fetchall()}
        conn.close()
        self.assertIn("food_log", tables)

        # cover print_metrics_summary
        print_metrics_summary(calculate_all_metrics(pipeline.transformed_data))

        # cover pipeline.transform branches when sources are missing/empty
        p2 = ETLPipeline(data_dir=str(tmp), db_path=str(tmp / "db2.sqlite"), report_dir=str(tmp / "r2"))
        p2.cleaned_data = {}
        p2.transform()

        # cover pipeline.load error branch
        bad_db_dir = tmp / "not_a_db_dir"
        bad_db_dir.mkdir(exist_ok=True)
        p3 = ETLPipeline(data_dir=str(tmp), db_path=str(bad_db_dir), report_dir=str(tmp / "r3"))
        p3.transformed_data = {"patient": pd.DataFrame({"a": [1]})}
        self.assertFalse(p3.load())

        # cover pipeline.run error branch (missing required file)
        p4 = ETLPipeline(data_dir=str(tmp), db_path=str(tmp / "db4.sqlite"), report_dir=str(tmp / "r4"))
        res = p4.run(file_mappings={"diet": "missing.csv"}, validate_data=False, generate_report=False)
        # Pipeline logs extraction error but continues; ensure it recorded an ERROR operation.
        self.assertIn(res["status"], ("SUCCESS", "ERROR"))
        self.assertTrue(any(e["status"] == "ERROR" for e in p4.operations_log))

        # cover pipeline.clean duplicate log (values_modified > 0)
        p_dup = ETLPipeline(data_dir=str(tmp), db_path=str(tmp / "ddup.sqlite"), report_dir=str(tmp / "rdup"))
        p_dup.raw_data = {"x": pd.DataFrame({"a": [1, 1], "b": [2, 2]})}
        p_dup.clean()

        # cover Patient_ID generation branch in transform
        p_ids = ETLPipeline(data_dir=str(tmp), db_path=str(tmp / "dids.sqlite"), report_dir=str(tmp / "rids"))
        p_ids.cleaned_data = {
            "diet": pd.DataFrame(
                {
                    "Age": [30],
                    "Gender": ["Male"],
                    "Weight_kg": [80.0],
                    "Height_cm": [180.0],
                    "BMI_Calculated": [24.7],
                }
            ),
            "gym": pd.DataFrame(),  # keep empty to skip
        }
        p_ids.transform()
        self.assertIn("patient", p_ids.transformed_data)

        # cover run() generate_report branch
        p_run = ETLPipeline(data_dir=str(tmp), db_path=str(tmp / "drun.sqlite"), report_dir=str(tmp / "rrun"))
        p_run.raw_data = {
            "diet": pd.read_csv(tmp / "diet_recommendations.csv"),
            "gym": pd.read_csv(tmp / "gym_members_exercise.csv"),
            "food_log": pd.read_csv(tmp / "daily_food_nutrition.csv"),
            "exercise": pd.read_json(tmp / "exercises.json"),
        }
        p_run.clean()
        p_run.transform()
        out = p_run.run(
            file_mappings={
                "diet": "diet_recommendations.csv",
                "gym": "gym_members_exercise.csv",
                "food_log": "daily_food_nutrition.csv",
                "exercise": "exercises.json",
            },
            validate_data=False,
            generate_report=True,
        )
        self.assertEqual(out["status"], "SUCCESS")

        # cover run() exception branch
        p_err = ETLPipeline(data_dir=str(tmp), db_path=str(tmp / "derr.sqlite"), report_dir=str(tmp / "rerr"))
        def boom(*args, **kwargs):
            raise RuntimeError("boom")
        p_err.extract = boom
        out2 = p_err.run(validate_data=False, generate_report=False)
        self.assertEqual(out2["status"], "ERROR")

        # cover run_etl() helper
        _ = run_etl(data_dir=str(tmp), db_path=str(tmp / "dhelper.sqlite"), report_dir=str(tmp / "rhelper"))

    def test_metrics_remaining_branches(self):
        # cover ColumnStats.to_dict branches (numeric + top_values)
        cs = ColumnStats(
            column_name="x",
            data_type="int",
            non_null_count=1,
            null_count=0,
            null_percentage=0.0,
            unique_count=1,
            min_value=1.0,
            max_value=2.0,
            mean_value=1.5,
            median_value=1.5,
            std_value=0.1,
            q1_value=1.0,
            q3_value=2.0,
            top_values=[("a", 1)],
        )
        d = cs.to_dict()
        self.assertIn("top_values", d)
        self.assertIn("min", d)

        # cover TableStats.to_dict simple
        ts = TableStats(table_name="t", row_count=0, column_count=0, memory_usage_mb=0.0, columns_stats=[cs])
        self.assertIn("columns", ts.to_dict())


if __name__ == "__main__":
    unittest.main()

