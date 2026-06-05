#!/usr/bin/env python3
"""
Cross-check federation catalog artifacts against the linked external pack at a pinned ref.

Validates that federation/modules/<name>/.catalog/ in agentic-collections matches the
skills and marketplace metadata of the external repository declared in
marketplace/rh-agentic-collection.yml.

Usage:
    uv run python scripts/validate_federation_catalog.py \\
      --module-name claude-code-setup \\
      --repo-url https://github.com/org/repo \\
      --ref <40-char-sha> \\
      --pack-path plugins/claude-code-setup \\
      [--module-json '<marketplace-module-json>'] \\
      [--json]
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import tempfile
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import collection_validate_lib as cvl
import pack_registry

REPO_ROOT = Path(__file__).resolve().parent.parent


@dataclass
class CheckResult:
    name: str
    passed: bool = False
    skipped: bool = False
    details: list[str] = field(default_factory=list)


@dataclass
class CatalogReport:
    module_name: str
    repository: str
    ref: str
    checks: list[CheckResult] = field(default_factory=list)

    @property
    def all_passed(self) -> bool:
        return all(c.passed for c in self.checks)


def _norm_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip().lower())


def _token_set(text: str) -> Set[str]:
    return {t for t in re.findall(r"[a-z0-9]+", _norm_text(text)) if len(t) > 2}


def _descriptions_align(a: str, b: str) -> bool:
    na, nb = _norm_text(a), _norm_text(b)
    if not na or not nb:
        return True
    if na in nb or nb in na:
        return True
    ta, tb = _token_set(a), _token_set(b)
    if not ta or not tb:
        return True
    overlap = len(ta & tb) / min(len(ta), len(tb))
    return overlap >= 0.5


def federation_catalog_dir(module_name: str, repo_root: Optional[Path] = None) -> str:
    return f"federation/modules/{module_name}"


def check_catalog_present(module_name: str, repo_root: Optional[Path] = None) -> CheckResult:
    check = CheckResult(name="catalog_present")
    root = repo_root or REPO_ROOT
    cat_dir = federation_catalog_dir(module_name)
    cat_yaml = root / cat_dir / ".catalog" / "collection.yaml"
    if not cat_yaml.is_file():
        check.details.append(f"Missing {cat_yaml.relative_to(root)}")
        return check
    check.passed = True
    check.details.append(f"Found {cat_yaml.relative_to(root)}")
    return check


def check_catalog_compliance(module_name: str, repo_root: Optional[Path] = None) -> CheckResult:
    check = CheckResult(name="catalog_compliance")
    cat_dir = federation_catalog_dir(module_name)
    errs = cvl.validate_pack_iteration5(cat_dir, repo_root, is_federated=True)
    if errs:
        check.details.extend(errs[:20])
        if len(errs) > 20:
            check.details.append(f"... and {len(errs) - 20} more")
        return check
    check.passed = True
    check.details.append("collection.yaml passes schema, fragments, and JSON mirror checks")
    return check


def check_external_skill_roster(
    module_name: str,
    external_pack_root: Path,
    skill_subset: Optional[List[str]] = None,
    repo_root: Optional[Path] = None,
) -> CheckResult:
    check = CheckResult(name="external_skill_roster")
    root = repo_root or REPO_ROOT
    cat_dir = federation_catalog_dir(module_name)
    data, errs = cvl.read_yaml_catalog(cat_dir, root)
    if errs or data is None:
        check.details.extend(errs)
        return check

    external = set(cvl.list_external_pack_skill_names(external_pack_root, skill_subset))
    yaml_path = root / cat_dir / ".catalog" / "collection.yaml"
    roster_errs = cvl.validate_external_skill_roster(
        cat_dir, data, external, yaml_path=yaml_path, root=root,
    )
    if roster_errs:
        check.details.extend(roster_errs)
        return check

    check.passed = True
    check.details.append(
        f"Catalog roster matches external pack ({len(external)} skill(s) at ref)"
    )
    return check


def check_plugins_json_title(module_name: str, repo_root: Optional[Path] = None) -> CheckResult:
    check = CheckResult(name="plugins_json_title")
    root = repo_root or REPO_ROOT
    plugins_path = root / "docs" / "plugins.json"
    cat_dir = federation_catalog_dir(module_name)

    if not plugins_path.is_file():
        check.details.append("Missing docs/plugins.json")
        return check

    data, errs = cvl.read_yaml_catalog(cat_dir, root)
    if errs or data is None:
        check.details.extend(errs)
        return check

    try:
        plugins = json.loads(plugins_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        check.details.append(f"Invalid docs/plugins.json: {exc}")
        return check

    entry = plugins.get(module_name)
    title = entry.get("title") if isinstance(entry, dict) else None
    if not str(title or "").strip():
        check.details.append(f"docs/plugins.json missing title for {module_name!r}")
        return check

    if data.get("id") != module_name:
        check.details.append(
            f"collection id {data.get('id')!r} must equal module name {module_name!r}"
        )
        return check

    if data.get("name") != title:
        check.details.append(
            f"collection name {data.get('name')!r} must equal plugins.json title {title!r}"
        )
        return check

    check.passed = True
    check.details.append(f"plugins.json title matches catalog name ({title!r})")
    return check


def check_marketplace_catalog_metadata(
    module_name: str,
    module_meta: Dict[str, Any],
    repo_root: Optional[Path] = None,
) -> CheckResult:
    check = CheckResult(name="marketplace_catalog_metadata")
    root = repo_root or REPO_ROOT
    cat_dir = federation_catalog_dir(module_name)
    data, errs = cvl.read_yaml_catalog(cat_dir, root)
    if errs or data is None:
        check.details.extend(errs)
        return check

    mp_version = str(module_meta.get("version") or "").strip()
    cat_version = str(data.get("version") or "").strip()
    if mp_version and cat_version and mp_version != cat_version:
        check.details.append(
            f"marketplace version {mp_version!r} != catalog version {cat_version!r}"
        )
        return check

    mp_desc = _norm_text(module_meta.get("description"))
    cat_desc = _norm_text(data.get("description"))
    if mp_desc and cat_desc and not _descriptions_align(
        str(module_meta.get("description") or ""),
        str(data.get("description") or ""),
    ):
        check.details.append(
            "marketplace description and catalog description appear unrelated "
            f"(marketplace={module_meta.get('description')!r}, catalog={data.get('description')!r})"
        )
        return check

    mp_repo = str(module_meta.get("repository") or "").rstrip("/")
    cat_repo = str(data.get("repository") or "").rstrip("/")
    if mp_repo and cat_repo and mp_repo != cat_repo:
        check.details.append(
            f"marketplace repository {mp_repo!r} != catalog repository {cat_repo!r}"
        )
        return check

    check.passed = True
    check.details.append("Marketplace version, description, and repository align with catalog")
    return check


def run_catalog_validation(
    module_name: str,
    repo_url: str,
    ref: str,
    pack_path: str,
    module_meta: Optional[Dict[str, Any]] = None,
    repo_root: Optional[Path] = None,
    external_pack_root: Optional[Path] = None,
    cleanup_clone: bool = True,
) -> CatalogReport:
    from validate_federation import check_federation_ref, clone_at_ref

    root = repo_root or REPO_ROOT
    report = CatalogReport(module_name=module_name, repository=repo_url, ref=ref)

    present = check_catalog_present(module_name, root)
    report.checks.append(present)
    if not present.passed:
        return report

    ref_check = check_federation_ref(ref)
    report.checks.append(ref_check)
    if not ref_check.passed:
        return report

    tmp: Optional[Path] = None
    pack_root = external_pack_root
    if pack_root is None:
        tmp = Path(tempfile.mkdtemp(prefix="federation-catalog-"))
        clone = clone_at_ref(repo_url, ref, tmp / "repo")
        report.checks.append(clone)
        if not clone.passed:
            if cleanup_clone and tmp:
                shutil.rmtree(tmp, ignore_errors=True)
            return report
        pack_root = tmp / "repo" / pack_path

    if not (pack_root / "skills").is_dir():
        fail = CheckResult(name="external_pack_path")
        fail.details.append(f"No skills/ directory at external pack path {pack_path!r}")
        report.checks.append(fail)
        if cleanup_clone and tmp:
            shutil.rmtree(tmp, ignore_errors=True)
        return report

    skill_subset = None
    if module_meta and module_meta.get("skills"):
        skill_subset = module_meta.get("skills")

    report.checks.append(check_catalog_compliance(module_name, root))
    report.checks.append(
        check_external_skill_roster(module_name, pack_root, skill_subset, root)
    )
    report.checks.append(check_plugins_json_title(module_name, root))
    if module_meta:
        report.checks.append(check_marketplace_catalog_metadata(module_name, module_meta, root))

    if cleanup_clone and tmp:
        shutil.rmtree(tmp, ignore_errors=True)

    return report


def print_report(report: CatalogReport) -> None:
    print()
    print("=" * 60)
    print("Federation Catalog Cross-Check")
    print(f"  Module:     {report.module_name}")
    print(f"  Repository: {report.repository}")
    print(f"  Ref:        {report.ref or '(missing)'}")
    print("=" * 60)

    for c in report.checks:
        if c.skipped:
            status, icon = "SKIP", "⚠️"
        elif c.passed:
            status, icon = "PASS", "✅"
        else:
            status, icon = "FAIL", "❌"
        print(f"\n{icon} [{status}] {c.name}")
        for d in c.details:
            print(f"    {d}")

    print()
    print("=" * 60)
    if report.all_passed:
        print("✅ CATALOG CROSS-CHECK PASSED")
    else:
        failed = [c.name for c in report.checks if not c.passed]
        print(f"❌ FAILED CHECKS: {', '.join(failed)}")
    print("=" * 60)
    print()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Cross-check federation catalog against external pack at pinned ref"
    )
    parser.add_argument("--module-name", required=True, help="Federated module name (marketplace name)")
    parser.add_argument("--repo-url", required=True, help="External repository URL")
    parser.add_argument("--ref", required=True, help="40-character commit SHA")
    parser.add_argument("--pack-path", default=".", help="Path to pack within external repo")
    parser.add_argument("--module-json", default=None, help="Marketplace module entry as JSON")
    parser.add_argument("--json", action="store_true", help="Output report as JSON")
    args = parser.parse_args()

    module_meta = json.loads(args.module_json) if args.module_json else None
    report = run_catalog_validation(
        module_name=args.module_name,
        repo_url=args.repo_url,
        ref=args.ref,
        pack_path=args.pack_path,
        module_meta=module_meta,
    )

    if args.json:
        print(json.dumps(asdict(report), indent=2))
    else:
        print_report(report)

    return 0 if report.all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
