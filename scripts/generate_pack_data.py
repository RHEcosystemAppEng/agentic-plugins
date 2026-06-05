#!/usr/bin/env python3
"""
Parse agentic packs and extract plugin metadata, skills, and agents.
"""

import json
import os
import re
from pathlib import Path
from typing import Dict, List, Any
import yaml

import pack_registry

# Union registry (marketplace ∪ plugins.json); docs site uses subset helper
PACK_DIRS = pack_registry.get_union_pack_dirs()
DOCS_PACK_DIRS = pack_registry.get_docs_pack_dirs()


def parse_yaml_frontmatter(file_path: Path) -> Dict[str, Any]:
    """
    Extract YAML frontmatter from a markdown file.

    Args:
        file_path: Path to the markdown file

    Returns:
        Dictionary containing the frontmatter data
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Match YAML frontmatter (---\n...\n---)
        match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
        if not match:
            return {}

        frontmatter_text = match.group(1)
        return yaml.safe_load(frontmatter_text) or {}

    except Exception as e:
        print(f"Warning: Failed to parse frontmatter from {file_path}: {e}")
        return {}


def load_plugin_titles() -> Dict[str, str]:
    """
    Load plugin title mappings from docs/plugins.json.

    Returns:
        Dictionary mapping plugin names to display titles
    """
    plugins_file = Path('docs/plugins.json')

    if not plugins_file.exists():
        print("Warning: docs/plugins.json not found, using default titles")
        return {}

    try:
        with open(plugins_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Extract just the titles into a simple mapping
        return {name: info['title'] for name, info in data.items()}

    except Exception as e:
        print(f"Warning: Failed to load docs/plugins.json: {e}")
        return {}


def parse_plugin_json(pack_dir: str, plugin_titles: Dict[str, str]) -> Dict[str, Any]:
    """
    Parse optional plugin.json from a pack directory and merge with title from docs/plugins.json.

    Args:
        pack_dir: Name of the pack directory
        plugin_titles: Dictionary mapping plugin names to display titles

    Returns:
        Dictionary with plugin metadata, or defaults if file doesn't exist
    """
    plugin_path = Path(pack_dir) / '.claude-plugin' / 'plugin.json'

    # Default values if plugin.json doesn't exist
    defaults = {
        'name': pack_dir,
        'version': '0.0.0',
        'description': f'{pack_dir} agentic collection',
        'author': {'name': 'Red Hat'},
        'license': 'Apache-2.0',
        'keywords': []
    }

    if not plugin_path.exists():
        # Use title from plugins.json if available
        if pack_dir in plugin_titles:
            defaults['title'] = plugin_titles[pack_dir]
        return defaults

    try:
        with open(plugin_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Merge with defaults (in case some fields are missing)
        result = {**defaults, **data}
        
        # Override with title from docs/plugins.json if available
        if pack_dir in plugin_titles:
            result['title'] = plugin_titles[pack_dir]
        elif 'title' not in result:
            # Fallback: use name as title if not set
            result['title'] = result['name']

        return result

    except Exception as e:
        print(f"Warning: Failed to parse {plugin_path}: {e}")
        # Use title from plugins.json if available even on error
        if pack_dir in plugin_titles:
            defaults['title'] = plugin_titles[pack_dir]
        return defaults


def overlay_plugin_version_from_marketplace(pack_dir: str, plugin: Dict[str, Any]) -> None:
    """
    Set plugin['version'] from marketplace/rh-agentic-collection.yml modules[].version
    when present. Overrides defaults and .claude-plugin/plugin.json so the docs site
    matches the Lola marketplace module version.
    """
    mod = pack_registry.load_marketplace_module_by_path(pack_dir)
    if not mod:
        return
    raw = mod.get("version")
    if raw is None:
        return
    ver = str(raw).strip()
    if ver:
        plugin["version"] = ver


def parse_skills(pack_dir: str) -> List[Dict[str, Any]]:
    """
    Parse skills from skills/*/SKILL.md files.

    Args:
        pack_dir: Name of the pack directory

    Returns:
        List of skill dictionaries with name, description, file_path
    """
    skills = []
    skills_dir = Path(pack_dir) / 'skills'

    if not skills_dir.exists():
        return skills

    # Find all SKILL.md files
    for skill_file in skills_dir.glob('*/SKILL.md'):
        frontmatter = parse_yaml_frontmatter(skill_file)

        # Extract name and description
        name = frontmatter.get('name', skill_file.parent.name)
        description = frontmatter.get('description', '')

        # Clean up description (remove leading/trailing whitespace, collapse newlines)
        if isinstance(description, str):
            description = ' '.join(description.split())

        skills.append({
            'name': name,
            'description': description,
            'file_path': str(skill_file.relative_to(pack_dir))
        })

    return sorted(skills, key=lambda s: s['name'])


