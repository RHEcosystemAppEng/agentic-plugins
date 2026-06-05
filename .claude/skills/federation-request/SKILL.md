---
name: federation-request
description: |
  Guide users through creating a federation PR to register an external agentic pack in the marketplace.
  Collects only repository URL and pack path, infers other metadata from the repo, and confirms before proceeding.

  Use when:
  - "I want to federate my pack"
  - "How do I add an external pack to the marketplace?"
  - "Create a federation request"
  - "Register an external module"
  - User mentions "federation request", "federate", or "external module"

  NOT for reviewing federation PRs (use /federation-review instead).
  NOT for direct contributions (use /agentic-contribution-skill instead).
license: Apache-2.0
model: inherit
color: green
allowed-tools: Read Edit Write Bash Glob Grep Skill
---

# Federation Request

Guide users through creating a complete federation PR — from discovering pack metadata in an external repo to opening the pull request with the `federation` label. Only repository URL and pack path are asked upfront; other fields are inferred and confirmed before any writes.

**Install scope:** Federated modules are full Lola packs. `lola install -f <name>` installs **every skill** in the pack, the same as in-repo modules (`rh-sre`, `rh-developer`, etc.). There is no marketplace field to install a subset.

**`ref` pinning:** Marketplace `ref` is required for CI/catalog in this repo but **ignored by Lola at install** until [lola#180](https://github.com/LobsterTrap/lola/issues/180).

## Prerequisites

**Required Tools**:
- `git` — version control
- `gh` — GitHub CLI for PR creation
- `uv` — Python environment manager (for `/create-collection`)

**Verification**:
```bash
which git >/dev/null && echo "✓ git" || echo "✗ git not found"
which gh >/dev/null && echo "✓ gh" || echo "✗ gh not found — install from https://cli.github.com"
which uv >/dev/null && echo "✓ uv" || echo "✗ uv not found — install from https://astral.sh/uv"
```

**Human Notification Protocol**:
If prerequisites fail:
```
❌ Cannot execute: <tool> not found
📋 Setup: <install instructions>
```

**Security**: Never display credentials. Never clone private repos without user confirmation.

## When to Use This Skill

Use when:
- A user wants to register an external agentic pack in the marketplace
- A user asks how to federate a pack they maintain in another repository
- A user wants to create a PR to add a federated module

Do NOT use when:
- Reviewing an existing federation PR → Use `/federation-review`
- Adding skills directly to this repository → Use `/agentic-contribution-skill`
- Listing or inspecting existing clusters → Use `/cluster-inventory`

## Workflow

### Phase 1: Discover and confirm module metadata

Collect only two inputs from the user, then infer the rest from the repository.

#### Step 1 — Ask for inputs (only these two)

1. **repository** — Git repository URL (e.g., `https://github.com/org/repo`)
   - Validate: valid URL; must NOT be `https://github.com/RHEcosystemAppEng/agentic-collections` (direct contribution, not federation)

2. **path** — Path to the skill pack inside the repo (e.g., `.`, `plugins/claude-code-setup`, `my-pack`)
   - Validate: non-empty; use `.` only when the pack root is the repo root

Do **not** ask for name, description, version, ref, tags, or maturity individually — infer them in Step 2.

#### Step 2 — Clone and infer fields automatically

After the user provides repository and path:

1. **Clone** the repository to a temporary directory and resolve the default-branch HEAD commit SHA:

```bash
TMP=/tmp/federation-discover-$$
git clone --quiet --no-checkout "<repository>" "$TMP"
REF=$(git -C "$TMP" ls-remote origin HEAD | cut -f1)
git -C "$TMP" checkout --quiet "$REF"
PACK="$TMP/<path>"
```

2. **Verify** the pack exists:

```bash
test -d "$PACK/skills" && echo "✓ Pack found" || echo "✗ No skills/ directory at <path>"
```

If verification fails, report the error and ask the user to correct the repository URL or path. Do not continue.

3. **Infer each field** using this precedence (first match wins):

| Field | Inference rules |
|-------|-------------------|
| **name** | 1) `.claude-plugin/plugin.json` or `.cursor-plugin/plugin.json` → `name` · 2) basename of `path` (if not `.`) · 3) sole `skills/<dir>/` folder name · Must be kebab-case, unique in `marketplace/rh-agentic-collection.yml` |
| **title** | Human-readable catalog display name · 1) `README.md` first `# ` heading · 2) title-case words from `name` (`claude-code-setup` → `Claude Code Setup`) · 3) short phrase from `plugin.json` `description` · Non-empty, ≤120 chars; used in `collection.yaml` `name:` and `docs/plugins.json` |
| **description** | 1) `plugin.json` → `description` · 2) `README.md` first substantive sentence · 3) first skill `SKILL.md` frontmatter `description` (flatten to one line, ≤200 chars) |
| **version** | 1) `plugin.json` → `version` (normalize to semver `X.Y.Z`) · 2) default `0.1.0` |
| **ref** | `REF` from clone above (40-char commit SHA of default branch HEAD) |
| **tags** | Derive 3–6 kebab-case tags from skill folder names, `plugin.json` keywords, README headings, and path segments; always append `federation` |
| **maturity** | Default **`ORANGE`** (recommended for new federations; not listed on public GitHub Pages until promoted to `GREEN`) |

