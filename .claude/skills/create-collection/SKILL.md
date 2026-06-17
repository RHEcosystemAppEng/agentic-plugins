---
name: create-collection
description: |
  Author or refresh `<pack>/.catalog/collection.yaml` and related `.catalog/` artifacts from golden sources (SKILL.md, README, AGENTS.md, Lola marketplace). Use when:
  - Adding a new pack or refreshing the collection catalog for GitHub Pages / tooling
  - Aligning catalog narrative, sample workflows, and decision guide with skills on disk
  - Preparing a PR after changing skills or marketplace metadata

  Outputs only under `<pack>/.catalog/` (never overwrite README, SKILL, CLAUDE, or marketplace YAML).
model: inherit
color: blue
allowed-tools: Read Glob Grep Bash
---

# Create collection catalog

**Audience:** Maintainers and assistants updating per-pack `.catalog/` data.

**Goal:** Produce a coherent `collection.yaml` that passes `make validate-collection-compliance`, using human judgment for synthesis—not a blind dump of frontmatter.

## Prerequisites

- Repository root as cwd.
- Read [COLLECTION_SPEC.md](../../COLLECTION_SPEC.md) and [catalog/schema.yaml](../../catalog/schema.yaml).
- Optional: run `uv run python scripts/scaffold_catalog.py <pack>` for a stdout draft roster.

## When to Use

- New marketplace module or new pack directory needs `.catalog/`.
- Skills were added/removed/renamed and roster parity must match disk.
- Marketplace `description` / `version` changed and catalog should reflect it (still edit marketplace in git separately).

## Workflow

1. **Resolve pack** — directory name must appear in `union(marketplace/modules[].path, docs/plugins.json keys)` and exist on disk.

2. **Read sources in order** (precedence):
   - `skills/*/SKILL.md` (frontmatter + body for summaries and orchestration hints)
   - `<pack>/README.md`
   - `<pack>/AGENTS.md` (intent routing → `skills_decision_guide` ideas)
   - Matching row in `marketplace/rh-agentic-collection.yml` (`path` == pack)

3. **Classify skills** — place each skill in `contents.skills` or `contents.orchestration_skills` using maintainer judgment. Optional hint: `metadata.collection.role: orchestration` in `SKILL.md` frontmatter. Names in YAML **must** match the `skills/<name>/` directory name.

