# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Repository Is

This is a **skills source repository** — one of potentially many that feed into the [agentic-catalog](https://github.com/RHEcosystemAppEng/agentic-catalog).  It contains agentic packs with skills, MCP server configurations, AI-optimized documentation, and catalog metadata for Red Hat platforms.

Contributors work here to create, improve, and validate skills. An internal process periodically fetches content from this repository (and others like it) to build the unified catalog and marketplace. **This repo does not serve the marketplace directly** — it is a source of skills that the catalog aggregates.

## Repository Structure

```
agentic-plugins/
├── rh-sre/              # Site Reliability Engineering pack (reference implementation)
├── rh-developer/        # Developer tools pack
├── ocp-admin/           # OpenShift administration pack
├── rh-virt/             # Virtualization management pack
├── rh-basic/            # Getting started pack
├── rh-ai-engineer/      # AI Engineering pack
├── rh-automation/       # Automation pack
├── rh-support-engineer/ # Support engineering pack
├── eval/                # Skill evaluation reports (report.json + report.md per skill)
├── scripts/             # Validation and CI helper scripts
├── catalog/             # JSON Schema for .catalog/collection.yaml validation
│   └── schema.yaml
└── .claude/skills/      # Repo-level Claude Code skills (contribution, linting, compliance)
```

### `catalog/schema.yaml`

This file defines the JSON Schema used by `validate_collection_schema.py` and `validate_collection_compliance.py` to validate each pack's `.catalog/collection.yaml`. It is not related to the catalog marketplace repository — it is a validation artifact that ensures catalog metadata is well-formed before the catalog build process consumes it.

### Agentic Pack Architecture

Each pack is persona-specific and follows this structure:

```
<pack-name>/
├── AGENTS.md            # AI Context Module instruction routing (persona, skills, rules)
├── README.md            # Pack description, persona, target marketplaces
├── mcps.json            # MCP server configurations (uses env vars for credentials)
├── .catalog/            # Collection metadata consumed by the catalog build process
│   ├── collection.yaml  # Pack catalog definition (golden source for catalog)
│   └── collection.json  # Deterministic JSON mirror of collection.yaml
├── skills/              # Specialized task executors (including orchestration skills)
│   └── <skill>/
│       └── SKILL.md     # Skill definition with YAML frontmatter
└── docs/                # AI-optimized knowledge base (optional, rh-sre reference)
```

### Relationship with the Catalog

Each pack's `.catalog/` directory contains metadata that describes the pack for the marketplace. This metadata stays here, alongside the skills it describes. The catalog build process reads it from this repo to assemble the unified marketplace. The golden sources are always `SKILL.md`, `AGENTS.md`, `README.md`, and `mcps.json` — `.catalog/` is derived from them, never the other way around.

## Contributing

Skills are added directly to this repository, inside an existing pack. The contributor opens a PR, skills are reviewed and merged, and maintainers own them from that point. Use `/agentic-contribution-skill` in Claude Code or follow [CONTRIBUTING.md](CONTRIBUTING.md).

## Working with Skills

**Skills** (`skills/<skill-name>/SKILL.md`):
- Single-purpose task executors
- Encapsulate specific tool access and domain knowledge
- Invoked via the `Skill` tool
- Structure: YAML frontmatter + implementation guide

**Key Pattern**: Skills encapsulate tools; orchestration skills invoke other skills. Never call MCP tools directly — always go through skills.

## Skill and Agent Requirements

**CRITICAL:** EVERY SKILL and AGENT must comply with:
- **Tier 1:** agentskills.io specification (AUTOMATED via linter)
- **Tier 2:** Repository design principles (MANUAL review)

The catalog's internal process applies its own evaluation and assigns a scorecard, but skills must pass Tier 1 and Tier 2 here before merging.

**Before committing any skill:**

1. **Run automated validation (Tier 1):**
   ```bash
   uv run python scripts/validate_skills_tier1.py <pack>/skills/<skill-name>/SKILL.md
   ```

2. **Manual review (Tier 2):**
   - Review [SKILL_DESIGN_PRINCIPLES.md](SKILL_DESIGN_PRINCIPLES.md) for complete requirements
   - Use appropriate template (general or collection-specific)

3. **Full validation:**
   ```bash
   make validate
   ```

**Documentation:**
- [SKILL_DESIGN_PRINCIPLES.md](SKILL_DESIGN_PRINCIPLES.md) - Complete design principles, templates, and rationale

### MCP Server Integration

MCP servers are configured in `<pack>/mcps.json`:
```json
{
  "mcpServers": {
    "server-name": {
      "command": "podman|docker|npx",
      "args": ["..."],
      "env": {
        "VAR_NAME": "${VAR_NAME}"
      },
      "security": {
        "isolation": "container",
        "network": "local",
        "credentials": "env-only"
      }
    }
  }
}
```

**Critical**: Never hardcode credentials. Always use `${ENV_VAR}` references.

## AI-Optimized Documentation (rh-sre Reference)

The `rh-sre` pack demonstrates advanced documentation patterns for token optimization:

### Semantic Indexing System

Located in `docs/.ai-index/`:
- `semantic-index.json` - Document metadata with semantic keywords
- `task-to-docs-mapping.json` - Pre-computed doc sets for common workflows
- `cross-reference-graph.json` - Document relationship graph

**Usage Pattern** (for AI agents reading rh-sre docs):
1. Read `semantic-index.json` first (~200 tokens)
2. Match task keywords to relevant docs
3. Load only required docs using progressive disclosure
4. Follow cross-references for related content

### Documentation Standards

All docs include YAML frontmatter:
```yaml
---
title: Document Title
category: rhel|ansible|openshift|insights|references
sources:
  - title: Official Red Hat Doc Title
    url: https://docs.redhat.com/...
    date_accessed: YYYY-MM-DD
tags: [keyword1, keyword2]
semantic_keywords: [phrases for AI discovery]
use_cases: [task_ids]
related_docs: [cross-references]
last_updated: YYYY-MM-DD
---
```

**Source Attribution**: All content derived from official Red Hat documentation (see `docs/SOURCES.md`)

## Naming Conventions

### Folders
- Lowercase with dash separators: `rh-sre`, `ocp-admin`
- Red Hat prefix: `rh-`
- Acronyms for brevity: `ocp` (OpenShift Container Platform), `virt` (Virtualization)

### Files
- Skills: `skills/<skill-name>/SKILL.md` (uppercase SKILL.md)
- Docs: Lowercase with dashes, categorized by directory

## Development Workflow

### Creating a New Agentic Pack

1. Create pack folder: `<pack-name>/`
2. Add `README.md` with description, persona, marketplaces
3. Add `AGENTS.md` with persona, skill-first rule, intent routing table, MCP servers, and global rules (see [rh-ai-engineer/AGENTS.md](rh-ai-engineer/AGENTS.md) for reference)
4. Create `skills/` directory
5. Add `mcps.json` when the pack integrates MCP servers (use `${VAR}` for secrets)
6. Update main `README.md` table with link

### Adding a Skill

1. Create `skills/<skill-name>/SKILL.md`
2. Define YAML frontmatter with mandatory fields:
   - `name`, `description` (agentskills.io spec)
   - `model` (inherit|sonnet|haiku), `color` (cyan|green|blue|yellow|red|magenta) - Repository requirement
   - Optional: `metadata` for custom fields (author, priority, version)
3. Follow [SKILL_DESIGN_PRINCIPLES.md](SKILL_DESIGN_PRINCIPLES.md) for:
   - Section structure and ordering
   - Prerequisites with verification
   - Workflow with precise parameters
   - Dependencies declaration
4. Include concrete examples and complete error handling
5. Update the pack's `AGENTS.md` intent routing table to include the new skill
6. Test with `Skill` tool invocation
7. Validate with `uv run python scripts/validate_skills_tier1.py <pack>/skills/<skill-name>/SKILL.md`

**Collection-Specific Standards:**
- **rh-virt**: Follow `rh-virt/SKILL_TEMPLATE.md` for enhanced quality standards including mandatory Common Issues and Example Usage sections

### Adding Documentation (rh-sre pattern)

1. Create doc in appropriate category: `docs/{rhel,ansible,openshift,insights,references}/`
2. Add complete YAML frontmatter with official sources
3. Follow content structure: Overview -> When to Use -> Main Content -> Related Docs
4. Lead with code examples (production-ready, not toy examples)
5. Update `docs/INDEX.md` navigation structure
6. Update `docs/SOURCES.md` with source URLs

## Integration with Red Hat Platforms

### Red Hat Lightspeed MCP Server
- CVE vulnerability data and risk assessment
- System inventory and compliance
- Remediation playbook generation
- Requires: `LIGHTSPEED_CLIENT_ID`, `LIGHTSPEED_CLIENT_SECRET` env vars

### Ansible MCP Server
- Playbook execution and job tracking
- Status monitoring
- Container-isolated execution

## Reference Implementations

### rh-sre (Full-Featured Reference)

The most complete pack, demonstrating:
- Full skill orchestration (10 skills)
- Orchestration skills (remediation skill orchestrates 6 skills)
- AI-optimized documentation system
- MCP server integration
- Red Hat Lightspeed platform integration

When creating new packs, use `rh-sre` as the architectural reference.

### rh-virt (Quality-Controlled Pattern)

Demonstrates skill quality standardization:
- Comprehensive skill templates (`SKILL_TEMPLATE.md`)
- Risk-based color coding (cyan/green/blue/yellow/red/magenta)
- Mandatory Common Issues and Example Usage sections
- Consistent section ordering and formatting

Use `rh-virt` as reference for packs requiring high consistency and maintainability.

## Key Principles

### Core Architecture
1. **Skills encapsulate tools** - Never call MCP tools directly; always invoke skills
2. **Orchestration skills invoke other skills** - Complex workflows delegate to specialized skills
3. **agentskills.io compliance** - All skills follow the official specification
4. **Progressive disclosure** - Load docs incrementally based on task needs

### Security & Configuration
5. **Environment variables for secrets** - Never hardcode credentials
6. **Never expose credential values** - Check env vars are set, but NEVER print their values in output
7. **MCP server integration** - Use `mcps.json` with environment variable references

### Documentation & Quality
8. **Official sources only** - Document all sources in SOURCES.md
9. **Production-ready examples** - No toy code, include error handling
10. **Persona-focused design** - Each pack serves specific user roles

**Validation:**
- Design principles and requirements: [SKILL_DESIGN_PRINCIPLES.md](./SKILL_DESIGN_PRINCIPLES.md)
- Automated linter (Tier 1): `uv run python scripts/validate_skills_tier1.py`
- Full validation: `make validate`