4. **Validate** inferred values before presenting:
   - **name**: kebab-case, 1–64 chars, not already in `marketplace/rh-agentic-collection.yml`
   - **title**: non-empty human-readable string; not identical to raw kebab-case `name` unless no better source exists
   - **description**: non-empty, under 200 characters
   - **version**: semver `X.Y.Z`
   - **ref**: 40 hexadecimal characters (run `uv run python -c "import sys; sys.path.insert(0,'scripts'); import pack_registry as pr; print(pr.federation_ref_error('<ref>') or 'ok')"` to verify)
   - **tags**: at least one tag besides `federation`

If inference fails or produces ambiguous results (e.g., multiple skill dirs with no plugin.json and path is `.`), show what was found and ask the user to clarify **only the conflicting field(s)**, then re-infer.

#### Step 3 — Present summary and wait for confirmation

Show inferred values in one table. Include maturity and note that the user may override any field before confirming:

```
## Inferred module metadata

| Field       | Value (inferred)                              | Source              |
|-------------|-----------------------------------------------|---------------------|
| Name        | <name>                                        | plugin.json / path  |
| Title       | <human-readable title>                        | README / name       |
| Description | <description>                                 | README / SKILL.md   |
| Version     | <version>                                     | plugin.json         |
| Repository  | <repository>                                  | (user provided)     |
| Ref         | <40-character commit SHA>                     | default branch HEAD |
| Path        | <path>                                        | (user provided)     |
| Tags        | <tag1>, <tag2>, ..., federation               | skills / README     |
| Maturity    | ORANGE                                        | default (new federation) |

Reply **yes** to proceed, or tell me what to change (e.g., "use GREEN maturity", "title should be …", "name should be foo-bar").
```

Wait for explicit user confirmation before Phase 2. Apply any corrections the user requests, then confirm again if values changed materially.

Keep the temporary clone at `$TMP` through Phase 2 if no corrections require re-cloning; otherwise re-clone at the confirmed `ref`.

### Phase 2: Create Marketplace Entry

1. **Action**: Read `marketplace/rh-agentic-collection.yml`
2. **Action**: Append the new federated module entry before the comment block at the end of the file. Use this format:

```yaml
  - name: "<name>"
    description: "<description>"
    version: "<version>"
    repository: "<repository>"
    ref: "<commit-sha>"         # required project extension: 40-character commit SHA (Lola ignores until lola#180)
    path: "<path>"
    tags:
      - "<tag1>"
      - "<tag2>"
      - "federation"
```

