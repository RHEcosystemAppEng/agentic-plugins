#!/usr/bin/env python3
"""
Validate agentic collection plugin structure (mcps.json, AGENTS.md; plugin.json optional).

Skill-level validation (frontmatter, sections, security) is handled by
validate_skills_tier1.py and validate_skills_tier2.py.
"""

import json
import sys
from pathlib import Path
from typing import List
import re

_REPO_ROOT = Path(__file__).resolve().parent.parent
_EXCLUDE = {"scripts", "catalog", ".claude", ".github", ".lola", "docs", "eval"}

PLUGIN_DIRS = sorted(
    d.name for d in _REPO_ROOT.iterdir()
    if d.is_dir() and d.name not in _EXCLUDE and not d.name.startswith(".")
    and ((d / "AGENTS.md").exists() or (d / "skills").is_dir())
)

AGENTS_MD_FILENAME = "AGENTS.md"
AGENTS_MD_DEPRECATED = "CLAUDE.md"


def validate_plugin_json(plugin_dir: str) -> List[str]:
    """
    Validate plugin.json structure when `.claude-plugin/plugin.json` exists.

    Args:
        plugin_dir: Collection directory name

    Returns:
        List of error messages (empty if valid or file absent)
    """
    errors = []
    plugin_path = Path(plugin_dir) / '.claude-plugin' / 'plugin.json'

    if not plugin_path.exists():
        # plugin.json is optional
        return errors

    try:
        with open(plugin_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Check required fields
        if 'name' not in data:
            errors.append(f"{plugin_dir}: plugin.json missing required field 'name'")
        if 'version' not in data:
            errors.append(f"{plugin_dir}: plugin.json missing required field 'version'")
        if 'description' not in data:
            errors.append(f"{plugin_dir}: plugin.json missing required field 'description'")

    except json.JSONDecodeError as e:
        errors.append(f"{plugin_dir}: Invalid JSON in plugin.json: {e}")
    except Exception as e:
        errors.append(f"{plugin_dir}: Error reading plugin.json: {e}")

    return errors


MCP_FILENAME = "mcps.json"
MCP_DEPRECATED = ".mcp.json"


def validate_mcp_json(plugin_dir: str) -> List[str]:
    """
    Validate mcps.json structure.
    Errors if deprecated .mcp.json exists (must be renamed to mcps.json).

    Args:
        plugin_dir: Plugin directory name

    Returns:
        List of error messages (empty if valid)
    """
    errors = []
    plugin_path = Path(plugin_dir)
    deprecated_path = plugin_path / MCP_DEPRECATED
    mcp_path = plugin_path / MCP_FILENAME

    if deprecated_path.exists():
        errors.append(
            f"{plugin_dir}: deprecated {MCP_DEPRECATED} found; rename to {MCP_FILENAME}"
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
            errors.append(f"{plugin_dir}: {MCP_FILENAME} missing 'mcpServers' key")
        elif not isinstance(data['mcpServers'], dict):
            errors.append(f"{plugin_dir}: {MCP_FILENAME} 'mcpServers' must be an object")

    except json.JSONDecodeError as e:
        errors.append(f"{plugin_dir}: Invalid JSON in {MCP_FILENAME}: {e}")
    except Exception as e:
        errors.append(f"{plugin_dir}: Error reading {MCP_FILENAME}: {e}")

    return errors


AGENTS_MD_REQUIRED_SECTIONS = [
    "Skill-First Rule",
    "Intent Routing",
    "MCP Servers",
    "Global Rules",
]


def validate_agents_md(plugin_dir: str) -> List[str]:
    """
    Validate AGENTS.md presence and structure.

    Required for any plugin that has skills. Checks for required sections
    and verifies that all skills appear in the intent routing content.
    Errors if deprecated plugin-level CLAUDE.md exists (Lola manages AGENTS.md).

    Args:
        plugin_dir: Plugin directory name

    Returns:
        List of error messages (empty if valid)
    """
    errors = []
    plugin_path = Path(plugin_dir)
    deprecated_path = plugin_path / AGENTS_MD_DEPRECATED
    agents_path = plugin_path / AGENTS_MD_FILENAME
    skills_dir = plugin_path / 'skills'

    has_skills = skills_dir.exists() and any(skills_dir.glob('*/SKILL.md'))

    if deprecated_path.exists():
        errors.append(
            f"{plugin_dir}: deprecated plugin-level {AGENTS_MD_DEPRECATED} found; "
            f"rename to {AGENTS_MD_FILENAME} (Lola AI Context Module convention)"
        )
        return errors

    if not agents_path.exists():
        if has_skills:
            errors.append(
                f"{plugin_dir}: Missing {AGENTS_MD_FILENAME} (required for plugins with skills)"
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
                    f"{plugin_dir}: {AGENTS_MD_FILENAME} missing required section '## {section}'"
                )

        # Check intent routing completeness
        if has_skills:
            skill_names = [p.parent.name for p in skills_dir.glob('*/SKILL.md')]
            for skill_name in skill_names:
                if skill_name not in content:
                    errors.append(
                        f"{plugin_dir}: {AGENTS_MD_FILENAME} intent routing missing skill '{skill_name}'"
                    )

    except Exception as e:
        errors.append(f"{plugin_dir}: Error reading {AGENTS_MD_FILENAME}: {e}")

    return errors


def validate_plugin(plugin_dir: str) -> List[str]:
    """
    Validate a single plugin.

    Args:
        plugin_dir: Plugin directory name

    Returns:
        List of error messages (empty if valid)
    """
    errors = []

    # Check if plugin directory exists
    if not Path(plugin_dir).exists():
        errors.append(f"{plugin_dir}: Plugin directory does not exist")
        return errors

    # Validate plugin.json
    errors.extend(validate_plugin_json(plugin_dir))

    # Validate mcps.json
    errors.extend(validate_mcp_json(plugin_dir))

    # Validate AGENTS.md
    errors.extend(validate_agents_md(plugin_dir))

    return errors


def main():
    """
    Main validation function.
    """
    print("🔍 Validating agentic collection structure...")
    print()

    all_errors = []

    for plugin_dir in PLUGIN_DIRS:
        print(f"Validating {plugin_dir}...", end=' ')
        errors = validate_plugin(plugin_dir)

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
