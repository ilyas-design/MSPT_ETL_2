import json
import tempfile
import unittest
from pathlib import Path

from Pipelines.monitoring import (
    MonitoringThresholds,
    build_monitoring_snapshot,
    evaluate_report,
    load_reports,
)


class TestMonitoring(unittest.TestCase):
    def _write_report(self, folder: Path, name: str, total_rows: int, total_errors: int, total_warnings: int, rate: float):
        payload = {
            "timestamp": "2026-04-16T10:00:00",
            "summary": {
                "tables_processed": 7,
                "total_rows": total_rows,
                "total_errors": total_errors,
                "total_warnings": total_warnings,
            },
            "validation_reports": {
                "patient": {"validation_rate": rate},
                "sante": {"validation_rate": rate},
            },
        }
        (folder / name).write_text(json.dumps(payload), encoding="utf-8")

    def test_evaluate_report_ok(self):
        report = {
            "timestamp": "2026-04-16T10:00:00",
            "summary": {
                "total_rows": 1500,
                "total_errors": 0,
                "total_warnings": 10,
            },
            "validation_reports": {
                "patient": {"validation_rate": 100.0},
                "sante": {"validation_rate": 99.0},
            },
        }
        result = evaluate_report(report, MonitoringThresholds())
        self.assertEqual(result["status"], "OK")
        self.assertEqual(len(result["alerts"]), 0)

    def test_build_monitoring_snapshot_warning(self):
        with tempfile.TemporaryDirectory(prefix="mspr_monitoring_") as tmp:
            report_dir = Path(tmp)
            self._write_report(report_dir, "etl_report_20260416_100000.json", 900, 0, 300, 98.0)
            self._write_report(report_dir, "etl_report_20260416_101000.json", 1000, 0, 200, 100.0)

            reports = load_reports(str(report_dir))
            self.assertEqual(len(reports), 2)

            snapshot = build_monitoring_snapshot(
                report_dir=str(report_dir),
                thresholds=MonitoringThresholds(max_warnings=250, min_total_rows=1000, min_validation_rate=99.0),
                trend_window=2,
            )

            self.assertEqual(snapshot["reports_found"], 2)
            self.assertIn(snapshot["overall_status"], {"OK", "WARNING", "CRITICAL"})
            self.assertIn("delta_vs_previous", snapshot["trend"])


if __name__ == "__main__":
    unittest.main()
