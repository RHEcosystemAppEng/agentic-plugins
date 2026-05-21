#!/usr/bin/env python3
"""
Validate an external repository for federation into Red Hat Agentic Collections.

Automates the mechanical checks from docs/FEDERATION_REVIEW_GUIDE.md:
  1. Clone at pinned ref
  2. Verify Lola pack structure
  3. Tier 1 validation (agentskills.io spec)
  4. Tier 2 validation (design principles)
  5. MCP version pinning (no :latest)
  6. Credential leak scan (gitleaks)

Usage:
    python scripts/validate_federation.py <repo-url> <ref> [--pack-path <path>] [--skills skill1 skill2]
    python scripts/validate_federation.py <repo-url> <ref> --json

Examples:
    # Validate entire pack at repo root
    python scripts/validate_federation.py https://github.com/org/repo v1.0.0

    # Pack lives in a subdirectory
    python scripts/validate_federation.py https://github.com/org/repo v1.0.0 --pack-path my-pack

    # Validate only specific skills
    python scripts/validate_federation.py https://github.com/org/repo abc123 --skills sdn-diagnostics ovn-trace
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field, asdict
from pathlib import Path


REQUIRED_FILES = ["CLAUDE.md", "README.md", "mcps.json"]
REQUIRED_DIRS = ["skills"]
REPO_ROOT = Path(__file__).resolve().parent.parent


@dataclass
class CheckResult:
    name: str
    passed: bool = False
    skipped: bool = False
    details: list[str] = field(default_factory=list)


@dataclass
class ValidationReport:
    repository: str
    ref: str
    checks: list[CheckResult] = field(default_factory=list)

    @property
    def all_passed(self) -> bool:
        return all(c.passed for c in self.checks)


def clone_at_ref(repo_url: str, ref: str, dest: Path) -> CheckResult:
    check = CheckResult(name="clone")
    try:
        subprocess.run(
            ["git", "clone", "--quiet", "--no-checkout", repo_url, str(dest)],
            check=True, capture_output=True, text=True, timeout=120,
        )
        subprocess.run(
            ["git", "checkout", "--quiet", ref],
            check=True, capture_output=True, text=True, cwd=dest, timeout=30,
        )
        check.passed = True
        check.details.append(f"Cloned and checked out {ref}")
    except subprocess.CalledProcessError as exc:
        check.passed = False
        check.details.append(exc.stderr.strip() or str(exc))
    except subprocess.TimeoutExpired:
        check.passed = False
        check.details.append("Git operation timed out")
    return check


def check_lola_structure(pack_dir: Path) -> CheckResult:
    check = CheckResult(name="lola_structure")
    missing = []
    for f in REQUIRED_FILES:
        if not (pack_dir / f).exists():
            missing.append(f)
    for d in REQUIRED_DIRS:
        if not (pack_dir / d).is_dir():
            missing.append(f"{d}/")

    skills = list((pack_dir / "skills").glob("*/SKILL.md")) if (pack_dir / "skills").is_dir() else []

    if missing:
        check.passed = False
        check.details.append(f"Missing: {', '.join(missing)}")
    elif not skills:
        check.passed = False
        check.details.append("No skills found in skills/")
    else:
        check.passed = True
        check.details.append(f"Structure valid: {len(skills)} skill(s) found")
    return check


def run_tier1(pack_dir: Path, skill_subset: list[str] | None = None) -> CheckResult:
    check = CheckResult(name="tier1_agentskills")
    linter = REPO_ROOT / ".claude" / "skills" / "skill-linter" / "scripts" / "validate-skill.sh"
    if not linter.exists():
        check.passed = False
        check.details.append("Linter script not found in agentic-collections repo")
        return check

    skills_dir = pack_dir / "skills"
    if skill_subset:
        skill_dirs = [skills_dir / s for s in skill_subset]
    else:
        skill_dirs = sorted(d for d in skills_dir.iterdir() if d.is_dir() and (d / "SKILL.md").exists())

    if not skill_dirs:
        check.passed = False
        check.details.append("No skills to validate")
        return check

    passed = 0
    failed = 0
    for sd in skill_dirs:
        if not (sd / "SKILL.md").exists():
            check.details.append(f"FAIL {sd.name}: SKILL.md not found")
            failed += 1
            continue
        try:
            result = subprocess.run(
                [str(linter), str(sd)],
                capture_output=True, text=True, timeout=30,
            )
            if result.returncode == 0:
                passed += 1
                if "[WARN]" in result.stdout:
                    check.details.append(f"WARN {sd.name}: passed with warnings")
                else:
                    check.details.append(f"PASS {sd.name}")
            else:
                failed += 1
                check.details.append(f"FAIL {sd.name}: linter errors")
        except subprocess.TimeoutExpired:
            failed += 1
            check.details.append(f"FAIL {sd.name}: timed out")

    check.passed = failed == 0
    check.details.insert(0, f"{passed}/{passed + failed} skills passed Tier 1")
    return check


def run_tier2(pack_dir: Path) -> CheckResult:
    check = CheckResult(name="tier2_design_principles")
    validator = REPO_ROOT / "scripts" / "validate_skill_design.py"
    if not validator.exists():
        check.passed = False
        check.details.append("Design validator not found")
        return check

    try:
        result = subprocess.run(
            [sys.executable, str(validator), str(pack_dir)],
            capture_output=True, text=True, timeout=60,
        )
        if result.returncode == 0:
            check.passed = True
            check.details.append("All skills passed Tier 2")
        else:
            check.passed = False
            for line in result.stdout.strip().splitlines():
                if line.strip() and ("❌" in line or "•" in line):
                    check.details.append(line.strip())
            if not check.details:
                check.details.append("Tier 2 validation failed (see output above)")
    except subprocess.TimeoutExpired:
        check.passed = False
        check.details.append("Validation timed out")
    return check


def check_mcp_pinning(pack_dir: Path) -> CheckResult:
    check = CheckResult(name="mcp_version_pinning")
    mcps_file = pack_dir / "mcps.json"

    if not mcps_file.exists():
        check.passed = True
        check.details.append("No mcps.json found (no MCP servers)")
        return check

    try:
        with open(mcps_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError) as exc:
        check.passed = False
        check.details.append(f"Failed to parse mcps.json: {exc}")
        return check

    servers = data.get("mcpServers", {})
    if not servers:
        check.passed = True
        check.details.append("mcps.json has no servers configured")
        return check

    latest_found = []
    hardcoded_creds = []

    for name, srv in servers.items():
        args_str = " ".join(srv.get("args", []))
        if ":latest" in args_str:
            latest_found.append(name)

        for k, v in srv.get("env", {}).items():
            if isinstance(v, str) and v.strip() and not v.startswith("${"):
                hardcoded_creds.append(f"{name}.env.{k}")

    if latest_found:
        check.details.append(f":latest found in: {', '.join(latest_found)}")
    if hardcoded_creds:
        check.details.append(f"Hardcoded credentials in: {', '.join(hardcoded_creds)}")

    check.passed = not latest_found and not hardcoded_creds
    if check.passed:
        check.details.append(f"{len(servers)} server(s) checked: all versions pinned, no hardcoded credentials")
    return check


def run_gitleaks(pack_dir: Path) -> CheckResult:
    check = CheckResult(name="gitleaks")
    if not shutil.which("gitleaks"):
        check.passed = True
        check.skipped = True
        check.details.append("gitleaks not installed — SKIPPED (install for full scan)")
        return check

    try:
        result = subprocess.run(
            ["gitleaks", "detect", "--source", str(pack_dir), "--no-git", "--quiet"],
            capture_output=True, text=True, timeout=60,
        )
        if result.returncode == 0:
            check.passed = True
            check.details.append("No secrets detected")
        else:
            check.passed = False
            check.details.append("Potential secrets detected")
            for line in result.stdout.strip().splitlines()[:10]:
                check.details.append(f"  {line}")
    except subprocess.TimeoutExpired:
        check.passed = False
        check.details.append("gitleaks timed out")
    return check


def print_report(report: ValidationReport) -> None:
    print()
    print("=" * 60)
    print("Federation Validation Report")
    print(f"  Repository: {report.repository}")
    print(f"  Ref:        {report.ref}")
    print("=" * 60)

    for c in report.checks:
        if c.skipped:
            status = "SKIP"
            icon = "⚠️"
        elif c.passed:
            status = "PASS"
            icon = "✅"
        else:
            status = "FAIL"
            icon = "❌"
        print(f"\n{icon} [{status}] {c.name}")
        for d in c.details:
            print(f"    {d}")

    print()
    print("=" * 60)
    if report.all_passed:
        print("✅ ALL CHECKS PASSED — ready for federation approval")
    else:
        failed = [c.name for c in report.checks if not c.passed]
        print(f"❌ FAILED CHECKS: {', '.join(failed)}")
    print("=" * 60)
    print()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate an external repo for federation"
    )
    parser.add_argument("repo_url", help="Public repository URL")
    parser.add_argument("ref", help="Commit SHA or release tag")
    parser.add_argument("--pack-path", default=".", help="Path to the pack within the repo (default: repo root)")
    parser.add_argument("--skills", nargs="*", help="Validate only these skills (by directory name)")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--keep-clone", action="store_true", help="Don't delete the cloned repo after validation")
    args = parser.parse_args()

    report = ValidationReport(repository=args.repo_url, ref=args.ref)
    tmp = Path(tempfile.mkdtemp(prefix="federation-review-"))

    try:
        # Step 1: Clone
        clone_result = clone_at_ref(args.repo_url, args.ref, tmp / "repo")
        report.checks.append(clone_result)
        if not clone_result.passed:
            if args.json:
                print(json.dumps(asdict(report), indent=2))
            else:
                print_report(report)
            return 1

        pack_dir = tmp / "repo" / args.pack_path

        # Step 2: Lola structure
        report.checks.append(check_lola_structure(pack_dir))

        # Step 3: Tier 1
        report.checks.append(run_tier1(pack_dir, args.skills))

        # Step 4: Tier 2
        report.checks.append(run_tier2(pack_dir))

        # Step 5: MCP pinning
        report.checks.append(check_mcp_pinning(pack_dir))

        # Step 6: Gitleaks
        report.checks.append(run_gitleaks(pack_dir))

    finally:
        if not args.keep_clone:
            shutil.rmtree(tmp, ignore_errors=True)
        else:
            print(f"Clone kept at: {tmp / 'repo'}")

    if args.json:
        print(json.dumps(asdict(report), indent=2))
    else:
        print_report(report)

    return 0 if report.all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
