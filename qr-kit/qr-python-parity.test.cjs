"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const { spawnSync } = require("node:child_process");
const browser = require("./qr-manager-logic.js");

const ROOT = path.resolve(__dirname, "..");
const PYTHON = process.env.PYTHON || (process.platform === "win32" ? "python" : "python3");
const TEMPLATE = JSON.parse(fs.readFileSync(path.join(__dirname, "kit-config.example.json"), "utf8"));

const PY_CHECK = [
  "import json, sys",
  "sys.path.insert(0, 'qr-kit')",
  "from preflight import PreflightError, check_kit, check_pack_alignment",
  "record = json.load(sys.stdin)",
  "try:",
  "    if record['pack'] is None:",
  "        check_kit(record['kit'])",
  "    else:",
  "        check_pack_alignment(record['kit'], record['pack'])",
  "except PreflightError:",
  "    print('REJECT')",
  "else:",
  "    print('ACCEPT')",
].join("\n");

function pair() {
  const kit = JSON.parse(JSON.stringify(TEMPLATE));
  const pack = {
    kit: kit.kit_id,
    stops: kit.stops.map(s => ({ id: s.order, code: s.code, name: s.name })),
  };
  return { kit, pack };
}

function pythonVerdict(record) {
  const child = spawnSync(PYTHON, ["-c", PY_CHECK], {
    cwd: ROOT, input: JSON.stringify(record), encoding: "utf8", timeout: 15_000,
    maxBuffer: 1024 * 1024,
  });
  assert.equal(child.status, 0, "Python parity runner failed; inspect stderr without dumping input");
  assert.equal(child.stderr, "", "Python preflight unexpectedly printed to stderr");
  const result = child.stdout.trim();
  assert.ok(["ACCEPT", "REJECT"].includes(result), "Unexpected Python verdict");
  return result === "ACCEPT";
}

function browserVerdict(record) {
  try {
    if (record.pack === null) browser.validateKit(record.kit);
    else browser.validatePack(record.kit, record.pack);
    return true;
  } catch (err) {
    assert.ok(err instanceof Error);
    return false;
  }
}

test("Python and browser accept/reject the same common QR/pack contract fixtures", async t => {
  const cases = [
    ["valid six-stop kit", () => ({ ...pair(), pack: null }), true],
    ["valid matched pack", () => pair(), true],
    ["array order irrelevant when stop IDs still match", () => {
      const r = pair(); r.kit.stops.reverse(); return r;
    }, true],
    ["too few signs", () => {
      const r = pair(); r.kit.stops.pop(); return r;
    }, false],
    ["duplicate sign orders", () => {
      const r = pair(); r.kit.stops[1].order = 1; return r;
    }, false],
    ["boolean order", () => {
      const r = pair(); r.kit.stops[0].order = true; return r;
    }, false],
    ["duplicate sign codes", () => {
      const r = pair(); r.kit.stops[0].code = r.kit.stops[1].code; return r;
    }, false],
    ["stop code equals access code", () => {
      const r = pair(); r.kit.stops[0].code = r.kit.access_code; return r;
    }, false],
    ["malformed sign token", () => {
      const r = pair(); r.kit.stops[0].code = "bad&value"; return r;
    }, false],
    ["non-string sign name", () => {
      const r = pair(); r.kit.stops[0].name = 9; return r;
    }, false],
    ["wrong kit identifier", () => {
      const r = pair(); r.pack.kit = "ANOTHER-KIT"; return r;
    }, false],
    ["wrong pack stop code", () => {
      const r = pair(); r.pack.stops[4].code = "WRONG-SIGN-CODE"; return r;
    }, false],
    ["wrong pack stop name", () => {
      const r = pair(); r.pack.stops[3].name = "Different Name"; return r;
    }, false],
    ["duplicate pack IDs", () => {
      const r = pair(); r.pack.stops[4].id = r.pack.stops[5].id; return r;
    }, false],
    ["boolean pack ID", () => {
      const r = pair(); r.pack.stops[1].id = true; return r;
    }, false],
    ["insecure HTTP URL", () => {
      const r = pair(); r.kit.play_base_url = "http://zqmlabs.com/play/"; return r;
    }, false],
    ["player URL already contains a query", () => {
      const r = pair(); r.kit.play_base_url += "?kit=OVERRIDE"; return r;
    }, false],
    ["URL embeds credentials", () => {
      const r = pair(); r.kit.play_base_url = "https://user:pass@zqmlabs.com/play/"; return r;
    }, false],
    ["URL lacks trailing slash", () => {
      const r = pair(); r.kit.play_base_url = "https://zqmlabs.com/play"; return r;
    }, false],
    ["unknown scare level", () => {
      const r = pair(); r.kit.scare_default = "superfast"; return r;
    }, false],
  ];
  for (const [name, make, expected] of cases) {
    await t.test(name, () => {
      const record = make();
      assert.equal(browserVerdict(record), expected, "browser contract differs from expected");
      assert.equal(pythonVerdict(record), expected, "Python contract differs from expected");
    });
  }
});
