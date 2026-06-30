#!/usr/bin/env python3
"""Shared HTML for the deprecated legacy catalog site banner."""

from __future__ import annotations

import html
import re
from pathlib import Path

ARCHIVED_REPO_URL = "https://github.com/RHEcosystemAppEng/agentic-collections"
CURRENT_CATALOG_SITE_URL = "https://rhecosystemappeng.github.io/agentic-collections-catalog/"
CURRENT_CATALOG_REPO_URL = "https://github.com/RHEcosystemAppEng/agentic-collections-catalog"
CURRENT_SKILLS_REPO_URL = "https://github.com/RHEcosystemAppEng/agentic-collections-skills"

BANNER_MARKER_START = "<!-- legacy-catalog-banner:start -->"
BANNER_MARKER_END = "<!-- legacy-catalog-banner:end -->"


def render_legacy_catalog_banner() -> str:
    """Return a prominent deprecation banner for archived catalog Pages."""
    archived = html.escape(ARCHIVED_REPO_URL, quote=True)
    catalog_site = html.escape(CURRENT_CATALOG_SITE_URL, quote=True)
    catalog_repo = html.escape(CURRENT_CATALOG_REPO_URL, quote=True)
    skills = html.escape(CURRENT_SKILLS_REPO_URL, quote=True)

    return f"""<aside class="legacy-catalog-banner" role="alert" aria-label="Legacy catalog notice">
    <div class="legacy-catalog-banner-inner">
        <p class="legacy-catalog-banner-kicker">Deprecated legacy catalog</p>
        <p class="legacy-catalog-banner-title">You are viewing a <strong>frozen snapshot</strong> from the archived <a href="{archived}" target="_blank" rel="noopener noreferrer">agentic-collections</a> repository.</p>
        <p class="legacy-catalog-banner-body">Active development now lives in two maintained repositories:</p>
        <ul class="legacy-catalog-banner-links">
            <li><a href="{skills}" target="_blank" rel="noopener noreferrer"><strong>agentic-collections-skills</strong> — packs, skills, and Lola modules</a></li>
            <li><a href="{catalog_repo}" target="_blank" rel="noopener noreferrer"><strong>agentic-collections-catalog</strong> — marketplace catalog and collection metadata</a></li>
        </ul>
        <p class="legacy-catalog-banner-cta"><a href="{catalog_site}" target="_blank" rel="noopener noreferrer">Go to the current Red Hat Agentic Catalog →</a></p>
    </div>
</aside>"""


def wrap_banner_markers(fragment: str) -> str:
    return f"{BANNER_MARKER_START}\n{fragment}\n{BANNER_MARKER_END}"


def sync_index_banner(index_path: Path) -> bool:
    """Insert or refresh the legacy banner block in docs/index.html."""
    if not index_path.is_file():
        return False

    content = index_path.read_text(encoding="utf-8")
    wrapped = wrap_banner_markers(render_legacy_catalog_banner())
    pattern = re.compile(
        re.escape(BANNER_MARKER_START) + r".*?" + re.escape(BANNER_MARKER_END),
        re.DOTALL,
    )

    if pattern.search(content):
        updated = pattern.sub(wrapped, content, count=1)
    elif "legacy-catalog-banner" in content:
        return False
    elif "<body>" in content:
        updated = content.replace("<body>", f"<body>\n    {wrapped}", 1)
    else:
        return False

    if updated != content:
        index_path.write_text(updated, encoding="utf-8")
        return True
    return False
