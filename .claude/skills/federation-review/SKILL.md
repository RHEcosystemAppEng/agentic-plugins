---
name: federation-review
description: |
  Validate a federation PR: license check, automated validation, and Lola marketplace verification.

  Use when:
  - "Review federation PR"
  - "Validate federated pack"
  - User mentions "federation", "federate", or "external pack"

  NOT for direct contributions (use /agentic-contribution-skill instead).
model: inherit
color: yellow
license: Apache-2.0
metadata:
  author: Red Hat Ecosystem Engineering
  version: 2.0.0
  category: internal-tooling
---

# Federation Review

Validate an external agentic pack proposed for federation in a PR. Checks license compatibility, runs automated validation, and verifies the module is loadable by Lola.

## Prerequisites

- Access to the agentic-collections repository
- `uv` installed for running validation scripts
- `lola` installed for marketplace verification
- Optional: `gitleaks` installed for credential scanning

## When to Use This Skill

Use this when reviewing a PR that adds or modifies a federated module in `marketplace/rh-agentic-collection.yml`. The contributor creates the PR — this skill helps the reviewer validate it.

## Workflow

### Phase 1: Identify the federated module

1. **Action:** Read the PR diff to find the new or changed module entry in `marketplace/rh-agentic-collection.yml`
2. **Extract:**
   - Module name
   - Repository URL
   - Ref (required 40-character commit SHA)
   - Path within the repo
3. **Validate ref format** before continuing:
   - Must be exactly 40 hexadecimal characters
   - Reject branch names, tags, or short SHAs
4. **Output to user:** Summary of the proposed federated module

### Phase 1.5: Validate catalog against external repo

Cross-check `federation/modules/<name>/.catalog/` against the external pack at the pinned `ref`, and verify `docs/plugins.json` / marketplace alignment.

1. **Action:** Run the catalog cross-check script (skip if the PR does not add a federation catalog yet):

```bash
uv run python scripts/validate_federation_catalog.py \
  --module-name <module-name> \
  --repo-url <repo-url> \
  --ref <commit-sha> \
  --pack-path <path> \
  --module-json '<module-json-from-marketplace-yaml>'
```

2. **Output to user:** Pass/fail for each check:
   - Catalog present under `federation/modules/<name>/.catalog/`
   - Collection compliance (schema, fragments, JSON mirror)
   - **External skill roster** — catalog `contents.skills` matches `skills/` in the linked repo at `ref`
   - `docs/plugins.json` title matches catalog `name:`; catalog `id:` matches module name
   - Marketplace `version`, `description`, and `repository` align with catalog

3. **If the catalog is missing** from the PR, report that cross-check was skipped and request the contributor add `federation/modules/<name>/.catalog/` before merge.

### Phase 2: License check

1. **Action:** Clone the repository at the pinned commit and check for a LICENSE file:

```bash
git clone --quiet --no-checkout <repo-url> /tmp/federation-review
cd /tmp/federation-review && git checkout --quiet <commit-sha>
cat LICENSE
```

2. **Evaluate** license compatibility with Apache 2.0:
   - Compatible: Apache-2.0, MIT, BSD-2-Clause, BSD-3-Clause
   - Incompatible: GPL, AGPL, SSPL, proprietary
3. **Output to user:** License found and compatibility result. Ask user to confirm.

### Phase 3: Run automated validation

1. **Action:** Run the validation script (``--ref`` is required and must be a commit SHA):

```bash
uv run python scripts/validate_federation.py <repo-url> --ref <commit-sha> --pack-path <path> --module-json '<module-json>'
```

2. **Output to user:** The full validation report with pass/fail for each check:
   - Federation ref (40-character commit SHA)
   - Clone and access at pinned commit
   - Lola module schema (name, description, version, repository)
   - Tier 1 (agentskills.io spec)
   - Tier 2 (design principles)
   - MCP version pinning
   - Credential scan (gitleaks)

### Phase 4: Lola marketplace verification

1. **Action:** Verify the module is loadable by Lola using the PR branch:

```bash
MARKET="federation-review-$(openssl rand -hex 4)"
lola market add "$MARKET" https://raw.githubusercontent.com/<owner>/<repo>/<branch>/marketplace/rh-agentic-collection.yml
lola market ls "$MARKET"
lola market rm "$MARKET"
```

2. **Check:** The federated module appears in the module list with correct name, version, and description.
3. **Output to user:** Lola verification result (visible or not, with details).

### Phase 5: Summary

Present a combined summary to the user:

| Check | Result |
|-------|--------|
| Catalog cross-check | Passed / Failed / Skipped (no catalog in PR) |
| License | Compatible / Incompatible / Not found |
| Automated validation | All passed / N checks failed |
| Lola verification | Module visible / Not visible |

**Output to user:** Overall recommendation (approve or request changes) with details on any failures.

## Dependencies

### Required MCP Servers

None — this skill uses CLI tools (`gh`, `git`, `uv`, `lola`) and repository scripts only.

### Required MCP Tools

None — no MCP tools are invoked.

### Related Skills

- `/agentic-contribution-skill` — for direct contributions (create or import skills into this repo)

### Reference Documentation

**Internal:**
- [Federation Review Guide](../../../FEDERATION_REVIEW_GUIDE.md) — full evaluation criteria
- [CONTRIBUTING.md](../../../CONTRIBUTING.md) — contribution paths overview
- [SKILL_DESIGN_PRINCIPLES.md](../../../SKILL_DESIGN_PRINCIPLES.md) — Tier 2 design principles

**Scripts:**
- `scripts/validate_federation.py` — external pack validation at pinned ref
- `scripts/validate_federation_catalog.py` — federation catalog cross-check vs external repo

## Human-in-the-Loop

This skill requires human confirmation at one point:
1. **License compatibility** (Phase 2): The reviewer confirms whether the detected license is acceptable.

## Example Usage

```
User: /federation-review
Skill: Reading PR diff...
       Found federated module: cursor-sdk
       Repository: https://github.com/cursor/plugins
       Path: cursor-sdk
       Ref: a1b2c3d4e5f6789012345678901234567890abcd

       Checking catalog vs external repo...
       uv run python scripts/validate_federation_catalog.py ...
       ✅ external_skill_roster matches linked repo at ref
       ✅ plugins.json title matches catalog

       Checking license at pinned commit...
       LICENSE file: MIT
       MIT is compatible with Apache 2.0. Confirm? [Y/n]
User: Y
Skill: Running automated validation...
       ✅ Clone & access
       ✅ Lola module schema
       ❌ Tier 1: 1/3 skills failed
       ✅ MCP pinning
       ✅ Credential scan

       Verifying Lola marketplace...
       ✅ Module "cursor-sdk" visible in marketplace

       Summary:
       - Catalog cross-check: ✅ roster and metadata aligned
       - License: ✅ MIT (compatible)
       - Validation: ❌ Tier 1 failures
       - Lola: ✅ Module loadable
       Recommendation: Request changes (Tier 1 failures need fixing)
```
