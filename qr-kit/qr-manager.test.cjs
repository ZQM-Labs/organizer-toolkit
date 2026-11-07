"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

const dir = __dirname;
const source = fs.readFileSync(path.join(dir, "qr-manager.html"), "utf8");
const { validateKit, validatePack, links } = require("./qr-manager-logic.js");
const example = JSON.parse(fs.readFileSync(path.join(dir, "kit-config.example.json"), "utf8"));

function kit() { return JSON.parse(JSON.stringify(example)); }
function pack(cfg) {
  return {
    kit: cfg.kit_id,
    stops: cfg.stops.map(s => ({ id: s.order, name: s.name, code: s.code })),
  };
}

test("local browser preview requires exactly six unique, valid sign entries", () => {
  const cfg = kit();
  assert.equal(validateKit(cfg).stops, 6);
  const values = links(cfg);
  assert.equal(values.length, 7);
  assert.equal(values[0].kind, "poster");
  const poster = new URL(values[0].url);
  assert.equal(poster.protocol, "https:");
  assert.deepEqual([...poster.searchParams.keys()], ["kit", "ac"]);
  for (const entry of values.slice(1)) {
    assert.deepEqual([...new URL(entry.url).searchParams.keys()], ["kit", "stop", "code"]);
  }
  const result = validatePack(cfg, pack(cfg));
  assert.equal(result.status, "kit_pack_aligned");
  assert.equal(result.released, false);
  assert.doesNotMatch(JSON.stringify(result), /access_code|LANTERN-/);
});

test("browser sign preview always sorts numeric stops without changing input", () => {
  const cfg = kit();
  cfg.stops.reverse();
  const before = cfg.stops.map(s => s.order);
  const items = links(cfg);
  assert.equal(items.length, 7);
  assert.deepEqual(items.slice(1).map(x => x.title.match(/^Stop (\\d+)/)[1]),
    ["1", "2", "3", "4", "5", "6"]);
  assert.deepEqual(items.slice(1).map(x => new URL(x.url).searchParams.get("stop")),
    ["1", "2", "3", "4", "5", "6"]);
  assert.deepEqual(cfg.stops.map(s => s.order), before, "Input order must not mutate");
  assert.equal(validatePack(cfg, pack(cfg)).pack_alignment_checked, true);
});

test("rejects invalid URL, wrong stop count, duplicate order, invalid code and cross-pack mismatch", () => {
  for (const bad of [
    "javascript:alert(1)", "http://zqmlabs.com/play/",
    "https://evil:password@zqmlabs.com/play/",
    "https://zqmlabs.com/play/?code=SECRET",
    "https://zqmlabs.com/play/#fragment",
    "https://zqmlabs.com/play",
    "https://zqmlabs.com/bad path/",
  ]) {
    const cfg = kit();
    cfg.play_base_url = bad;
    assert.throws(() => validateKit(cfg), /play_base_url/);
  }
  const cases = [
    c => c.stops.pop(),
    c => { c.stops[0].order = c.stops[1].order; },
    c => { c.stops[0].order = true; },
    c => { c.stops[0].code = c.access_code; },
    c => { c.stops[0].code = "bad&value"; },
  ];
  for (const modify of cases) {
    const cfg = kit();
    modify(cfg);
    assert.throws(() => validateKit(cfg));
  }
  for (const mutate of [
    p => { p.kit = "WRONG"; },
    p => { p.stops[0].name = "wrong"; },
    p => { p.stops[0].code = "WRONG-CODE"; },
    p => { p.stops[0].id = 9; },
    p => { p.stops[0].id = p.stops[1].id; },
  ]) {
    const cfg = kit(), p = pack(cfg);
    mutate(p);
    assert.throws(() => validatePack(cfg, p));
  }
});

