#!/usr/bin/env python3
"""Run validate_federation_catalog.py for every federated module with a local catalog."""

from __future__ import annotations

import sys
from pathlib import Path

import pack_registry
from validate_federation_catalog import print_report, run_catalog_validation

REPO_ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    modules = pack_registry.load_federated_modules()
    if not modules:
        print("No federated modules configured in marketplace YAML.")
        return 0

    failed = False
    for mod in modules:
        name = mod.get("name", "")
        repository = mod.get("repository", "")
        ref = mod.get("ref", "")
        pack_path = mod.get("path", ".")
        cat_dir = REPO_ROOT / "federation" / "modules" / name / ".catalog" / "collection.yaml"
        if not cat_dir.is_file():
            print(f"Skipping {name}: no federation catalog at {cat_dir.relative_to(REPO_ROOT)}")
            continue

        ref_err = pack_registry.federation_ref_error(ref)
        if ref_err:
            print(f"FAIL {name}: {ref_err}")
            failed = True
            continue

        print(f"\n--- Catalog cross-check: {name} ---")
        report = run_catalog_validation(
            module_name=name,
            repo_url=repository,
            ref=ref,
            pack_path=pack_path,
            module_meta=mod,
            repo_root=REPO_ROOT,
        )
        print_report(report)
        if not report.all_passed:
            failed = True

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
