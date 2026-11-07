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

    def test_printed_sign_order_is_numeric_even_if_config_is_reversed(self):
        cfg = example()
        cfg["stops"] = list(reversed(cfg["stops"]))
        pack = matching_pack(cfg)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            kit_file = root / "kit.json"
            pack_file = root / "pack.json"
            output = root / "signs.html"
            kit_file.write_text(json.dumps(cfg), encoding="utf-8")
            pack_file.write_text(json.dumps(pack), encoding="utf-8")
            proc = subprocess.run(
                [sys.executable, str(QR / "generate_qr_signs.py"),
                 str(kit_file), str(output), "--pack", str(pack_file)],
                capture_output=True, text=True, timeout=30,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            body = output.read_text(encoding="utf-8")
            positions = [body.index(f"Stop {i}:") for i in range(1, 7)]
            self.assertEqual(positions, sorted(positions))
            self.assertEqual(body.count('class="sign"'), 7)
            self.assertNotIn("NOT VALIDATED AGAINST A QUEST PACK", body)

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

    def test_art_asset_filename_cannot_inject_html(self):
        import generate_qr_signs as generator

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            suspicious = 'photo" onerror="alert(1).png'
            (root / suspicious).write_bytes(b"synthetic image stub")
            destination = root / "output"
            fragment = generator.art_html(suspicious, str(root), str(destination), 'alt "value"')
            self.assertRegex(fragment, r'src="art/asset-[0-9a-f]{24}\.png"')
            self.assertNotIn('onerror="alert(1)"', fragment)
            self.assertNotIn('photo&quot;', fragment)
            self.assertIn("alt=\"alt &quot;value&quot;\"", fragment)
            self.assertEqual(len(list((destination / "art").iterdir())), 1)

    def test_two_distinct_artworks_with_same_basename_are_not_overwritten(self):
        import generate_qr_signs as generator
        import re

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "a").mkdir()
            (root / "b").mkdir()
            (root / "a" / "scene.png").write_bytes(b"first synthetic image")
            (root / "b" / "scene.png").write_bytes(b"second synthetic image")
            output = root / "signout"
            first = generator.art_html("a/scene.png", str(root), str(output), "First")
            second = generator.art_html("b/scene.png", str(root), str(output), "Second")
            pattern = r'src="art/(asset-[0-9a-f]{24}\.png)"'
            name_a = re.search(pattern, first).group(1)
            name_b = re.search(pattern, second).group(1)
            self.assertNotEqual(name_a, name_b)
            self.assertEqual((output / "art" / name_a).read_bytes(), b"first synthetic image")
            self.assertEqual((output / "art" / name_b).read_bytes(), b"second synthetic image")
            # Re-using an identical source is idempotent, not another overwrite.
            self.assertEqual(first, generator.art_html("a/scene.png", str(root), str(output), "First"))
            self.assertEqual(len(list((output / "art").iterdir())), 2)

    def test_artwork_collision_symlink_and_oversize_fail_closed(self):
        import generate_qr_signs as generator
        import re

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "artwork.png").write_bytes(b"synthetic content")
            outdir = root / "out"
            html = generator.art_html("artwork.png", str(root), str(outdir), "Artwork")
            filename = re.search(r'src="art/([^"]+)"', html).group(1)
            (outdir / "art" / filename).write_bytes(b"tampered existing content")
            with self.assertRaisesRegex(preflight.PreflightError, "collision"):
                generator.art_html("artwork.png", str(root), str(outdir), "Artwork")

            (root / "too-large.png").write_bytes(b"x" * (generator.ART_MAX_BYTES + 1))
            with self.assertRaisesRegex(preflight.PreflightError, "8 MiB"):
                generator.art_html("too-large.png", str(root), str(outdir), "Too large")

            linked = root / "linked"
            linked.mkdir()
            (linked / "art").symlink_to(outdir / "art", target_is_directory=True)
            with self.assertRaisesRegex(preflight.PreflightError, "symlink"):
                generator.art_html("artwork.png", str(root), str(linked), "Blocked")

    def test_missing_configured_art_cannot_silently_disappear_from_signs(self):
        cfg = example()
        cfg["poster_art"] = "missing-artwork.png"
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            kit = root / "kit.json"
            output = root / "signs.html"
            kit.write_text(json.dumps(cfg), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(QR / "generate_qr_signs.py"), str(kit), str(output)],
                capture_output=True, text=True, timeout=30,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(output.exists())
            self.assertIn("configured artwork is missing", result.stderr)
            self.assertNotIn(cfg["access_code"], result.stdout + result.stderr)

    def test_generator_force_replaces_html_but_refuses_symlink_output(self):
        cfg = example()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = root / "kit.json"
            config.write_text(json.dumps(cfg), encoding="utf-8")
            output = root / "signs.html"
            command = [sys.executable, str(QR / "generate_qr_signs.py"), str(config), str(output)]
            self.assertEqual(
                subprocess.run(command, capture_output=True, text=True, timeout=30).returncode,
                0,
            )
            output.write_text("previous output")
            denied = subprocess.run(command, capture_output=True, text=True, timeout=30)
            self.assertNotEqual(denied.returncode, 0)
            self.assertEqual(output.read_text(), "previous output")
            allowed = subprocess.run(command + ["--force"], capture_output=True, text=True, timeout=30)
            self.assertEqual(allowed.returncode, 0, allowed.stderr)
            self.assertIn("class=\"sign\"", output.read_text())
            self.assertFalse(any(root.glob(".qr-stage-*")))

            real = root / "private.txt"
            real.write_text("must not be replaced")
            output.unlink()
            output.symlink_to(real)
            rejected = subprocess.run(command + ["--force"], capture_output=True, text=True, timeout=30)
            self.assertNotEqual(rejected.returncode, 0)
            self.assertEqual(real.read_text(), "must not be replaced")
            self.assertTrue(output.is_symlink())

    def test_output_directory_lock_blocks_overlapping_asset_and_html_commit(self):
        import generate_qr_signs as generator

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            stage = root / "stage"
            (stage / "art").mkdir(parents=True)
            item = stage / "art" / "asset-123456789012345678901234.png"
            item.write_bytes(b"synthetic staged art")
            out = root / "signs.html"
            guard = root / ".qr-publish.lock"
            with generator.publication_lock(str(root)):
                self.assertTrue(guard.is_dir())
                with self.assertRaisesRegex(preflight.PreflightError, "locked"):
                    generator.publish_private_bundle(str(stage), str(out), "seven private signs")
                self.assertFalse(out.exists())
                self.assertFalse((root / "art").exists())
            self.assertFalse(guard.exists())
            generator.publish_private_bundle(str(stage), str(out), "seven private signs")
            self.assertEqual(out.read_text(), "seven private signs")
            self.assertEqual((root / "art" / item.name).read_bytes(), item.read_bytes())
            self.assertFalse(guard.exists())

    def test_cli_refuses_stale_lock_without_disclosing_codes_or_changing_signs(self):
        cfg = example()
        cfg["access_code"] = "PRIVATE-KEEP-HIDDEN"
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            kit = root / "kit.json"
            out = root / "signs.html"
            guard = root / ".qr-publish.lock"
            kit.write_text(json.dumps(cfg), encoding="utf-8")
            args = [sys.executable, str(QR / "generate_qr_signs.py"), str(kit), str(out)]
            initial = subprocess.run(args, capture_output=True, text=True, timeout=30)
            self.assertEqual(initial.returncode, 0, initial.stderr)
            original = out.read_bytes()
            guard.mkdir()
            blocked = subprocess.run(args + ["--force"], capture_output=True, text=True, timeout=30)
            self.assertNotEqual(blocked.returncode, 0)
            self.assertIn("directory is locked", blocked.stderr)
            self.assertNotIn(cfg["access_code"], blocked.stdout + blocked.stderr)
            self.assertEqual(out.read_bytes(), original)
            self.assertTrue(guard.is_dir())
            self.assertFalse(any(root.glob(".qr-stage-*")))
            guard.rmdir()
            retried = subprocess.run(args + ["--force"], capture_output=True, text=True, timeout=30)
            self.assertEqual(retried.returncode, 0, retried.stderr)
            self.assertFalse(guard.exists())
            self.assertEqual(out.read_bytes(), original)

    def test_failed_publication_releases_lock_for_next_attempt(self):
        import generate_qr_signs as generator

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            out = root / "signs.html"
            out.write_text("previous signs", encoding="utf-8")
            stage = root / "stage"
            stage.mkdir()
            with self.assertRaises(FileExistsError):
                generator.publish_private_bundle(str(stage), str(out), "new signs", force=False)
            self.assertFalse((root / ".qr-publish.lock").exists())
            self.assertEqual(out.read_text(), "previous signs")
            generator.publish_private_bundle(str(stage), str(out), "new signs", force=True)
            self.assertEqual(out.read_text(), "new signs")
            self.assertFalse((root / ".qr-publish.lock").exists())

    def test_private_bundle_publishes_complete_html_and_assets_only(self):
        import generate_qr_signs as generator
        import os
        import stat

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            destination = root / "out"
            destination.mkdir()
            html = destination / "signs.html"
            stage = destination / ".qr-stage-test"
            (stage / "art").mkdir(parents=True)
            asset = stage / "art" / "asset-123456789012345678901234.png"
            asset.write_bytes(b"small synthetic artwork")
            generator.publish_private_bundle(str(stage), str(html), "COMPLETE SIGN BUNDLE")
            self.assertEqual(html.read_text(), "COMPLETE SIGN BUNDLE")
            self.assertEqual((destination / "art" / asset.name).read_bytes(), asset.read_bytes())
            if os.name != "nt":
                self.assertEqual(stat.S_IMODE(html.stat().st_mode), 0o600)
                self.assertEqual(stat.S_IMODE((destination / "art" / asset.name).stat().st_mode), 0o600)

    def test_existing_html_rolls_back_newly_linked_art(self):
        import generate_qr_signs as generator

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            html = root / "signs.html"
            html.write_text("existing private signs", encoding="utf-8")
            stage = root / "stage"
            (stage / "art").mkdir(parents=True)
            asset = stage / "art" / "asset-123456789012345678901234.png"
            asset.write_bytes(b"new art")
            with self.assertRaises(FileExistsError):
                generator.publish_private_bundle(str(stage), str(html), "new signs")
            self.assertEqual(html.read_text(), "existing private signs")
            self.assertFalse((root / "art" / asset.name).exists())
            self.assertFalse((root / "art").exists())

    def test_existing_asset_conflict_preserves_old_html_and_art(self):
        import generate_qr_signs as generator

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            html = root / "signs.html"
            html.write_text("previous signs", encoding="utf-8")
            artwork = root / "art"
            artwork.mkdir()
            stage = root / "stage"
            (stage / "art").mkdir(parents=True)
            filename = "asset-123456789012345678901234.png"
            (stage / "art" / filename).write_bytes(b"new asset")
            (artwork / filename).write_bytes(b"untouched prior asset")
            with self.assertRaisesRegex(preflight.PreflightError, "collision"):
                generator.publish_private_bundle(str(stage), str(html), "new signs", force=True)
            self.assertEqual(html.read_text(), "previous signs")
            self.assertEqual((artwork / filename).read_bytes(), b"untouched prior asset")

    def test_force_bundle_replaces_html_atomically_and_reuses_identical_asset(self):
        import generate_qr_signs as generator
        import os
        import stat

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            html = root / "signs.html"
            html.write_text("old signs", encoding="utf-8")
            assets = root / "art"
            assets.mkdir()
            stage = root / "stage"
            (stage / "art").mkdir(parents=True)
            filename = "asset-123456789012345678901234.png"
            payload = b"identical existing artwork"
            (stage / "art" / filename).write_bytes(payload)
            (assets / filename).write_bytes(payload)
            generator.publish_private_bundle(str(stage), str(html), "new complete signs", force=True)
            self.assertEqual(html.read_text(), "new complete signs")
            self.assertEqual((assets / filename).read_bytes(), payload)
            if os.name != "nt":
                self.assertEqual(stat.S_IMODE(html.stat().st_mode), 0o600)

    def test_art_rendering_failure_stays_inside_private_staging(self):
        import generate_qr_signs as generator

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "good.png").write_bytes(b"first asset")
            cfg = example()
            cfg["poster_art"] = "good.png"
            cfg["stops"][4]["art"] = "missing-later.png"
            destination = root / "out"
            destination.mkdir()
            with tempfile.TemporaryDirectory(dir=destination, prefix=".qr-stage-") as staged:
                with self.assertRaisesRegex(preflight.PreflightError, "configured artwork is missing"):
                    generator.render_signs(cfg, str(root), staged, cfg["play_base_url"])
                self.assertTrue(list((Path(staged) / "art").iterdir()))
                self.assertFalse((destination / "art").exists())
                self.assertFalse((destination / "signs.html").exists())
            self.assertEqual(list(destination.iterdir()), [])

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
