#!/usr/bin/env python3
"""
Fetch and validate skills from federated external repositories.

Identifies federated modules (external repository) in the marketplace YAML
modules list, clones each at its pinned ref, runs Tier 1 validation on
declared skills, and reports results as structured JSON.

Usage:
    python scripts/fetch_federated_skills.py                  # validate all
    python scripts/fetch_federated_skills.py --json           # JSON output
    python scripts/fetch_federated_skills.py --fetch-only     # clone without validating
    python scripts/fetch_federated_skills.py --output-dir /tmp/fed  # custom clone target
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import List, Optional

import pack_registry


@dataclass
class SkillResult:
    path: str
    passed: bool
    warnings: bool = False
    output: str = ""


@dataclass
class ModuleResult:
    name: str
    repository: str
    ref: str
    pack_path: str
    clone_ok: bool = False
    skills: List[SkillResult] = field(default_factory=list)
    error: str = ""
    clone_path: str = ""


def _strip_ansi(text: str) -> str:
    return re.sub(r"\x1b\[[0-9;]*m", "", text)


def format_linter_lines(output: str, marker: str) -> List[str]:
    """Extract linter lines containing marker (e.g. [FAIL], [WARN])."""
    cleaned = _strip_ansi(output)
    return [line.strip() for line in cleaned.splitlines() if marker in line]


def print_skill_validation_details(sr: SkillResult) -> None:
    """Print Tier 1 linter details to the console (human-readable mode)."""
    if sr.passed:
        if sr.warnings:
            for line in format_linter_lines(sr.output, "[WARN]"):
                print(f"      {line}")
        return

    fail_lines = format_linter_lines(sr.output, "[FAIL]")
    if fail_lines:
        for line in fail_lines:
            print(f"      {line}")
        return

    if sr.output.strip():
        for line in _strip_ansi(sr.output).splitlines():
            stripped = line.strip()
            if stripped:
                print(f"      {stripped}")
        return

    print("      (no linter output captured)")


def clone_at_ref(repository: str, ref: str, dest: Path) -> Optional[str]:
    """Clone a repository and checkout a pinned commit SHA. Returns error string or None."""
    err = pack_registry.federation_ref_error(ref)
    if err:
        return err
    sha = pack_registry.normalize_federation_ref(ref)
    try:
        subprocess.run(
            ["git", "clone", "--quiet", "--no-checkout", repository, str(dest)],
            check=True, capture_output=True, text=True, timeout=120,
        )
        subprocess.run(
            ["git", "checkout", "--quiet", sha],
            check=True, capture_output=True, text=True, cwd=dest, timeout=30,
        )
        return None
    except subprocess.CalledProcessError as exc:
        return exc.stderr.strip() or str(exc)
    except subprocess.TimeoutExpired:
        return "git operation timed out"


def validate_skill(skill_dir: Path, repo_root: Path) -> SkillResult:
    """Run the Tier 1 linter on a single skill directory."""
    skill_md = skill_dir / "SKILL.md"
    rel_path = str(skill_dir.relative_to(repo_root))

    if not skill_md.exists():
        return SkillResult(path=rel_path, passed=False, output=f"SKILL.md not found at {rel_path}")

    linter = Path(__file__).resolve().parent.parent / ".claude" / "skills" / "skill-linter" / "scripts" / "validate-skill.sh"
    if not linter.exists():
        return SkillResult(path=rel_path, passed=False, output="Linter script not found")

    try:
        result = subprocess.run(
            [str(linter), str(skill_dir)],
            capture_output=True,
            text=True,
            timeout=30,
        )
        has_warnings = "[WARN]" in result.stdout
        combined = result.stdout
        if result.stderr.strip():
            combined = f"{combined}\n{result.stderr}".strip()
        return SkillResult(
            path=rel_path,
            passed=result.returncode == 0,
            warnings=has_warnings,
            output=combined.strip(),
        )
    except subprocess.TimeoutExpired:
        return SkillResult(path=rel_path, passed=False, output="Linter timed out")


def process_module(
    module: dict,
    base_dir: Path,
    validate: bool = True,
) -> ModuleResult:
    """Clone and optionally validate a single federated module."""
    name = module.get("name", "unknown")
    repository = module.get("repository", "")
    ref = module.get("ref", "")
    pack_path = module.get("path", ".")

    result = ModuleResult(name=name, repository=repository, ref=ref, pack_path=pack_path)

    if not repository:
        result.error = "Missing repository"
        return result

    ref_err = pack_registry.federation_ref_error(ref)
    if ref_err:
        result.error = ref_err
        return result

    clone_dest = base_dir / name
    err = clone_at_ref(repository, ref, clone_dest)
    if err:
        result.error = f"Clone failed: {err}"
        return result

    result.clone_ok = True
    result.clone_path = str(clone_dest)
    pack_root = clone_dest / pack_path

    if not validate:
        return result

    skills_dir = pack_root / "skills"
    skill_dirs = sorted(
        d for d in skills_dir.iterdir()
        if d.is_dir() and (d / "SKILL.md").exists()
    ) if skills_dir.is_dir() else []

    for skill_dir in skill_dirs:
        sr = validate_skill(skill_dir, pack_root)
        result.skills.append(sr)

    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch and validate federated skills")
    parser.add_argument("--json", action="store_true", help="Output results as JSON")
    parser.add_argument("--fetch-only", action="store_true", help="Clone repos without validating")
    parser.add_argument("--output-dir", type=str, help="Directory to clone repos into (default: temp dir)")
    parser.add_argument("--module", type=str, help="Validate only this module name")
    args = parser.parse_args()

    modules = pack_registry.load_federated_modules()
    if not modules:
        if args.json:
            print(json.dumps({"modules": [], "summary": "No federated modules configured"}))
        else:
            print("No federated modules configured in marketplace YAML.")
        return 0

    if args.module:
        modules = [m for m in modules if m.get("name") == args.module]
        if not modules:
            print(f"Module '{args.module}' not found in federated modules", file=sys.stderr)
            return 1

    use_temp = args.output_dir is None
    base_dir = Path(tempfile.mkdtemp(prefix="federated-")) if use_temp else Path(args.output_dir)
    base_dir.mkdir(parents=True, exist_ok=True)

    results: List[ModuleResult] = []
    any_failure = False

    for mod in modules:
        if not args.json:
            print(f"\n{'='*60}")
            print(f"Module: {mod.get('name', '?')}")
            print(f"  Repository: {mod.get('repository', '?')}")
            print(f"  Ref: {mod.get('ref') or '(missing — required 40-character commit SHA)'}")
            print(f"  Pack path: {mod.get('path', '.')}")
            print(f"{'='*60}")

        mr = process_module(mod, base_dir, validate=not args.fetch_only)
        results.append(mr)

        if not args.json:
            if not mr.clone_ok:
                print(f"  CLONE FAILED: {mr.error}")
                any_failure = True
                continue

            print(f"  Cloned to: {mr.clone_path}")

            if args.fetch_only:
                print("  (fetch-only mode, skipping validation)")
                continue

            for sr in mr.skills:
                status = "PASS" if sr.passed else "FAIL"
                warn = " (warnings)" if sr.warnings else ""
                print(f"  [{status}{warn}] {sr.path}")
                if not sr.passed or sr.warnings:
                    print_skill_validation_details(sr)
                if not sr.passed:
                    any_failure = True

        elif mr.error or any(not s.passed for s in mr.skills):
            any_failure = True

    if args.json:
        output = {
            "modules": [asdict(r) for r in results],
            "all_passed": not any_failure,
        }
        print(json.dumps(output, indent=2))

    if use_temp and not args.fetch_only:
        shutil.rmtree(base_dir, ignore_errors=True)

    if not args.json:
        print()
        total_skills = sum(len(r.skills) for r in results)
        passed = sum(1 for r in results for s in r.skills if s.passed)
        failed = sum(1 for r in results for s in r.skills if not s.passed)
        print(f"Summary: {passed}/{total_skills} skills passed, {failed} failed")
        if failed:
            print("See [FAIL] lines above for Tier 1 linter details (or re-run with --json).")

    return 1 if any_failure else 0


if __name__ == "__main__":
    sys.exit(main())
