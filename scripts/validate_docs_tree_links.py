#!/usr/bin/env python3
"""
Validate markdown link integrity for runtime-adjacent docs trees.

Scope:
- skills/*/references/**/*.md
- skills/*/*.md (skill-root markdown such as SKILL.md and REBALANCE_*.md)
- <plugin>/references/**/*.md
- leftover <plugin>/docs/**/*.md (if present after incomplete migration)
- <plugin>/README.md
- <plugin>/.catalog/*.md

Checks:
- local markdown link targets exist
- symlink targets resolve
- no symlink loops
- resolved targets do not escape plugin root

Plugin README / catalog fragments: validate plugin-local docs links
(`references/`, `skills/`, and leftover `docs/`) so stale `docs/INDEX.md`
pointers fail CI after a `docs/` → `references/` migration.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Iterable

DEFAULT_PLUGINS = [
    "rh-sre",
    "rh-developer",
    "ocp-admin",
    "rh-virt",
    "rh-ai-engineer",
    "rh-automation",
]

MD_LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")


def is_external(target: str) -> bool:
    lower = target.lower()
    return (
        lower.startswith("http://")
        or lower.startswith("https://")
        or lower.startswith("mailto:")
        or lower.startswith("#")
    )


def resolve_plugins(paths: Iterable[str]) -> set[Path]:
    plugins: set[Path] = set()
    for p in paths:
        path = Path(p)
        if path.is_file():
            if path.name == "SKILL.md" and path.parent.parent.name == "skills":
                plugins.add(path.parent.parent.parent.resolve())
            elif path.name.endswith(".md"):
                # If file belongs to a plugin directory, infer it.
                parts = path.resolve().parts
                if "skills" in parts:
                    idx = parts.index("skills")
                    plugins.add(Path(*parts[:idx]).resolve())
            continue
        if path.is_dir():
            if (path / "skills").exists():
                plugins.add(path.resolve())
                continue
            # Maybe path is plugin name that exists in cwd
            if (Path.cwd() / path / "skills").exists():
                plugins.add((Path.cwd() / path).resolve())
    return plugins


def _dedupe(paths: Iterable[Path]) -> list[Path]:
    # Dedupe by the path used for relative-link resolution, not the symlink target.
    # Shared-pool copies must be scanned from each skill directory.
    seen: set[str] = set()
    out: list[Path] = []
    for path in paths:
        key = str(path)
        if key in seen:
            continue
        seen.add(key)
        out.append(path)
    return out


def _is_plugin_local_doc_link(base: str) -> bool:
    """README/catalog links that must resolve from the plugin root."""
    normalized = base.replace("\\", "/")
    if normalized.startswith("./"):
        normalized = normalized[2:]
    return (
        normalized.startswith("references/")
        or normalized.startswith("skills/")
        or normalized.startswith("docs/")
    )


def scan_targets(plugin_root: Path) -> list[Path]:
    targets: list[Path] = []
    skills_dir = plugin_root / "skills"
    if skills_dir.exists():
        for skill_dir in sorted(skills_dir.glob("*")):
            if not skill_dir.is_dir() or not (skill_dir / "SKILL.md").exists():
                continue
            targets.extend(sorted(skill_dir.glob("references/**/*.md")))
            targets.extend(sorted(skill_dir.glob("*.md")))
    plugin_refs = plugin_root / "references"
    if plugin_refs.exists():
        targets.extend(sorted(plugin_refs.glob("**/*.md")))
    plugin_docs = plugin_root / "docs"
    if plugin_docs.exists():
        targets.extend(sorted(plugin_docs.glob("**/*.md")))
    readme = plugin_root / "README.md"
    if readme.exists():
        targets.append(readme)
    catalog = plugin_root / ".catalog"
    if catalog.exists():
        targets.extend(sorted(catalog.glob("*.md")))
    return _dedupe(targets)


def validate_file(path: Path, plugin_root: Path) -> list[str]:
    errs: list[str] = []
    text = path.read_text(encoding="utf-8", errors="ignore")
    is_plugin_meta = (path == (plugin_root / "README.md")) or (path.parent == (plugin_root / ".catalog"))
    for line_no, line in enumerate(text.splitlines(), start=1):
        for m in MD_LINK_RE.finditer(line):
            raw = m.group(1).strip()
            if is_external(raw):
                continue
            base = raw.split("#", 1)[0].strip()
            if not base.endswith(".md"):
                continue

            # For plugin README / catalog fragments, validate plugin-local docs references
            # including leftover docs/ links from incomplete migrations.
            if is_plugin_meta:
                if not _is_plugin_local_doc_link(base):
                    continue
                link_base = base.replace("\\", "/")
                if link_base.startswith("./"):
                    link_base = link_base[2:]
                link_path = plugin_root / link_base
            else:
                link_path = path.parent / base
            try:
                resolved = link_path.resolve(strict=True)
            except FileNotFoundError:
                errs.append(f"{path}:{line_no}: missing linked doc '{raw}'")
                continue
            except RuntimeError:
                errs.append(f"{path}:{line_no}: symlink loop for '{raw}'")
                continue

            try:
                resolved.relative_to(plugin_root)
            except ValueError:
                errs.append(
                    f"{path}:{line_no}: link escapes plugin root '{raw}' -> '{resolved}'"
                )

            if link_path.is_symlink():
                raw_link = os.readlink(link_path)
                immediate = (
                    link_path.parent / raw_link
                    if not os.path.isabs(raw_link)
                    else Path(raw_link)
                )
                if immediate.is_symlink():
                    errs.append(
                        f"{path}:{line_no}: symlink chain detected for '{raw}'"
                    )
    return errs


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate markdown links in skill docs, plugin references, README, and catalog fragments"
    )
    parser.add_argument(
        "paths",
        nargs="*",
        default=DEFAULT_PLUGINS,
        help="Plugin directories or SKILL.md paths",
    )
    parser.add_argument("--json-out", help="Optional JSON summary output path")
    args = parser.parse_args()

    plugins = resolve_plugins(args.paths)
    if not plugins:
        plugins = {Path(p).resolve() for p in DEFAULT_PLUGINS if (Path(p) / "skills").exists()}

    all_errors: list[str] = []
    scanned_files = 0
    for plugin in sorted(plugins):
        for f in scan_targets(plugin):
            scanned_files += 1
            all_errors.extend(validate_file(f, plugin))

    summary = {
        "plugins_scanned": len(plugins),
        "files_scanned": scanned_files,
        "error_count": len(all_errors),
    }

    if args.json_out:
        Path(args.json_out).write_text(
            json.dumps({"summary": summary, "errors": all_errors}, indent=2),
            encoding="utf-8",
        )

    if all_errors:
        print("❌ Docs tree link validation failed:")
        for err in all_errors:
            print(f"  • {err}")
        print(json.dumps(summary, indent=2))
        return 1

    print("✅ Docs tree links validated successfully")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
