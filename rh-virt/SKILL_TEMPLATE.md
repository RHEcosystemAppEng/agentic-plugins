# Skill Template for rh-virt Collection

This template provides the standardized structure for all skills in the `rh-virt` agentic collection. Use this when creating new skills to ensure consistency, maintainability, and compliance with Claude Code requirements.

## Overview

This template implements:
- **Repository Standards**: rh-virt collection-specific patterns and conventions
- **Claude Guidelines**: Official skill structure from [SKILL_DESIGN_PRINCIPLES.md](/SKILL_DESIGN_PRINCIPLES.md) (Design Principles #1-7)
- **MCP Integration**: OpenShift Virtualization MCP server tool usage patterns
- **Human-in-the-Loop**: Safety confirmations for critical operations

**Reference**: See [SKILL_DESIGN_PRINCIPLES.md](/SKILL_DESIGN_PRINCIPLES.md) for complete rationale.

## Quick Start

1. Copy this template to `skills/<skill-name>/SKILL.md`
2. Replace all `<placeholders>` with actual content
3. Follow the validation checklist at the end of this template
4. Verify compliance with `SKILLS_CHECKLIST.md`
5. Test the skill before committing

## Claude Code Requirements Summary

Before using this template, understand these mandatory requirements:

### 1. Document Consultation Transparency (Design Principle #1)
- Skills MUST actually read documentation using Read tool before invoking MCP tools
- Skills MUST declare consultation to user: "I consulted [file] to understand [topic]"
- **REQUIRED** for rh-virt when relevant troubleshooting docs exist (references/troubleshooting/)

### 2. Precise Parameter Specification (Design Principle #2)
- Provide exact parameter names and formats with examples
- Ensures first-attempt success when invoking MCP tools

### 3. Skill Precedence and Conciseness (Design Principle #3)
- Description field in YAML frontmatter MUST be under 500 tokens
- Focus on "when to use" with 3-5 concrete examples

### 4. Dependencies Declaration (Design Principle #4)
- List all MCP servers, tools, related skills, and documentation
- Follows specific format (see Dependencies section below)

### 5. Human-in-the-Loop Requirements (Design Principle #5)
- Skills performing critical operations MUST require explicit user confirmation
- Positioned AFTER Dependencies section (not before)
- Read-only skills use "Not Applicable" pattern

### 6. Mandatory Skill Sections (Design Principle #6)
- All sections must appear in correct order (see Template Structure below)

### 7. MCP Server Availability Verification (Design Principle #7)
- Verify MCP server configuration before executing
- NEVER expose credential values in output

---

## Template Structure

### YAML Frontmatter

**Purpose**: Loaded at agent initialization to help Claude decide which skill to invoke.

**Requirements** (from CLAUDE.md Design Principle #3):
- Description field MUST be under 500 tokens total
- Focus on "when to use" with 3-5 concrete user phrases
- Include clear anti-patterns with alternatives
- Keep summary line under 100 characters for readability

```yaml
---
name: <skill-name>        # REQUIRED: Lowercase with dashes, matches directory name
description: |            # REQUIRED: Must be under 500 tokens total
  # IMPORTANT: Keep entire description field under 500 tokens
  # This includes all lines: summary, use cases, and anti-patterns
  # Claude loads this at agent initialization - conciseness matters!

  <One-line summary of what this skill does> (max 100 characters)

  Use when:
  - "<concrete user phrase 1>"     # Actual phrases users would say
  - "<concrete user phrase 2>"     # Not generic descriptions
  - "<concrete user phrase 3>"     # At least 3 examples required

  <Key differentiator - what makes this skill unique> (1 sentence)

  NOT for <anti-pattern> (use <alternative-skill> instead).

model: inherit           # REQUIRED: Always "inherit" unless special case
                         # Only use "sonnet" or "haiku" if skill needs specific model
color: <risk-color>      # REQUIRED: red|yellow|blue|green|cyan|magenta - see Color Guide below
                         # Indicates operation risk level for user safety
metadata:                # Optional: Custom fields (2026 Agentic Skills standard)
  author: "team-name"
  priority: "high"
---

# /<skill-name> Skill

<One paragraph overview describing what this skill does, its purpose, and when to use it>

**Implementation Note** (OPTIONAL): <Any important technical notes about MCP tool usage, workarounds, or design decisions>

## Prerequisites

**Required MCP Server**: `openshift-virtualization` ([OpenShift MCP Server](https://github.com/openshift/openshift-mcp-server))

**Required MCP Tools**:
- `tool_name` (from openshift-virtualization) - Brief description of what it does
- `another_tool` (from openshift-virtualization) - Brief description

**Required Environment Variables**:
- `KUBECONFIG` - Path to Kubernetes configuration file with cluster access
- `OTHER_VAR` (if applicable) - Description

**Required Cluster Setup**:
- OpenShift cluster (>= 4.19)
- OpenShift Virtualization operator installed
- ServiceAccount with RBAC permissions to <action> <resources>
- <Any other cluster requirements>

### Prerequisite Verification

**Before executing, verify MCP server availability:**

1. **Check MCP Server Configuration**
   - Verify `openshift-virtualization` exists in `mcps.json`
   - If missing → Report to user with setup instructions

2. **Check Environment Variables**
   - Verify `KUBECONFIG` is set (check presence only, never expose value)
   - If missing → Report to user

3. **Check <Other Prerequisites>** (optional verification)
   - Verify <specific requirement>
   - If missing → Report to user

**Human Notification Protocol:**

When prerequisites fail:

```
❌ Cannot execute <skill-name>: MCP server 'openshift-virtualization' is not available

📋 Setup Instructions:
1. Add openshift-virtualization to mcps.json
2. Set KUBECONFIG environment variable: export KUBECONFIG="/path/to/kubeconfig"
3. Restart Claude Code to reload MCP servers

🔗 Documentation: https://github.com/openshift/openshift-mcp-server

❓ How would you like to proceed?
Options:
- "setup" - Help configure the MCP server now
- "skip" - Skip this skill
- "abort" - Stop workflow

Please respond with your choice.
```

⚠️ **SECURITY**: Never display actual KUBECONFIG path or credential values in output.

## When to Use This Skill

**Trigger this skill when:**
- User <specific scenario 1>
- User <specific scenario 2>
- User <specific scenario 3>
- User explicitly invokes `/<skill-name>` command

**User phrases that trigger this skill:**
- "<exact user phrase 1>"
- "<exact user phrase 2>"
- "<exact user phrase 3>"
- `/<skill-name>` (explicit command)

**Do NOT use this skill when:**
- User wants to <anti-pattern 1> → Use `<alternative-skill-1>` skill instead
- User wants to <anti-pattern 2> → Use `<alternative-skill-2>` skill instead
- User wants to <anti-pattern 3> → <Alternative action>

## Workflow

**Purpose**: Step-by-step instructions for executing this skill.

**Requirements** (from SKILL_DESIGN_PRINCIPLES.md Design Principles #1-2):
- Document Consultation BEFORE tool invocation (REQUIRED when relevant troubleshooting docs exist)
- Precise parameter specifications with examples
- Clear error handling for each step

### Step 1: <Action Name>

<Brief description of what this step does>

**CRITICAL (Include if relevant troubleshooting documentation exists)**: Document consultation MUST happen BEFORE tool invocation.

**Document Consultation** (REQUIRED when relevant troubleshooting docs exist):
1. **Action**: Read [doc.md](references/troubleshooting/doc.md) using the Read tool to understand [specific topic]
2. **Output to user**: "I consulted [doc.md](references/troubleshooting/doc.md) to understand [specific topic]."

**When to consult troubleshooting docs**:
- VM creation/lifecycle skills → Read scheduling-errors.md, storage-errors.md, network-errors.md
- VM snapshot skills → Read storage-errors.md
- Any skill encountering errors → Read relevant troubleshooting doc before reporting to user

**Available troubleshooting documentation**:
- references/troubleshooting/INDEX.md - Master index of all troubleshooting docs
- references/troubleshooting/scheduling-errors.md - VM scheduling failures (ErrorUnschedulable, taints, resources)
- references/troubleshooting/storage-errors.md - Storage and PVC issues
- references/troubleshooting/network-errors.md - Network attachment failures (Multus, NAD)
- references/troubleshooting/lifecycle-errors.md - VM lifecycle state errors
- references/troubleshooting/runtime-errors.md - Runtime and crash issues

See CLAUDE.md Design Principle #1 for complete rationale.

**MCP Tool**: `tool_name` or `category__tool_name` (from openshift-virtualization)

**Parameters** (Design Principle #2 - Precise Parameter Specification):

Provide exact parameter names, types, formats, and examples to ensure first-attempt success.

```json
{
  "param1": "<value>",          // REQUIRED: Description of param1
                                 // Example: "database-01" (exact format shown)
  "param2": "<value>",          // OPTIONAL: Description of param2
                                 // Example: "production" (namespace name)
  "param3": true                // REQUIRED: Description of what this boolean controls
                                 // Example: true (enables feature X)
}
```

**Alternative Format** (bullet list - recommended by CLAUDE.md):
- `param1`: [exact specification] - REQUIRED
  - Example: `"database-01"` (VM name to operate on)
- `param2`: [exact specification] - OPTIONAL
  - Example: `"production"` (namespace where VM exists)
- `param3`: [exact specification] - REQUIRED
  - Example: `true` (whether to enable feature X)

**Example tool invocation:**
```json
tool_name({
  "param1": "database-01",
  "param2": "production",
  "param3": true
})
```

**Expected Output**: <What the tool returns>

**Error Handling**:
- If <error condition 1> → <action to take>
- If <error condition 2> → <action to take>
- If <error condition 3> → <action to take>

**Extract/Store Information:**
- `field1` - <What to extract and why>
- `field2` - <What to extract and why>

### Step 2: <Next Action>

<Continue the same pattern for all workflow steps>

### Step N: Report Results

**On success:**

```markdown
## ✓ <Operation> Successful

**<Resource>**: `<name>` (namespace: `<namespace>`)

### <Details Section>
- **Detail 1**: <value>
- **Detail 2**: <value>
- **Detail 3**: <value>

### <Impact Section>
- ✓ <Positive outcome 1>
- ✓ <Positive outcome 2>

### Next Steps

**To <follow-up action 1>:**
"<user command>"

**To <follow-up action 2>:**
"<user command>"
```

**On failure:**

```markdown
## ❌ <Operation> Failed

**Error**: <error-message>

**<Resource>**: `<name>` (namespace: `<namespace>`)

**Common Causes:**
- **<Cause 1>** - <Explanation>
- **<Cause 2>** - <Explanation>
- **<Cause 3>** - <Explanation>

**Troubleshooting Steps:**

1. **<Step 1 title>:**
   <Instructions>

2. **<Step 2 title>:**
   <Instructions>

3. **<Step 3 title>:**
   <Instructions>

Would you like help troubleshooting this error?
```

## Common Issues

### Issue 1: <Problem Title>

**Error**: "<error message or symptom>"

**Cause**: <Why this happens>

**Solution:**
1. <Step 1 to resolve>
2. <Step 2 to resolve>
3. <Alternative if steps fail>

**Related**: See [<doc-name>.md](references/troubleshooting/<doc-name>.md) for more details

### Issue 2: <Next Problem>

**Error**: "<error message or symptom>"

**Cause**: <Why this happens>

**Solution:**
1. <Step 1>
2. <Step 2>

### Issue 3: <Third Problem>

**Error**: "<error message or symptom>"

**Cause**: <Why this happens>

**Solution:**
1. <Step 1>
2. <Step 2>

**Minimum**: Include at least 3 common issues. Add more based on actual user pain points.

## Dependencies

**Purpose**: Declare all external dependencies for debugging and prerequisite verification.

**Requirements** (from CLAUDE.md Design Principle #4):
- List MCP servers, tools, related skills, and documentation
- Makes dependencies explicit for troubleshooting
- Enables proper error handling when dependencies missing

### Required MCP Servers
- `openshift-virtualization` - OpenShift MCP server with kubevirt toolset
  - Source: https://github.com/openshift/openshift-mcp-server

### Required MCP Tools

List each tool with its purpose, parameters, and source.

- `tool_name` (from openshift-virtualization) - Brief description of what it does
  - **Used for**: <specific use case in this skill>
  - **Parameters**: <key parameters used by this skill>
  - **Source**: https://github.com/openshift/openshift-mcp-server

- `another_tool` (from openshift-virtualization) - Brief description
  - **Used for**: <specific use case>
  - **Parameters**: <key parameters>
  - **Source**: https://github.com/openshift/openshift-mcp-server

### Related Skills

List skills that complement or replace this skill.

- `skill-name-1` - When to use it instead of this skill (alternative)
- `skill-name-2` - Complementary skill (use together)
- `skill-name-3` - Follow-up skill (use after this one completes)

### Reference Documentation

**Internal Troubleshooting Documentation**:
- [INDEX.md](references/troubleshooting/INDEX.md) - Master troubleshooting index
- [scheduling-errors.md](references/troubleshooting/scheduling-errors.md) - VM scheduling failures
- [storage-errors.md](references/troubleshooting/storage-errors.md) - Storage and PVC issues
- [network-errors.md](references/troubleshooting/network-errors.md) - Network attachment failures
- [lifecycle-errors.md](references/troubleshooting/lifecycle-errors.md) - VM lifecycle errors
- [runtime-errors.md](references/troubleshooting/runtime-errors.md) - Runtime and crash issues

**Official Red Hat Documentation**:
- [Topic - OpenShift <version>](https://docs.redhat.com/en/documentation/openshift_container_platform/<version>/html-single/virtualization/index#section) - Main documentation
- [Blog Post Title](https://www.redhat.com/en/blog/post-slug) - Additional context

**Upstream Documentation**:
- [KubeVirt Topic](https://kubevirt.io/user-guide/...) - Upstream project docs
- [Kubernetes Topic](https://kubernetes.io/docs/...) - K8s specification

**IMPORTANT**: Always use the latest stable OpenShift version available for documentation links (check https://docs.redhat.com/ for current version).

## Critical: Human-in-the-Loop Requirements

**Purpose**: Define when and how to request user confirmation for critical operations.

**Requirements** (from CLAUDE.md Design Principle #5):
- Skills performing critical operations MUST require explicit user confirmation
- This section appears AFTER Dependencies section (Design Principle #6)
- Read-only skills use "Not Applicable" pattern (see vm-inventory for example)

**When to Include**:
- Playbook execution (ansible-mcp-server)
- System modifications (package updates, config changes)
- Multi-system operations (batch remediation)
- Data deletion or irreversible actions
- Resource creation that consumes cluster capacity

**When to Omit**:
- Read-only operations (list/view operations) - Use "Not Applicable" pattern instead

---

**IMPORTANT:** This skill <performs X operations>. You MUST:

1. **<Requirement Category>** (e.g., "Before Creating Resources")
   - <Specific action 1>
   - <Specific action 2>
   - <Expected behavior>
   - Ask: "Should I proceed with [specific action]?"
   - Wait for explicit user confirmation

2. **<Next Requirement Category>** (e.g., "Before Destructive Actions")
   - Display preview of changes
   - <Specific action 2>
   - Ask: "Review the changes above. Should I execute this?"
   - Wait for explicit "yes" or "proceed"

3. **Never Auto-Execute**
   - **NEVER <action> without <condition>**
   - **NEVER <action> when <condition>**
   - **NEVER skip <critical step>**
   - **NEVER assume approval** - always wait for explicit user confirmation

**Why This Matters:**
- **<Impact 1>**: <Explanation of business/operational impact>
- **<Impact 2>**: <Explanation of business/operational impact>
- **<Impact 3>**: <Explanation of business/operational impact>

**Rationale**: Prevents unintended automation; maintains user control over critical operations.

---

**For Read-Only Skills** (use this pattern instead):

**Not applicable** - This skill performs read-only operations and does not modify any cluster resources. No user confirmation is required.

**Read-only operations:**
- <Operation 1>
- <Operation 2>
- <Operation 3>

**No modifications performed:**
- ✓ Does not change cluster state
- ✓ Does not modify resources
- ✓ Does not consume cluster resources

## Security Considerations

- **RBAC Enforcement**: Requires <specific permissions> for <resource types>
- **Data Protection**: <How data is protected during operation>
- **Namespace Isolation**: <How namespace boundaries are enforced>
- **Storage Quotas**: <How quotas are respected>
- **Audit Trail**: <What operations are logged>
- **KUBECONFIG Security**: Credentials never exposed in output
- **<Other Security Aspect>**: <Description>

## Example Usage

### Example 1: <Scenario Name>

```
User: "<user request>"

Agent: [Invokes <skill-name> skill]
       [<Step 1 description>]

<Output shown to user - use actual markdown formatting>

## <Output Title>

**Field**: `value`

| Column 1 | Column 2 | Column 3 |
|----------|----------|----------|
| data1    | data2    | data3    |

User: "<user response>"

Agent: [<Next action>]

<Final output>

## ✓ <Success Message>

Next steps: "<follow-up command>"
```

### Example 2: <Another Scenario> (OPTIONAL)

<Follow same format as Example 1>

**Minimum**: Include at least 1 complete example showing the full workflow.

## Advanced Features (OPTIONAL)

Include this section only if there are advanced use cases.

### <Advanced Feature 1>

<Description and usage>

### <Advanced Feature 2>

<Description and usage>

**Examples:**
- Batch operations
- Special configurations
- Integration with other tools
- Performance optimizations
```

---

## Color Guide

Use the following color codes based on operation characteristics:

| Color | When to Use | Examples |
|-------|-------------|----------|
| **cyan** | Read-only operations (list/view) | vm-inventory, vm-snapshot-list |
| **green** | Additive operations (create new resources) | vm-create, vm-snapshot-create |
| **blue** | Reversible state changes | vm-lifecycle-manager, vm-clone |
| **yellow** | Destructive but recoverable operations | vm-snapshot-delete |
| **red** | Irreversible/critical operations (data loss risk) | vm-delete, vm-snapshot-restore |
| **magenta** | Creative, generation | content generation, templating |

---

## Comprehensive Validation Checklist

Before committing your skill, verify compliance with both **repository standards** and **Claude Code requirements**.

### 1. YAML Frontmatter (Design Principle #3)

- [ ] **name**: Lowercase with dashes, matches directory name
- [ ] **description**: Under 500 tokens total (CRITICAL)
- [ ] **description**: Includes 3-5 concrete "Use when" examples
- [ ] **description**: Includes anti-patterns with alternatives ("NOT for X, use Y instead")
- [ ] **description**: Summary line under 100 characters
- [ ] **model**: Set to "inherit" (unless special case requires specific model)
- [ ] **color**: Matches operation type (see Color Guide)

### 2. Section Presence and Order (Design Principle #6)

Sections MUST appear in this exact order:

- [ ] 1. Skill title (`# /skill-name Skill`)
- [ ] 2. **Prerequisites** (with MCP server verification)
- [ ] 3. **When to Use This Skill** (with anti-patterns)
- [ ] 4. **Workflow** (with step-by-step instructions)
- [ ] 5. **Common Issues** (at least 3 issues documented)
- [ ] 6. **Dependencies** (MCP servers, tools, skills, docs)
- [ ] 7. **Critical: Human-in-the-Loop Requirements** (if applicable)
- [ ] 8. **Security Considerations**
- [ ] 9. **Example Usage** (at least 1 complete example)
- [ ] 10. **Advanced Features** (optional)

### 3. Prerequisites Section (Design Principle #7)

- [ ] Lists required MCP servers with setup guide links
- [ ] Lists required MCP tools with descriptions
- [ ] Lists required environment variables (if applicable)
- [ ] Includes prerequisite verification steps
- [ ] Includes Human Notification Protocol for failures
- [ ] **SECURITY**: Never exposes credential values in output

### 4. Workflow Section (SKILL_DESIGN_PRINCIPLES.md #1-2)

- [ ] **Document Consultation** pattern included when relevant troubleshooting docs exist
  - REQUIRED when skill relates to documented error scenarios
  - Consultation happens BEFORE tool invocation
  - Includes "Output to user" declaration
  - References specific troubleshooting docs (scheduling-errors.md, storage-errors.md, etc.)
- [ ] **Parameters**: Precise specifications with exact formats
- [ ] **Parameters**: Includes examples for each parameter
- [ ] **Expected Output**: Describes what tools return
- [ ] **Error Handling**: Documented for each step

### 5. Common Issues Section

- [ ] At least 3 common issues documented
- [ ] Each issue has: Error, Cause, Solution
- [ ] Solutions include 2-4 actionable steps
- [ ] Concise format (8-12 lines per issue)

### 6. Dependencies Section (Design Principle #4)

- [ ] **Required MCP Servers**: Listed with source links
- [ ] **Required MCP Tools**: Listed with parameters and use cases
- [ ] **Related Skills**: Listed with relationship explanation
- [ ] **Reference Documentation**: Latest stable OpenShift version
- [ ] Documentation links are valid and accessible

### 7. Human-in-the-Loop Section (Design Principle #5)

- [ ] Positioned AFTER Dependencies section (not before)
- [ ] Required for: resource creation, state changes, destructive operations
- [ ] Uses "Not Applicable" pattern for read-only skills
- [ ] Specifies exact confirmation points
- [ ] Includes "Why This Matters" rationale
- [ ] Uses **NEVER** statements to prevent auto-execution

### 8. Security Considerations

- [ ] RBAC enforcement documented
- [ ] Data protection mechanisms explained
- [ ] Namespace isolation described
- [ ] Audit trail mentioned
- [ ] KUBECONFIG security confirmed (credentials never exposed)

### 9. Example Usage

- [ ] At least 1 complete example included
- [ ] Shows realistic user-agent interaction
- [ ] Demonstrates full workflow from start to finish
- [ ] Uses actual markdown formatting in output

### 10. Quality and Style

- [ ] No emojis (unless explicitly requested by user)
- [ ] Markdown formatting correct (tables, code blocks, lists)
- [ ] No credential exposure in examples or text
- [ ] Cross-references use relative paths
- [ ] Skill name used consistently throughout

### 11. Testing

- [ ] Skill file loads without YAML parse errors
- [ ] All internal links are valid (skills, docs)
- [ ] All external links are accessible (Red Hat docs, GitHub)
- [ ] Skill has been tested with actual MCP server
- [ ] All workflow steps produce expected results

### 12. Repository Standards

- [ ] File located at `skills/<skill-name>/SKILL.md`
- [ ] Directory name matches frontmatter `name` field
- [ ] Color code appropriate for operation risk
- [ ] Follows rh-virt collection conventions
- [ ] No conflicts with existing skill names

---

**Quick Verification Commands**:

```bash
# Check frontmatter token count (rough estimate)
wc -w skills/<skill-name>/SKILL.md | head -n 20

# Verify section order
grep "^## " skills/<skill-name>/SKILL.md

# Check for credential exposure (should return nothing)
grep -i "password\|secret\|token.*=" skills/<skill-name>/SKILL.md
```

---

See `SKILLS_CHECKLIST.md` for the complete validation guide with scoring criteria.

---

## Tips for Writing Great Skills

### Content Quality

1. **Be Specific**: Use concrete examples, not generic placeholders
   - ❌ "Create a VM with specified parameters"
   - ✅ "Create VM database-01 with 4GB RAM in production namespace"

2. **Show Real Output**: Include actual markdown formatting in examples
   - Use real table data, actual status messages, realistic error text
   - Demonstrate what users will actually see

3. **Test First**: Run the skill before documenting to capture real behavior
   - Document actual tool outputs, not assumptions
   - Include real error messages you encountered

4. **Think Like Users**: Use actual phrases users would say
   - "List all VMs" not "Enumerate virtual machine resources"
   - "Start the database VM" not "Initiate VM power-on sequence"

### Claude Code Compliance

5. **Follow Design Principles**: Reference [SKILL_DESIGN_PRINCIPLES.md](/SKILL_DESIGN_PRINCIPLES.md) for rationale
   - **Principle #1**: Document Consultation (read docs before tools)
   - **Principle #2**: Precise Parameters (exact formats with examples)
   - **Principle #3**: Concise Descriptions (under 500 tokens)
   - **Principle #4**: Dependencies Declaration (explicit listing)
   - **Principle #5**: Human-in-the-Loop (user confirmation for critical ops)
   - **Principle #6**: Mandatory Sections (correct order)
   - **Principle #7**: MCP Verification (check availability)

6. **Link Everything**: Cross-reference related skills and documentation
   - Use skill-local paths: `references/file.md` or `../other-skill/SKILL.md`
   - Verify links are valid before committing

7. **Keep Current**: Use latest stable OpenShift version for all docs
   - Check https://docs.redhat.com/ for current version
   - Update documentation links when new versions release

### Style and Safety

8. **No Jargon**: Explain technical terms when first introduced
   - First use: "VirtualMachineInstance (VMI) - the running pod for a VM"
   - Subsequent: "VMI" is fine

9. **Error First**: Document common failures before edge cases
   - Users hit common issues 90% of the time
   - Rare edge cases can go in Advanced Features

10. **Security Always**: Never expose credentials, always check RBAC
    - ✓ "KUBECONFIG is set"
    - ❌ "KUBECONFIG=/path/to/kubeconfig"
    - ✓ "Requires update permissions for VirtualMachines"
    - ❌ Never include actual secrets, tokens, passwords

### Maintainability

11. **Consistency Matters**: Follow this template exactly
    - Same section order across all skills
    - Same formatting for MCP tools
    - Same pattern for error handling

12. **Version Control**: Document when you reference external content
    - "As of OpenShift 4.21..." for version-specific behavior
    - Link to specific doc versions when behavior may change

13. **Self-Documenting**: Skill should be understandable without external context
    - Don't assume user has read other skills
    - Repeat critical information (RBAC requirements, prerequisites)
    - Link to related skills for more detail

### Common Pitfalls to Avoid

- ❌ Hardcoding version numbers (use "latest stable" unless version-specific)
- ❌ Assuming prerequisites are met (always verify MCP server availability)
- ❌ Verbose Common Issues sections (keep 8-12 lines per issue)
- ❌ Missing anti-patterns in frontmatter (always include "NOT for X")
- ❌ Parameters without examples (always show exact format)
- ❌ Human-in-the-Loop before Dependencies (wrong section order)
- ❌ Description over 500 tokens (violates Claude requirement)

### Quality Checklist Before Committing

- [ ] Ran the skill with actual MCP server
- [ ] Captured real tool outputs in examples
- [ ] Verified all links are valid
- [ ] Checked frontmatter under 500 tokens
- [ ] Included 3-5 "Use when" examples
- [ ] Documented 3+ common issues
- [ ] Positioned Human-in-the-Loop correctly (after Dependencies)
- [ ] No credentials exposed anywhere
- [ ] Followed color guide for operation type
- [ ] Used latest stable OpenShift version

**Remember**: Skills are loaded by Claude Code's agent system. Clear, precise, concise documentation helps Claude make correct decisions about when to invoke your skill.

---

## Claude Code Design Principles Reference

For complete details, see [SKILL_DESIGN_PRINCIPLES.md](/SKILL_DESIGN_PRINCIPLES.md).

### Principle #1: Document Consultation Transparency

**What**: Skills MUST read documentation before invoking tools, then declare consultation to user.

**Why**: Ensures AI enriches context with domain knowledge; provides transparency to users.

**How**:
```markdown
**Document Consultation** (REQUIRED - Execute FIRST):
1. **Action**: Read [doc.md](path) using Read tool to understand [topic]
2. **Output to user**: "I consulted [doc.md](path) to understand [topic]."
```

**Status for rh-virt**: REQUIRED when relevant troubleshooting documentation exists. Skills should consult references/troubleshooting/ files before handling errors or complex operations.

### Principle #2: Precise Parameter Specification

**What**: Provide exact parameter names, types, and formats with examples.

**Why**: Ensures first-attempt success when invoking MCP tools; reduces wasted cycles.

**How**:
```markdown
**Parameters**:
- `param1`: "value" (exact format)
  - Example: `"database-01"` (VM name to operate on)
```

### Principle #3: Skill Precedence and Conciseness

**What**: Description field MUST be under 500 tokens; focus on "when to use".

**Why**: Minimizes token usage at agent initialization while maintaining clarity.

**How**: Keep frontmatter concise with 3-5 concrete examples, defer details to skill body.

### Principle #4: Dependencies Declaration

**What**: List all MCP servers, tools, related skills, and documentation.

**Why**: Makes dependencies explicit for debugging and error handling.

**How**: Follow required format in Dependencies section of template.

### Principle #5: Human-in-the-Loop Requirements

**What**: Skills performing critical operations MUST require explicit user confirmation.

**Why**: Prevents unintended automation; maintains user control.

**How**: Position AFTER Dependencies section; specify exact confirmation points.

### Principle #6: Mandatory Skill Sections

**What**: All sections must appear in correct order.

**Why**: Standardizes skill structure for consistency and completeness.

**How**: Follow exact order: Prerequisites → When to Use → Workflow → Common Issues → Dependencies → Human-in-the-Loop → Security → Examples.

### Principle #7: MCP Server Availability Verification

**What**: Verify MCP server configuration before executing.

**Why**: Provides graceful degradation and clear user guidance when dependencies missing.

**How**: Include verification steps in Prerequisites section with Human Notification Protocol.

**CRITICAL SECURITY**: Never expose credential values in output (only report presence/absence).

---

## Repository Context

**Collection**: rh-virt (OpenShift Virtualization management)
**MCP Server**: openshift-virtualization (https://github.com/openshift/openshift-mcp-server)
**Pattern**: MCP-first approach (always use MCP tools, not CLI fallbacks)
**Documentation**: skills/*/references/troubleshooting/ contains error resolution guides (6 documents)

**Related Collections**:
- rh-sre: Reference implementation with plugin references/ index and semantic indexing
- Use rh-sre as architectural reference for advanced patterns

---

## Getting Help

- **Template Issues**: See `SKILLS_CHECKLIST.md` for detailed validation guide
- **Claude Requirements**: Read `/CLAUDE.md` for complete design principles
- **MCP Server**: Check https://github.com/openshift/openshift-mcp-server for tool documentation
- **OpenShift Virt**: Reference https://docs.redhat.com/ for latest virtualization docs

---

**Last Updated**: 2026-02-18
**Template Version**: 2.0 (Claude Code compliant)
