---
name: collection-compliance
description: |
  Diagnose and fix `.catalog/` validation failures (schema, roster, banners, sample workflows, JSON mirror). Use when:
  - `make validate` or CI reports collection compliance errors
  - A PR adds skills but catalog was not updated
  - `collection.json` is out of sync with `collection.yaml`
  - Catalog metadata/fragments might have drifted from README/CLAUDE/SKILL golden sources

  Remediation is via the create-collection workflow and `catalog_yaml_to_json.py`—not by weakening checks.
model: inherit
color: yellow
allowed-tools: Read Glob Grep Bash
---

# Collection compliance

**Audience:** Contributors fixing `.catalog/` CI failures.

**Goal:** Clear reported violations from `scripts/validate_collection_compliance.py` and `scripts/validate_collection_schema.py`, then perform AI semantic alignment review against golden sources.

## Prerequisites

- Run from repository root.
- Read [COLLECTION_SPEC.md](../../COLLECTION_SPEC.md).

## When to Use

- After `make validate-collection-compliance` fails locally or in GitHub Actions.

## Workflow

1. **Re-run** `uv run python scripts/validate_collection_compliance.py` and capture errors (pack path + message).

2. **Classify**
   - **Missing file** — create `.catalog/collection.yaml` via create-collection skill (or `uv run python scripts/bootstrap_catalog.py --pack <pack>` for bootstrap baseline).
   - **Schema** — align YAML with [catalog/schema.yaml](../../catalog/schema.yaml) (includes required **`maturity`**: `GREEN` or `ORANGE`; site listing uses **`GREEN`** only per `pack_registry.get_docs_pack_dirs()`).
   - **Roster** — every `skills/<n>/SKILL.md` must appear once under `contents.skills` or `contents.orchestration_skills` with `name == <n>`.
   - **Banner** — `collection.yaml` must mention `create-collection` and `Golden sources` in the opening `#` block.
   - **`collection.json` drift** — run `uv run python scripts/catalog_yaml_to_json.py --pack <pack>` or `make catalog-mirror-json`.
   - **Fragment refs / length** — `deploy_and_use`, `documentation_section`, `mcp_section`, and `security_model` may be inline or a one-line `#…md` ref naming a sibling file under `.catalog/` (e.g. `#install.md`). Refs must start with `#`. Inline monitored fields over **500** code points must move to a fragment on **that same key** (see COLLECTION_SPEC).
   - **Fragment provenance (`.catalog/*.md`)** — each referenced fragment must start with a leading HTML **`<!-- … -->`** block with the **same intent** as the `collection.yaml` banner: **create-collection** workflow and **Golden sources** (SKILL, README, CLAUDE, marketplace). See [COLLECTION_SPEC.md](../../COLLECTION_SPEC.md) **Provenance banners** (CI does not yet assert this text; fix when reviewing fragments).
   - **Thin `deploy_and_use` (manual review)** — if the pack has **`mcps.json`** MCP servers, **`deploy_and_use`** (inline or **`#deploy_and_use.md`**) should meet [COLLECTION_SPEC.md](../../COLLECTION_SPEC.md) **install + env + MCP** (prerequisites, **`export`** for each **`${VAR}`** name, Lola **`path:`**, MCP notes, optional Claude/Cursor install). CI may not fail; fix via **create-collection** when reviewing PRs.

3. **AI semantic alignment review (required)**
   - Treat scripts as **structural guards only**; they do not fully verify semantic alignment.
   - Compare each pack's catalog metadata and referenced fragments against golden sources:
     - `skills/*/SKILL.md` (names, descriptions, scope, orchestration intent)
     - `README.md` (installation, prerequisites, env variables, usage caveats)
     - `AGENTS.md` (persona, routing, global rules, MCP posture)
     - `marketplace/rh-agentic-collection.yml` (module `path`, module name/description/tags)
   - Fail review if any of these drift conditions are found:
     - Installation steps differ in substance (for example Lola module IDs/paths mismatch)
     - Required env vars in `mcps.json` are missing or inconsistent in `deploy_and_use`
     - Skill inventory/routing intent in catalog contradicts `skills/` + `AGENTS.md`
     - Fragment prose overstates/understates capabilities versus README/skills
   - Remediate via create-collection workflow and then regenerate JSON mirror.

4. **Re-validate** — `make validate-collection-compliance`.

## Dependencies

- create-collection skill (sibling under `.cursor/skills/`)

## Common Issues

- **`skills_decision_guide` with no skills** — guide must be `[]` if the pack has no `skills/` tree.
- **Orchestration miscount** — move skills that delegate end-to-end flows to `orchestration_skills` per COLLECTION_SPEC judgment rules.
- **Install drift** — `README.md` and `.catalog/deploy_and_use(.md)` disagree on Lola commands/module IDs.
- **Env drift** — `${VAR}` names in `mcps.json` are not fully represented in `deploy_and_use`.

## Example usage

```bash
make validate-collection-compliance
uv run python scripts/catalog_yaml_to_json.py --pack rh-developer
make validate-collection-compliance
```
