#!/usr/bin/env python3
"""
Validate agentic collection pack structure (mcps.json, AGENTS.md; plugin.json optional).

Skill-level validation (frontmatter, sections, security) is handled by
validate-skills.sh and run-skill-linter.sh.
"""

import json
import sys
from pathlib import Path
from typing import List
import re

import pack_registry

# Union of Lola marketplace paths and docs/plugins.json keys (existing dirs only)
PACK_DIRS = pack_registry.get_union_pack_dirs()

AGENTS_MD_FILENAME = "AGENTS.md"
AGENTS_MD_DEPRECATED = "CLAUDE.md"


def validate_plugin_json(pack_dir: str) -> List[str]:
    """
    Validate plugin.json structure when `.claude-plugin/plugin.json` exists.

    Args:
        pack_dir: Collection directory name

    Returns:
        List of error messages (empty if valid or file absent)
    """
    errors = []
    plugin_path = Path(pack_dir) / '.claude-plugin' / 'plugin.json'

    if not plugin_path.exists():
        # plugin.json is optional
        return errors

    try:
        with open(plugin_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Check required fields
        if 'name' not in data:
            errors.append(f"{pack_dir}: plugin.json missing required field 'name'")
        if 'version' not in data:
            errors.append(f"{pack_dir}: plugin.json missing required field 'version'")
        if 'description' not in data:
            errors.append(f"{pack_dir}: plugin.json missing required field 'description'")

    except json.JSONDecodeError as e:
        errors.append(f"{pack_dir}: Invalid JSON in plugin.json: {e}")
    except Exception as e:
        errors.append(f"{pack_dir}: Error reading plugin.json: {e}")

    return errors


MCP_FILENAME = "mcps.json"
MCP_DEPRECATED = ".mcp.json"


def validate_mcp_json(pack_dir: str) -> List[str]:
    """
    Validate mcps.json structure.
    Errors if deprecated .mcp.json exists (must be renamed to mcps.json).

    Args:
        pack_dir: Pack directory name

    Returns:
        List of error messages (empty if valid)
    """
    errors = []
    pack_path = Path(pack_dir)
    deprecated_path = pack_path / MCP_DEPRECATED
    mcp_path = pack_path / MCP_FILENAME

    if deprecated_path.exists():
        errors.append(
            f"{pack_dir}: deprecated {MCP_DEPRECATED} found; rename to {MCP_FILENAME}"
        )
        return errors

    if not mcp_path.exists():
        # mcps.json is optional
        return errors

    try:
        with open(mcp_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Check for mcpServers key
        if 'mcpServers' not in data:
            errors.append(f"{pack_dir}: {MCP_FILENAME} missing 'mcpServers' key")
        elif not isinstance(data['mcpServers'], dict):
            errors.append(f"{pack_dir}: {MCP_FILENAME} 'mcpServers' must be an object")

    except json.JSONDecodeError as e:
        errors.append(f"{pack_dir}: Invalid JSON in {MCP_FILENAME}: {e}")
    except Exception as e:
        errors.append(f"{pack_dir}: Error reading {MCP_FILENAME}: {e}")

    return errors


AGENTS_MD_REQUIRED_SECTIONS = [
    "Skill-First Rule",
    "Intent Routing",
    "MCP Servers",
    "Global Rules",
]


def validate_agents_md(pack_dir: str) -> List[str]:
    """
    Validate AGENTS.md presence and structure.

    Required for any pack that has skills. Checks for required sections
    and verifies that all skills appear in the intent routing content.
    Errors if deprecated pack-level CLAUDE.md exists (Lola manages AGENTS.md).

    Args:
        pack_dir: Pack directory name

    Returns:
        List of error messages (empty if valid)
    """
    errors = []
    pack_path = Path(pack_dir)
    deprecated_path = pack_path / AGENTS_MD_DEPRECATED
    agents_path = pack_path / AGENTS_MD_FILENAME
    skills_dir = pack_path / 'skills'

    has_skills = skills_dir.exists() and any(skills_dir.glob('*/SKILL.md'))

    if deprecated_path.exists():
        errors.append(
            f"{pack_dir}: deprecated pack-level {AGENTS_MD_DEPRECATED} found; "
            f"rename to {AGENTS_MD_FILENAME} (Lola AI Context Module convention)"
        )
        return errors

    if not agents_path.exists():
        if has_skills:
            errors.append(
                f"{pack_dir}: Missing {AGENTS_MD_FILENAME} (required for packs with skills)"
            )
        return errors

    try:
        with open(agents_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check required sections
        headings = re.findall(r'^## (.+)$', content, re.MULTILINE)
        for section in AGENTS_MD_REQUIRED_SECTIONS:
            if not any(section in h for h in headings):
                errors.append(
                    f"{pack_dir}: {AGENTS_MD_FILENAME} missing required section '## {section}'"
                )

        # Check intent routing completeness
        if has_skills:
            skill_names = [p.parent.name for p in skills_dir.glob('*/SKILL.md')]
            for skill_name in skill_names:
                if skill_name not in content:
                    errors.append(
                        f"{pack_dir}: {AGENTS_MD_FILENAME} intent routing missing skill '{skill_name}'"
                    )

    except Exception as e:
        errors.append(f"{pack_dir}: Error reading {AGENTS_MD_FILENAME}: {e}")

    return errors


def validate_pack(pack_dir: str) -> List[str]:
    """
    Validate a single pack.

    Args:
        pack_dir: Pack directory name

    Returns:
        List of error messages (empty if valid)
    """
    errors = []

    # Check if pack directory exists
    if not Path(pack_dir).exists():
        errors.append(f"{pack_dir}: Pack directory does not exist")
        return errors

    # Validate plugin.json
    errors.extend(validate_plugin_json(pack_dir))

    # Validate mcps.json
    errors.extend(validate_mcp_json(pack_dir))

    # Validate AGENTS.md
    errors.extend(validate_agents_md(pack_dir))

    return errors


def main():
    """
    Main validation function.
    """
    print("🔍 Validating agentic collection structure...")
    print()

    all_errors = []

    for pack_dir in PACK_DIRS:
        print(f"Validating {pack_dir}...", end=' ')
        errors = validate_pack(pack_dir)

        if errors:
            print("❌")
            all_errors.extend(errors)
        else:
            print("✓")

    print()

    if all_errors:
        print("❌ Validation failed:")
        print()
        for error in all_errors:
            print(f"  • {error}")
        print()
        return 1
    else:
        print("✅ All collections validated successfully")
        print()
        return 0


if __name__ == '__main__':
    sys.exit(main())
