/* Browser-only QR Manager preflight. No network calls, analytics or storage.
   The Python preflight remains authoritative for strict duplicate-key JSON.
   This file is a classic script (works on file://); exports are testable in Node.
*/
(function (root, factory) {
  "use strict";
  const api = factory();
  root.ZQMQR = api;
  if (typeof module !== "undefined" && module.exports) module.exports = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  "use strict";

  const CODE = /^[A-Z0-9][A-Z0-9-]{2,63}$/;
  const DIAL = new Set(["cozy", "spooky", "afterdark", "overdrive"]);
  const FIELDS = ["access_code", "community", "game_title", "kit_id", "play_base_url", "window", "stops"];

  function record(value) {
    return !!value && typeof value === "object" && !Array.isArray(value);
  }
  function printable(value, field, max = 150) {
    if (typeof value !== "string" || !value.trim() || value.length > max ||
        /[\u0000-\u001f\u007f]/.test(value)) {
      throw new Error(field + " must be nonempty printable text");
    }
    return value;
  }
  function code(value, field) {
    if (typeof value !== "string" || !CODE.test(value)) {
      throw new Error(field + " must be 3–64 uppercase letters, digits or hyphens");
    }
    return value;
  }
  function baseURL(value) {
    printable(value, "play_base_url", 512);
    if (/\s/.test(value)) throw new Error("play_base_url contains whitespace");
    let url;
    try { url = new URL(value); }
    catch (_) { throw new Error("play_base_url is malformed"); }
    if (url.protocol !== "https:" || !url.hostname || url.username || url.password ||
        url.search || url.hash || !url.pathname.endsWith("/")) {
      throw new Error("play_base_url requires HTTPS, trailing /, no credentials, query or fragment");
    }
    return value;
  }

  function validateKit(cfg) {
    if (!record(cfg) || FIELDS.some(key => !Object.prototype.hasOwnProperty.call(cfg, key))) {
      throw new Error("kit config missing required organizer fields");
    }
    baseURL(cfg.play_base_url);
    code(cfg.kit_id, "kit_id");
    code(cfg.access_code, "access_code");
    for (const key of ["community", "game_title", "window"]) printable(cfg[key], key);
    if (cfg.scare_default !== undefined && !DIAL.has(cfg.scare_default)) {
      throw new Error("invalid scare_default");
    }
    if (!Array.isArray(cfg.stops) || cfg.stops.length !== 6) {
      throw new Error("kit must contain exactly six stops");
    }
    const orders = new Set();
    const codes = new Set();
    for (const [index, stop] of cfg.stops.entries()) {
      if (!record(stop)) throw new Error("stop " + (index + 1) + " must be an object");
      const n = stop.order;
      if (!Number.isInteger(n) || n < 1 || n > 6 || orders.has(n)) {
        throw new Error("stop orders must be distinct integers 1–6");
      }
      orders.add(n);
      const token = code(stop.code, "stop code");
      if (codes.has(token) || token === cfg.access_code) {
        throw new Error("stop codes must be unique and distinct from access code");
      }
      codes.add(token);
      printable(stop.name, "stop name");
      printable(stop.placement, "stop placement", 250);
    }
    return { status: "kit_structure_valid", stops: 6, pack_alignment_checked: false, released: false };
  }

  function validatePack(cfg, pack) {
    const summary = validateKit(cfg);
    if (!record(pack) || pack.kit !== cfg.kit_id) {
      throw new Error("quest pack kit identifier does not match");
    }
    if (!Array.isArray(pack.stops) || pack.stops.length !== 6) {
      throw new Error("quest pack must contain exactly six stops");
    }
    const byId = new Map();
    for (const stop of pack.stops) {
      if (!record(stop) || !Number.isInteger(stop.id) || stop.id < 1 || stop.id > 6 ||
          byId.has(stop.id)) {
        throw new Error("quest pack stop IDs must be unique 1–6");
      }
      byId.set(stop.id, stop);
    }
    for (const sign of cfg.stops) {
      const stop = byId.get(sign.order);
      if (!stop || stop.code !== sign.code) {
        throw new Error("stop " + sign.order + ": sign code differs from pack");
      }
      if (stop.name !== sign.name) {
        throw new Error("stop " + sign.order + ": sign name differs from pack");
      }
    }
    return { ...summary, status: "kit_pack_aligned", pack_alignment_checked: true };
  }

  function createLink(base, entries) {
    const parsed = new URL(base);
    for (const [name, value] of entries) parsed.searchParams.set(name, String(value));
    return parsed.href;
  }

  function links(cfg) {
    validateKit(cfg);
    return [{
      kind: "poster",
      title: "Start poster",
      url: createLink(cfg.play_base_url, [["kit", cfg.kit_id], ["ac", cfg.access_code]]),
      visible: "Access-code join link (hidden until copied or opened)",
    }, ...cfg.stops.map(s => ({
      kind: "stop",
      title: "Stop " + s.order + " — " + s.name,
      url: createLink(cfg.play_base_url, [["kit", cfg.kit_id], ["stop", s.order], ["code", s.code]]),
      visible: "Stop code " + s.code + " (no access-code parameter)",
    }))];
  }

  return Object.freeze({ validateKit, validatePack, links });
});
