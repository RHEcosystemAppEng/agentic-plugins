#!/usr/bin/env python3
"""
Bootstrap <pack>/.catalog/collection.yaml for every union-registry pack (initial CI-friendly content).

Intended for first-time repo setup; refine catalogs via the create-collection skill and PRs.
Does not modify README, SKILL, AGENTS, or marketplace files.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

import yaml

import pack_registry
from generate_pack_data import parse_yaml_frontmatter

REPO_ROOT = Path(__file__).resolve().parent.parent

CATALOG_YAML_BANNER = """# Catalog: maintained via create-collection workflow (assistant + maintainer + PR review).
# Golden sources: skills/*/SKILL.md, README.md, AGENTS.md, marketplace/rh-agentic-collection.yml
# Do not edit ad hoc — follow COLLECTION_SPEC.md and the create-collection skill.
"""

PACK_CATALOG_IDS = {
    "rh-virt": "openshift-virtualization",
    "ocp-admin": "openshift-administration",
}


def _flatten_description(desc: Any) -> str:
    if desc is None:
        return ""
    if isinstance(desc, list):
        desc = "\n".join(str(x) for x in desc)
    return " ".join(str(desc).split())


def _is_orchestration(fm: Dict[str, Any]) -> bool:
    d = _flatten_description(fm.get("description")).lower()
    if "orchestrat" in d:
        return True
    meta = fm.get("metadata") or {}
    if isinstance(meta, dict):
        coll = meta.get("collection")
        if isinstance(coll, dict) and str(coll.get("role", "")).lower() == "orchestration":
            return True
    return False


def _skill_entries(pack_dir: str, root: Path) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    regular: List[Dict[str, Any]] = []
    orch: List[Dict[str, Any]] = []
    skills_dir = root / pack_dir / "skills"
    if not skills_dir.is_dir():
        return regular, orch
    for skill_md in sorted(skills_dir.glob("*/SKILL.md")):
        fm = parse_yaml_frontmatter(skill_md)
        dirname = skill_md.parent.name
        # Catalog skill name must match directory name (roster parity / compliance).
        name = dirname
        desc = _flatten_description(fm.get("description"))
        if len(desc) > 220:
            desc = desc[:217] + "..."
        sm = (
            f"**Use when:** See the skill description and AGENTS.md intent routing.\n\n"
            f"**What it does:** {desc or 'See SKILL.md for workflow and prerequisites.'}"
        )
        entry = {"name": name, "description": desc or f"Skill `{name}` in pack `{pack_dir}`.", "summary_markdown": sm}
        if _is_orchestration(fm):
            orch.append(entry)
        else:
            regular.append(entry)
    return regular, orch


def _decision_rows(pack_dir: str, regular: List[Dict[str, Any]], orch: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for s in (orch + regular)[:5]:
        rows.append(
            {
                "user_request": f'User: "I need help related to {s["name"]}"',
                "skill_to_use": s["name"],
                "reason": f"Use `{s['name']}` for workflows described in that skill and in AGENTS.md.",
            }
        )
    return rows


def build_collection_data(pack_dir: str, root: Path) -> Dict[str, Any]:
    mod = pack_registry.load_marketplace_module_by_path(pack_dir, root)
    title = pack_registry.load_plugin_title(pack_dir, root) or (mod or {}).get("name") or pack_dir
    version = (mod or {}).get("version") or "0.1.0"
    mod_desc = _flatten_description((mod or {}).get("description")) or f"Agentic collection `{pack_dir}`."
    tags = (mod or {}).get("tags") or []
    categories: List[str] = []
    seen_cat: set[str] = set()
    for t in tags:
        c = str(t).replace("-", " ").strip().title()
        if c and c not in seen_cat:
            seen_cat.add(c)
            categories.append(c)
        if len(categories) >= 6:
            break
    if not categories:
        categories = ["Red Hat", "Automation"]
    personas = ["Red Hat platform engineer"]
    regular, orch = _skill_entries(pack_dir, root)
    contents_desc = (
        f"The pack provides {len(regular)} skills"
        + (f" and {len(orch)} orchestration skills" if orch else "")
        + f" under `{pack_dir}` for Red Hat platforms."
    )
    sample_workflows = [
        {
            "name": "Choose the right skill",
            "workflow": (
                'User: "I have a task for this collection"\n'
                "- Open AGENTS.md intent routing and match your request to a skill name.\n"
                "- Invoke that skill and follow its workflow and prerequisites.\n"
            ),
        }
    ]
    resources = [
        {
            "title": "agentic-collections repository",
            "description": "Source repository for these packs and skills.",
            "url": "https://github.com/RHEcosystemAppEng/agentic-collections",
        }
    ]
    deploy_and_use = (
        "## Install (Lola)\n\n"
        "Add the marketplace and install this module from `marketplace/rh-agentic-collection.yml` "
        f"(path `{pack_dir}`). See the pack `README.md` for prerequisites, MCP env vars, and safety notes.\n"
    )
    summary = (
        f"- **Pack:** `{pack_dir}`\n"
        f"- **Focus:** {mod_desc[:280]}{'...' if len(mod_desc) > 280 else ''}\n"
        "- **Skills:** see `.catalog/collection.yaml` contents for the authoritative list.\n"
    )
    return {
        "id": PACK_CATALOG_IDS.get(pack_dir, pack_dir),
        "name": title,
        "provider": "Red Hat",
        "version": version,
        "categories": categories,
        "personas": personas,
        "marketplaces": ["Claude Code", "Cursor"],
        "description": mod_desc,
        "summary": summary,
        "contents": {
            "description": contents_desc,
            "skills": regular,
            "orchestration_skills": orch,
            "skills_decision_guide": _decision_rows(pack_dir, regular, orch),
        },
        "deploy_and_use": deploy_and_use,
        "sample_workflows": sample_workflows,
        "resources": resources,
        "repository": "https://github.com/RHEcosystemAppEng/agentic-collections",
        "license": "Apache-2.0",
    }


def write_pack(pack_dir: str, root: Path, force: bool) -> None:
    out_y = root / pack_dir / ".catalog" / "collection.yaml"
    if out_y.exists() and not force:
        print(f"skip {pack_dir} (exists, use --force)")
        return
    data = build_collection_data(pack_dir, root)
    out_y.parent.mkdir(parents=True, exist_ok=True)
    body = yaml.dump(
        data,
        default_flow_style=False,
        allow_unicode=True,
        sort_keys=False,
        width=120,
    )
    out_y.write_text(CATALOG_YAML_BANNER.rstrip() + "\n\n" + body, encoding="utf-8")
    print(f"wrote {out_y.relative_to(root)}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pack", help="Only this pack")
    ap.add_argument("--force", action="store_true", help="Overwrite existing collection.yaml")
    args = ap.parse_args()
    root = REPO_ROOT
    packs = [args.pack] if args.pack else pack_registry.get_union_pack_dirs(root)
    for p in packs:
        if not (root / p).is_dir():
            print(f"skip missing dir: {p}", file=sys.stderr)
            continue
        write_pack(p, root, args.force)
    return 0


if __name__ == "__main__":
    sys.exit(main())
