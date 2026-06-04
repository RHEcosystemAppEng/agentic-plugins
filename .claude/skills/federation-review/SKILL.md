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
   - Ref (if provided)
   - Path within the repo
   - License (if declared)
3. **Output to user:** Summary of the proposed federated module

### Phase 2: License check

1. **Action:** Check the repository for a LICENSE file:

```bash
git clone --quiet --depth 1 <repo-url> /tmp/federation-review
cat /tmp/federation-review/LICENSE
```

2. **Evaluate** license compatibility with Apache 2.0:
   - Compatible: Apache-2.0, MIT, BSD-2-Clause, BSD-3-Clause
   - Incompatible: GPL, AGPL, SSPL, proprietary
3. **Output to user:** License found and compatibility result. Ask user to confirm.

### Phase 3: Run automated validation

1. **Action:** Run the validation script:

```bash
uv run python scripts/validate_federation.py <repo-url> --pack-path <path> --module-json '<module-json>'

# With a specific ref
uv run python scripts/validate_federation.py <repo-url> --ref <ref> --pack-path <path> --module-json '<module-json>'
```

2. **Output to user:** The full validation report with pass/fail for each check:
   - Clone and access
   - Lola module schema (name, description, version, repository)
   - Tier 1 (agentskills.io spec)
   - Tier 2 (design principles)
   - MCP version pinning
   - Credential scan (gitleaks)

### Phase 4: Lola marketplace verification

1. **Action:** Verify the module is loadable by Lola using the PR branch:

```bash
lola market add test-federation https://raw.githubusercontent.com/<owner>/<repo>/<branch>/marketplace/rh-agentic-collection.yml
lola market ls test-federation
lola market rm test-federation
```

2. **Check:** The federated module appears in the module list with correct name, version, and description.
3. **Output to user:** Lola verification result (visible or not, with details).

### Phase 5: Summary

Present a combined summary to the user:

| Check | Result |
|-------|--------|
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
- [Federation Review Guide](../../../docs/FEDERATION_REVIEW_GUIDE.md) — full evaluation criteria
- [CONTRIBUTING.md](../../../CONTRIBUTING.md) — contribution paths overview
- [SKILL_DESIGN_PRINCIPLES.md](../../../SKILL_DESIGN_PRINCIPLES.md) — Tier 2 design principles

**Scripts:**
- `scripts/validate_federation.py` — automated validation checks

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
       Ref: (default branch)

       Checking license...
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
       - License: ✅ MIT (compatible)
       - Validation: ❌ Tier 1 failures
       - Lola: ✅ Module loadable
       Recommendation: Request changes (Tier 1 failures need fixing)
```
