#!/usr/bin/env python3
"""
Validate skills against agentskills.io specification (Tier 1).

This is the single Tier 1 validator for the repository.  Tier 2 (repo design
principles) is handled by validate_skills_tier2.py.

Checks performed:
  1.  Frontmatter delimiters present (---)
  2.  name: required, 1-64 chars, kebab-case, matches directory
  3.  description: required, 1-1024 chars
  4.  license: required, must be Apache-2.0
  5.  compatibility: if present, ≤500 chars
  6.  allowed-tools: space-delimited (fail on commas/arrays/YAML list)
  7.  Line count ≤ 500
  8.  Subdirectories: only scripts/, references/, assets/ allowed
  9.  No ASCII art outside fenced code blocks (WARNING)
  10. No persona statements outside fenced code blocks (ERROR)
  11. Description routing keywords (WARNING)
  12. No marketing buzzwords in description (WARNING)
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

import yaml

# ── Constants ────────────────────────────────────────────────────────────────

NAME_PATTERN = re.compile(r"^[a-z][a-z0-9]*(-[a-z0-9]+)*$")
MAX_NAME_LEN = 64
MAX_DESCRIPTION_LEN = 1024
MAX_COMPATIBILITY_LEN = 500
MAX_LINE_COUNT = 500
ALLOWED_SUBDIRS = {"scripts", "references", "assets"}
DEPRECATED_SUBDIRS = {"resources"}

ASCII_ART_PATTERN = re.compile(
    r"[─│┌┐└┘├┤┬┴┼╭╮╯╰═║╔╗╚╝╠╣╦╩╬↑↓←→↔⇒⇐⇔▲▼◄►]{3,}"
)
PERSONA_PATTERN = re.compile(
    r"^[  ]*You are (a|an|the) ", re.IGNORECASE | re.MULTILINE
)
ROUTING_KEYWORDS = re.compile(
    r"(use when|don't use|not for|triggers on)", re.IGNORECASE
)
MARKETING_BUZZWORDS = re.compile(
    r"(comprehensive|powerful|robust|cutting-edge|world-class"
    r"|state-of-the-art|best-in-class|game-changing)",
    re.IGNORECASE,
)

DEFAULT_PLUGINS = [
    "rh-sre", "rh-developer", "ocp-admin", "rh-virt",
    "rh-ai-engineer", "rh-automation", "rh-basic",
]

# ── Output formatting ────────────────────────────────────────────────────────

RED = "\033[0;31m"
GREEN = "\033[0;32m"
YELLOW = "\033[0;33m"
BOLD = "\033[1m"
NC = "\033[0m"
SEPARATOR = "=" * 70


# ── Data model ───────────────────────────────────────────────────────────────

@dataclass
class ValidationResult:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


# ── Helpers ──────────────────────────────────────────────────────────────────

def _strip_fenced_blocks(content: str) -> str:
    """Remove fenced code blocks, returning only prose content."""
    lines = content.splitlines()
    result: list[str] = []
    in_fence = False
    for line in lines:
        if line.startswith("```"):
            in_fence = not in_fence
            continue
        if not in_fence:
            result.append(line)
    return "\n".join(result)


def _extract_frontmatter(content: str) -> tuple[str | None, str | None]:
    """Return (frontmatter_text, error_message).

    If frontmatter is valid, error_message is None. Otherwise frontmatter_text
    is None and error_message explains the problem.
    """
    lines = content.splitlines()
    if not lines or lines[0].rstrip() != "---":
        return None, "Missing frontmatter opening delimiter (---)"
    closing = None
    for i, line in enumerate(lines[1:], start=1):
        if line.rstrip() == "---":
            closing = i
            break
    if closing is None:
        return None, "Missing frontmatter closing delimiter (---)"
    return "\n".join(lines[1:closing]), None


def _parse_frontmatter(fm_text: str) -> dict | None:
    """Parse YAML frontmatter text, return dict or None on error."""
    try:
        return yaml.safe_load(fm_text) or {}
    except yaml.YAMLError:
        return None


def _rel(path: Path) -> str:
    """Return a short relative-ish path for display."""
    try:
        return str(path.relative_to(Path.cwd()))
    except ValueError:
        return str(path)


def _plugin_name(skill_path: Path) -> str:
    """Extract plugin name from a skill path like rh-sre/skills/cve-impact/SKILL.md."""
    if skill_path.parent.parent.name == "skills":
        return str(skill_path.parent.parent.parent)
    return str(skill_path.parent)


# ── Per-skill validation ─────────────────────────────────────────────────────

def validate_skill(skill_path: Path) -> ValidationResult:
    """Run all Tier 1 (agentskills.io) checks on a single skill."""
    result = ValidationResult()
    skill_dir = skill_path.parent
    dir_name = skill_dir.name
    content = skill_path.read_text(encoding="utf-8")

    # 1. Frontmatter delimiters
    fm_text, fm_err = _extract_frontmatter(content)
    if fm_err:
        result.errors.append(fm_err)
        return result  # can't continue without frontmatter

    fm = _parse_frontmatter(fm_text)
    if fm is None:
        result.errors.append("Invalid YAML in frontmatter")
        return result

    # 2. name field
    name = fm.get("name")
    if not name or not isinstance(name, str):
        result.errors.append("Missing required field: name")
        return result

    name = name.strip()
    name_len = len(name)
    if name_len < 1 or name_len > MAX_NAME_LEN:
        result.errors.append(
            f"Name length must be 1-{MAX_NAME_LEN} chars (got {name_len})"
        )
        return result

    if not NAME_PATTERN.match(name):
        if name.startswith("-"):
            result.errors.append(f"Name cannot start with hyphen: {name}")
        elif name.endswith("-"):
            result.errors.append(f"Name cannot end with hyphen: {name}")
        elif "--" in name:
            result.errors.append(f"Name cannot contain consecutive hyphens: {name}")
        elif any(c.isupper() for c in name):
            result.errors.append(f"Name must be lowercase: {name}")
        elif "_" in name:
            result.errors.append(f"Name cannot contain underscores (use hyphens): {name}")
        else:
            result.errors.append(
                f"Name must match pattern ^[a-z][a-z0-9]*(-[a-z0-9]+)*$: {name}"
            )
        return result

    # name must match directory
    if name != dir_name:
        result.errors.append(
            f"Name '{name}' does not match directory name '{dir_name}'"
        )
        return result

    # 3. description field
    desc_raw = fm.get("description")
    if not desc_raw:
        result.errors.append("Missing required field: description")
        return result

    desc = str(desc_raw).strip()
    desc_len = len(desc)
    if desc_len < 1:
        result.errors.append("Description cannot be empty")
        return result
    if desc_len > MAX_DESCRIPTION_LEN:
        result.errors.append(
            f"Description exceeds {MAX_DESCRIPTION_LEN} chars (got {desc_len})"
        )
        return result

    # 4. license field
    license_val = fm.get("license")
    if not license_val:
        result.errors.append("Missing required field: license (must be 'Apache-2.0')")
        return result
    if str(license_val).strip() != "Apache-2.0":
        result.errors.append(
            f"License must be 'Apache-2.0' (got '{license_val}')"
        )
        return result

    # 5. compatibility (optional, ≤500 chars)
    compat = fm.get("compatibility")
    if compat:
        compat_len = len(str(compat).strip())
        if compat_len > MAX_COMPATIBILITY_LEN:
            result.errors.append(
                f"Compatibility exceeds {MAX_COMPATIBILITY_LEN} chars (got {compat_len})"
            )
            return result

    # 6. allowed-tools format
    allowed_tools = fm.get("allowed-tools")
    if allowed_tools is not None:
        if isinstance(allowed_tools, list):
            result.errors.append(
                "allowed-tools must be space-delimited, not YAML array"
            )
        else:
            tools_str = str(allowed_tools)
            if "," in tools_str:
                result.errors.append(
                    f"allowed-tools must be space-delimited, not comma-separated: {tools_str}"
                )
            elif "[" in tools_str or "]" in tools_str:
                result.errors.append(
                    f"allowed-tools must be space-delimited, not array syntax: {tools_str}"
                )

    # 7. Line count
    line_count = len(content.splitlines())
    if line_count > MAX_LINE_COUNT:
        result.errors.append(
            f"Line count exceeds {MAX_LINE_COUNT} (got {line_count})"
        )
        return result

    # 8. Subdirectories
    if skill_dir.is_dir():
        for subdir in sorted(skill_dir.iterdir()):
            if not subdir.is_dir():
                continue
            subdir_name = subdir.name
            if subdir_name in DEPRECATED_SUBDIRS:
                result.warnings.append(
                    f"resources/ is deprecated — use references/, assets/, scripts/ instead"
                )
            elif subdir_name == "docs":
                result.errors.append(
                    "docs/ is not allowed — use references/ and delete docs/ after migration"
                )
            elif subdir_name not in ALLOWED_SUBDIRS:
                result.warnings.append(
                    f"Non-standard subdirectory: {subdir_name} "
                    f"(allowed: {', '.join(sorted(ALLOWED_SUBDIRS))})"
                )

    # 9-10. Content checks outside fenced code blocks
    prose = _strip_fenced_blocks(content)

    if ASCII_ART_PATTERN.search(prose):
        result.warnings.append(
            "ASCII art detected outside code blocks - use plain lists or tables"
        )

    if PERSONA_PATTERN.search(prose):
        result.errors.append(
            "Persona statement detected ('You are a/an/the...') "
            "- use Audience/Goal framing"
        )

    # 11. Description routing keywords
    if not ROUTING_KEYWORDS.search(desc):
        result.warnings.append(
            "Description lacks routing keywords (use when, don't use, not for, triggers on)"
        )

    # 12. Marketing buzzwords
    if MARKETING_BUZZWORDS.search(desc):
        result.warnings.append(
            "Description contains marketing buzzwords - use precise, functional language"
        )

    return result


# ── Main ─────────────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate skills against agentskills.io specification (Tier 1)"
    )
    parser.add_argument(
        "paths",
        nargs="*",
        default=DEFAULT_PLUGINS,
        help="Plugin directories or specific SKILL.md paths to validate",
    )
    parser.add_argument(
        "--warnings-as-errors",
        action="store_true",
        help="Treat warnings as errors",
    )
    args = parser.parse_args()

    # Resolve paths to skill files
    skill_files: list[Path] = []
    for p in args.paths:
        path = Path(p)
        if path.is_file() and path.name == "SKILL.md":
            skill_files.append(path)
        elif path.is_dir():
            skills_dir = path / "skills"
            if skills_dir.exists():
                skill_files.extend(sorted(skills_dir.glob("*/SKILL.md")))

    if not skill_files:
        print("No SKILL.md files found to validate.")
        return 0

    print(SEPARATOR)
    print(f"{BOLD}  agentskills.io Specification Validator (Tier 1){NC}")
    print(SEPARATOR)
    print()

    all_errors: list[tuple[Path, str]] = []
    all_warnings: list[tuple[Path, str]] = []

    # Validate and group results by plugin
    results_by_plugin: dict[str, list[tuple[Path, ValidationResult]]] = {}
    for skill_path in sorted(skill_files):
        r = validate_skill(skill_path)
        plugin = _plugin_name(skill_path)
        results_by_plugin.setdefault(plugin, []).append((skill_path, r))

        for err in r.errors:
            all_errors.append((skill_path, err))
        for warn in r.warnings:
            all_warnings.append((skill_path, warn))
            if args.warnings_as_errors:
                all_errors.append((skill_path, f"[WARN] {warn}"))

    # Print results grouped by plugin
    total_skills = 0
    passed_skills = 0
    warned_skills = 0
    failed_skills = 0

    for plugin, plugin_results in sorted(results_by_plugin.items()):
        print(SEPARATOR)
        print(f"{BOLD}  Plugin: {plugin}{NC}")
        print(SEPARATOR)

        for skill_path, r in plugin_results:
            skill_name = skill_path.parent.name
            total_skills += 1

            if r.errors:
                failed_skills += 1
                print(f"  {RED}❌{NC} {skill_name}")
                for err in r.errors:
                    print(f"     {RED}•{NC} {err}")
                for warn in r.warnings:
                    print(f"     {YELLOW}•{NC} {warn}")
            elif r.warnings:
                warned_skills += 1
                print(f"  {YELLOW}⚠{NC}  {skill_name}")
                for warn in r.warnings:
                    print(f"     {YELLOW}•{NC} {warn}")
            else:
                passed_skills += 1
                print(f"  {GREEN}✓{NC}  {skill_name}")

        print()

    # Summary
    print(SEPARATOR)
    print(f"{BOLD}  Summary{NC}")
    print(SEPARATOR)
    print(f"  Total skills:  {total_skills}")
    print(f"  {GREEN}✓{NC}  Passed:     {passed_skills}")
    print(f"  {YELLOW}⚠{NC}  Warnings:   {warned_skills}")
    print(f"  {RED}❌{NC} Failed:     {failed_skills}")
    print(SEPARATOR)

    if all_errors or (args.warnings_as_errors and all_warnings):
        print(f"{RED}{BOLD}❌ Validation failed{NC}")
        return 1

    if all_warnings:
        print(f"{GREEN}{BOLD}✅ Validation passed{NC} {YELLOW}(with warnings){NC}")
    else:
        print(f"{GREEN}{BOLD}✅ All skills validated successfully{NC}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