4. **Write `<pack>/.catalog/collection.yaml`** — start with the standard **# banner** (see COLLECTION_SPEC). Include every field required by [catalog/schema.yaml](../../catalog/schema.yaml). Keep inline strings under **500 Unicode code points** for monitored fields (`summary`, `documentation_section`, `mcp_section`, `security_model`, and inline **`deploy_and_use`**); otherwise move prose to a sibling **`.md`** and set **the same field** to a one-line ref, e.g. **`documentation_section: '#documentation_section.md'`** or **`deploy_and_use: '#deploy_and_use.md'`** (see COLLECTION_SPEC). Do **not** use parallel `documentation_section_file` / `mcp_section_file` / `security_model_file` keys.

   **`deploy_and_use` / install prose:** Follow [COLLECTION_SPEC.md](../../COLLECTION_SPEC.md) **`deploy_and_use` content (install + env + MCP)**. If **`mcps.json`** defines MCP servers, document prerequisites, **`export`** lines for **every `${VAR}`** name used there, Lola + marketplace **`path:`**, optional Claude/Cursor install when those marketplaces are listed, and an MCP configuration subsection. Prefer **`deploy_and_use: '#deploy_and_use.md'`** plus **`deploy_and_use.md`** structured like **`rh-sre/.catalog/deploy_and_use.md`** (see **`rh-virt/.catalog/deploy_and_use.md`** for a kubeconfig-focused variant).

   **YAML multiline style (`|` literal blocks):** For `contents.description`, every **`summary_markdown`** (regular and orchestration skills), and every **`sample_workflows[].workflow`**, use a **literal block scalar** (`field: |`) instead of a single-quoted string that continues across many YAML lines with spacer blanks. Indent each body line one level deeper than the key line. Inside the block, keep **consecutive lines without empty lines** between the intro, `**Use when:**`, list items, and `**What it does:**` (and similar headings) unless you intentionally want extra paragraph breaks in rendered markdown—reference **`rh-sre`** and **`rh-developer`** `.catalog/collection.yaml` for the house style. Prose with apostrophes (e.g. *What's*) stays readable in `|` without `''` escaping.

5. **Mirror JSON** — from repo root: `uv run python scripts/catalog_yaml_to_json.py --pack <pack>` (or `make catalog-mirror-json`).

6. **Self-review checklist**
   - Every on-disk `skills/<n>/SKILL.md` appears exactly once in `skills` ∪ `orchestration_skills` (orchestration-only skills such as `/remediation` still live under `skills/<name>/`; list them **only** under `contents.orchestration_skills` when they orchestrate others).
   - No `TODO:` / `TBD` in `sample_workflows.workflow`; each workflow includes `User:` and `-` bullets.
   - `skills_decision_guide` empty if the pack has **no** skills; otherwise each `skill_to_use` matches a skill dir.
   - `resources[].url` set; `embedded_doc` only if that path exists under the pack.
   - **Install / deploy (`deploy_and_use`):** **inline** (≤ **500** code points) *or* one-line **`#deploy_and_use.md`** ref (see [COLLECTION_SPEC.md](../../COLLECTION_SPEC.md) **install + env + MCP**). If **`mcps.json`** has MCP servers: fragment (or inline) must include prerequisites, **`export`** examples for each **`${VAR}`** name from **`mcps.json`**, Lola/marketplace **`path:`**, and MCP configuration notes; add Claude Code / Cursor install when **`marketplaces`** lists them. Fragments use the HTML provenance banner. Use **`mcps.json`**, not `.mcp.json`.
   - **Other long blocks:** **`documentation_section`**, **`mcp_section`**, and **`security_model`** follow **`deploy_and_use`**: inline markdown (≤ **500** code points) **or** one-line **`#fragment.md`** on that same key (sibling under `.catalog/`; no `.catalog/` prefix in the YAML string).
   - **Publication-style metadata:** **`maturity`** (**required**) — `GREEN` (listed on GitHub Pages catalog) or `ORANGE` (in-repo only until promoted). Also when useful: `support_level`, `author`, `homepage`, `keywords`, `legal_resources` (URLs only).
   - **`version` / listing fields:** Align `version` and core listing copy with the matching **`marketplace/rh-agentic-collection.yml`** row (`path` == pack); do not bump marketplace YAML from the catalog workflow.
   - **Multiline fields:** `contents.description`, all **`summary_markdown`**, and all **`sample_workflows[].workflow`** use **`|`** block scalars (not long single-quoted multiline); content lines are compact unless extra blank lines are deliberate for markdown.

7. **Validate** — `make validate-collection-compliance` before commit.

## Dependencies

- `make validate-collection-compliance`
- `uv run python scripts/scaffold_catalog.py <pack>` (optional)

## Common Issues

- **CI: `collection.json` drift** — regenerate with `make catalog-mirror-json`.
- **Roster errors** — YAML `name` must equal the skill folder name, not a display alias.
- **Empty support pack** — if there are no `skills/`, use empty `skills`, `orchestration_skills`, and `skills_decision_guide: []`.
- **Unreadable multiline YAML** — replace spanning `'`…`'` blocks with **`field: |`** and indented lines; see step 4 **YAML multiline style**.
- **Thin `deploy_and_use`** — pack has **`mcps.json`** but catalog only says “see README”; add **Environment setup** (`export` for each **`${VAR}`**) and **MCP configuration** per COLLECTION_SPEC (use **`#deploy_and_use.md`** like **rh-sre** / **rh-virt**).

## Example usage

```bash
uv run python scripts/scaffold_catalog.py rh-sre
uv run python scripts/catalog_yaml_to_json.py --pack rh-sre
make validate-collection-compliance
```
