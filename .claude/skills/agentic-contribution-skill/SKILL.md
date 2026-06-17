---
name: agentic-contribution-skill
description: |
  Interactive skill creation and import with automated validation and marketplace compliance.

  Use when:
  - "Create a new skill"
  - "Import an existing skill"
  - "Create a new agentic pack"
  - "Add skill to <pack>"
  - "Build skill for <rh-product>"
  - User mentions "skill builder", "contribute", "new skill", "import skill", or "new pack"

  Two modes: create from scratch or import existing SKILL.md. Guides through discovery, definition, generation, and validation. Enforces SKILL_DESIGN_PRINCIPLES.md and agentskills.io spec.
license: Apache-2.0
model: inherit
color: green
metadata:
  author: "Red Hat Ecosystem Engineering"
  version: "1.1.0"
---

# /agentic-contribution-skill Skill

Interactive AI assistant for creating production-ready skills and agentic packs for **Red Hat products and platforms** with automated quality validation.

All skills created follow **Red Hat product guidelines, official documentation standards** (docs.redhat.com, access.redhat.com), and **best practices** for Red Hat Enterprise Linux, OpenShift Container Platform, Ansible Automation Platform, Red Hat Lightspeed, and other Red Hat ecosystem products.

**Creates**: Complete skill structure with YAML frontmatter, all mandatory sections, pack integration, and new agentic packs (Lola-compatible)
**Validates**: Tier 1 (agentskills.io) + Tier 2 (repository design principles)
**Applies**: Red Hat documentation compliance (uses official Red Hat documentation to adapt skill content to manufacturer guidelines - not automated validation)
**Marketplace**: Registers packs in `marketplace/rh-agentic-collection.yml` for Lola package manager installation

## Prerequisites

**Required Tools**:
- `git` - Version control
- `uv` - Python environment manager
- `bash` - Shell for validation scripts

**Verification**:
```bash
test -d .git && echo "✓ Git repo" || echo "✗ Not a git repo"
which uv >/dev/null && echo "✓ uv installed" || echo "✗ Install uv"
test -f SKILL_DESIGN_PRINCIPLES.md && echo "✓ Valid repo" || echo "✗ Wrong directory"
```

**Human Notification Protocol**:

If prerequisites fail:
```
❌ Cannot execute: <issue>
📋 Setup: <specific_steps>
🔗 Doc: CONTRIBUTING.md
```

**Security**: Never display git credentials or secrets.

## When to Use This Skill

**Use when**:
- Creating new skill for any pack
- Importing an existing SKILL.md into the repository
- Creating new agentic pack collection
- Developing or editing skills for this agentic collection
- User explicitly invokes `/agentic-contribution-skill`

**Do NOT use when**:
- Asking about standards (direct to SKILL_DESIGN_PRINCIPLES.md)
- General contributing questions (direct to CONTRIBUTING.md)

## Workflow

### Phase 0: Mode Selection

Ask: **"Are you creating a new skill from scratch, or importing an existing SKILL.md?"**

- **Create** → Proceed to Phase 1 (Discovery)
- **Import** → Proceed to Phase 1-Import (Analysis)

### Phase 1: Discovery (5 questions max)

Ask concisely, validate before proceeding. Make additional questions if needed to gather complete context.

1. **Purpose & Red Hat Product**: "What does the skill do? (1 sentence) For which Red Hat product(s) is this skill targeted?"
2. **Persona**: "What role uses it?" (detect existing pack or suggest new)
3. **Pack**: "Use <existing-pack>? (yes/no/create-new)"
4. **MCP Tools**: 
   - Read pack's `mcps.json` to list existing MCP servers
   - If MCP server mentioned, verify it exists in the file
   - For tools mentioned, verify they exist in MCP server documentation or configuration
   - Ask: "What MCP tools does this skill need? Available MCPs in <pack>: <list>. Will you use existing MCPs, need new ones, or both?"
   - **Never suggest tools based on intuition** - only recommend tools you've verified exist
