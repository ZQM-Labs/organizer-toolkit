"""Privacy-preserving host outcome metrics, no trackers or network."""
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROGRAM = ROOT / "event-kit" / "summarize_outcomes.py"
SPEC = importlib.util.spec_from_file_location("host_outcomes", PROGRAM)
metrics = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(metrics)
SAMPLE = ROOT / "event-kit" / "examples" / "outcomes.synthetic.json"


class OutcomeTests(unittest.TestCase):
    def fixture(self):
        return metrics.load(SAMPLE)

    def test_known_synthetic_rates_and_denominators(self):
        report = metrics.calculate(self.fixture())
        self.assertEqual(report["basis"], "synthetic_demo")
        self.assertFalse(report["source_verified"])
        self.assertFalse(report["publishable_sales_proof"])
        self.assertEqual(
            report["metrics"]["team_start_rate_percent"]["value"], 80.0
        )
        self.assertEqual(
            report["metrics"]["team_completion_rate_percent"]["value"], 78.1
        )
        self.assertEqual(
            report["metrics"]["voluntary_share_rate_percent"]["value"], 55.0
        )
        self.assertEqual(
            report["metrics"]["mean_completion_minutes"]["value"], 42.0
        )
        self.assertEqual(
            report["metrics"]["host_proposal_rate_percent"]["value"], 50.0
        )
        self.assertEqual(
            report["metrics"]["pilot_acceptance_rate_percent"]["value"], 50.0
        )
        # Never echo event/team labels, identities, raw counts or input.
        self.assertNotIn("teams_invited", json.dumps(report))
        self.assertNotIn("event_id", json.dumps(report))
        self.assertNotIn("participants", json.dumps(report).lower())

    def test_low_denominator_and_complementary_suppression(self):
        raw = self.fixture()
        raw.update(teams_invited=8, teams_started=7, teams_completed=6,
                   teams_sharing_offered=6, teams_shared_reported=1,
                   teams_with_timing=6,total_completion_minutes=240)
        report = metrics.calculate(raw)
        for key in (
            "team_start_rate_percent", "team_completion_rate_percent",
            "voluntary_share_rate_percent", "mean_completion_minutes",
        ):
            self.assertIsNone(report["metrics"][key]["value"])
            self.assertEqual(report["metrics"][key]["status"], "suppressed")
        raw = self.fixture()
        raw["teams_started"] = 39
        raw["teams_completed"] = 25
        raw["teams_sharing_offered"] = 20
        report = metrics.calculate(raw)
        self.assertIsNone(report["metrics"]["team_start_rate_percent"]["value"],
                          "A single nonstarter must remain suppressed")

    def test_zero_denominator_never_divides_by_zero(self):
        raw = {key: 0 for key in metrics.COUNT_KEYS}
        raw.update(schema_version=1,source_basis="manual_host_aggregate")
        report = metrics.calculate(raw)
        self.assertTrue(all(m["value"] is None for m in report["metrics"].values()))
        self.assertFalse(report["publishable_sales_proof"])

    def test_reject_unexpected_identifiers_and_sensitive_data(self):
        for key in ("participant_id", "student_roster", "precise_gps",
                    "stripe_payment_id", "private_photo_exif", "team_names"):
            raw = self.fixture()
            raw[key] = "secret"
            with self.subTest(key=key), self.assertRaises(ValueError):
                metrics.calculate(raw)

    def test_reject_invalid_numeric_types_and_order(self):
        edits = [
            ("teams_started", True),
            ("teams_started", -1),
            ("teams_started", 1.5),
            ("teams_started", 1_000_001),
            ("teams_started", 45),
            ("teams_completed", 40),
            ("teams_sharing_offered", 30),
            ("teams_shared_reported", 21),
            ("teams_with_timing", 30),
            ("proposals_sent", 21),
            ("pilots_accepted", 11),
            ("total_completion_minutes", 0),
            ("total_completion_minutes", 18 * 481),
            ("schema_version", True),
            ("source_basis", "verified"),
        ]
        for key, value in edits:
            raw = self.fixture()
            raw[key] = value
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                metrics.calculate(raw)

    def test_reject_duplicate_fields_nonfinite_and_raw_log_size(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "private.json"
            for text in (
                '{"schema_version":1,"schema_version":2}',
                '{"source_basis":NaN}',
                '{"source_basis":Infinity}',
            ):
                path.write_text(text,encoding="utf-8")
                with self.assertRaises(ValueError):
                    metrics.load(path)
            path.write_text(" " * 17_000,encoding="utf-8")
            with self.assertRaisesRegex(ValueError,"16 KiB"):
                metrics.load(path)

    def test_cli_prints_safe_json_without_external_io(self):
        proc = subprocess.run(
            [sys.executable,str(PROGRAM),str(SAMPLE)],
            text=True,capture_output=True,timeout=10
        )
        self.assertEqual(proc.returncode,0,proc.stderr)
        report = json.loads(proc.stdout)
        self.assertEqual(report["basis"],"synthetic_demo")
        self.assertFalse(report["analytics_automatically_collected"])
        self.assertNotIn("teams_started",proc.stdout)


if __name__ == "__main__":
    unittest.main()
