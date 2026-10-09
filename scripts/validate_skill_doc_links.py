#!/usr/bin/env python3
"""
Validate skill markdown links to enforce skill-local references convention.

Rules:
- Forbid upward traversal into plugin docs (../references, ../../references, etc).
- Internal docs links must use references/... path from skill directory.
- Linked reference files must exist (symlinks allowed, dangling symlinks rejected).
- Resolved targets must stay within the plugin root.

Scans SKILL.md and other skill-root markdown (for example REBALANCE_*.md).
Plugin-level references/**/*.md is covered by validate_docs_tree_links.py.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, field
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


def _skill_root_markdown(skills_dir: Path) -> list[Path]:
    """SKILL.md plus companion skill-root markdown; skip shared pools like skills/references/."""
    files: list[Path] = []
    for skill_dir in sorted(skills_dir.glob("*")):
        if not skill_dir.is_dir() or not (skill_dir / "SKILL.md").exists():
            continue
        files.extend(sorted(skill_dir.glob("*.md")))
    return files


@dataclass
class ValidationResult:
    scanned_files: int = 0
    scanned_links: int = 0
    checked_docs_links: int = 0
    errors: list[str] = field(default_factory=list)


def iter_skill_files(paths: Iterable[str]) -> list[Path]:
    files: list[Path] = []
    for p in paths:
        path = Path(p)
        if path.is_file() and path.name == "SKILL.md":
            files.append(path)
            continue
        if path.is_dir():
            skills_dir = path / "skills"
            if skills_dir.exists():
                files.extend(_skill_root_markdown(skills_dir))
                continue
        plugin_path = Path(p)
        if (plugin_path / "skills").exists():
            files.extend(_skill_root_markdown(plugin_path / "skills"))
    dedup = sorted(set(files))
    return dedup


def is_external_link(target: str) -> bool:
    lower = target.lower()
    return (
        lower.startswith("http://")
        or lower.startswith("https://")
        or lower.startswith("mailto:")
        or lower.startswith("#")
    )


def _is_skill_local_references_link(target: str) -> bool:
    normalized = target.replace("\\", "/")
    return normalized.startswith("references/") or normalized.startswith("./references/")


def validate_skill_file(skill_file: Path, result: ValidationResult) -> None:
    skill_dir = skill_file.parent
    plugin_root = skill_file.parent.parent.parent.resolve()
    text = skill_file.read_text(encoding="utf-8")

    for line_no, line in enumerate(text.splitlines(), start=1):
        for m in MD_LINK_RE.finditer(line):
            result.scanned_links += 1
            raw_target = m.group(1).strip()
            if is_external_link(raw_target):
                continue

            target = raw_target.split("#", 1)[0].strip()
            if ".md" not in target or "references/" not in target:
                continue

            result.checked_docs_links += 1
            normalized = target.replace("\\", "/")

            # Forbid upward traversal to references.
            if normalized.startswith("../") or "/../" in normalized:
                result.errors.append(
                    f"{skill_file}:{line_no}: forbidden upward references path '{raw_target}'"
                )

            # Enforce skill-local references path (references/ or ./references/).
            if not _is_skill_local_references_link(normalized):
                result.errors.append(
                    f"{skill_file}:{line_no}: references link must be skill-local "
                    f"'references/...' or './references/...', got '{raw_target}'"
                )
                continue

            link_path = skill_dir / normalized
            if link_path.is_symlink():
                raw_link = os.readlink(link_path)
                immediate = (
                    link_path.parent / raw_link
                    if not os.path.isabs(raw_link)
                    else Path(raw_link)
                )
                if immediate.is_symlink():
                    result.errors.append(
                        f"{skill_file}:{line_no}: symlink chain detected for '{raw_target}'"
                    )

            if link_path.is_symlink() and not link_path.exists():
                result.errors.append(
                    f"{skill_file}:{line_no}: dangling symlink '{raw_target}'"
                )
                continue

            try:
                resolved = link_path.resolve(strict=True)
            except FileNotFoundError:
                result.errors.append(
                    f"{skill_file}:{line_no}: missing linked doc '{raw_target}'"
                )
                continue
            except RuntimeError:
                result.errors.append(
                    f"{skill_file}:{line_no}: symlink loop for '{raw_target}'"
                )
                continue

            try:
                resolved.relative_to(plugin_root)
            except ValueError:
                result.errors.append(
                    f"{skill_file}:{line_no}: linked doc escapes plugin root '{raw_target}' -> '{resolved}'"
                )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate skill docs links (skill-local docs convention)"
    )
    parser.add_argument(
        "paths",
        nargs="*",
        default=DEFAULT_PLUGINS,
        help="Plugin directories or SKILL.md paths to validate",
    )
    parser.add_argument(
        "--json-out",
        help="Optional path to write machine-readable summary JSON",
    )
    args = parser.parse_args()

    skill_files = iter_skill_files(args.paths)
    result = ValidationResult(scanned_files=len(skill_files))

    if not skill_files:
        print("No SKILL.md files found for docs-link validation.")
        return 0

    print("🔍 Validating skill docs links...")
    for sf in skill_files:
        validate_skill_file(sf, result)

    summary = {
        "scanned_files": result.scanned_files,
        "scanned_links": result.scanned_links,
        "checked_docs_links": result.checked_docs_links,
        "error_count": len(result.errors),
    }

    if args.json_out:
        Path(args.json_out).write_text(
            json.dumps({"summary": summary, "errors": result.errors}, indent=2),
            encoding="utf-8",
        )

    if result.errors:
        print("❌ Skill docs link validation failed:")
        for err in result.errors:
            print(f"  • {err}")
        print(json.dumps(summary, indent=2))
        return 1

    print("✅ Skill docs links validated successfully")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
