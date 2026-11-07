"""Host kit / pack binding and credential-safe sign-generation regressions."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QR = ROOT / "qr-kit"
sys.path.insert(0, str(QR))
import preflight  # noqa: E402  (tested as script in the same directory)

KIT_FILE = QR / "kit-config.example.json"


def example():
    return preflight.read_json(KIT_FILE, preflight.KIT_BYTES)


def matching_pack(cfg):
    # Fully formed synthetic SPEC-v1-like pack, never a field-tested route.
    stops = []
    for st in cfg["stops"]:
        order = st["order"]
        stops.append({
            "id": order,
            "name": st["name"],
            "code": st["code"],
            "lat": 10.0 + 0.001 * order,
            "lng": 20.0,
            "story": {"cozy": "Synthetic clue only"},
            "puzzle": {"cozy": {"q": "Synthetic question?", "a": f"SYN-{order}"}},
            "fallback": {"q": "Fallback?", "a": "Synthetic"},
            "hints": ["Read sign", "Observe clue", "Ask host"],
        })
    return {"kit": cfg["kit_id"], "title": "Synthetic host parity fixture", "stops": stops}


class KitPreflightTests(unittest.TestCase):
    def test_demo_has_exactly_six_signs(self):
        cfg = example()
        report = preflight.check_kit(cfg)
        self.assertEqual(report["kit_stop_count"], 6)
        self.assertFalse(report["pack_alignment_checked"])
        preflight.verify_url_shapes(cfg)
        from urllib.parse import parse_qs, urlsplit
        poster = parse_qs(urlsplit(preflight.poster_url(cfg)).query)
        self.assertEqual(set(poster), {"kit", "ac"})
        for sign in cfg["stops"]:
            q = parse_qs(urlsplit(preflight.stop_url(cfg, sign)).query)
            self.assertEqual(set(q), {"kit", "stop", "code"})

    def test_matching_pack_is_alignment_only(self):
        cfg = example()
        report = preflight.check_pack_alignment(cfg, matching_pack(cfg))
        self.assertEqual(report["status"], "kit_pack_aligned")
        self.assertTrue(report["pack_alignment_checked"])
        self.assertFalse(report["field_or_entitlement_verified"])
        self.assertNotIn("access_code", json.dumps(report))
        self.assertNotIn(cfg["access_code"], json.dumps(report))

    def test_reject_mismatched_codes_names_kit_and_stop_ids(self):
        for field, replacement in (
            ("kit", "NOT-MATCHED"),
            ("code", "NOT-MATCHED"),
            ("name", "Unexpected stop name"),
            ("id", True),
            ("id", 9),
        ):
            cfg = example()
            pack = matching_pack(cfg)
            if field == "kit":
                pack["kit"] = replacement
            else:
                pack["stops"][2][field] = replacement
            with self.subTest(field=field), self.assertRaises(preflight.PreflightError):
                preflight.check_pack_alignment(cfg, pack)

    def test_signs_can_be_out_of_array_order_but_id_mapping_must_match(self):
        cfg = example()
        cfg["stops"] = list(reversed(cfg["stops"]))
        self.assertEqual(preflight.check_kit(cfg)["kit_stop_count"], 6)
        self.assertTrue(preflight.check_pack_alignment(cfg, matching_pack(cfg))["pack_alignment_checked"])
        cfg["stops"][0]["code"] = cfg["stops"][1]["code"]
        with self.assertRaisesRegex(preflight.PreflightError, "unique"):
            preflight.check_kit(cfg)

    def test_reject_duplicate_missing_extra_and_bool_orders(self):
        cfg = example()
        cfg["stops"] = cfg["stops"][:5]
        with self.assertRaisesRegex(preflight.PreflightError, "exactly six"):
            preflight.check_kit(cfg)
        cfg = example()
        cfg["stops"][1]["order"] = 1
        with self.assertRaisesRegex(preflight.PreflightError, "duplicate"):
            preflight.check_kit(cfg)
        cfg = example()
        cfg["stops"][1]["order"] = True
        with self.assertRaisesRegex(preflight.PreflightError, "integer order"):
            preflight.check_kit(cfg)
        cfg = example()
        cfg["stops"][1]["code"] = cfg["access_code"]
        with self.assertRaisesRegex(preflight.PreflightError, "distinct"):
            preflight.check_kit(cfg)

    def test_reject_malformed_url_injection_and_bad_art(self):
        bad_urls = (
            "http://zqmlabs.com/games/hunt-for-wisps/play/",
            "https://user:password@zqmlabs.com/games/hunt-for-wisps/play/",
            "https://zqmlabs.com/games/hunt-for-wisps/play/?kit=OVERRIDE",
            "https://zqmlabs.com/games/hunt-for-wisps/play/#secret",
            "https://zqmlabs.com/games/hunt-for-wisps/play",
            "https://zqmlabs.com:99999/",
            "javascript:alert(1)",
            "https://zqmlabs.com/invalid path/",
        )
        for url in bad_urls:
            cfg = example()
            cfg["play_base_url"] = url
            with self.subTest(url=url), self.assertRaises(preflight.PreflightError):
                preflight.check_kit(cfg)
        for asset in ("../../private.png", "/etc/passwd", "C:\\private\\art.jpg", "https://example.org/file.png"):
            cfg = example()
            cfg["poster_art"] = asset
            with self.subTest(asset=asset), self.assertRaises(preflight.PreflightError):
                preflight.check_kit(cfg)

    def test_reject_duplicate_keys_bad_unicode_nonfinite_and_large_input(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "kit.json"
            for src in (
                b'{"access_code":"ONE","access_code":"TWO"}',
                b'{"nested":{"key":"a","\\u006bey":"b"}}',
                b'{"number":NaN}',
                b'{"number":Infinity}',
                b"\xff",
                b" " * (preflight.KIT_BYTES + 1),
            ):
                with self.subTest(head=src[:25]):
                    path.write_bytes(src)
                    with self.assertRaises((ValueError, UnicodeError)):
                        preflight.read_json(path, preflight.KIT_BYTES)

    def test_cli_does_not_log_secret_values(self):
        cfg = example()
        cfg["access_code"] = "PRIVATE-DO-NOT-PRINT"
        # Deliberately invalid code format, and duplicate source case.
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "kit.json"
            path.write_text(json.dumps(cfg), encoding="utf-8")
            cli = subprocess.run(
                [sys.executable, str(QR / "preflight.py"), str(path), "--json"],
                capture_output=True, text=True, timeout=15,
            )
            self.assertEqual(cli.returncode, 0, cli.stderr)
            self.assertNotIn(cfg["access_code"], cli.stdout + cli.stderr)
            decoded = json.loads(cli.stdout)
            self.assertFalse(decoded["pack_alignment_checked"])
            tester = subprocess.run(
                [sys.executable, str(QR / "test_qr_signs.py"), str(path)],
                capture_output=True, text=True, timeout=15,
            )
            self.assertEqual(tester.returncode, 0, tester.stderr)
            self.assertNotIn(cfg["access_code"], tester.stdout + tester.stderr)
            pack = matching_pack(cfg)
            pack["stops"][0]["code"] = "PRIVATE-STOP-CODE"
            pack_path = Path(tmp) / "pack.json"
            pack_path.write_text(json.dumps(pack), encoding="utf-8")
            rejected = subprocess.run(
                [sys.executable, str(QR / "preflight.py"), str(path), "--pack", str(pack_path)],
                capture_output=True, text=True, timeout=15,
            )
            self.assertEqual(rejected.returncode, 1)
            for secret in (cfg["access_code"], "PRIVATE-STOP-CODE"):
                self.assertNotIn(secret, rejected.stdout + rejected.stderr)

    def test_generator_honors_pack_and_does_not_overwrite(self):
        cfg = example()
        pack = matching_pack(cfg)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = root / "kit.json"
            config.write_text(json.dumps(cfg), encoding="utf-8")
            approved = root / "pack.json"
            approved.write_text(json.dumps(pack), encoding="utf-8")
            output = root / "signs.html"
            args = [
                sys.executable, str(QR / "generate_qr_signs.py"),
                str(config), str(output), "--pack", str(approved),
            ]
            result = subprocess.run(args, capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stderr)
            html = output.read_text(encoding="utf-8")
            self.assertEqual(html.count('class="sign"'), 7)
            self.assertNotIn("NOT VALIDATED AGAINST A QUEST PACK", html)
            self.assertIn(cfg["access_code"], html)  # intentionally on private printed poster
            denied = subprocess.run(args, capture_output=True, text=True, timeout=30)
            self.assertNotEqual(denied.returncode, 0)
            self.assertIn("output already exists", denied.stderr)
            self.assertNotIn(cfg["access_code"], denied.stdout + denied.stderr)
            unverified = root / "unverified.html"
            unverified_result = subprocess.run(
                [sys.executable, str(QR / "generate_qr_signs.py"),
                 str(config), str(unverified)],
                capture_output=True, text=True, timeout=30,
            )
            self.assertEqual(unverified_result.returncode, 0, unverified_result.stderr)
            self.assertIn("NOT VALIDATED AGAINST A QUEST PACK", unverified.read_text())
            self.assertIn("NOT been matched", unverified_result.stderr)

    def test_mismatched_generator_refuses_to_write_signs(self):
        cfg = example()
        wrong_pack = matching_pack(cfg)
        wrong_pack["stops"][0]["code"] = "WRONG-STOP-CODE"
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            conf = root / "kit.json"
            pack = root / "pack.json"
            output = root / "signs.html"
            conf.write_text(json.dumps(cfg), encoding="utf-8")
            pack.write_text(json.dumps(wrong_pack), encoding="utf-8")
            proc = subprocess.run(
                [sys.executable, str(QR / "generate_qr_signs.py"),
                 str(conf), str(output), "--pack", str(pack)],
                capture_output=True, text=True, timeout=30,
            )
            self.assertNotEqual(proc.returncode, 0)
            self.assertFalse(output.exists())
            self.assertNotIn("WRONG-STOP-CODE", proc.stderr)


if __name__ == "__main__":
    unittest.main()
