#!/usr/bin/env python3
"""
Validate Compass component lifecycle rules.

Enforces (APPENG-6307 and lifecycle formalization):

  - Allowed ``spec.lifecycle`` values:
    development, beta, GA, deprecated, archived.
  - Maturity order for the ceiling rule:
    development (0) < beta (1) < GA (2).
    ``production`` is not accepted; use ``GA``.
  - Ceiling: a child skill cannot be more mature than its parent plugin.
  - Missing lifecycles default to "development" for ceiling comparison.
  - ``deprecated`` and ``archived`` entities are exempt from the ceiling.
  - Non-blocking warning when ``distribution: external`` is paired with
    ``lifecycle: development`` (development is never published externally).

Packs are discovered from the root ``catalog-info.yaml`` ``spec.targets``
(the same set Compass ingests), mirroring ``validate_compass_manifests.py``.
See ``LIFECYCLE.md`` for the canonical lifecycle model.
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

_REPO_ROOT = Path(__file__).resolve().parent.parent

# Canonical lifecycle values (exact spellings used in manifests).
ALLOWED_LIFECYCLES = ("development", "beta", "GA", "deprecated", "archived")
_ALLOWED_BY_LOWER = {value.lower(): value for value in ALLOWED_LIFECYCLES}

# Maturity order for ceiling: development < beta < GA.
LIFECYCLE_RANK = {"development": 0, "beta": 1, "GA": 2}
DEFAULT_LIFECYCLE = "development"
CEILING_EXEMPT_LIFECYCLES = frozenset({"deprecated", "archived"})


def _load_yaml(path: Path) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected mapping at top level")
    return data


def canonicalize_lifecycle(lifecycle: str | None) -> str | None:
    """
    Map a lifecycle string to its canonical form, or None if empty/missing.

    Matching is case-insensitive so ``ga`` / ``GA`` both become ``GA``.
    Unknown values are returned stripped but not rewritten.
    """
    if lifecycle is None:
        return None
    value = str(lifecycle).strip()
    if not value:
        return None
    return _ALLOWED_BY_LOWER.get(value.lower(), value)


def normalize_lifecycle(lifecycle: str | None) -> str:
    """Return the effective lifecycle string, defaulting missing values to development."""
    canonical = canonicalize_lifecycle(lifecycle)
    return canonical if canonical is not None else DEFAULT_LIFECYCLE


def is_allowed_lifecycle(lifecycle: str | None) -> bool:
    """Return True when lifecycle is missing (defaults) or a known allowed value."""
    canonical = canonicalize_lifecycle(lifecycle)
    if canonical is None:
        return True
    return canonical in ALLOWED_LIFECYCLES


def is_ceiling_exempt(lifecycle: str | None) -> bool:
    """Return True when the lifecycle is deprecated or archived (ceiling skipped)."""
    return normalize_lifecycle(lifecycle) in CEILING_EXEMPT_LIFECYCLES


def is_deprecated(lifecycle: str | None) -> bool:
    """Return True when the (normalized) lifecycle is 'deprecated'."""
    return normalize_lifecycle(lifecycle) == "deprecated"


def lifecycle_rank(lifecycle: str | None) -> int:
    """Map a lifecycle string to its maturity rank (missing -> development)."""
    value = normalize_lifecycle(lifecycle)
    if value not in LIFECYCLE_RANK:
        allowed = ", ".join(ALLOWED_LIFECYCLES)
        raise ValueError(
            f"unknown lifecycle '{lifecycle}'; expected one of: {allowed}"
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


def _mcp_manifests(root: Path) -> list[Path]:
    mcps_catalog = root / "mcps" / "catalog-info.yaml"
    if not mcps_catalog.is_file():
        return []
    try:
        data = _load_yaml(mcps_catalog)
    except (OSError, ValueError, yaml.YAMLError):
        return []
    manifests: list[Path] = []
    mcps_dir = root / "mcps"
    for target in data.get("spec", {}).get("targets", []):
        if not isinstance(target, str):
            continue
        path = (mcps_dir / target).resolve()
        if path.is_file():
            manifests.append(path)
    return manifests


def iter_component_manifests(root: Path) -> list[Path]:
    """Return plugin, skill, and MCP manifests for registered packs + mcps Location."""
    paths: list[Path] = []
    for pack in registered_packs(root):
        pack_dir = root / pack
        plugin_path = pack_dir / f"{pack}-plugin.yaml"
        if plugin_path.is_file():
            paths.append(plugin_path)
        paths.extend(_skill_manifests(pack_dir))
    paths.extend(_mcp_manifests(root))
    return paths


def _distribution_label(data: dict) -> str | None:
    labels = data.get("metadata", {}).get("labels") or {}
    if not isinstance(labels, dict):
        return None
    value = labels.get("distribution")
    if value is None:
        return None
    return str(value).strip() or None


def check_allowed_lifecycles(root: Path, errors: list[str], warnings: list[str]) -> None:
    """Reject unknown lifecycle values; warn on external + development."""
    allowed = ", ".join(ALLOWED_LIFECYCLES)
    for manifest in iter_component_manifests(root):
        try:
            data = _load_yaml(manifest)
        except (OSError, ValueError, yaml.YAMLError) as exc:
            errors.append(f"{manifest.relative_to(root)}: failed to load ({exc})")
            continue

        raw_lifecycle = data.get("spec", {}).get("lifecycle")
        if raw_lifecycle is not None and str(raw_lifecycle).strip() != "":
            if not is_allowed_lifecycle(raw_lifecycle):
                errors.append(
                    f"{manifest.relative_to(root)}: invalid lifecycle "
                    f"'{raw_lifecycle}'; expected one of: {allowed}"
                )
                continue

        effective = normalize_lifecycle(raw_lifecycle)
        if effective == "development" and _distribution_label(data) == "external":
            name = data.get("metadata", {}).get("name", manifest.name)
            warnings.append(
                f"{manifest.relative_to(root)}: component '{name}' has "
                f"distribution: external with lifecycle: development — "
                f"it will not be published externally"
            )


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

    raw_plugin_lifecycle = plugin_data.get("spec", {}).get("lifecycle")
    # Invalid values are reported by check_allowed_lifecycles; skip ceiling here.
    if not is_allowed_lifecycle(raw_plugin_lifecycle):
        return

    plugin_lifecycle = normalize_lifecycle(raw_plugin_lifecycle)
    if is_ceiling_exempt(plugin_lifecycle):
        # Retired plugins are exempt — none of their skills are enforced either.
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
        raw_skill_lifecycle = skill_data.get("spec", {}).get("lifecycle")
        if not is_allowed_lifecycle(raw_skill_lifecycle):
            continue  # reported by check_allowed_lifecycles

        skill_lifecycle = normalize_lifecycle(raw_skill_lifecycle)

        if is_ceiling_exempt(skill_lifecycle):
            continue  # retired skills are exempt from the ceiling check

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


def validate_all(root: Path) -> tuple[list[str], list[str]]:
    """
    Run lifecycle validation for registered packs and MCP manifests.

    Returns (errors, warnings). Warnings are non-blocking.
    """
    errors: list[str] = []
    warnings: list[str] = []
    root_catalog = root / "catalog-info.yaml"
    if not root_catalog.is_file():
        errors.append(f"missing root catalog Location: {root_catalog}")
        return errors, warnings

    check_allowed_lifecycles(root, errors, warnings)
    for pack in registered_packs(root):
        check_pack(root, pack, errors)
    return errors, warnings


def main() -> int:
    errors, warnings = validate_all(_REPO_ROOT)

    if warnings:
        print("Lifecycle validation warnings:")
        for warn in warnings:
            print(f"  ⚠ {warn}")

    if errors:
        print("Lifecycle validation failed:", file=sys.stderr)
        for err in errors:
            print(f"  • {err}", file=sys.stderr)
        return 1

    print("✓ Lifecycle validation passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