def parse_agents(pack_dir: str) -> List[Dict[str, Any]]:
    """
    Parse agents from agents/*.md files.

    Args:
        pack_dir: Name of the pack directory

    Returns:
        List of agent dictionaries with name, description, model, tools, file_path
    """
    agents = []
    agents_dir = Path(pack_dir) / 'agents'

    if not agents_dir.exists():
        return agents

    # Find all .md files in agents directory
    for agent_file in agents_dir.glob('*.md'):
        frontmatter = parse_yaml_frontmatter(agent_file)

        # Extract metadata
        name = frontmatter.get('name', agent_file.stem)
        description = frontmatter.get('description', '')
        model = frontmatter.get('model', 'inherit')
        tools = frontmatter.get('tools', [])

        # Clean up description
        if isinstance(description, str):
            description = ' '.join(description.split())

        agents.append({
            'name': name,
            'description': description,
            'model': model,
            'tools': tools,
            'file_path': str(agent_file.relative_to(pack_dir))
        })

    return sorted(agents, key=lambda a: a['name'])


def sanitize_for_json(obj: Any) -> Any:
    """
    Convert objects to JSON-serializable format.
    Handles date objects and other non-serializable types.

    Args:
        obj: Object to sanitize

    Returns:
        JSON-serializable version of the object
    """
    from datetime import date, datetime

    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {k: sanitize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [sanitize_for_json(item) for item in obj]
    else:
        return obj


def parse_docs(pack_dir: str) -> List[Dict[str, Any]]:
    """
    Parse documentation files from docs/**/*.md files.

    Args:
        pack_dir: Name of the pack directory

    Returns:
        List of doc dictionaries with title, sources, category, file_path
    """
    docs = []
    docs_dir = Path(pack_dir) / 'docs'

    if not docs_dir.exists():
        return docs

    # Files to exclude from documentation parsing
    EXCLUDE_FILES = {'README.md', 'INDEX.md', 'SOURCES.md'}

    # Find all .md files recursively (excluding .ai-index directory)
    for doc_file in docs_dir.rglob('*.md'):
        # Skip excluded files and files in .ai-index directory
        if doc_file.name in EXCLUDE_FILES or '.ai-index' in doc_file.parts:
            continue

        frontmatter = parse_yaml_frontmatter(doc_file)

        # Extract metadata
        title = frontmatter.get('title', doc_file.stem.replace('-', ' ').title())
        category = frontmatter.get('category', doc_file.parent.name)
        sources = frontmatter.get('sources', [])

        # Ensure sources is a list and sanitize for JSON
        if not isinstance(sources, list):
            sources = []
        sources = sanitize_for_json(sources)

        docs.append({
            'title': title,
            'category': category,
            'sources': sources,
            'file_path': str(doc_file.relative_to(pack_dir))
        })

    # Sort by category first, then by title
    return sorted(docs, key=lambda d: (d['category'], d['title']))


def detect_repo_license(repo_root: Path, pack_path: str = ".") -> str:
    """Best-effort SPDX identifier from LICENSE files in a cloned repository."""
    candidates = [
        repo_root / pack_path / "LICENSE",
        repo_root / pack_path / "LICENSE.txt",
        repo_root / "LICENSE",
        repo_root / "LICENSE.txt",
    ]
    for path in candidates:
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")[:8000]
        except OSError:
            continue
        upper = text.upper()
        if "APACHE LICENSE" in upper and "VERSION 2.0" in upper:
            return "Apache-2.0"
        if "MIT LICENSE" in upper or "PERMISSION IS HEREBY GRANTED, FREE OF CHARGE" in upper:
            return "MIT"
        if "BSD 3-CLAUSE" in upper or "REDISTRIBUTION AND USE IN SOURCE AND BINARY FORMS" in upper:
            if "3-CLAUSE" in upper or "3 CLAUSE" in upper:
                return "BSD-3-Clause"
            return "BSD-2-Clause"
    return "Unknown"


def load_federated_packs(plugin_titles: Dict[str, str] | None = None) -> List[Dict[str, Any]]:
    """
    Fetch federated modules and return them as standalone pack entries.

    Each federated pack gets ``source: "federated"`` so the docs site can
    badge it differently from in-tree packs.
    """
    import shutil
    import subprocess
    import tempfile

    titles = plugin_titles if plugin_titles is not None else load_plugin_titles()
    modules = pack_registry.load_federated_modules()
    if not modules:
        return []

    repo_root = Path(__file__).resolve().parent.parent
    packs: List[Dict[str, Any]] = []
    tmp = Path(tempfile.mkdtemp(prefix="federated-build-"))

    try:
        for mod in modules:
            name = mod.get("name", "unknown")
            fed_catalog_dir = f"federation/modules/{name}"
            maturity = pack_registry.load_pack_maturity(fed_catalog_dir, repo_root)
            if maturity != pack_registry.DOCS_MATURITY_PUBLISH:
                label = maturity or "missing catalog"
                print(
                    f"  Skipping federated '{name}' for docs site: maturity {label} "
                    f"(only GREEN is published)"
                )
                continue

            repository = mod.get("repository", "")
            ref = mod.get("ref", "")
            description = mod.get("description", "")
            version = mod.get("version", "0.0.0")
            tags = mod.get("tags", [])
            pack_path = mod.get("path", ".")

            if not repository:
                print(f"  Warning: federated module '{name}' missing repository, skipping")
                continue

            ref_err = pack_registry.federation_ref_error(ref)
            if ref_err:
                print(f"  Warning: federated module '{name}' invalid ref: {ref_err}")
                continue

            clone_dest = tmp / name
            try:
                subprocess.run(
                    ["git", "clone", "--quiet", "--no-checkout", repository, str(clone_dest)],
                    check=True, capture_output=True, text=True, timeout=120,
                )
                subprocess.run(
                    ["git", "checkout", "--quiet", pack_registry.normalize_federation_ref(ref)],
                    check=True, capture_output=True, text=True, cwd=clone_dest, timeout=30,
                )
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
                print(f"  Warning: failed to clone '{name}': {exc}")
                continue

            pack_dir = clone_dest / pack_path
            license_id = detect_repo_license(clone_dest, pack_path)
            skills = parse_skills(str(pack_dir))

            pack = {
                "name": name,
                "path": repository,
                "catalog_dir": fed_catalog_dir,
                "source": "federated",
                "repository": repository,
                "ref": pack_registry.normalize_federation_ref(ref)[:12],
                "plugin": {
                    "name": name,
                    "title": titles.get(name, name.replace("-", " ").title()),
                    "version": version,
                    "description": description,
                    "author": {"name": "External"},
                    "license": license_id,
                    "keywords": tags,
                },
                "skills": sorted(skills, key=lambda s: s["name"]),
                "agents": [],
                "docs": [],
                "has_readme": (pack_dir / "README.md").exists(),
            }
            packs.append(pack)
            print(f"  ✓ Federated '{name}': {len(skills)} skill(s) from {repository}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    return packs


def generate_pack_data() -> List[Dict[str, Any]]:
    """
    Generate pack data for all agentic packs.

    Returns:
        List of pack dictionaries
    """
    packs = []

    # Load plugin title mappings from docs/plugins.json
    plugin_titles = load_plugin_titles()

    for pack_dir in DOCS_PACK_DIRS:
        pack_path = Path(pack_dir)

        if not pack_path.exists():
            print(f"Warning: Pack directory {pack_dir} does not exist, skipping")
            continue

        docs = parse_docs(pack_dir)

        plugin = parse_plugin_json(pack_dir, plugin_titles)
        overlay_plugin_version_from_marketplace(pack_dir, plugin)

        pack = {
            'name': pack_dir,
            'path': f'./{pack_dir}',
            'plugin': plugin,
            'skills': parse_skills(pack_dir),
            'agents': parse_agents(pack_dir),
            'docs': docs,
            'has_readme': (pack_path / 'README.md').exists()
        }

        packs.append(pack)

        # Use title from plugin data for display
        plugin_title = pack['plugin'].get('title', pack_dir)
        print(f"✓ Parsed {plugin_title}: {len(pack['skills'])} skills, {len(pack['agents'])} agents, {len(docs)} docs")

    federated = load_federated_packs(plugin_titles)
    if federated:
        packs.extend(federated)
        print(f"✓ Added {len(federated)} federated pack(s)")

    return packs


if __name__ == '__main__':
    # Test the script
    print("Parsing agentic collections...")
    print()

    packs = generate_pack_data()

    print()
    print(f"Found {len(packs)} collections total")
    print()
    print("Summary:")
    for pack in packs:
        plugin = pack['plugin']
        title = plugin.get('title', plugin['name'])
        print(f"  • {title} v{plugin['version']}")
        print(f"    ({plugin['name']})")
        print(f"    Skills: {len(pack['skills'])}, Agents: {len(pack['agents'])}, Docs: {len(pack['docs'])}")
