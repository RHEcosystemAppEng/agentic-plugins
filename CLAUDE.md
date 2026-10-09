# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Repository Is

This is a **skills source repository** — one of potentially many that feed into the [agentic-catalog](https://github.com/RHEcosystemAppEng/agentic-catalog).  It contains agent plugins with skills, MCP server configurations, AI-optimized documentation, and catalog metadata for Red Hat platforms.

Contributors work here to create, improve, and validate skills. An internal process periodically fetches content from this repository (and others like it) to build the unified catalog and marketplace. **This repo does not serve the marketplace directly** — it is a source of skills that the catalog aggregates.

## Repository Structure

```
agentic-plugins/
├── catalog-info.yaml    # Root Location — entry point for Compass ingestion
├── system.yaml          # System entity (agentic-plugins) — models the whole repo
├── rh-sre/              # Site Reliability Engineering plugin (reference implementation)
├── rh-developer/        # Developer tools plugin
├── ocp-admin/           # OpenShift administration plugin
├── rh-virt/             # Virtualization management plugin
├── rh-basic/            # Getting started plugin
├── rh-ai-engineer/      # AI/ML engineering plugin
├── rh-automation/       # IT automation plugin
├── mcps/                # MCP server Compass manifests (3 MCPServer entities)
├── eval/                # Skill evaluation reports (report.json + report.md per skill)
├── scripts/             # Validation and CI helper scripts
├── catalog/             # JSON Schema for .catalog/collection.yaml validation
│   └── schema.yaml
└── .claude/skills/      # Repo-level Claude Code skills (contribution, linting, compliance)
```

### `catalog/schema.yaml`

This file defines the JSON Schema used by `validate_collection_schema.py` and `validate_collection_compliance.py` to validate each plugin's `.catalog/collection.yaml`. It is not related to the catalog marketplace repository — it is a validation artifact that ensures catalog metadata is well-formed before the catalog build process consumes it.

### Agent Plugin Architecture

Each plugin is persona-specific and follows this structure:

```
<plugin-name>/
├── catalog-info.yaml    # Location entity — indexes this plugin's Compass manifests
├── <plugin-name>-plugin.yaml  # AiResource (type: plugin) — defines the plugin itself
├── AGENTS.md            # AI Context Module instruction routing (persona, skills, rules)
├── README.md            # Plugin description, persona, target marketplaces
├── mcps.json            # MCP server configurations (uses env vars for credentials)
├── .catalog/            # Collection metadata consumed by the catalog build process
│   ├── collection.yaml  # Plugin catalog definition (golden source for catalog)
│   └── collection.json  # Deterministic JSON mirror of collection.yaml
├── skills/              # Specialized task executors (including orchestration skills)
│   └── <skill>/
│       ├── SKILL.md     # Skill definition with YAML frontmatter
│       └── catalog-info.yaml  # AiResource (type: skill) — Compass manifest
└── docs/                # AI-optimized knowledge base (optional, rh-sre reference)
```

### Relationship with the Catalog

Each plugin's `.catalog/` directory contains metadata that describes the plugin for the marketplace. This metadata stays here, alongside the skills it describes. The catalog build process reads it from this repo to assemble the unified marketplace. The golden sources are always `SKILL.md`, `AGENTS.md`, `README.md`, and `mcps.json` — `.catalog/` is derived from them, never the other way around.

### Compass / Backstage Manifests

The repository is registered in [Red Hat Compass](https://compass.redhat.com) (internal Backstage instance) through a hierarchy of Backstage entity manifests. All manifests use `apiVersion: backstage.io/v1alpha1` except MCPServer entities which use `apiVersion: mcp/v1beta1`.

#### Entity Kinds

| Kind | Purpose | spec.type | Count |
|------|---------|-----------|-------|
| **Location** | Index that references other manifest files | — | 6 (1 root + 4 plugins + 1 mcps) |
| **System** | Top-level grouping for the repository | — | 1 (`agentic-plugins`) |
| **AiResource** | Skills and plugin definitions | `plugin` (plugins) / `skill` (skills) | 4 plugins + 37 skills |
| **MCPServer** | MCP server configurations | `local` / `remote` | 3 |

#### Location Hierarchy

Compass ingests a single root Location. Everything else is discovered through delegation:

```
catalog-info.yaml (root Location)
├── system.yaml                         → System: agentic-plugins
├── ocp-admin/catalog-info.yaml         → Location → ocp-admin-plugin.yaml + 8 skills
├── rh-sre/catalog-info.yaml            → Location → rh-sre-plugin.yaml + 13 skills
├── rh-virt/catalog-info.yaml           → Location → rh-virt-plugin.yaml + 10 skills
├── rh-basic/catalog-info.yaml          → Location → rh-basic-plugin.yaml + 6 skills
└── mcps/catalog-info.yaml              → Location → 3 MCPServers
```

#### Entity Relationships

Use `dependsOn` / `dependencyOf` for custom kinds (`AiResource`, `MCPServer`); do not use `partOf` / `hasPart` on those kinds. Compass does not auto-generate inverse relations (COMPASS-1288) — declare both sides on every edge.

Full relationship matrix, bidirectional policy, entity ref formats, and file touch lists: [`.claude/skills/compass-manifest-maintenance/references/relationship-rules.md`](.claude/skills/compass-manifest-maintenance/references/relationship-rules.md). Use the **compass-manifest-maintenance** skill when adding or updating manifests. CI enforces structural rules via `scripts/validate_compass_manifests.py` (`make validate-compass-manifests`).

#### Namespaces

All entities (skills, plugins, and MCP servers) share a single namespace: `ai5-marketplace`. The root System `agentic-plugins` uses the `default` namespace.

#### Entity Reference Formats

- Skills: `airesource:ai5-marketplace/<skill-name>`
- Plugins: `airesource:ai5-marketplace/<plugin-name>`
- MCP servers: `mcpserver:ai5-marketplace/<server-name>`

#### Adding Compass Manifests for a New Skill

When adding a skill, create `skills/<skill-name>/catalog-info.yaml`. Set `spec.lifecycle` from the plugin manifest (`<plugin>/<plugin>-plugin.yaml`); default to the plugin value and ask the user before changing it — a skill may match the plugin or use a **less mature** lifecycle only (never above the plugin). New plugins default the plugin to `development`.

```yaml
apiVersion: backstage.io/v1alpha1
kind: AiResource
metadata:
  name: <skill-name>
  namespace: ai5-marketplace
  title: <Skill Title>
  description: >
    <skill description>
  labels:
    distribution: external
  annotations:
    backstage.io/source-location: >-
      url:https://github.com/RHEcosystemAppEng/agentic-plugins/blob/main/<plugin>/skills/<skill>/SKILL.md
  tags:
    - ai-skill
  links:
    - url: https://github.com/RHEcosystemAppEng/agentic-plugins
      title: Source Repository
      icon: github
spec:
  type: skill
  lifecycle: <plugin-lifecycle>  # from <plugin>-plugin.yaml; same or less mature than plugin
  owner: group:redhat/ai5-marketplace
  disciplines:
    - <discipline>
  categories:
    - <category>
  agents: []
  dependsOn:
    - airesource:ai5-marketplace/<plugin-name>
    # Add mcpserver and airesource (skill) dependencies as needed
    - mcpserver:ai5-marketplace/<server-name>
```

Then update **both sides** of every relationship:
1. Add the file as a target in the plugin's `catalog-info.yaml` Location
2. Add the skill to the plugin's `dependencyOf` list in `<plugin>-plugin.yaml`
3. Add the skill to each referenced MCP server's `dependencyOf` list in `mcps/<server>.yaml`
4. If the skill depends on other skills, add `dependencyOf` entries in those skills' manifests

## Contributing

Skills are added directly to this repository, inside an existing plugin. The contributor opens a PR, skills are reviewed and merged, and maintainers own them from that point. Use `/agentic-contribution-skill` in Claude Code or follow [CONTRIBUTING.md](CONTRIBUTING.md).

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
   uv run python scripts/validate_skills_tier1.py <plugin>/skills/<skill-name>/SKILL.md
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

MCP servers are configured in `<plugin>/mcps.json`:
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

The `rh-sre` plugin demonstrates advanced documentation patterns for token optimization:

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
- Compass manifests: `catalog-info.yaml` (Locations), `<plugin-name>-plugin.yaml` (plugin AiResource), `system.yaml` (System entities)
- Docs: Lowercase with dashes, categorized by directory

## Development Workflow

### Creating a New Agent Plugin

1. Create plugin folder: `<plugin-name>/`
2. Add `README.md` with description, persona, marketplaces
3. Add `AGENTS.md` with persona, skill-first rule, intent routing table, MCP servers, and global rules (see [rh-ai-engineer/AGENTS.md](rh-ai-engineer/AGENTS.md) for reference)
4. Create `skills/` directory
5. Add `mcps.json` when the plugin integrates MCP servers (use `${VAR}` for secrets)
6. Create Compass manifests:
   - `<plugin-name>-plugin.yaml` — AiResource with `type: plugin`, `system: agentic-plugins`
   - `catalog-info.yaml` — Location targeting the plugin file and all skill catalog-info.yaml files
7. Add the plugin's `catalog-info.yaml` as a target in the root `catalog-info.yaml`
8. Update main `README.md` table with link

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
5. Update the plugin's `AGENTS.md` intent routing table to include the new skill
6. Run **compass-manifest-maintenance** (`.claude/skills/compass-manifest-maintenance/`) to create or update Compass manifests — skill `catalog-info.yaml`, plugin Location targets, plugin/MCP inverse `dependencyOf` (see "Adding Compass Manifests for a New Skill")
7. Run `make validate-compass-manifests` (or full `make validate`)
8. Test with `Skill` tool invocation
9. Validate with `uv run python scripts/validate_skills_tier1.py <plugin>/skills/<skill-name>/SKILL.md`

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

The most complete plugin, demonstrating:
- Full skill orchestration (13 skills)
- Orchestration skills (remediation skill orchestrates 6 skills)
- AI-optimized documentation system
- MCP server integration
- Red Hat Lightspeed platform integration

When creating new plugins, use `rh-sre` as the architectural reference.

### rh-virt (Quality-Controlled Pattern)

Demonstrates skill quality standardization:
- Comprehensive skill templates (`SKILL_TEMPLATE.md`)
- Risk-based color coding (cyan/green/blue/yellow/red/magenta)
- Mandatory Common Issues and Example Usage sections
- Consistent section ordering and formatting

Use `rh-virt` as reference for plugins requiring high consistency and maintainability.

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
10. **Persona-focused design** - Each plugin serves specific user roles

**Validation:**
- Design principles and requirements: [SKILL_DESIGN_PRINCIPLES.md](./SKILL_DESIGN_PRINCIPLES.md)
- Automated linter (Tier 1): `uv run python scripts/validate_skills_tier1.py`
- Full validation: `make validate`
