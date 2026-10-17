#!/usr/bin/env python3
"""Validate relative Markdown links without network access."""
from __future__ import annotations
import html
import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path.cwd()
SKIP_DIRS = {".git", ".venv", "node_modules", "site", "build", "dist"}
LINK_RE = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")


def strip_fenced_code(text: str) -> str:
    kept = []
    fence = None
    for line in text.splitlines():
        stripped = line.lstrip()
        ticks = chr(96) * 3
        marker = ticks if stripped.startswith(ticks) else ("~~~" if stripped.startswith("~~~") else None)
        if marker:
            if fence is None:
                fence = marker
            elif marker == fence:
                fence = None
            continue
        if fence is None:
            kept.append(line)
    return "\n".join(kept)


def main() -> int:
    failures = []
    files = sorted(p for p in ROOT.rglob("*.md") if not any(part in SKIP_DIRS for part in p.parts))
    for source in files:
        text = strip_fenced_code(source.read_text(encoding="utf-8"))
        for match in LINK_RE.finditer(text):
            raw = html.unescape(match.group(1).strip())
            if raw.startswith("<") and ">" in raw:
                raw = raw[1:raw.index(">")]
            else:
                raw = raw.split()[0] if raw else ""
            if not raw or raw.startswith(("#", "/")):
                continue
            parsed = urlsplit(raw)
            if parsed.scheme or parsed.netloc:
                continue
            target = unquote(parsed.path)
            if not target:
                continue
            resolved = (source.parent / target).resolve()
            if not resolved.exists():
                failures.append(f"{source.relative_to(ROOT)}: broken relative link: {raw}")
    if failures:
        print("\n".join(failures))
        print(f"FAIL: {len(failures)} broken Markdown link(s) across {len(files)} file(s)")
        return 1
    print(f"PASS: checked relative Markdown links in {len(files)} file(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