test("the browser HTML has no untrusted HTML injection or false verified-live indicators", () => {
  assert.match(source, /<script src="\.\/qr-manager-logic\.js"><\/script>/);
  assert.doesNotMatch(source, /innerHTML|onclick\s*=|document\.write\s*\(/i);
  assert.doesNotMatch(source, /Play URL reachable.*true|class="status ok"/);
  assert.match(source, /cannot reject duplicate object/);
  assert.match(source, /noopener noreferrer/);
  assert.match(source, /textContent/);
  assert.match(source, /not a release approval/i);
});

function newElement(tag = "div") {
  const node = {
    tag,
    textContent: "",
    className: "",
    value: "",
    children: [],
    listeners: {},
    attributes: {},
    classList: {
      add() {},
      remove() {},
    },
    append(...children) { this.children.push(...children); },
    replaceChildren(...children) { this.children = [...children]; },
    addEventListener(name, callback) { this.listeners[name] = callback; },
  };
  return node;
}

function visibleText(node) {
  return [node.textContent || "", ...(node.children || []).flatMap(child => [visibleText(child)])].join(" ");
}

test("DOM preview hides start access code from displayed text and avoids stale pack pairing", async () => {
  const ids = ["kit-file", "pack-file", "results", "kit-title", "summary", "qr-list", "checklist", "status"];
  const elements = Object.fromEntries(ids.map(id => [id, newElement()]));
  const document = {
    getElementById: id => elements[id],
    createElement: tag => newElement(tag),
  };
  const script = source.match(/<script>\s*([\s\S]*?)<\/script>\s*<\/body>/);
  assert.ok(script, "Inline UI script missing");
  let copied = null;
  const sandbox = vm.createContext({
    document, ZQMQR: require("./qr-manager-logic.js"), navigator: {
      clipboard: { writeText: async str => { copied = str; } },
    },
  });
  vm.runInContext(script[1], sandbox);
  const cfg = kit();
  cfg.access_code = "PRIVATE-KEEP-HIDDEN";
  const p = pack(cfg);
  sandbox.upload = { size: 2000, text: async () => JSON.stringify(cfg) };
  await vm.runInContext('selected("kit", upload)', sandbox);
  assert.match(elements.status.textContent, /Private QR link previews prepared/);
  assert.match(elements.summary.textContent, /no matching quest pack/);
  assert.doesNotMatch(visibleText(elements["qr-list"]), /PRIVATE-KEEP-HIDDEN/);
  assert.equal(elements["qr-list"].children.length, 7);
  const firstRow = elements["qr-list"].children[0];
  const actions = firstRow.children[1].children[2].children;
  assert.equal(actions[0].target, "_blank");
  assert.equal(actions[0].rel, "noopener noreferrer");
  await actions[1].listeners.click();
  assert.ok(copied?.includes("PRIVATE-KEEP-HIDDEN"), "Copying is a deliberate host action");

  sandbox.upload = { size: 1000, text: async () => JSON.stringify(p) };
  await vm.runInContext('selected("pack", upload)', sandbox);
  assert.match(elements.summary.textContent, /align/);

  // A new kit upload deliberately clears any previously verified pack state.
  sandbox.upload = { size: 2000, text: async () => JSON.stringify(cfg) };
  await vm.runInContext('selected("kit", upload)', sandbox);
  assert.match(elements.summary.textContent, /no matching quest pack/);

  const invalid = kit();
  invalid.stops[0].code = "bad&value";
  sandbox.upload = { size: 2000, text: async () => JSON.stringify(invalid) };
  await vm.runInContext('selected("kit", upload)', sandbox);
  assert.match(elements.status.textContent, /Preview rejected/);
});

test("browser errors do not reveal code material", () => {
  const cfg = kit();
  cfg.access_code = "PRIVATE-KEEP-HIDDEN";
  const p = pack(cfg);
  p.stops[0].code = "PRIVATE-STOP-CODE";
  assert.throws(() => validatePack(cfg, p), e =>
    !e.message.includes("PRIVATE-KEEP-HIDDEN") && !e.message.includes("PRIVATE-STOP-CODE")
  );
});