5. **Operation Type**: "Read-only, additive, or destructive?" (determines color)

**Color Mapping** (risk-based, with Red Hat/OpenShift examples):

| Color | Use Case | Examples |
|-------|----------|----------|
| 🔵 cyan | Read-only operations | list clusters, view VM status, check node health, get CVE data |
| 🟢 green | Additive operations | create VM, deploy cluster, generate playbook, add backup |
| 🔵 blue | Reversible operations | restart pod, pause MCP, start VM, stop service |
| 🟡 yellow | Destructive but recoverable | delete snapshot, remove annotation, uncordon node |
| 🔴 red | Critical/irreversible | upgrade cluster, delete cluster, restore ETCD, execute remediation |

**Validation**:
- Purpose: specific, under 100 chars
- Red Hat product: identified (OpenShift, RHEL, Ansible, etc.)
- Persona: matches known or justifies new pack
- MCP tools: **verified to exist** (no assumptions/intuition)
- Operation type → Color selected from table above

### Phase 2: Definition (6 questions max)

1. **Name**: Ask "Skill name? (kebab-case, unique)" → Validate if name is representative of purpose and Red Hat product. If NOT representative, propose 2-3 better alternatives and ask user to choose → Check: `test -d <pack>/skills/<name>/` for uniqueness
2. **Use Cases**: "3-5 user phrases for 'Use when'" (concrete, not generic)
3. **Anti-Patterns**: "NOT for? (with alternative)"
4. **Workflow**: "Steps with MCP tools?" (e.g., "1. Validate VM - resources_get")
5. **Common Issues**: "3+ issues: problem: cause: solution"
6. **Prerequisites**: "Special requirements? (env vars, permissions)"
7. **External Resources**: "Any external docs/links/KB articles referenced?" (will be saved to `docs/` folder)

**Quality over Speed**: Focus on gathering complete, accurate information. Validation and iteration will ensure correctness - prioritize quality of final result over generation time.

### Phase 1-Import: Analysis (import mode only)

1. **Get file**: Ask for the path to the existing SKILL.md
2. **Read & parse**: Read the file with Read tool. Parse YAML frontmatter, extract name, description, workflow steps, MCP tools mentioned
3. **Pack suggestion**: Analyze skill content keywords and suggest the best-fit pack:

   | Keywords in skill content | Suggested pack |
   |---|---|
   | VM, virtual machine, KubeVirt, snapshot, migration, clone | rh-virt |
   | CVE, vulnerability, remediation, compliance, RHEL, SRE | rh-sre |
   | deploy, build, S2I, Helm, container, route, BuildConfig | rh-developer |
   | cluster, install, Assisted Installer, multi-cluster, ROSA | ocp-admin |
   | model, inference, GPU, vLLM, KServe, RHOAI, workbench | rh-ai-engineer |
   | Ansible, AAP, playbook, governance, job template | rh-automation |
   | CVE explanation, product lifecycle, support severity, diagnostics, patching, support case, troubleshooting, customer issue, knowledge base, must-gather | rh-basic |

   - Present top match with reasoning: "This skill mentions X, Y, Z which aligns with `<pack>` (persona: <role>)"
   - Ask user to confirm or override

4. **Color inference**: If frontmatter has no `color`, analyze the skill's workflow steps and operations to infer the risk level. Present your conclusion to the user:
   ```
   Inferred color: <color> — Reason: <operations are read-only/additive/destructive/etc.>
   Confirm? (yes/override)
   ```
   Use the color mapping table from Phase 1 (Discovery).

5. **MCP tool verification**: Identify all MCP tools referenced in the skill. Read the target pack's `mcps.json` and verify each tool exists. Flag any tools not found — they may need a new MCP server or the skill may need adaptation.

6. **Report analysis**:
   ```
   Analyzed: <path>
   Name: <name> | Lines: <N> | Frontmatter: <valid/needs-fixes>
   Suggested pack: <pack> (keywords: <matched>)
   Color: <color> (<inferred or from frontmatter>)
   MCP tools: <N verified, M not found>
   Missing sections: <list or "none">
   
   Proceed with adaptation? (yes/no/try another file)
   ```

   If user says **no**: ask "Would you like to try a different file, or cancel?" and act accordingly.