3. **Output to user**: "Added module entry to `marketplace/rh-agentic-collection.yml`."

4. **Action**: Add a display-title entry to `docs/plugins.json`. Key **must** match the marketplace module `name` (not the repo path):

```json
"<name>": {
  "title": "<human-readable title>"
}
```

   - Merge into existing `docs/plugins.json`; preserve JSON formatting (2-space indent, trailing newline).
   - Skip if the key already exists — update `title` only when the user corrected it in Phase 1.
   - **Output to user**: "Added `docs/plugins.json` entry for `<name>`."

### Phase 3: Generate Collection Files

1. **Action**: Reuse the Phase 1 clone if still valid at the confirmed `ref`, or clone again:

```bash
git clone --quiet --no-checkout <repository> /tmp/federation-<name>
cd /tmp/federation-<name> && git checkout --quiet <commit-sha>
```

2. **Action**: Verify the pack exists at the declared path (skip if already verified in Phase 1):

```bash
test -d /tmp/federation-<name>/<path>/skills && echo "✓ Pack found" || echo "✗ No skills/ directory at <path>"
```

If the pack is not found, report the error and ask the user to verify the repository URL and path.

3. **Action**: Create the federation module directory:

```bash
mkdir -p federation/modules/<name>
```

4. **Action**: Invoke the `/create-collection` skill targeting the cloned pack. The skill will generate `collection.yaml` and `collection.json` under `.catalog/`.

   Since `/create-collection` expects the pack to be a local directory registered in the marketplace, work as follows:
   - Point `/create-collection` to the cloned pack at `/tmp/federation-<name>/<path>/`
   - After generation, copy the resulting `.catalog/` contents to `federation/modules/<name>/.catalog/`
   - Set **`id:`** to the module `name` (kebab-case marketplace identifier)
   - Set **`name:`** in `collection.yaml` to the confirmed **`title`** (must match `docs/plugins.json` → `title`)
   - Set **`maturity:`** in `collection.yaml` to the value confirmed in Phase 1 (default `ORANGE`), then regenerate `collection.json` with `uv run python scripts/catalog_yaml_to_json.py --pack federation/modules/<name>`

```bash
mkdir -p federation/modules/<name>/.catalog
cp /tmp/federation-<name>/<path>/.catalog/collection.yaml federation/modules/<name>/.catalog/
cp /tmp/federation-<name>/<path>/.catalog/collection.json federation/modules/<name>/.catalog/
# Copy any fragment .md files too
cp /tmp/federation-<name>/<path>/.catalog/*.md federation/modules/<name>/.catalog/ 2>/dev/null || true
```

5. **Action**: Clean up the temporary clone:

```bash
rm -rf /tmp/federation-<name>
```

6. **Output to user**: "Generated collection files at `federation/modules/<name>/.catalog/`."

### Phase 4: Create Pull Request

1. **Action**: Create a feature branch:

```bash
git checkout -b feat/federate-<name>
```

2. **Action**: Stage all changes:

```bash
git add marketplace/rh-agentic-collection.yml docs/plugins.json federation/modules/<name>/
```

3. **Action**: Show the user what will be committed:

```bash
git diff --cached --stat
```

4. **Action**: Ask user to confirm the commit. Propose message:
   ```
   feat: federate <name> module from <repository>
   ```
   Wait for explicit confirmation.

5. **Action**: Commit and push:

```bash
git commit -m "<approved message>"
git push -u origin feat/federate-<name>
```

6. **Action**: Create the PR with the `federation` label:

```bash
gh pr create \
  --title "feat: federate <name> module" \
  --body "$(cat <<'EOF'
## Federation Request

Adds **<name>** as a federated module from [<repository>](<repository>).

### Module Details

| Field       | Value            |
|-------------|------------------|
| Name        | <name>           |
| Title       | <title>          |
| Version     | <version>        |
| Path        | <path>           |
| Ref         | <commit-sha>     |

### What's Included

- Module entry in `marketplace/rh-agentic-collection.yml`
- Display title in `docs/plugins.json`
- Collection catalog at `federation/modules/<name>/.catalog/`

### Validation

CI will run automated federation validation (repo LICENSE check, Tier 1, Tier 2, MCP pinning, credential scan) when the `federation` label is detected.
EOF
)" \
  --label "federation"
```

