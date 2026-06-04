---
name: federation-request
description: |
  Guide users step-by-step through creating a federation PR to register an external agentic pack in the marketplace.

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

Guide users through creating a complete federation PR — from gathering module metadata to opening the pull request with the `federation` label. Assumes the user has no prior knowledge of the federation process.

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

### Phase 1: Gather Module Data

Ask the user for each field, one at a time. Explain what each field is and provide examples. Validate each answer before moving to the next question.

**Fields to collect:**

1. **name** (required)
   - Ask: "What is the module name? Use kebab-case (e.g., `partner-network-tools`). This will be the identifier in the marketplace."
   - Validate: kebab-case, 1-64 chars, `a-z0-9-`, no consecutive `--`, no leading/trailing `-`
   - Validate uniqueness: check it does not already exist in `marketplace/rh-agentic-collection.yml`

2. **description** (required)
   - Ask: "Describe the module in 1-2 sentences. What does it do and who is it for?"
   - Validate: non-empty, under 200 characters

3. **version** (required)
   - Ask: "What version is the module? Use semver format (e.g., `1.0.0`, `0.1.0`)."
   - Validate: matches semver pattern `X.Y.Z`

4. **repository** (required)
   - Ask: "What is the Git repository URL? (e.g., `https://github.com/org/repo`)"
   - Validate: valid URL, must NOT be `https://github.com/RHEcosystemAppEng/agentic-collections` (that would be a direct contribution, not federation)

5. **license** (required)
   - Ask: "What license does the repository use? Must be compatible with Apache 2.0. Compatible licenses: Apache-2.0, MIT, BSD-2-Clause, BSD-3-Clause."
   - Validate: must be one of the compatible licenses

6. **ref** (optional)
   - Ask: "Do you want to pin to a specific commit SHA, tag, or branch? Leave empty to use the default branch."
   - If provided, the ref is appended to the repository URL with `@`: `https://github.com/org/repo@<ref>`
   - The `repository` field in the marketplace YAML will contain the full URL with ref embedded (e.g., `https://github.com/org/repo@v1.0.0` or `https://github.com/org/repo@abc123...`)
   - There is NO separate `ref` field in the marketplace entry

7. **path** (optional, default: `.`)
   - Ask: "Where is the Lola pack inside the repository? Use `.` if it's at the repo root, or specify a subdirectory path (e.g., `my-pack`)."
   - Default: `.`

8. **tags** (required)
   - Ask: "List tags for discoverability, comma-separated (e.g., `networking, sdn, troubleshooting`). The tag `federation` will be added automatically."
   - Validate: at least 1 tag provided
   - Always append `federation` tag if not already included

**After collecting all fields**, present a summary table and ask for confirmation:

```
## Module Summary

| Field       | Value                                         |
|-------------|-----------------------------------------------|
| Name        | <name>                                        |
| Description | <description>                                 |
| Version     | <version>                                     |
| Repository  | <repository> or <repository>@<ref>            |
| License     | <license>                                     |
| Path        | <path>                                        |
| Tags        | <tag1>, <tag2>, ..., federation               |

Proceed? (yes/no)
```

Wait for explicit user confirmation before continuing.

### Phase 2: Create Marketplace Entry

1. **Action**: Read `marketplace/rh-agentic-collection.yml`
2. **Action**: Append the new federated module entry before the comment block at the end of the file. Use this format:

```yaml
  - name: "<name>"
    description: "<description>"
    version: "<version>"
    license: "<license>"
    repository: "<repository>"        # includes @<ref> if ref was provided
    path: "<path>"
    tags:
      - "<tag1>"
      - "<tag2>"
      - "federation"
```

If a ref was provided, the `repository` value must be `<repository-url>@<ref>` (e.g., `https://github.com/org/repo@v1.0.0`). If no ref, use the plain URL.

3. **Output to user**: "Added module entry to `marketplace/rh-agentic-collection.yml`."

### Phase 3: Generate Collection Files

1. **Action**: Clone the external repository to a temporary directory. If the repository URL contains `@<ref>`, split it to get the base URL and ref:

```bash
# If repository is "https://github.com/org/repo@ref":
git clone --quiet --no-checkout https://github.com/org/repo /tmp/federation-<name>
cd /tmp/federation-<name> && git checkout --quiet <ref>

# If repository has no @ref (plain URL):
git clone --quiet --depth 1 <repository> /tmp/federation-<name>
```

2. **Action**: Verify the pack exists at the declared path:

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
git add marketplace/rh-agentic-collection.yml federation/modules/<name>/
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
| Version     | <version>        |
| License     | <license>        |
| Repository  | <repository>     |
| Path        | <path>           |

### What's Included

- Module entry in `marketplace/rh-agentic-collection.yml`
- Collection catalog at `federation/modules/<name>/.catalog/`

### Validation

CI will run automated federation validation (license, Tier 1, Tier 2, MCP pinning, credential scan) when the `federation` label is detected.
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
- [Federation Review Guide](../../../docs/FEDERATION_REVIEW_GUIDE.md) — evaluation criteria for federated packs
- [COLLECTION_SPEC.md](../../../COLLECTION_SPEC.md) — collection catalog specification
- [CONTRIBUTING.md](../../../CONTRIBUTING.md) — contribution paths overview

## Critical: Human-in-the-Loop Requirements

**MUST confirm before:**

1. **Module data** (Phase 1): Present summary table, wait for "yes"
2. **Commit** (Phase 4): Show staged changes and proposed message, wait for approval
3. **Push & PR** (Phase 4): Confirm before pushing and creating the PR

**NEVER:**
- Push without explicit approval
- Create commits without confirmation
- Skip the summary confirmation in Phase 1
- Proceed if the pack is not found at the declared path

## Example Usage

```
User: /federation-request

Skill: Let's set up a federation request to add your external pack to the marketplace.
       I'll guide you through each step.

       First — what is the module name? Use kebab-case (e.g., partner-network-tools).

User: network-diagnostics

Skill: Got it. Now describe the module in 1-2 sentences.

User: Network troubleshooting skills for SDN and OVN diagnostics on OpenShift clusters.

Skill: What version? Use semver (e.g., 1.0.0).

User: 0.2.0

Skill: Repository URL?

User: https://github.com/partner-org/net-diag-skills

Skill: License? Must be compatible with Apache 2.0 (Apache-2.0, MIT, BSD-2-Clause, BSD-3-Clause).

User: MIT

Skill: Pin to a specific commit SHA, tag, or branch? Leave empty for default branch.

User: v0.2.0

Skill: Path inside the repo where the pack lives? Use "." for repo root.

User: .

Skill: Tags for discoverability (comma-separated)? "federation" will be added automatically.

User: networking, sdn, ovn, troubleshooting

Skill: ## Module Summary
       | Field       | Value                                          |
       |-------------|------------------------------------------------|
       | Name        | network-diagnostics                            |
       | Description | Network troubleshooting skills for SDN and ... |
       | Version     | 0.2.0                                          |
       | Repository  | https://github.com/partner-org/net-diag-skills@v0.2.0 |
       | License     | MIT                                            |
       | Path        | .                                              |
       | Tags        | networking, sdn, ovn, troubleshooting, federation |

       Proceed? (yes/no)

User: yes

Skill: ✅ Added module to marketplace/rh-agentic-collection.yml
       ✅ Cloned repository, pack found at root
       ✅ Generated collection files at federation/modules/network-diagnostics/.catalog/
       ✅ Created PR: https://github.com/RHEcosystemAppEng/agentic-collections/pull/42
          Label: federation — CI validation will run automatically.
```