### Phase 2-Import: Adaptation (import mode only)

**Document Consultation** (REQUIRED): Read [SKILL_DESIGN_PRINCIPLES.md](../../../SKILL_DESIGN_PRINCIPLES.md) using Read tool. Output: "I consulted SKILL_DESIGN_PRINCIPLES.md to ensure compliant adaptation."

1. **Fix frontmatter**: Ensure `model: inherit` and `color` set (use value confirmed by user in Phase 1-Import). Add `metadata` block if missing
2. **Add missing sections**: Per DP6/DP7 — Prerequisites, When to Use, Workflow, Common Issues, Dependencies. Keep existing content, add structure around it
3. **Validate naming**: kebab-case, check uniqueness: `test -d <pack>/skills/<name>/`
4. **Place file**: Copy to `<pack>/skills/<skill-name>/SKILL.md`
5. **Update routing**: Add entry to `<pack>/AGENTS.md` intent routing table
6. **Show changes**: Present summary of all modifications to user, wait for confirmation

After confirmation → proceed to Phase 5 (Validation & Iteration).

### Phase 3: Pre-Generation Summary & Document Consultation

**Document Consultation** (REQUIRED - Execute BEFORE generation):
1. **Action**: Read [SKILL_DESIGN_PRINCIPLES.md](../../../SKILL_DESIGN_PRINCIPLES.md) using Read tool to understand:
   - Mandatory section structure (DP7)
   - Precise workflow step format (DP2)
   - Human Notification Protocol (DP8)
   - Prerequisites template (DP8)
   - All design principles (DP1-11)
2. **Output to user**: "I consulted SKILL_DESIGN_PRINCIPLES.md to ensure compliant generation."

**Modularity Assessment**:
- If workflow has >10 steps OR could logically divide into phases, present modularity options to user
- **Default**: Single comprehensive skill (keeps related logic together, especially for critical operations)
- If subdivision makes sense (technical/temporal/logical separation), propose to user but let them decide
- **User decision is final**

Show complete spec:

```markdown
## Review Before Generation

**Pack**: <pack> | **Skill**: <name> | **Color**: <color>

**Purpose**: <purpose>
**Red Hat Product**: <rh-product>

**Use When**: <3-5 examples>
**NOT for**: <anti-pattern>

**Workflow**: <N> steps
**Common Issues**: <N> documented
**MCP Tools**: <tool_count> tools (verified to exist)
**External Resources**: <count> (will be saved to docs/)
**Human-in-the-Loop**: <Yes/No>

[If >10 steps or complex workflow]:
💡 **Modularity Note**: This skill has <N> steps. Options:
1. Single comprehensive skill (recommended for critical/cohesive workflows)
2. Subdivide into <N> modular skills (if logical separation exists)

Default: Option 1. Subdivide? (yes/no)

Proceed with generation? (yes/no)
```

### Phase 4: Generation

**Create structure**:
```bash
mkdir -p <pack>/skills/<skill-name>/
# If external resources provided by user:
mkdir -p <pack>/skills/<skill-name>/docs/
```

**Generate files**:
1. **SKILL.md**: YAML frontmatter + mandatory sections (follow SKILL_DESIGN_PRINCIPLES.md template - already consulted in Phase 3)
   - Focus on complete, production-ready content
   - Include all relevant information from user and verified sources
   - Keep main skill focused; detailed content can go to `docs/` if needed
2. **docs/ folder** (if applicable):
   - `docs/workflow-details.md` - Extended workflow explanations if skill is concise
   - `docs/common-issues.md` - Detailed troubleshooting with full KB article content
   - `docs/examples.md` - Comprehensive usage examples
   - `docs/external-resources.md` - Any external docs/links/KB articles mentioned by user
