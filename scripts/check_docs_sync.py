#!/usr/bin/env python3
"""Check that docs/ copies of organizer guides stay in sync with sources.

Organizer-toolkit restructure (satellite pilot): the real guides live at the
repo root (guides/, faq.md) and are copied verbatim into docs/ so MkDocs
renders them on-site with nav + search. This script fails when a source
changes without its docs/ copy being updated, and when a docs/ guide page
exists with no source mapping.

Mapping (source -> docs copy). Exactly one documented rewrite is allowed:
in guides/qr-generator.md the repo-relative ``../qr-kit/`` link becomes the
absolute GitHub tree URL, because qr-kit/ lives outside docs/ and MkDocs
--strict fails on the relative form. Everything else must be byte-identical.

NOT covered here, deliberately: docs/index.md is homepage prose, not a
copy, so prose drift is a review concern, not a script failure. README.md
is never copied into docs/ (MkDocs excludes it as an index.md conflict);
its link stays an absolute GitHub URL in docs/index.md.

Usage: python scripts/check_docs_sync.py [repo-root]   (default: cwd)
Exit 0 when every copy is present, in sync, listed in nav, and linked from
docs/index.md. Exit 1 listing every violation.
"""

import re
import sys
from pathlib import Path

REPO_URL = "https://github.com/ZQM-Labs/organizer-toolkit"

# (source path, docs path, [(old, new), ...] rewrites applied to source)
MAPPING = [
    ("guides/setup-checklist.md", "docs/guides/setup-checklist.md", []),
    (
        "guides/qr-generator.md",
        "docs/guides/qr-generator.md",
        [("](../qr-kit/)", "](" + REPO_URL + "/tree/main/qr-kit/)")],
    ),
    ("guides/print-specs.md", "docs/guides/print-specs.md", []),
    (
        "guides/day-of-troubleshooting.md",
        "docs/guides/day-of-troubleshooting.md",
        [],
    ),
    ("faq.md", "docs/faq.md", []),
]

NAV_ENTRY = re.compile(r"^\s+-\s+[^:]+:\s+(\S+\.md)\s*$")


def expected_copy(source_text, rewrites):
    """Apply the documented rewrites to a source file's text."""
    text = source_text
    for old, new in rewrites:
        if old not in text:
            raise ValueError(f"rewrite anchor not found in source: {old!r}")
        text = text.replace(old, new)
    return text


def nav_pages(mkdocs_text):
    """Nav .md targets from mkdocs.yml (only lines under the nav: block)."""
    pages = set()
    in_nav = False
    for line in mkdocs_text.splitlines():
        if line.startswith("nav:"):
            in_nav = True
            continue
        if in_nav:
            if line and not line.startswith(" ") and not line.startswith("\t"):
                break
            m = NAV_ENTRY.match(line)
            if m:
                pages.add(m.group(1))
    return pages


def main(argv):
    root = Path(argv[1]) if len(argv) > 1 else Path.cwd()
    failures = []

    docs_dir = root / "docs"
    mapped_docs = {docs for _, docs, _ in MAPPING}

    for source_rel, docs_rel, rewrites in MAPPING:
        source = root / source_rel
        copy = root / docs_rel
        if not source.exists():
            failures.append(f"MISSING SOURCE: {source_rel}")
            continue
        if not copy.exists():
            failures.append(f"MISSING COPY: {docs_rel} (source {source_rel} changed or added without a docs/ copy)")
            continue
        try:
            expected = expected_copy(source.read_text(encoding="utf-8"), rewrites)
        except ValueError as exc:
            failures.append(f"REWRITE BROKEN for {source_rel}: {exc}")
            continue
        actual = copy.read_text(encoding="utf-8")
        if actual != expected:
            failures.append(
                f"STALE COPY: {docs_rel} differs from {source_rel} "
                "(update the docs/ copy, or record a new documented rewrite)"
            )

    # No orphan docs guide pages: every .md under docs/guides/ or docs/faq.md
    # must be in the mapping (index.md and overrides/ excluded by location).
    orphans = []
    guides_dir = docs_dir / "guides"
    if guides_dir.is_dir():
        for path in sorted(guides_dir.glob("*.md")):
            rel = str(path.relative_to(root))
            if rel not in mapped_docs:
                orphans.append(rel)
    faq = docs_dir / "faq.md"
    if faq.exists() and "docs/faq.md" not in mapped_docs:
        orphans.append("docs/faq.md")
    for orphan in orphans:
        failures.append(f"UNMAPPED DOCS PAGE: {orphan} (add a mapping or remove it)")

    # Nav + homepage linkage for every mapped copy.
    mkdocs = root / "mkdocs.yml"
    if mkdocs.exists():
        nav = nav_pages(mkdocs.read_text(encoding="utf-8"))
        for _, docs_rel, _ in MAPPING:
            # Nav paths are relative to docs_dir, so they omit the docs/ prefix.
            nav_rel = docs_rel[len("docs/"):]
            if nav_rel not in nav:
                failures.append(f"NAV GAP: {docs_rel} not listed in mkdocs.yml nav")
    else:
        failures.append("MISSING: mkdocs.yml")

    index = docs_dir / "index.md"
    if index.exists():
        index_text = index.read_text(encoding="utf-8")
        for _, docs_rel, _ in MAPPING:
            short = docs_rel[len("docs/"):]
            if f"]({short})" not in index_text:
                failures.append(f"INDEX GAP: docs/index.md does not link {short}")
    else:
        failures.append("MISSING: docs/index.md")

    if failures:
        print("check_docs_sync: FAIL")
        for failure in failures:
            print(f"  - {failure}")
        return 1
    print(f"check_docs_sync: PASS ({len(MAPPING)} copies in sync, nav + index linked)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
