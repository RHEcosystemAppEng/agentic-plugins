#!/usr/bin/env python3
"""
Build the documentation website by combining pack data and MCP data into data.json.
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any

# Import our data generators
from catalog_site_bundle import bundle_catalog_for_site
from eval_site_enrichment import apply_eval_enrichment
from generate_collection_pages import generate_collection_pages
from generate_pack_data import generate_pack_data
from generate_mcp_data import generate_mcp_data


def load_icons() -> Dict[str, Dict[str, str]]:
    """
    Load icon mappings from docs/icons.json.
    
    Returns:
        Dictionary with 'packs' and 'mcp_servers' icon mappings
    """
    icons_file = Path('docs/icons.json')
    
    if not icons_file.exists():
        print("⚠️  Warning: docs/icons.json not found, icons will not be loaded")
        return {'packs': {}, 'mcp_servers': {}}
    
    try:
        with open(icons_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠️  Warning: Failed to load docs/icons.json: {e}")
        return {'packs': {}, 'mcp_servers': {}}


def build_website():
    """
    Generate the complete website data file.
    """
    print("🔨 Building documentation website...")
    print()

    # Load icons
    print("🎨 Loading icons...")
    icons = load_icons()
    print()

    # Generate pack data
    print("📦 Parsing agentic collections...")
    pack_data = generate_pack_data()
    
    root = Path(__file__).resolve().parent.parent

    # Merge pack icons and optional resolved collection catalog (for Pages UI)
    for pack in pack_data:
        pack_name = pack['name']
        pack['icon'] = icons['packs'].get(pack_name, '')
        catalog_dir = pack.get('catalog_dir', pack_name)
        cat_bundle, cat_warns = bundle_catalog_for_site(catalog_dir, root)
        for w in cat_warns:
            print(f"⚠️  {w}")
        if cat_bundle is not None:
            pack['collection'] = cat_bundle

    # Keep pack cards deterministic and alphabetically ordered.
    pack_data = sorted(pack_data, key=lambda p: p['name'])

    print("📊 Enriching packs with eval/reports (eval/<pack>/<skill>/report.json)...")
    apply_eval_enrichment(pack_data, root)
    print()

    # Generate MCP server data
    print("🔌 Parsing MCP servers...")
    mcp_data = generate_mcp_data()
    
    # Merge MCP server icons
    for server in mcp_data:
        server_name = server['name']
        server['icon'] = icons['mcp_servers'].get(server_name, '')
    
    print()

    # Generate static collection pages (fork-compatible UX)
    print("📄 Generating static collection pages...")
    page_count = generate_collection_pages(pack_data, mcp_data)
    print(f"✅ Generated {page_count} pages in docs/collections/")
    print()

    # Combine into final output
    output = {
        'repository': {
            'name': 'agentic-collections',
            'owner': 'Red Hat Ecosystem Engineering',
            'description': 'Agentic collections for Red Hat platforms and products',
            'url': 'https://github.com/RHEcosystemAppEng/agentic-collections'
        },
        'packs': pack_data,
        'mcp_servers': mcp_data,
        'generated_at': datetime.now(timezone.utc).isoformat()
    }

    # Ensure docs directory exists
    docs_dir = Path('docs')
    docs_dir.mkdir(exist_ok=True)

    # Write data.json
    output_file = docs_dir / 'data.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"✅ Generated {output_file}")
    print()
    print("📊 Summary:")
    print(f"   • {len(pack_data)} agentic collections")
    total_skills = sum(len(p['skills']) for p in pack_data)
    total_agents = sum(len(p['agents']) for p in pack_data)
    print(f"   • {total_skills} skills")
    print(f"   • {total_agents} agents")
    print(f"   • {len(mcp_data)} MCP servers")
    print()

    return 0


if __name__ == '__main__':
    sys.exit(build_website())