3. **Update <pack>/AGENTS.md**: Add intent routing entry
4. **Create <pack>/mcps.json**: If new MCP server needed (use `${ENV_VAR}` format)
5. **Update marketplace/rh-agentic-collection.yml**: If new pack (register pack for Lola installation)
6. **Create pack structure**: If new pack (README.md, AGENTS.md, skills/ directory)

Generate SKILL.md following the mandatory section template in SKILL_DESIGN_PRINCIPLES.md (already consulted in Phase 3). If SKILL.md becomes too long, move detailed content to `docs/` with references in main file.

### Phase 5: Validation & Iteration

**Validation always runs** - quality is the priority, not speed.

**Tier 1 - agentskills.io**:
```bash
./scripts/run-skill-linter.sh <pack>/skills/<skill-name>/
```

**Tier 2 - Design Principles**:
```bash
python scripts/validate_skill_design.py <pack>/skills/<skill-name>/SKILL.md
```

**Report clearly**:
- ✅ PASSED → Proceed to Phase 6
- ⚠️ WARNINGS → Review warnings with user
  - Non-standard subdirectory (docs/) is acceptable if needed
  - Description buzzwords acceptable if accurate for critical skills
  - Ask: "Warnings acceptable? (yes/no)"
- ❌ ERRORS → **Fix required**, iterate until validation passes

**Iteration Protocol** (if validation fails):
1. **Analyze errors**: Identify specific issues (line count, missing sections, format problems)
2. **Determine fix strategy**:
   - Line count exceeded → Move detailed content to `docs/` folder, keep main skill concise
   - Missing sections → Add required sections per DP7
   - Format issues → Correct frontmatter, section headers, or structure
3. **Apply fixes**: Edit SKILL.md and/or create docs/ files
4. **Re-validate**: Run both Tier 1 and Tier 2 again
5. **Repeat until ✅ PASSED**

**Note**: We iterate as many times as needed to achieve production-ready quality. Each iteration improves the skill.

### Phase 6: Post-Validation Summary

Present a concise summary to the user:
- List all created/modified files with line counts
- Validation results (Tier 1 + Tier 2, pass/warning counts)
- Quality metrics (line count, section count, workflow steps, common issues)
- Iteration count if applicable
- Your assessment of readiness and fit within the pack
- Ask: "Ready to commit? (yes/no)"

### Phase 7: Git Workflow (Optional - User Controls)

**User has full control**. Each step requires explicit confirmation:

1. **Branch**: "Create `feat/<skill-name>`? (yes/no)"
2. **Stage**: Show files, ask confirmation
3. **Commit**: Propose message (`feat: add <skill-name> skill to <pack>`), wait for approval
4. **Push**: "Push changes? (yes/no)"
5. **PR**: Use `gh pr create` if available, or provide manual steps

User can skip any step.

### Phase 8: Final Summary

Report: skill path, quality status, PR URL (if created), and note that CI checks will run automatically.

## Common Issues

### Issue 1: "Description exceeds 500 tokens"

**Fix**: Shorten frontmatter - move details to body sections.

### Issue 2: "Skill name exists"

**Fix**: Choose more specific name. Check: `ls <pack>/skills/`

### Issue 3: "MCP server not configured"

**Fix**: Add to `<pack>/mcps.json` using `${ENV_VAR}` format.

### Issue 4: "Git push authentication failed"

**Fix**: Configure credentials:
```bash
# HTTPS
git config --global credential.helper store

# SSH
ssh-add ~/.ssh/id_ed25519
```

### Issue 5: "uv not found"

**Fix**: Install:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Issue 6: "New pack not installable via Lola"

**Cause**: Pack not registered in `marketplace/rh-agentic-collection.yml`

**Fix**: Add pack entry to marketplace file:
```yaml
- name: <pack-name>
  version: 0.1.0
  description: <pack-description>
  path: <pack-name>
```

### Issue 7: "Line count exceeds 500"

**Cause**: Skill content is comprehensive but exceeds agentskills.io 500-line limit

