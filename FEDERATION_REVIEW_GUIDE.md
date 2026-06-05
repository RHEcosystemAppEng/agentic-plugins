# Federation Review Guide

Step-by-step guide for maintainers evaluating a federation PR.

Federation means referencing an **external agentic pack** in our catalog. The code stays in the external repo — we don't copy or modify it. Users install federated packs directly from the external repo via Lola.

Contributors: see [FEDERATION_REQUEST_GUIDE.md](FEDERATION_REQUEST_GUIDE.md) for how to open a federation PR.

> **Lola `ref` field:** Marketplace `ref` is required here for validation and catalog pinning, but **Lola ignores it at install time** until [LobsterTrap/lola#180](https://github.com/LobsterTrap/lola/issues/180) is fixed.

## Two ways to review

| Method | When to use |
|--------|------------|
| **`/federation-review` skill** | Interactive review from Claude Code. Reads the issue, runs validation, guides you through manual checks, and creates the registration PR if approved. |
| **Manual (this guide)** | Step-by-step commands when you prefer to review without Claude Code. |

CI also runs automated validation on any PR with the `federation` label (see [CI automation](#ci-automation) below).

---

## Automated validation (recommended)

Steps 1–6 can be run with a single command from the agentic-collections repo root:

```bash
# Full pack at repo root, pinned to a commit SHA
uv run python scripts/validate_federation.py <repo-url> --ref <40-character-commit-sha>

# Pack in a subdirectory
uv run python scripts/validate_federation.py <repo-url> --ref <commit-sha> --pack-path <path>

# JSON output (for CI)
uv run python scripts/validate_federation.py <repo-url> --ref <commit-sha> --json
```

The script checks: commit SHA format, clone access at the pinned commit, Lola module schema, Tier 1, Tier 2, MCP version pinning, and gitleaks.

### Catalog cross-check (in-repo federation artifacts)

When the PR includes `federation/modules/<name>/.catalog/`, verify the catalog matches the external pack at `ref`:

```bash
uv run python scripts/validate_federation_catalog.py \
  --module-name <name> \
  --repo-url <repo-url> \
  --ref <commit-sha> \
  --pack-path <path> \
  --module-json '<marketplace-module-json>'
```

This checks collection compliance, **skill roster parity** with the linked repo at `ref`, `docs/plugins.json` title alignment, and marketplace version/description/repository consistency.

If all pass, the pack is ready for manual review (steps 7–8).

---

## Manual steps

### Step 1: Verify access and basic info

- [ ] Repository URL is reachable and public
- [ ] `ref` is a 40-character commit SHA (not a branch or tag) and exists: `git ls-remote <repo-url> <commit-sha>`
- [ ] Owner/contact information is provided
- [ ] License file exists in the repo and is compatible with Apache 2.0 (e.g., Apache-2.0, MIT, BSD-2-Clause, BSD-3-Clause)

```bash
git clone --no-checkout <repo-url> /tmp/federation-review
cd /tmp/federation-review
git checkout <commit-sha>
```

### Step 2: Verify Lola module schema

The module entry in `marketplace/rh-agentic-collection.yml` must have the required Lola fields:

| Field | Required | Description |
|-------|----------|-------------|
| `name` | Yes | Module identifier |
| `description` | Yes | Brief description |
| `version` | Yes | Module version |
| `repository` | Yes | Git URL to the external repo |
| `ref` | Yes (project extension) | 40-character commit SHA (required by this repo; **Lola ignores until [lola#180](https://github.com/LobsterTrap/lola/issues/180)**) |

All skills under the pack's `path` are validated and installed — the same scope as in-repo marketplace modules.

### Step 3: Validate skills — Tier 1 (agentskills.io spec)

Tier 1 is **mandatory**. Run the linter on each skill:

```bash
# From the agentic-collections repo root:
for skill_dir in /tmp/federation-review/skills/*/; do
  ./scripts/run-skill-linter.sh "$skill_dir"
done
```

**Result:** All skills must pass (exit code 0). Warnings are acceptable; errors block federation.

### Step 4: Validate skills — Tier 2 (design principles)

Tier 2 is **mandatory**. Run the design principles validator:

```bash
uv run python scripts/validate_skill_design.py /tmp/federation-review
```

See [SKILL_DESIGN_PRINCIPLES.md](../SKILL_DESIGN_PRINCIPLES.md) for the full list of design principles.

### Step 5: Validate MCP configuration

If the pack uses MCP servers (`mcps.json` is not empty):

- [ ] **No `:latest` tags** — All container images must use pinned versions or SHAs
- [ ] **No hardcoded credentials** — All secrets use `${ENV_VAR}` format

```bash
grep -r ":latest" mcps.json && echo "FAIL: found :latest" || echo "PASS: no :latest"
```

### Step 6: Security review

- [ ] No credentials or secrets in any file
- [ ] Destructive operations have human-in-the-loop confirmation

```bash
gitleaks detect --source /tmp/federation-review --no-git --no-banner --verbose
```

LLM-based security scan is triggered **on-demand** by a maintainer due to cost.

### Step 7: AI agent compatibility

Verify the declared AI agent compatibility from the issue:

- [ ] If **Claude Code** is declared: CLAUDE.md exists with proper intent routing
- [ ] If **Cursor** is declared: check for Cursor-compatible configuration
- [ ] If **ChatGPT** is declared: check for ChatGPT-compatible configuration

### Step 8: Decision

| Result | Action |
|--------|--------|
| All checks pass | Approve — create registration PR with label `federation` |
| Minor issues | Comment on issue with specific fixes, label `federation/changes-requested` |
| Major issues | Reject with explanation, label `federation/rejected`, close issue |

When approving, add the pack as a new entry in `modules` in `marketplace/rh-agentic-collection.yml` (use the external repository URL; license compatibility is verified from the repo's LICENSE file during review) and link back to the issue.

---

## CI automation

PRs with the `federation` label automatically trigger the **Federation Validation** workflow (`.github/workflows/federation-validation.yml`). It:

1. Identifies federated modules (external repository) in `marketplace/rh-agentic-collection.yml`
2. Runs `scripts/validate_federation.py` on each entry
3. Posts a summary comment on the PR with pass/fail results

The label-based trigger ensures validation only runs on federation PRs, not on every marketplace YAML change.

---

## Verifying federation with Lola

After merging a federation PR, verify the module is visible in the marketplace:

```bash
# Use a unique ephemeral market name for each verification run
MARKET="federation-review-$(openssl rand -hex 4)"

# Add the marketplace (use the raw YAML URL for a specific branch or main)
lola market add "$MARKET" https://raw.githubusercontent.com/RHEcosystemAppEng/agentic-collections/main/marketplace/rh-agentic-collection.yml

# List modules — the federated pack should appear alongside internal packs
lola market ls "$MARKET"

# Clean up when done
lola market rm "$MARKET"
```

To test a PR branch before merging, replace `main` with the branch name in the URL.

---

## Cleanup

```bash
rm -rf /tmp/federation-review
```

## Quick reference

| Check | Required | Automated | Tool/Command |
|-------|----------|-----------|--------------|
| Public access | Yes | Yes | `git ls-remote` |
| License compatibility | Yes | No | Manual review |
| Lola module schema | Yes | Yes | `scripts/validate_federation.py` |
| Federation catalog cross-check | Yes | Yes | `scripts/validate_federation_catalog.py` |
| Tier 1 (agentskills.io) | Yes | Yes | `scripts/validate_federation.py` |
| Tier 2 (design principles) | Yes | Yes | `scripts/validate_federation.py` |
| MCP version pinning | Yes | Yes | `scripts/validate_federation.py` |
| Credential scan | Yes | Yes | `gitleaks` via script |
| AI agent compatibility | Yes | No | Manual review |
| Security scan (LLM) | On-demand | No | Maintainer-triggered |
