# Component Lifecycle Model

Canonical reference for `spec.lifecycle` on skills, pack plugins, and MCP servers in this repository.

Compass manifests (`catalog-info.yaml`, `*-plugin.yaml`, `mcps/*.yaml`) declare lifecycle so owners, reviewers, and the catalog publication pipeline share one maturity vocabulary.

## Valid lifecycle values

| Value | Meaning |
|-------|---------|
| `development` | In active development, not ready for consumption |
| `beta` | Functional and available for early adoption; may have rough edges |
| `GA` | Generally Available — production-ready, fully supported |
| `deprecated` | Still functional but no longer maintained — consumers should migrate |
| `archived` | End of life — preserved for reference only, not maintained |

These are the **only** allowed values for `spec.lifecycle`. CI rejects any other string (including the former name `production`; use `GA` instead).

### Maturity ordering (ceiling)

For the skill-vs-pack ceiling rule, maturity ranks as:

```text
development < beta < GA
```

`deprecated` and `archived` are retirement states. They are not ranked against the ceiling (see [Ceiling rule](#ceiling-rule)).

## How owners change lifecycle

1. Edit `spec.lifecycle` in the component’s Compass manifest:
   - Skill: `<pack>/skills/<skill-name>/catalog-info.yaml`
   - Pack plugin: `<pack>/<pack>-plugin.yaml`
   - MCP server: `mcps/<server-name>.yaml`
2. Open a pull request with the change.
3. Reviewers approve the transition; merge is the governance gate.

There is **no enforced state machine**. Owners may move between any allowed values (for example `development` → `GA`) when the PR is justified. Prefer gradual promotion (`development` → `beta` → `GA`) and explicit retirement (`GA`/`beta` → `deprecated` → `archived`) when that matches product reality.

### Defaults when authoring

- **New pack plugin:** default `development` (confirm before raising maturity).
- **New skill:** copy `spec.lifecycle` from the parent pack plugin. The skill may match the plugin or use a **less mature** value only — never above the plugin (see ceiling rule).

## Ceiling rule

A skill’s lifecycle must not exceed its parent pack plugin’s lifecycle:

```text
skill lifecycle ≤ pack lifecycle
```

Examples:

| Pack | Skill | Result |
|------|-------|--------|
| `beta` | `beta` | Allowed |
| `GA` | `development` | Allowed |
| `development` | `beta` | **Rejected** |
| `beta` | `GA` | **Rejected** |

Retirement exemptions: if the skill or the pack plugin is `deprecated` or `archived`, the ceiling comparison is skipped for that entity (deprecated/archived plugins skip enforcement for all of their skills).

Enforced by `scripts/validate_lifecycle_ceiling.py` (`make validate-lifecycle-ceiling`, included in `make validate-structure`).

## Interaction with `distribution`

Manifests may set `metadata.labels.distribution` (commonly `external`). Lifecycle and distribution together control external publication:

| Lifecycle | `distribution: external` | External publication |
|-----------|--------------------------|----------------------|
| `development` | any | **Never** — always internal-only |
| `beta` | `external` | Eligible for external publish |
| `GA` | `external` | Eligible for external publish |
| `deprecated` | any | **Never** — always internal-only |
| `archived` | any | **Never** — always internal-only |

Notes:

- Only `beta` and `GA` components with `distribution: external` are published externally.
- `deprecated` and `archived` are always internal-only, regardless of the distribution label.
- `development` is always internal-only. CI emits a **non-blocking warning** when `distribution: external` is paired with `lifecycle: development`, because the label will not cause external publication.

## Catalog publication pipeline

The catalog build/publication pipeline (APPENG-6026) uses lifecycle (and distribution) when routing components for internal vs external publication. Lifecycle awareness for that pipeline is tracked under APPENG-6026; this repository’s role is to keep `spec.lifecycle` accurate and CI-valid so the pipeline can trust the field.

## Related documentation

- Compass relationship and authoring rules: [`.claude/skills/compass-manifest-maintenance/references/relationship-rules.md`](.claude/skills/compass-manifest-maintenance/references/relationship-rules.md)
- Validator: [`scripts/validate_lifecycle_ceiling.py`](scripts/validate_lifecycle_ceiling.py)
