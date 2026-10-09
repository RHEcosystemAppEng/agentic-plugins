# Collection catalog specification

This repository uses a **plugin-local collection catalog**: curated metadata and summaries live under **`<plugin>/.catalog/`** (YAML as the source of record, JSON as a deterministic mirror for consumers that prefer it). **Golden sources** are plugin `SKILL.md` files, `README.md`, and `AGENTS.md`. Catalog files **describe** the collection for tooling and documentation; they are **authored** primarily via the [**create-collection**](.claude/skills/create-collection/SKILL.md) skill (assistant + maintainer + PR review) and must not overwrite READMEs.

**Machine validation:** [`catalog/schema.yaml`](catalog/schema.yaml) (JSON Schema expressed in YAML) and [`scripts/validate_collection_compliance.py`](scripts/validate_collection_compliance.py). These checks are primarily structural and cannot fully evaluate semantic parity with golden-source docs. **Required review gate:** run an AI semantic alignment review (via [`.claude/skills/collection-compliance/SKILL.md`](.claude/skills/collection-compliance/SKILL.md)) to confirm catalog metadata/fragments remain aligned with `SKILL.md`, `README.md`, and `AGENTS.md`.

### `maturity` (required)

| Value | Meaning |
|-------|---------|
| **`GREEN`** | Plugin is ready for promotion to the public catalog. |
| **`ORANGE`** | Collection metadata is maintained under `.catalog/` for validation and future promotion; excluded from the public catalog surface until explicitly moved to **`GREEN`**. |

Set in **`collection.yaml`** as a plain string (`maturity: GREEN` or `maturity: ORANGE`).

## Layout

| Path | Purpose |
|------|---------|
| `<plugin>/.catalog/collection.yaml` | Canonical catalog document (YAML) |
| `<plugin>/.catalog/collection.json` | Deterministic JSON mirror of YAML (CI fails on drift) |
| `<plugin>/.catalog/*.md` | Optional prose fragments, **siblings of** `collection.yaml`. Reference them with **`#<filename>.md`** (quoted in YAML) **on the same field** as inline text would use—for example `documentation_section: '#docs.md'` or `deploy_and_use: '#install.md'`. If inline text in `collection.yaml` for a monitored field exceeds **`CATALOG_INLINE_CHAR_LIMIT`** (500 Unicode code points; see `scripts/collection_validate_lib.py`), move prose here and set **that same field** to the ref. |

**Multiline YAML in `collection.yaml`:** For `contents.description`, each **`summary_markdown`**, and each **`sample_workflows[].workflow`**, authors should use YAML **literal block scalars** (`field: |`) with indented lines—see step 4 of the [**create-collection**](.claude/skills/create-collection/SKILL.md) skill (reference **`rh-sre`** / **`rh-developer`** `.catalog/collection.yaml`). CI does not assert this style; it is a maintainability convention.

### External references (`#…md` on the same field)

- **Path rule:** refs are **siblings of** `collection.yaml` inside **`<plugin>/.catalog/`**. Write **`#install.md`**, not `#.catalog/install.md` (omit the `.catalog/` segment in the string).
- **One field, two shapes:** for **`deploy_and_use`**, **`documentation_section`**, **`mcp_section`**, and **`security_model`**, the value is either **inline** markdown or a **one-line** fragment ref **`#<filename>.md`**. Do **not** use separate `documentation_section_file` / `mcp_section_file` / `security_model_file` keys.
- **Monitored inline length:** for **`summary`**, **`documentation_section`**, **`mcp_section`**, and **`security_model`**, if the value is **inline** (not a `#…md` ref) and longer than **500 Unicode code points**, move the prose to a fragment file and set **that same key** to **`#<filename>.md`** (one line only). For **`deploy_and_use`**, the same limit applies when it is **inline** markdown (not a one-line ref).
- **`deploy_and_use` (two flavors):** (1) **Inline** — markdown in YAML, ≤ **500** code points unless you externalize. (2) **File ref** — one line only: **`#<file>.md`** next to `collection.yaml`. CI resolves the file under **`<plugin>/.catalog/`**.
- **Fragment ref values:** must start with **`#`** (e.g. `#documentation_section.md`). Legacy `#.catalog/…` is accepted and normalized to a sibling path.

