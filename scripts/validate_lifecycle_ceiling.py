#!/usr/bin/env python3
"""
Validate the Compass "lifecycle ceiling" rule.

By design, a child skill cannot have a more mature ``spec.lifecycle`` than
its parent plugin (pack). This script enforces that rule in CI:

  - The allowed lifecycle order is: development (0) < beta (1) < production (2).
  - Missing lifecycles default to "development".
  - Entities with lifecycle "deprecated" (skills or plugins) are skipped —
    they are not compared against the ceiling.
  - Packs are discovered from the root ``catalog-info.yaml`` ``spec.targets``
    (the same set Compass ingests), mirroring ``validate_compass_manifests.py``.
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

_REPO_ROOT = Path(__file__).resolve().parent.parent

# Allowed lifecycle maturity order: development < beta < production.
LIFECYCLE_RANK = {"development": 0, "beta": 1, "production": 2}
DEFAULT_LIFECYCLE = "development"
DEPRECATED_LIFECYCLE = "deprecated"


def _load_yaml(path: Path) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected mapping at top level")
    return data


def normalize_lifecycle(lifecycle: str | None) -> str:
    """Return the effective lifecycle string, defaulting missing values to development."""
    if lifecycle is None:
        return DEFAULT_LIFECYCLE
    value = str(lifecycle).strip().lower()
    return value or DEFAULT_LIFECYCLE


def is_deprecated(lifecycle: str | None) -> bool:
    """Return True when the (normalized) lifecycle is 'deprecated'."""
    return normalize_lifecycle(lifecycle) == DEPRECATED_LIFECYCLE


def lifecycle_rank(lifecycle: str | None) -> int:
    """Map a lifecycle string to its maturity rank (missing -> development)."""
    value = normalize_lifecycle(lifecycle)
    if value not in LIFECYCLE_RANK:
        raise ValueError(
            f"unknown lifecycle '{lifecycle}'; expected one of "
            f"{sorted(LIFECYCLE_RANK)} or '{DEPRECATED_LIFECYCLE}'"
        )
    return LIFECYCLE_RANK[value]


def registered_packs(root: Path) -> list[str]:
    """Return pack directory names referenced from the root catalog-info.yaml."""
    root_catalog = root / "catalog-info.yaml"
    data = _load_yaml(root_catalog)
    packs: list[str] = []
    for target in data.get("spec", {}).get("targets", []):
        if not isinstance(target, str):
            continue
        if target.startswith("./mcps/"):
            continue
        if not target.endswith("/catalog-info.yaml"):
            continue
        parts = Path(target).parts
        if len(parts) != 2:
            continue
        packs.append(parts[0])
    return sorted(set(packs))


def _skill_manifests(pack_dir: Path) -> list[Path]:
    skills_dir = pack_dir / "skills"
    if not skills_dir.is_dir():
        return []
    return sorted(skills_dir.glob("*/catalog-info.yaml"))


def check_pack(root: Path, pack: str, errors: list[str]) -> None:
    """Validate the lifecycle ceiling for a single pack (skills vs. their plugin)."""
    pack_dir = root / pack
    plugin_path = pack_dir / f"{pack}-plugin.yaml"
    if not plugin_path.is_file():
        errors.append(f"{pack}: missing plugin manifest {plugin_path.relative_to(root)}")
        return

    try:
        plugin_data = _load_yaml(plugin_path)
    except (OSError, ValueError, yaml.YAMLError) as exc:
        errors.append(f"{plugin_path.relative_to(root)}: failed to load ({exc})")
        return

    plugin_lifecycle = normalize_lifecycle(plugin_data.get("spec", {}).get("lifecycle"))
    if is_deprecated(plugin_lifecycle):
        # Deprecated plugins are exempt — none of their skills are enforced either.
        return

    try:
        plugin_rank = lifecycle_rank(plugin_lifecycle)
    except ValueError as exc:
        errors.append(f"{plugin_path.relative_to(root)}: {exc}")
        return

    for manifest in _skill_manifests(pack_dir):
        try:
            skill_data = _load_yaml(manifest)
        except (OSError, ValueError, yaml.YAMLError) as exc:
            errors.append(f"{manifest.relative_to(root)}: failed to load ({exc})")
            continue

        skill_name = skill_data.get("metadata", {}).get("name", manifest.parent.name)
        skill_lifecycle = normalize_lifecycle(skill_data.get("spec", {}).get("lifecycle"))

        if is_deprecated(skill_lifecycle):
            continue  # deprecated skills are exempt from the ceiling check

        try:
            skill_rank = lifecycle_rank(skill_lifecycle)
        except ValueError as exc:
            errors.append(f"{manifest.relative_to(root)}: {exc}")
            continue

        if skill_rank > plugin_rank:
            errors.append(
                f"{pack}/{skill_name}: lifecycle '{skill_lifecycle}' exceeds parent "
                f"plugin '{pack}' lifecycle '{plugin_lifecycle}' "
                f"({manifest.relative_to(root)})"
            )


def validate_all(root: Path) -> list[str]:
    """Run the lifecycle ceiling check for every pack registered in catalog-info.yaml."""
    errors: list[str] = []
    root_catalog = root / "catalog-info.yaml"
    if not root_catalog.is_file():
        errors.append(f"missing root catalog Location: {root_catalog}")
        return errors

    for pack in registered_packs(root):
        check_pack(root, pack, errors)
    return errors


def main() -> int:
    errors = validate_all(_REPO_ROOT)

    if errors:
        print("Lifecycle ceiling validation failed:", file=sys.stderr)
        for err in errors:
            print(f"  • {err}", file=sys.stderr)
        return 1

    print("✓ Lifecycle ceiling validation passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