**Fix**: Iterate to move detailed content to `docs/` folder:
1. Create `<skill>/docs/` directory
2. Move detailed workflow explanations to `docs/workflow-details.md`
3. Move full troubleshooting KB articles to `docs/common-issues.md`
4. Move comprehensive examples to `docs/examples.md`
5. Keep main SKILL.md concise with references to docs/
6. Re-run validation

**Example**:
```markdown
## Common Issues

See [docs/common-issues.md](docs/common-issues.md) for detailed solutions.

### Issue 1: Snapshot Fails
Storage doesn't support snapshots.
**Solution**: Use snapshot-capable storage. [Details](docs/common-issues.md#issue-1)
```

## Dependencies

### Required MCP Servers

None - This skill operates on repository files and git operations only. No MCP servers required.

### Required MCP Tools

None - Uses Claude Code built-in tools (Read, Write, Edit, Bash, Skill) for file operations and validation.

### Related Skills

None - agentic-contribution-skill is self-contained and doesn't invoke other skills.

### Repository Files

- `SKILL_DESIGN_PRINCIPLES.md` - Design principles (DP1-11)
- `scripts/run-skill-linter.sh` - Tier 1 validation
- `scripts/validate_skill_design.py` - Tier 2 validation
- `Makefile` - Validation targets
- `marketplace/rh-agentic-collection.yml` - Lola marketplace registry

### System Requirements

See [Prerequisites](#prerequisites) section for required system tools (git, uv, bash).

### Reference Documentation

**Internal**:
- [SKILL_DESIGN_PRINCIPLES.md](../../../SKILL_DESIGN_PRINCIPLES.md) - Complete design principles (DP1-11)
- [CONTRIBUTING.md](../../../CONTRIBUTING.md) - Contribution workflow guide

**External**:
- [agentskills.io Specification](https://agentskills.io/specification) - Base skill standard
- [Conventional Commits](https://www.conventionalcommits.org/) - Commit message format
- [Lola Package Manager](https://github.com/LobsterTrap/lola) - AI skills package manager

## Critical: Human-in-the-Loop Requirements

**MUST confirm before**:

1. **File Generation**: Show pre-generation summary, wait for "yes"
2. **Git Branch**: Ask before creating branch
3. **Git Commit**: Show commit message, wait for approval
4. **Git Push**: Confirm before pushing to remote
5. **Quality Enforcement**: Block on validation errors, warn on warnings

**NEVER**:
- Create commits without confirmation
- Push without explicit approval
- Skip validation steps
- Proceed if Tier 1 or Tier 2 validation fails with errors

**Why**: User controls their repository. Quality standards ensure CI success.

## Security Considerations

- **Git Credentials**: Never display tokens, SSH keys, or passwords
- **Environment Variables**: Report presence only, never values
- **User Repository**: Only operate in user's workspace
- **File Overwrite**: Warn before overwriting, require confirmation
- **MCP Credentials**: Only `${ENV_VAR}` format, never hardcoded
- **Script Execution**: User's repo context only

## Example Usage

**See [docs/examples.md](docs/examples.md) for comprehensive examples.**

### Quick Example: Creating VM Backup Skill

```
User: "Create skill for rh-virt to backup VMs"

Skill guides through:
1. Discovery (5 questions) - Verifies MCP tools exist
2. Definition (6 questions) - Gathers workflow details
3. Pre-generation summary - Consults SKILL_DESIGN_PRINCIPLES.md
4. Generation - Creates SKILL.md with all mandatory sections
5. Validation - Tier 1 + Tier 2, iterates if needed
6. Git workflow - User confirms each step

Result: Production-ready skill in rh-virt/skills/vm-backup-create/
```

**More examples**: [docs/examples.md](docs/examples.md)
- Example 1: VM backup skill (complete create interaction)
- Example 2: Non-representative name correction
- Example 3: Importing an existing skill (analysis, adaptation, validation)
- Example 4: Large skill requiring docs/ folder with iteration