### `deploy_and_use` content (install + env + MCP)

Consumers read **`deploy_and_use`** (resolved from inline YAML or from **`#deploy_and_use.md`**) for marketplace install steps and operator setup. **CI does not yet cross-check `mcps.json` or README install parity;** reviewers enforce this section with the [**create-collection**](.claude/skills/create-collection/SKILL.md) and [**collection-compliance**](.claude/skills/collection-compliance/SKILL.md) workflows.

**When `<plugin>/mcps.json` defines one or more MCP servers**, the prose behind **`deploy_and_use`** (inline or fragment) **must** cover, in substance:

1. **Prerequisites** — Cluster/product access, CLIs, operators, or accounts needed before install, aligned with **`README.md`** / **`AGENTS.md`**.
2. **Environment setup** — Example **`export VAR=...`** (or host env equivalent) for **every** environment variable **name** referenced in **`mcps.json`** via **`${VAR}`** in `command`, `args`, or `env`. Variable **names** must match **`mcps.json`** exactly. State that secrets are never committed and must not be echoed in assistant output.
3. **MCP configuration** — Server definitions live in **`mcps.json`** at the plugin root; use **`${...}`** placeholders only; briefly note isolation/network/credentials posture if it affects the user (see existing plugin fragments).
4. **Installation** — At minimum **Lola** (`lola install -f <plugin>`). If the catalog includes **Claude Code** or **Cursor**, include install notes for those hosts (copy the pattern from **`rh-sre/.catalog/deploy_and_use.md`**).

**Layout recommendation:** Prefer **`deploy_and_use: '#deploy_and_use.md'`** and a sibling **`deploy_and_use.md`** so `collection.yaml` stays short. Use the **same section order** as **`rh-sre/.catalog/deploy_and_use.md`**: Prerequisites → Environment setup → Installation (Lola, then Claude Code / Cursor as applicable) → MCP configuration. For a kubeconfig-only MCP story, see **`rh-virt/.catalog/deploy_and_use.md`**.

**Plugins with no MCP servers** (or a trivial single-token env story): a compact **`deploy_and_use: |`** under **500** Unicode code points is acceptable if it still states Lola/repo install and defers detail to **`README.md`** where needed.

**Plugin / install IDs:** default `id` equals the plugin directory name. Overrides: **`rh-virt`** → `openshift-virtualization`; **`ocp-admin`** → `openshift-administration`.

## Source precedence (plugin-local)

When multiple sources could supply the same logical field:

1. **`skills/*/SKILL.md`** (per-skill `name`, `description`, body for `summary_markdown` hints)
2. **`<plugin>/README.md`**
3. **`<plugin>/AGENTS.md`** (intent routing for decision-guide hints, personas)

## Provenance banners

| Artifact | Banner |
|----------|--------|
| `collection.yaml` | Leading `#` comment block: must mention **create-collection** workflow and **golden sources** (SKILL, README, AGENTS). |
| `.catalog/*.md` fragments | Leading HTML `<!-- ... -->` with the same intent. |
| `collection.json` | **No** embedded banner; **CI** regenerates from YAML and fails if the committed file differs. |

## Orchestration vs regular skills

**Primary:** maintainer / assistant judgment while following **create-collection**. **Optional:** `metadata.collection.role: orchestration` in `SKILL.md` frontmatter for clearer compliance checks — not required on every skill.

## Completeness and CI

All **required** schema fields must be present on merge to `main` (no empty placeholders, no `TODO:` / `TBD` in `sample_workflows.workflow`). Author field values so they stay aligned with **`AGENTS.md`**, **`mcps.json`**, and **`README.md`** where those sources define behavior; fragment refs follow [External references](#external-references-md-on-the-same-field). CI runs **`make validate`** (includes structure + **collection compliance**).

## Related

- [`SKILL_DESIGN_PRINCIPLES.md`](SKILL_DESIGN_PRINCIPLES.md) — skill content (Tier 2)
- [`.claude/skills/collection-compliance/SKILL.md`](.claude/skills/collection-compliance/SKILL.md) — validation workflow
