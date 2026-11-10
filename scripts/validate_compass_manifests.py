#!/usr/bin/env python3
"""
Validate Compass catalog-info.yaml manifests and skill references layout.

Structural checks (no SKILL.md semantic inference):
  - Roster parity: skills on disk vs plugin Location targets vs manifest files
  - Plugin spec.includes / legacy spec.skills dual-write vs disk roster
  - Skill dependsOn plugin (until Phase C H.5 retires that edge)
  - Bidirectional dependsOn/dependencyOf for skill→skill and skill→owned-MCP
  - Plugin→owned-MCP inverse; plugin MCP dependsOn union vs skills
  - Forbidden partOf/hasPart on skill manifests; redundant plugin dependsOn system
  - Dangling airesource refs; canonical mcpserver:redhat/* allowed without local file
  - Basic field conventions on skill manifests (namespace, owner, agents, distribution;
    no plugin-only includes/skills/system)
  - Skill documentation layout (all plugins with skills/):
      no skills/<name>/docs/; no references/references/ nesting;
      no internal docs/ links; symlinks under references/ must not target docs/
  - Skill scripts layout: symlinks into plugin scripts/<group>/ must fan out all
      non-test files in that group; skill docs must not use <plugin>/scripts/ paths
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

import yaml

_REPO_ROOT = Path(__file__).resolve().parent.parent
_ROOT_CATALOG = _REPO_ROOT / "catalog-info.yaml"
_SKILL_TARGET_RE = re.compile(r"^\./skills/([^/]+)/catalog-info\.yaml$")
_PLUGIN_REF = "airesource:ai5-marketplace/{plugin}"
_FORBIDDEN_RELATION_RE = re.compile(r"^\s+(partOf|hasPart)\s*:", re.MULTILINE)
_CANONICAL_MCP_PREFIXES = ("mcpserver:redhat/", "mcpserver:default/")
_EXPECTED_OWNER = "group:redhat/ai5-marketplace"
_EXPECTED_NAMESPACE = "ai5-marketplace"
_ALLOWED_INCLUDE_TYPES = frozenset({"skill", "mcp-server"})
_PLUGIN_ONLY_SKILL_SPEC_KEYS = ("includes", "skills", "system")
_MD_LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
_SKILL_DOCS_STANDARD = "https://agent-plugins.org/specification"
_SHARED_SCRIPT_SYMLINK_RE = re.compile(
    r"^(?:\.\./)+scripts/([^/]+)/(.+)$"
)
_TEST_SCRIPT_RE = re.compile(r"^test_.*\.py$")


def _load_yaml(path: Path) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected mapping at top level")
    return data


def _refs(spec: dict, key: str) -> list[str]:
    value = spec.get(key) or []
    if not isinstance(value, list):
        return []
    return [str(item) for item in value]


def all_plugins_with_skills() -> list[str]:
    plugins: list[str] = []
    for entry in sorted(_REPO_ROOT.iterdir()):
        if not entry.is_dir() or entry.name.startswith("."):
            continue
        if (entry / "skills").is_dir():
            plugins.append(entry.name)
    return plugins


def registered_plugins() -> list[str]:
    data = _load_yaml(_ROOT_CATALOG)
    plugins: list[str] = []
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
        plugins.append(parts[0])
    return sorted(set(plugins))


def skills_on_disk(plugin_dir: Path) -> set[str]:
    skills_dir = plugin_dir / "skills"
    if not skills_dir.is_dir():
        return set()
    return {
        entry.name
        for entry in skills_dir.iterdir()
        if entry.is_dir() and (entry / "SKILL.md").is_file()
    }


def location_skill_targets(loc_data: dict) -> set[str]:
    targets: set[str] = set()
    for target in loc_data.get("spec", {}).get("targets", []):
        if not isinstance(target, str):
            continue
        match = _SKILL_TARGET_RE.match(target)
        if match:
            targets.add(match.group(1))
    return targets


def load_owned_mcps() -> dict[str, Path]:
    owned: dict[str, Path] = {}
    for path in sorted((_REPO_ROOT / "mcps").glob("*.yaml")):
        if path.name == "catalog-info.yaml":
            continue
        data = _load_yaml(path)
        meta = data.get("metadata", {})
        name = meta.get("name")
        namespace = meta.get("namespace", _EXPECTED_NAMESPACE)
        if name:
            owned[f"mcpserver:{namespace}/{name}"] = path
    return owned


def _is_allowed_dangling_mcp(ref: str) -> bool:
    return ref.startswith(_CANONICAL_MCP_PREFIXES)


def _expected_include_type(entity_ref: str) -> str | None:
    if entity_ref.startswith("airesource:ai5-marketplace/"):
        return "skill"
    if entity_ref.startswith("mcpserver:"):
        return "mcp-server"
    return None


def _is_external_link(target: str) -> bool:
    lower = target.lower()
    return (
        lower.startswith("http://")
        or lower.startswith("https://")
        or lower.startswith("mailto:")
        or lower.startswith("#")
    )


def _is_forbidden_docs_link(target: str) -> bool:
    if _is_external_link(target):
        return False
    normalized = target.split("#", 1)[0].strip().replace("\\", "/")
    if normalized.startswith("docs/") or normalized.startswith("./docs/"):
        return True
    return "/docs/" in normalized


def _check_skill_docs_layout(skill_dir: Path, errors: list[str]) -> None:
    """Enforce agent-plugins.org / agentskills.io references/ layout (APPENG-6308)."""
    docs_dir = skill_dir / "docs"
    if docs_dir.is_dir():
        rel = docs_dir.relative_to(_REPO_ROOT)
        errors.append(
            f"{rel}: skill documentation must use references/ not docs/ "
            f"(rename to references/, update links, then delete docs/; "
            f"see {_SKILL_DOCS_STANDARD})"
        )

    nested_refs = skill_dir / "references" / "references"
    if nested_refs.is_dir():
        rel = nested_refs.relative_to(_REPO_ROOT)
        errors.append(
            f"{rel}: flatten references/references/ into skills/<name>/references/ "
            f"(no nested references directories; see {_SKILL_DOCS_STANDARD})"
        )

    references_dir = skill_dir / "references"
    if references_dir.is_dir():
        for path in sorted(references_dir.rglob("*")):
            if not path.is_symlink():
                continue
            raw = os.readlink(path)
            normalized = raw.replace("\\", "/")
            if "/docs/" in normalized or normalized.startswith("docs/"):
                rel = path.relative_to(_REPO_ROOT)
                errors.append(
                    f"{rel}: symlink still targets docs/ path '{raw}' — "
                    "update to references/ after migration"
                )

    for md_file in sorted(skill_dir.rglob("*.md")):
        if md_file.is_symlink() and not md_file.exists():
            continue
        try:
            text = md_file.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        rel_md = md_file.relative_to(_REPO_ROOT)
        for line_no, line in enumerate(text.splitlines(), start=1):
            for match in _MD_LINK_RE.finditer(line):
                raw_target = match.group(1).strip()
                if _is_forbidden_docs_link(raw_target):
                    errors.append(
                        f"{rel_md}:{line_no}: update docs/ link to references/: "
                        f"'{raw_target}'"
                    )
                target = raw_target.split("#", 1)[0].strip().replace("\\", "/")
                if "references/references/" in target:
                    errors.append(
                        f"{rel_md}:{line_no}: flatten references/references/ link to "
                        f"references/: '{raw_target}'"
                    )


def _parse_shared_script_symlink_target(raw: str) -> tuple[str, str] | None:
    normalized = raw.replace("\\", "/")
    match = _SHARED_SCRIPT_SYMLINK_RE.match(normalized)
    if not match:
        return None
    return match.group(1), match.group(2)


def _check_skill_scripts_layout(plugin: str, skill_dir: Path, errors: list[str]) -> None:
    scripts_dir = skill_dir / "scripts"
    if not scripts_dir.is_dir():
        return

    plugin_dir = skill_dir.parent.parent
    skill_rel = skill_dir.relative_to(_REPO_ROOT)
    linked_by_group: dict[str, set[str]] = {}

    for entry in sorted(scripts_dir.iterdir()):
        if not entry.is_symlink():
            continue
        parsed = _parse_shared_script_symlink_target(os.readlink(entry))
        if not parsed:
            continue
        group, filename = parsed
        linked_by_group.setdefault(group, set()).add(filename)

    if not linked_by_group:
        return

    for group, linked_files in sorted(linked_by_group.items()):
        group_dir = plugin_dir / "scripts" / group
        if not group_dir.is_dir():
            errors.append(
                f"{skill_rel}/scripts: symlinks reference scripts/{group}/ but "
                f"{plugin}/scripts/{group}/ is missing"
            )
            continue
        for path in sorted(group_dir.iterdir()):
            if not path.is_file():
                continue
            if _TEST_SCRIPT_RE.match(path.name):
                continue
            if path.name not in linked_files:
                errors.append(
                    f"{skill_rel}/scripts: missing symlink for "
                    f"{plugin}/scripts/{group}/{path.name} — fan out all non-test "
                    f"files when linking from scripts/{group}/"
                )

    forbidden = f"{plugin}/scripts/"
    for md_file in sorted(skill_dir.rglob("*.md")):
        if md_file.is_symlink() and not md_file.exists():
            continue
        try:
            text = md_file.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        rel_md = md_file.relative_to(_REPO_ROOT)
        for line_no, line in enumerate(text.splitlines(), start=1):
            if forbidden in line:
                errors.append(
                    f"{rel_md}:{line_no}: use skill-local scripts/ paths, not "
                    f"'{forbidden}' (authoring-repo layout only)"
                )


def _check_skill_conventions(path: Path, data: dict, errors: list[str]) -> None:
    meta = data.get("metadata") or {}
    spec = data.get("spec") or {}
    rel = path.relative_to(_REPO_ROOT)

    if meta.get("namespace") != _EXPECTED_NAMESPACE:
        errors.append(f"{rel}: metadata.namespace must be {_EXPECTED_NAMESPACE}")
    labels = meta.get("labels") or {}
    if labels.get("distribution") != "external":
        errors.append(f"{rel}: labels.distribution must be external")
    if spec.get("owner") != _EXPECTED_OWNER:
        errors.append(f"{rel}: spec.owner must be {_EXPECTED_OWNER}")
    if spec.get("agents") != []:
        errors.append(f"{rel}: spec.agents must be []")
    if spec.get("type") != "skill":
        errors.append(f"{rel}: spec.type must be skill")
    for key in _PLUGIN_ONLY_SKILL_SPEC_KEYS:
        if key in spec:
            errors.append(f"{rel}: spec.{key} is plugin-only; omit it on skill manifests")


def _validate_plugin_dual_write(
    plugin_path: Path,
    plugin_ref: str,
    plugin_data: dict,
    plugin_spec: dict,
    disk: set[str],
    owned_mcps: dict[str, Path],
    errors: list[str],
) -> None:
    rel = plugin_path.relative_to(_REPO_ROOT)
    plugin_spec = plugin_spec or {}
    labels = (plugin_data.get("metadata") or {}).get("labels") or {}
    if labels.get("distribution") != "external":
        errors.append(f"{rel}: metadata.labels.distribution must be external")

    if not disk:
        return

    skills_raw = plugin_spec.get("skills")
    if skills_raw is None:
        errors.append(f"{rel}: missing spec.skills (legacy dual-write required)")
        skill_refs: list[str] = []
    elif not isinstance(skills_raw, list):
        errors.append(f"{rel}: spec.skills must be a list")
        skill_refs = []
    elif not skills_raw:
        errors.append(f"{rel}: spec.skills must not be empty")
        skill_refs = []
    else:
        skill_refs = [str(item) for item in skills_raw]
        for ref in skill_refs:
            if not ref.startswith("airesource:ai5-marketplace/"):
                errors.append(f"{rel}: spec.skills entries must be airesource refs, got {ref!r}")

    skill_names_legacy = {
        ref.split("/", 1)[1]
        for ref in skill_refs
        if ref.startswith("airesource:ai5-marketplace/")
    }
    if skill_names_legacy != disk:
        missing = disk - skill_names_legacy
        extra = skill_names_legacy - disk
        if missing:
            errors.append(f"{rel}: spec.skills missing {sorted(missing)}")
        if extra:
            errors.append(f"{rel}: spec.skills lists unknown skills {sorted(extra)}")
    includes_raw = plugin_spec.get("includes")
    if includes_raw is None:
        errors.append(f"{rel}: missing spec.includes")
        return
    if not isinstance(includes_raw, list):
        errors.append(f"{rel}: spec.includes must be a list")
        return
    if not includes_raw:
        errors.append(f"{rel}: spec.includes must not be empty")

    seen: set[str] = set()
    include_skills: set[str] = set()
    include_mcps: set[str] = set()

    for index, entry in enumerate(includes_raw):
        loc = f"{rel}: spec.includes[{index}]"
        if isinstance(entry, str):
            errors.append(f"{loc} must be a mapping, not a string")
            continue
        if not isinstance(entry, dict):
            errors.append(f"{loc} must be a mapping")
            continue
        if entry.get("gitRef") is not None:
            errors.append(f"{loc} must not set gitRef")
        member_type = entry.get("type")
        if member_type == "plugin":
            errors.append(f"{loc} must not include a plugin member")
            continue
        if member_type not in _ALLOWED_INCLUDE_TYPES:
            if member_type:
                errors.append(f"{loc} type must be skill or mcp-server, got {member_type!r}")
            else:
                errors.append(f"{loc} type is required (skill or mcp-server)")

        entity_ref = entry.get("entityRef")
        if not isinstance(entity_ref, str) or not entity_ref.strip():
            errors.append(f"{loc} missing string entityRef")
            continue
        if entity_ref in seen:
            errors.append(f"{rel}: duplicate includes entityRef {entity_ref}")
        seen.add(entity_ref)
        if entity_ref == plugin_ref:
            errors.append(f"{rel}: includes must not self-reference the plugin")
            continue

        expected_type = _expected_include_type(entity_ref)
        if (
            member_type in _ALLOWED_INCLUDE_TYPES
            and expected_type is not None
            and member_type != expected_type
        ):
            errors.append(
                f"{loc} type must be {expected_type} to match entityRef, got {member_type!r}"
            )

        if expected_type == "skill":
            name = entity_ref.split("/", 1)[1]
            include_skills.add(name)
        elif expected_type == "mcp-server":
            if entity_ref.startswith(_CANONICAL_MCP_PREFIXES):
                errors.append(f"{loc} canonical MCP {entity_ref} must not be in includes")
            include_mcps.add(entity_ref)
        else:
            errors.append(f"{loc} unknown entityRef {entity_ref!r}")

    if include_skills != disk:
        missing = disk - include_skills
        extra = include_skills - disk
        if missing:
            errors.append(f"{rel}: spec.includes missing skills {sorted(missing)}")
        if extra:
            errors.append(f"{rel}: spec.includes lists unknown skills {sorted(extra)}")
    if skill_names_legacy != include_skills:
        errors.append(f"{rel}: spec.skills and spec.includes skill rosters must match")

    plugin_mcp_deps = {
        dep for dep in _refs(plugin_spec, "dependsOn") if dep.startswith("mcpserver:")
    }
    expected_mcp_includes = {
        dep for dep in plugin_mcp_deps if dep in owned_mcps and dep in plugin_mcp_deps
    }
    if include_mcps != expected_mcp_includes:
        missing = expected_mcp_includes - include_mcps
        extra = include_mcps - expected_mcp_includes
        if missing:
            errors.append(f"{rel}: spec.includes missing owned MCPs {sorted(missing)}")
        if extra:
            errors.append(f"{rel}: spec.includes lists unexpected MCPs {sorted(extra)}")


def validate_plugin_layout(plugin: str, errors: list[str]) -> None:
    plugin_dir = _REPO_ROOT / plugin
    for skill in sorted(skills_on_disk(plugin_dir)):
        skill_dir = plugin_dir / "skills" / skill
        _check_skill_docs_layout(skill_dir, errors)
        _check_skill_scripts_layout(plugin, skill_dir, errors)


def validate_plugin(plugin: str, owned_mcps: dict[str, Path], errors: list[str]) -> None:
    plugin_dir = _REPO_ROOT / plugin
    loc_path = plugin_dir / "catalog-info.yaml"
    plugin_path = plugin_dir / f"{plugin}-plugin.yaml"
    plugin_ref = _PLUGIN_REF.format(plugin=plugin)

    if not loc_path.is_file():
        errors.append(f"{plugin}: missing {loc_path.relative_to(_REPO_ROOT)}")
        return
    if not plugin_path.is_file():
        errors.append(f"{plugin}: missing {plugin_path.relative_to(_REPO_ROOT)}")
        return

    loc_data = _load_yaml(loc_path)
    plugin_data = _load_yaml(plugin_path)
    plugin_spec = plugin_data.get("spec") or {}

    disk = skills_on_disk(plugin_dir)
    loc_targets = location_skill_targets(loc_data)

    for skill in sorted(disk - loc_targets):
        errors.append(
            f"{plugin}: skill '{skill}' on disk but missing from "
            f"{loc_path.relative_to(_REPO_ROOT)} targets"
        )
    for skill in sorted(loc_targets - disk):
        errors.append(
            f"{plugin}: {loc_path.relative_to(_REPO_ROOT)} targets skill '{skill}' "
            "but skills/<name>/SKILL.md not found"
        )

    _validate_plugin_dual_write(
        plugin_path,
        plugin_ref,
        plugin_data,
        plugin_spec,
        disk,
        owned_mcps,
        errors,
    )

    if "system:default/agentic-plugins" in _refs(plugin_spec, "dependsOn"):
        errors.append(
            f"{plugin_path.relative_to(_REPO_ROOT)}: redundant "
            "dependsOn system:default/agentic-plugins (use spec.system)"
        )

    skill_depends: dict[str, list[str]] = {}
    skill_depof: dict[str, set[str]] = {}
    plugin_skill_mcp_union: set[str] = set()

    for skill in sorted(disk):
        skill_dir = plugin_dir / "skills" / skill
        _check_skill_docs_layout(skill_dir, errors)
        _check_skill_scripts_layout(plugin, skill_dir, errors)

        manifest = skill_dir / "catalog-info.yaml"
        if not manifest.is_file():
            errors.append(f"{plugin}: missing {manifest.relative_to(_REPO_ROOT)}")
            continue

        raw = manifest.read_text(encoding="utf-8")
        if _FORBIDDEN_RELATION_RE.search(raw):
            errors.append(
                f"{manifest.relative_to(_REPO_ROOT)}: partOf/hasPart not supported on AiResource"
            )

        data = _load_yaml(manifest)
        _check_skill_conventions(manifest, data, errors)
        spec = data.get("spec", {})
        deps = _refs(spec, "dependsOn")
        skill_depends[skill] = deps
        skill_depof[skill] = set(_refs(spec, "dependencyOf"))

        if plugin_ref not in deps:
            errors.append(
                f"{manifest.relative_to(_REPO_ROOT)}: missing dependsOn {plugin_ref}"
            )

        for dep in deps:
            if dep.startswith("mcpserver:"):
                plugin_skill_mcp_union.add(dep)

    plugin_mcp_deps = {
        d for d in _refs(plugin_spec, "dependsOn") if d.startswith("mcpserver:")
    }
    if plugin_mcp_deps != plugin_skill_mcp_union:
        missing_on_plugin = plugin_skill_mcp_union - plugin_mcp_deps
        extra_on_plugin = plugin_mcp_deps - plugin_skill_mcp_union
        if missing_on_plugin:
            errors.append(
                f"{plugin}: {plugin_path.relative_to(_REPO_ROOT)} missing plugin dependsOn "
                f"MCP union entries: {sorted(missing_on_plugin)}"
            )
        if extra_on_plugin:
            errors.append(
                f"{plugin}: {plugin_path.relative_to(_REPO_ROOT)} extra plugin dependsOn "
                f"MCP refs not used by any skill: {sorted(extra_on_plugin)}"
            )

    for skill, deps in skill_depends.items():
        orchestrator_ref = f"airesource:ai5-marketplace/{skill}"
        for dep in deps:
            if dep == plugin_ref:
                continue
            if dep.startswith("airesource:ai5-marketplace/"):
                target = dep.split("/", 1)[1]
                if target not in disk:
                    errors.append(
                        f"{plugin}/skills/{skill}/catalog-info.yaml: dependsOn {dep} "
                        "but skill not in plugin"
                    )
                    continue
                if orchestrator_ref not in skill_depof.get(target, set()):
                    errors.append(
                        f"{plugin}/skills/{target}/catalog-info.yaml: missing dependencyOf "
                        f"{orchestrator_ref} (inverse of {skill} dependsOn)"
                    )
            elif dep.startswith("mcpserver:"):
                if dep in owned_mcps:
                    mcp_path = owned_mcps[dep]
                    mcp_spec = _load_yaml(mcp_path).get("spec", {})
                    if orchestrator_ref not in set(_refs(mcp_spec, "dependencyOf")):
                        errors.append(
                            f"{mcp_path.relative_to(_REPO_ROOT)}: missing dependencyOf "
                            f"{orchestrator_ref} (inverse of {skill} dependsOn {dep})"
                        )
                elif not _is_allowed_dangling_mcp(dep):
                    errors.append(
                        f"{plugin}/skills/{skill}/catalog-info.yaml: unknown mcpserver ref {dep}"
                    )

    for dep in _refs(plugin_spec, "dependsOn"):
        if dep.startswith("mcpserver:") and dep in owned_mcps:
            mcp_path = owned_mcps[dep]
            mcp_spec = _load_yaml(mcp_path).get("spec", {})
            if plugin_ref not in set(_refs(mcp_spec, "dependencyOf")):
                errors.append(
                    f"{mcp_path.relative_to(_REPO_ROOT)}: missing dependencyOf "
                    f"{plugin_ref} (inverse of plugin dependsOn {dep})"
                )


def main() -> int:
    errors: list[str] = []
    owned_mcps = load_owned_mcps()

    registered: list[str] = []
    if not _ROOT_CATALOG.is_file():
        errors.append(
            f"missing root catalog Location: {_ROOT_CATALOG.relative_to(_REPO_ROOT)}"
        )
    else:
        registered = registered_plugins()
        for plugin in registered:
            validate_plugin(plugin, owned_mcps, errors)

    registered_set = set(registered)
    for plugin in all_plugins_with_skills():
        if plugin not in registered_set:
            validate_plugin_layout(plugin, errors)

    if errors:
        print("Compass manifest validation failed:", file=sys.stderr)
        for err in errors:
            print(f"  • {err}", file=sys.stderr)
        return 1

    print("✓ Compass manifest validation passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
