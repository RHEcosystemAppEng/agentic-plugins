# Design Principles for Skills and Agents

Repository-specific design principles for creating skills and agents in agentic collections. Referenced from [CLAUDE.md](CLAUDE.md).

**Scope**: Tier 2 requirements - repository enhancements beyond base agentskills.io specification (Tier 1 validated by linter).

**Distribution (Lola):** Packs are installed with the [Lola](https://github.com/LobsterTrap/lola) package manager from the registry in [`marketplace/rh-agentic-collection.yml`](marketplace/rh-agentic-collection.yml). Layout and install flow are documented in [CLAUDE.md](CLAUDE.md) and the root [README.md](README.md).

**Collection catalog (pack-local):** Each pack may include **`<pack>/.catalog/collection.yaml`** and a **`collection.json`** mirror so tooling and docs can show a structured view of the collection. Authors follow [COLLECTION_SPEC.md](COLLECTION_SPEC.md) and the **create-collection** skill; field constraints are defined in **[`catalog/schema.yaml`](catalog/schema.yaml)** (JSON Schema in YAML). Pack **`SKILL.md`**, **`README.md`**, **`AGENTS.md`**, and **`marketplace/rh-agentic-collection.yml`** stay the **sources of truth**; the catalog aggregates and summarizes them and does **not** replace or regenerate README or marketplace content.

**MCP configuration:** Use `<pack>/mcps.json` for MCP server definitions (never hardcode secrets; use `${VAR}` references). The deprecated filename `.mcp.json` is not used in this repository.

**Optional Claude Code manifest:** `.claude-plugin/plugin.json` is optional—only needed for Claude Code–specific plugin publishing. It is not required for Lola installation or for Tier 2 skill content compliance.

---

## Core Design Principles

### 1. Document Consultation Transparency

When consulting documentation, **MUST** actually read the file using Read tool, then declare consultation.

**Required Pattern:**
```markdown
**Document Consultation** (REQUIRED - Execute FIRST):
1. **Action**: Read [file.md](path/to/file.md) using Read tool to understand [topic]
2. **Output to user**: "I consulted [file.md](path/to/file.md) to understand [topic]."
```

**❌ WRONG - Transparency Theater:**
```markdown
I consulted file.md to understand [topic].  # Claim without actually reading
```

**Rationale**: Ensures AI enriches context with domain knowledge; users understand knowledge sources; auditable via Read tool logs.

---

### 2. Precise Parameter Specification

Specify **exact parameters** with formats and examples for first-attempt success.

**Required Workflow Step Format:**
```markdown
### Step N: [Action Name]

**Document Consultation** (if applicable): [See Principle #1]

**MCP Tool**: `tool_name` or `category__tool_name` (from server-name)

**Parameters**:
- `param`: "value" (type, constraints, format details)

**Expected Output**: [Description]

**Error Handling**:
- If [condition]: [resolution]
```

**✅ Good Example:**
```markdown
**Parameters**:
- `impact`: "7,6" (comma-separated: 7=Important, 6=Moderate, 5=Low)
- `sort`: "-cvss_score" (use - for descending)
- `limit`: 20 (integer, range: 1-100)
```

**❌ Bad Example:**
```markdown
**Parameters**:
- Use the CVE ID
- Set severity to high
```

**Rationale**: Exact names/formats prevent errors; first-attempt success reduces wasted cycles.

---

### 3. Skill Precedence and Conciseness

**A. Skills Over Tools**

Delegate to skills, not raw MCP tools.

**✅ CORRECT:** `invoke the vm-inventory skill`
**❌ WRONG:** `use the resources_list tool`

**B. Concise Descriptions**

- Under 500 tokens in frontmatter `description`
- 3-5 "Use when" examples
- "NOT for" anti-patterns with alternatives
- Defer implementation to skill body

**✅ Complete Example:**
```yaml
---
description: |
  Analyze CVE impact without remediation.

  Use when:
  - "What are critical vulnerabilities?"
  - "Show CVEs affecting systems"
  - User mentions "CVEs", "vulnerabilities"

  NOT for remediation actions (use remediation skill instead).
model: inherit        # Root: Runtime configuration required before skill execution
color: blue           # Root: UX - IDE sidebar/terminal theme
---
```

**Rationale**: Minimizes token usage at initialization; prevents skill misuse.

---

### 4. Dependencies Declaration

Every skill MUST include complete Dependencies section.

**Standard Color Values** (Cursor, Claude Code):

| Color | Use Case |
|-------|----------|
| blue, cyan | Analysis, read-only |
| green | Success, deployment |
| yellow | Caution, validation |
| red | Critical, security, remediation |

## 4. Skill-to-Skill Invocation Standard

**Standard format**: Use the slash format `/skill-name` when one skill or agent invokes another.

```markdown
**How to invoke**: Execute the `/mcp-lightspeed-validator` skill
**Action**: Execute the `/mcp-aap-validator` skill
```

**❌ Avoid** - Skill tool format (inconsistent):
```markdown
Use the Skill tool:
  skill: "mcp-lightspeed-validator"
```

**✅ Use** - Slash format (consistent across rh-sre):
```markdown
Execute the `/mcp-lightspeed-validator` skill
Invoke the `/playbook-executor` skill
```

**Applies to**:
- Skill → skill (remediation invokes `/cve-validation`, `/playbook-generator`, etc.)
- Skill → skill prerequisites (cve-validation invokes `/mcp-lightspeed-validator`)
- Skill → skill delegation (playbook-generator delegates to `/playbook-executor`)

**Rationale**: Single format across agent and skill invocations improves consistency and reduces confusion.

## 5. Dependencies Declaration

Every skill MUST include a **Dependencies** section listing:
- **Skills**: Other skills this skill may invoke
- **MCP Tools**: Specific tools from MCP servers
- **MCP Servers**: Required MCP server names
- **Documentation**: Reference docs for context

**Required Format**:
```markdown
## Dependencies

### Required MCP Servers
- `server-name` - Description ([setup guide](link))

### Required MCP Tools
- `tool_name` (from server-name) - What it does
  - Parameters: param1, param2

### Related Skills
- `skill-name` - When to use instead

### Reference Documentation
**Internal:** [doc.md](path) - Purpose
**Official:** [Title - Product](https://docs.redhat.com/...)
```

**Skill-local docs rule (required):**
- Internal docs consumed by a skill must resolve under that skill directory using `docs/...` links.
- Do **not** use upward traversal links to pack-level docs such as `../docs/...`, `../../docs/...`, or `../../../docs/...`.
- Shared docs may be reused via symlinks under `skills/<skill>/docs/...`.
- Pack-level `docs/INDEX.md` and `docs/SOURCES.md` may exist for repository navigation/source attribution, but skills must not depend on them at execution time.

**Rationale**: Makes dependencies explicit for debugging and troubleshooting.

## 6. Human-in-the-Loop Requirements

Skills performing critical operations MUST require explicit confirmation.

**When Required:** Create, delete, modify, restore, execute commands, affect multiple systems
**NOT Required:** Read-only operations (list, view, get)

**Required Section:**
```markdown
## Critical: Human-in-the-Loop Requirements

1. **Before [Action]**
   - Display preview: [what will happen]
   - Ask: "Should I [action]?"
   - Wait for confirmation (yes/no)

**Never assume approval** - always wait for explicit confirmation.
```

**For Destructive Operations - Add Typed Confirmation:**
```markdown
2. **Typed Confirmation**
   - Ask: "Type exact resource name to confirm: <name>"
   - Verify exact match, cancel if mismatch
  - Ask: "Type 'DELETE' to proceed"
  - Only proceed on exact match
```

**Rationale**: Prevents unintended automation; maintains user control; reduces accidental data loss.

**When to Use**:
- Playbook execution (ansible-mcp-server)
- System modifications (package updates, config changes)
- Multi-system operations (batch remediation)
- Data deletion or irreversible actions

## 7. Mandatory Skill Sections

Every skill MUST include these sections in order:

**Required Section Order:**
1. YAML frontmatter
2. `# [Skill Name]` heading + overview (1-2 sentences)
3. `## Critical: Human-in-the-Loop Requirements` (if applicable)
4. `## Prerequisites`
5. `## When to Use This Skill`
6. `## Workflow`
7. `## Dependencies`
8. `## Example Usage` (recommended)

**A. Mandatory Frontmatter Fields:**
```yaml
---
name: skill-name                # MANDATORY - kebab-case, matches directory
description: |                  # MANDATORY - <500 tokens, includes use cases
  [With "Use when" and "NOT for"]
model: inherit                  # MANDATORY - inherit | sonnet | haiku
color: green                    # MANDATORY - cyan|green|blue|yellow|red|magenta
---
```

**Model Values:**
- `inherit` - Use parent context (recommended)
- `sonnet` - Complex reasoning
- `haiku` - Simple, fast operations

**Validation Enforcement:**
- `scripts/validate_skill_design.py` and `scripts/validate-skills.sh` MUST both enforce required `model` presence and valid model values.
- Any drift between validators is treated as a policy inconsistency and must be corrected before merge.

**Color Values (Risk-Based):**
- `cyan` - Read-only (list, view, get)
- `green` - Additive (create, clone)
- `blue` - Reversible (start, stop, restart)
- `yellow` - Destructive but recoverable (snapshot-delete)
- `red` - Irreversible (delete, restore)
- `magenta` - Creative/generative workflows (content generation, templating)

**B. Prerequisites Section Must Include:**
- Required MCP Servers with setup links
- Required MCP Tools with descriptions
- Environment Variables (if any)
- Verification Steps
- Human Notification Protocol
- Security warning

See Principle #7 for details.

**C. When to Use Section Must Include:**
- 3+ specific scenarios
- "Do NOT use when" with alternatives

**D. Workflow Section Steps Must Include:**
- `### Step N: [Action]` heading
- Document consultation (if applicable)
- MCP Tool with server
- Parameters with exact format
- Expected output
- Error handling (2+ conditions)

---

## 8. MCP Server Availability Verification

Prerequisites MUST include verification and human notification protocol.

**CRITICAL SECURITY - NEVER expose credential values:**

**❌ WRONG:**
```bash
echo $API_SECRET                      # Exposes value
echo "SECRET=$API_SECRET"             # Exposes value
```

**✅ CORRECT:**
```bash
# Report boolean only
test -n "$API_SECRET" && echo "✓ API_SECRET is set" || echo "✗ Not set"
```

**Required Prerequisites Pattern:**
```markdown
## Prerequisites

**Required MCP Servers:** `server-name` ([setup](link))

**Required MCP Tools:** `tool_name` - Description

**Environment Variables:** `VAR` - What it controls

**Verification Steps:**
1. Check `server-name` in `mcps.json`
2. Verify `VAR` is set (without exposing value)
3. If missing → Human Notification Protocol

**Human Notification Protocol:**

When prerequisites fail:
1. **Stop immediately** - No tool calls
2. **Report error:**
 ```
 ❌ Cannot execute skill: MCP server `name` unavailable
 📋 Setup: [instructions + link]
 ```
3. **Request decision:** "How to proceed? (setup/skip/abort)"
4. **Wait for user input**

**Security:** Never display credential values.
```

**Rationale**: Graceful degradation; clear guidance; prevents credential exposure.

---

## Additional Quality Standards

### 8. Single Responsibility

One clear purpose per skill.

**✅ Good:** `vm-create`, `vm-delete`, `vm-inventory` (separate skills)
**❌ Bad:** `vm-manager` (creates, deletes, lists - too broad)

---

### 9. Naming Conventions

- kebab-case only
- Folder matches `name` field exactly
- File named `SKILL.md` (uppercase)
- Name: 1-64 chars, `a-z0-9-`, no consecutive `--`, no leading/trailing `-`

**✅ Correct:** `skills/vm-create/SKILL.md`
**❌ Wrong:** `skills/VM-Create/skill.md`, `skills/vm_create/SKILL.md`

---

### 10. Content Quality

**Required:**
- No hardcoded values (use `<namespace>`, `<vm-name>`)
- No broken links
- Production-ready examples
- Complete error handling

**✅ Good:** `namespace: "<namespace>"`
**❌ Bad:** `namespace: "production"`

---

### 11. Pack-Level AGENTS.md

Every pack with skills MUST have an `AGENTS.md` in its root directory. This file is the [Lola AI Context Module](https://lobstertrap.org/lola/guides/creating-modules/#add-an-agentsmd) instruction router for the pack persona, intent routing, and global rules. Do **not** use pack-level `CLAUDE.md` — Lola manages `AGENTS.md`, not `CLAUDE.md`.

**Required Sections:**
- `## Skill-First Rule` — enforce skill invocation over direct MCP tool calls
- `## Intent Routing` — table mapping user intents to skill names
- `## MCP Servers` — list available MCP servers with descriptions
- `## Global Rules` — credential safety, confirmation requirements, next-step suggestions

**When adding a new skill**, update the pack's `AGENTS.md` intent routing table to include it.

**Reference:** [rh-ai-engineer/AGENTS.md](rh-ai-engineer/AGENTS.md)

**Validated by:** `scripts/validate_structure.py` (automated — checks existence, required sections, intent routing completeness, and rejects deprecated pack-level `CLAUDE.md`)

---

## Root-Level Frontmatter (2026 Standard)

UI/runtime fields at root; custom fields in `metadata`.

| Field Type | Location | Examples |
|------------|----------|----------|
| Runtime | Root | `model`, `allowed-tools` |
| UX/UI | Root | `color`, `version` |
| Custom | `metadata` | `author`, `priority` |

---

## Skill Template

```yaml
---
name: skill-name
description: |
[Description]

Use when:
- "Example query 1"
- "Example query 2"
- User mentions "keyword"

NOT for [use case] (use [skill] instead).
model: inherit
color: green
metadata:
author: "team"
version: "1.0"
---

# /skill-name Skill

[Overview - 1-2 sentences]

## Critical: Human-in-the-Loop Requirements
[See Principle #5 - if applicable]

## Prerequisites

**Required MCP Servers:** `server` ([setup](link))
**Required MCP Tools:** `tool` (from server) - Description
**Environment Variables:** `VAR` - Description

**Verification Steps:**
[See Principle #7]

**Human Notification Protocol:**
[See Principle #7]

**Security:** Never display credential values.

## When to Use This Skill

Use when:
- [Scenario 1]
- [Scenario 2]

Do NOT use when:
- [Anti-pattern] → Use `skill` instead

## Workflow

### Step 1: [Action]

**Document Consultation** (if needed):
1. **Action**: Read [doc.md](path) using Read tool
2. **Output**: "I consulted [doc.md](path)..."

**MCP Tool:** `tool_name` (from server)

**Parameters:**
- `param`: "value" (format details)

**Expected Output:**
```json
{"status": "success"}
```

**Error Handling:**
- If [condition]: [resolution]

## Dependencies

### Required MCP Servers
- `server` - Description ([setup](link))

### Required MCP Tools
- `tool` (from server) - What it does

### Related Skills
- `skill` - When to use

### Reference Documentation
**Internal:** [doc.md](path)
**Official:** [Title](link)

## Example Usage
[User query + skill response]
```

---

## Agent Template

```yaml
---
name: agent-name
description: |
Multi-step workflow orchestrating skills.

Use when:
- [Complex workflow]

NOT for single ops (use skills).
model: inherit
color: red
metadata:
author: "team"
tools: ["All"]
---

# [Agent Name]

[Overview]

## Prerequisites
[MCP servers and skills - see Principle #7]

## When to Use This Agent
[Multi-step workflows vs individual skills]

## Workflow

### Step 1: [Action]

**Invoke skill:**
```
Skill: skill-name
Args: [precise parameters]
```

**Human Confirmation** (if critical):
Ask: "Proceed?" Wait for confirmation.

## Dependencies
[Skills, tools, docs - see Principle #4]

## Critical: Human-in-the-Loop Requirements
[If applicable - see Principle #5]
```

---

## Summary

**Core Principles:**
1. **Document Consultation Transparency** - Read files, then declare
2. **Precise Parameter Specification** - Exact formats with examples
3. **Skill Precedence and Conciseness** - Skills over tools; <500 tokens
4. **Dependencies Declaration** - Explicit dependencies
5. **Human-in-the-Loop** - Confirmations for critical ops
6. **Mandatory Sections** - Standard structure
7. **MCP Verification** - Prerequisites with security
8. **Single Responsibility** - One purpose per skill
9. **Naming Conventions** - kebab-case
10. **Content Quality** - Production-ready examples
11. **Pack-Level AGENTS.md** - Instruction routing for every pack with skills (Lola convention)

---

**Last Updated**: 2026-03-02
**Version**: 5.0
**Applies To**: All agentic collections
**Specification Compliance**: agentskills.io v1.0
