"""Host-owned event-kit tests: only offline plans, never player or tracking state."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILE = ROOT / "event-kit" / "build_event.py"
SPEC = importlib.util.spec_from_file_location("host_event", FILE)
event = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(event)


class EventKitTests(unittest.TestCase):
    def fixture(self, name="community-day.sample.json"):
        return event.load_config(ROOT / "event-kit" / "examples" / name)

    def test_all_theme_samples_are_valid_planning_only(self):
        directory = ROOT / "event-kit" / "examples"
        names = sorted(directory.glob("*.sample.json"))
        self.assertEqual(len(names), 4)
        for name in names:
            with self.subTest(name=name.name):
                plan = event.compile_event(event.load_config(name))
                self.assertEqual(plan["status"], "planning_only_unverified")
                self.assertEqual(len(plan["photo_cards"]), 6)
                self.assertEqual([c["stop"] for c in plan["photo_cards"]], list(range(1, 7)))
                self.assertEqual(plan["team_slots"], len(plan["starts_local"]))
                self.assertIsNone(plan.get("join_link"))
                self.assertNotIn("access_code", json.dumps(plan))
                self.assertNotIn("\"lat\":", json.dumps(plan))
                self.assertNotIn("\"lng\":", json.dumps(plan))
                self.assertEqual(plan["player_integration"].startswith("none"), True)

    def test_utc_schedule_and_stagger_are_deterministic(self):
        c = self.fixture()
        a = event.compile_event(c)
        self.assertEqual(a, event.compile_event(c))
        self.assertEqual(a["start_utc"], "2027-05-15T14:00+00:00")
        self.assertEqual(a["starts_local"][0], "2027-05-15T10:00-04:00")
        self.assertEqual(a["starts_local"][1], "2027-05-15T10:10-04:00")
        self.assertEqual(a["finale_local"], "2027-05-15T12:05-04:00")
        self.assertEqual(a["end_local"], "2027-05-15T12:30-04:00")
        self.assertIn(a["optional_bonus"], event.BONUSES)

    def test_winter_utc_offset_and_no_surprise(self):
        c = self.fixture()
        c.update(start_local="2027-01-16T10:00",surprise_enabled=False)
        a = event.compile_event(c)
        self.assertEqual(a["start_utc"], "2027-01-16T15:00+00:00")
        self.assertIsNone(a["optional_bonus"])

    def test_reject_ambiguous_and_nonexistent_dst(self):
        c = self.fixture()
        for start in ("2027-03-14T02:30", "2027-11-07T01:30"):
            with self.subTest(start=start):
                c["start_local"] = start
                with self.assertRaisesRegex(ValueError, "ambiguous or nonexistent"):
                    event.compile_event(c)

    def test_reject_event_crossing_clock_change(self):
        c = self.fixture()
        c.update(start_local="2027-03-14T01:00",duration_minutes=150)
        with self.assertRaisesRegex(ValueError, "spans a timezone clock change"):
            event.compile_event(c)

    def test_reject_unknown_or_personal_data_fields(self):
        for additional in ("participant_gps", "student_roster", "access_code", "join_url", "private_answers"):
            c = self.fixture()
            c[additional] = "something"
            with self.subTest(additional=additional), self.assertRaises(ValueError):
                event.compile_event(c)

    def test_reject_invalid_types_and_unsafe_schedule(self):
        replacements = [
            ("event_id", "../unsafe"),
            ("schema_version", True),
            ("team_slots", True),
            ("team_slots", 25),
            ("stagger_minutes", -1),
            ("surprise_enabled", 0),
            ("timezone", "Mars/Canal"),
            ("theme", []),
            ("start_local", "2027-05-15T10:00Z"),
            ("start_local", "not a date"),
            ("duration_minutes", 50),
            ("event_title", "<" * 120),
        ]
        for key, value in replacements:
            with self.subTest(field=key, value=str(value)[:30]):
                c = self.fixture()
                c[key] = value
                with self.assertRaises(ValueError):
                    event.compile_event(c)
        c = self.fixture()
        c.update(team_slots=20,stagger_minutes=30)
        with self.assertRaisesRegex(ValueError,"at least 30 minutes"):
            event.compile_event(c)

    def test_generated_html_escapes_host_text_and_does_not_call_network(self):
        c = self.fixture()
        c["event_title"] = "Test <img src=x onerror=alert(1)>"
        c["venue_label"] = 'Hall "onload=evil()"'
        a = event.compile_event(c)
        page = event.render_html(a)
        self.assertNotIn("<img", page)
        self.assertNotIn("<img src=x onerror=alert(1)>", page)
        self.assertIn("&lt;img", page)
        self.assertIn("&quot;onload", page)
        self.assertIn("name=\"robots\"", page)
        self.assertNotIn("<script", page)
        self.assertNotIn("fetch(", page)
        self.assertNotIn("navigator.geolocation", page)

    def test_config_rejects_duplicate_keys_nonfinite_and_oversize(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / "in.json"
            for data in (
                '{"event_id":"one","event_id":"two"}',
                '{"number":NaN}',
                '{"number":Infinity}',
            ):
                f.write_text(data)
                with self.assertRaises(ValueError):
                    event.load_config(f)
            f.write_text(" " * 17_000)
            with self.assertRaisesRegex(ValueError, "16 KiB"):
                event.load_config(f)

    def test_build_creates_only_static_files_and_refuses_clobber(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "new"
            result = event.build(ROOT / "event-kit" / "examples" / "community-day.sample.json", out)
            files = {p.name for p in out.iterdir()}
            self.assertEqual(files, {"host-sheet.html", "event-plan.json"})
            self.assertEqual(json.loads((out / "event-plan.json").read_text()), result)
            self.assertIn("noindex", (out / "host-sheet.html").read_text())
            with self.assertRaisesRegex(ValueError, "Refusing to overwrite"):
                event.build(ROOT / "event-kit" / "examples" / "community-day.sample.json", out)


if __name__ == "__main__":
    unittest.main()