7. **Output to user**: The PR URL and a note that CI validation will run automatically.

### Phase 5: Summary

Present final summary:

```
## Federation Request Complete

| Item                  | Status |
|-----------------------|--------|
| Marketplace entry     | ✅ Added to marketplace/rh-agentic-collection.yml |
| plugins.json title    | ✅ Added to docs/plugins.json |
| Collection files      | ✅ Generated at federation/modules/<name>/.catalog/ |
| Pull request          | ✅ <PR-URL> |
| CI validation         | ⏳ Will run automatically (federation label applied) |

**Next steps:**
- CI will validate the federated module automatically
- A maintainer will review using `/federation-review`
- Once approved and merged, the module will be installable via `lola install -f <name>`
```

## Dependencies

### Required MCP Servers

None — this skill uses CLI tools only.

### Required MCP Tools

None — no MCP tools are invoked.

### Related Skills

- `/create-collection` — generates `.catalog/collection.yaml` and `collection.json` for the federated pack
- `/federation-review` — used by maintainers to validate the resulting PR
- `/agentic-contribution-skill` — for direct contributions (not federation)

### Reference Documentation

**Internal:**
- [Federation Request Guide](../../../FEDERATION_REQUEST_GUIDE.md) — contributor guide for federation requests
- [Federation Review Guide](../../../FEDERATION_REVIEW_GUIDE.md) — evaluation criteria for federated packs
- [COLLECTION_SPEC.md](../../../COLLECTION_SPEC.md) — collection catalog specification
- [CONTRIBUTING.md](../../../CONTRIBUTING.md) — contribution paths overview

## Critical: Human-in-the-Loop Requirements

**MUST confirm before:**

1. **Inferred metadata** (Phase 1): Present summary table with all inferred fields (including maturity); wait for **yes** or apply user corrections first
2. **Commit** (Phase 4): Show staged changes and proposed message, wait for approval
3. **Push & PR** (Phase 4): Confirm before pushing and creating the PR

**NEVER:**
- Push without explicit approval
- Create commits without confirmation
- Skip the Phase 1 confirmation step
- Proceed if the pack is not found at the declared path

## Example Usage

```
User: /federation-request

Skill: I'll add your external pack to the marketplace. I only need two things:
       1. Git repository URL
       2. Path to the skill pack inside the repo (use "." if it's at the repo root)

User: https://github.com/partner-org/net-diag-skills
       plugins/network-diagnostics

Skill: Cloning and inspecting the repository...

       ## Inferred module metadata

       | Field       | Value                                          | Source              |
       |-------------|------------------------------------------------|---------------------|
       | Name        | network-diagnostics                            | plugin.json         |
       | Title       | Network Diagnostics                            | README.md           |
       | Description | Network troubleshooting skills for SDN and ... | README.md           |
       | Version     | 0.2.0                                          | plugin.json         |
       | Repository  | https://github.com/partner-org/net-diag-skills | (user provided)     |
       | Ref         | a1b2c3d4e5f6789012345678901234567890abcd       | default branch HEAD |
       | Path        | plugins/network-diagnostics                    | (user provided)     |
       | Tags        | networking, sdn, ovn, troubleshooting, federation | skills / README  |
       | Maturity    | ORANGE                                         | default             |

       Reply **yes** to proceed, or tell me what to change.

User: yes

Skill: ✅ Added module to marketplace/rh-agentic-collection.yml
       ✅ Added docs/plugins.json entry
       ✅ Generated collection files at federation/modules/network-diagnostics/.catalog/
       ...
```
