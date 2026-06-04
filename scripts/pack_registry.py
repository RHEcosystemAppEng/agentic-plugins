"""
Resolve the set of agentic pack directories from Lola marketplace + docs/plugins.json.

Policy (union): include every ``modules[].path`` from ``marketplace/rh-agentic-collection.yml``
and every key from ``docs/plugins.json``, keeping only directory names that exist on disk.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import yaml

DEFAULT_MARKETPLACE = Path("marketplace/rh-agentic-collection.yml")
DEFAULT_PLUGINS_JSON = Path("docs/plugins.json")


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def load_marketplace_module_paths(marketplace_path: Optional[Path] = None) -> List[str]:
    path = marketplace_path or (_repo_root() / DEFAULT_MARKETPLACE)
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    modules = data.get("modules") or []
    out: List[str] = []
    for mod in modules:
        p = mod.get("path")
        if isinstance(p, str) and p.strip():
            out.append(p.strip().strip("/"))
    return out


def load_plugins_json_keys(plugins_path: Optional[Path] = None) -> List[str]:
    path = plugins_path or (_repo_root() / DEFAULT_PLUGINS_JSON)
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        return []
    return sorted(data.keys())


def get_union_pack_dirs(
    repo_root: Optional[Path] = None,
    marketplace_path: Optional[Path] = None,
    plugins_path: Optional[Path] = None,
) -> List[str]:
    """
    Sorted unique pack directory names that exist under repo root and appear in
    marketplace and/or docs/plugins.json union.
    """
    root = repo_root or _repo_root()
    names: Set[str] = set()
    names.update(load_marketplace_module_paths(marketplace_path))
    names.update(load_plugins_json_keys(plugins_path))
    existing: List[str] = []
    for name in sorted(names):
        if (root / name).is_dir():
            existing.append(name)
    return existing


def load_marketplace_module_by_path(
    pack_dir: str,
    repo_root: Optional[Path] = None,
    marketplace_path: Optional[Path] = None,
) -> Optional[Dict[str, Any]]:
    """Return the marketplace module dict for a pack path, or None."""
    root = repo_root or _repo_root()
    path = marketplace_path or (root / DEFAULT_MARKETPLACE)
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    for mod in data.get("modules") or []:
        if mod.get("path") == pack_dir:
            return mod
    return None


MAIN_REPO_URL = "https://github.com/RHEcosystemAppEng/agentic-collections"


def parse_repo_url(repository: str) -> tuple:
    """Split ``repository`` into ``(base_url, ref_or_none)``.

    The marketplace format embeds an optional ref with ``@``:
    ``https://github.com/org/repo@commitOrBranch``.  A bare URL without
    ``@`` returns ``(url, None)``.
    """
    repo = repository.rstrip("/")
    # Match the last @ that comes after the host/path portion.
    # We look for @ after "github.com/org/repo" — i.e., not inside the scheme.
    idx = repo.rfind("@")
    if idx > 0 and "://" in repo and idx > repo.index("://") + 3:
        return repo[:idx], repo[idx + 1:]
    return repo, None


def load_federated_modules(
    marketplace_path: Optional[Path] = None,
) -> List[Dict[str, Any]]:
    """Return modules whose repository differs from the main repo (federated packs)."""
    path = marketplace_path or (_repo_root() / DEFAULT_MARKETPLACE)
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    modules = data.get("modules") or []
    if not isinstance(modules, list):
        return []
    return [
        m for m in modules
        if isinstance(m, dict)
        and parse_repo_url(m.get("repository", ""))[0].rstrip("/") != MAIN_REPO_URL
    ]


def get_federation_module_dirs(repo_root: Optional[Path] = None) -> List[str]:
    """Return ``federation/modules/<name>`` paths that have a ``.catalog/collection.yaml`` on disk."""
    root = repo_root or _repo_root()
    fed_root = root / "federation" / "modules"
    if not fed_root.is_dir():
        return []
    return sorted(
        f"federation/modules/{p.name}"
        for p in fed_root.iterdir()
        if p.is_dir() and (p / ".catalog" / "collection.yaml").is_file()
    )


def is_federation_module(pack_dir: str) -> bool:
    """Return ``True`` if *pack_dir* lives under ``federation/modules/``."""
    return pack_dir.startswith("federation/modules/")


def load_plugin_title(pack_dir: str, repo_root: Optional[Path] = None) -> Optional[str]:
    root = repo_root or _repo_root()
    p = root / DEFAULT_PLUGINS_JSON
    if not p.exists():
        return None
    with open(p, "r", encoding="utf-8") as f:
        data = json.load(f)
    entry = data.get(pack_dir)
    if isinstance(entry, dict):
        t = entry.get("title")
        if isinstance(t, str):
            return t
    return None


# Catalog `maturity` value that is included in GitHub Pages / docs/data.json generation.
DOCS_MATURITY_PUBLISH: str = "GREEN"


def load_pack_maturity(pack_dir: str, repo_root: Optional[Path] = None) -> Optional[str]:
    """Return uppercase maturity from ``<pack>/.catalog/collection.yaml``, or None if missing/invalid."""
    root = repo_root or _repo_root()
    path = root / pack_dir / ".catalog" / "collection.yaml"
    if not path.is_file():
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
    except (OSError, yaml.YAMLError):
        return None
    m = data.get("maturity")
    if isinstance(m, str) and m.strip():
        return m.strip().upper()
    return None


def get_docs_pack_dirs(
    repo_root: Optional[Path] = None,
) -> List[str]:
    """Pack dirs included in GitHub Pages data.json: union registry packs whose catalog maturity is GREEN."""
    root = repo_root or _repo_root()
    out: List[str] = []
    for p in get_union_pack_dirs(repo_root):
        if load_pack_maturity(p, root) == DOCS_MATURITY_PUBLISH:
            out.append(p)
    return out
