---
name: execution-risk-analyzer
description: |
  Analyze execution risk by classifying inventory, scanning extra_vars for secrets, and assessing scope.

  Use when:
  - "Execute on production", "Deploy to production" (as first step before launch)
  - "Is this execution safe?"
  - "Check execution risk"
  - "Validate the execution target"

  NOT for: launching jobs (use governed-job-launcher) or troubleshooting failures (use job-failure-analyzer).
model: inherit
color: yellow
license: Apache-2.0
allowed-tools: job_templates_list job_templates_retrieve job_templates_launch_retrieve jobs_list jobs_job_events_list workflow_job_templates_list inventories_list hosts_list
---

# Execution Risk Analyzer

## Prerequisites

**Required MCP Servers**:
- `aap-mcp-job-management` - Job template lookup and launch parameter inspection
- `aap-mcp-inventory-management` - Inventory and host data

**Verification**: Run the `aap-mcp-validator` skill with these 2 servers before proceeding.

## When to Use This Skill

Use this skill when:
- User requests a job execution targeting any environment
- Before any job template launch (as part of governance-executor workflow)
- User asks to check if an execution is safe
- User asks to validate execution parameters

Do NOT use when:
- Actually launching the job (use `governed-job-launcher` skill after this skill)
- Troubleshooting a failed job (use `job-failure-analyzer` skill)
- Assessing platform governance (use `governance-readiness-assessor` skill)

## Workflow

### Step 1: Consult Execution Governance Documentation

**CRITICAL**: Document consultation MUST happen BEFORE any MCP tool invocations.

**Document Consultation** (REQUIRED - Execute FIRST):
1. **Action**: Read [execution-governance.md](../../docs/aap/execution-governance.md) using the Read tool to understand inventory risk classification, extra_vars safety scanning, and governance controls
2. **Output to user**: "I consulted [execution-governance.md](docs/aap/execution-governance.md) which cites Red Hat's Security Best Practices and Job Templates documentation for execution governance controls."

### Step 2: Identify the Job Template

**MCP Tool**: `job_templates_list` (from aap-mcp-job-management)
**Parameters**:
- `search`: `"<template_name_from_user_request>"`
- `page_size`: `10`

If the user provides a template ID directly:

**MCP Tool**: `job_templates_retrieve` (from aap-mcp-job-management)
**Parameters**:
- `id`: `"<template_id>"`

### Step 3: Inspect Launch Parameters

**MCP Tool**: `job_templates_launch_retrieve` (from aap-mcp-job-management)
**Parameters**:
- `id`: `"<template_id>"`

This returns the template's expected extra_vars, defaults, required fields, and inventory configuration.

### Step 4: Classify Inventory Risk

**MCP Tool**: `inventories_list` (from aap-mcp-inventory-management)
**Parameters**:
- `page_size`: `100`

Identify the target inventory from the job template configuration or user-provided override. Apply the risk classification from execution-governance.md:

| Inventory Name Pattern | Risk Level | Governance Required |
|---|---|---|
| Contains `prod`, `production`, `live` | **CRITICAL** | Check mode + approval + phased rollout recommended |
| Contains `stage`, `staging`, `uat`, `preprod` | **HIGH** | Check mode + approval |
| Contains `test`, `qa` | **MEDIUM** | Confirmation only |
| Contains `dev`, `development`, `sandbox`, `lab` | **LOW** | Direct execution permitted |

For unclassifiable inventories, check host count:

**MCP Tool**: `hosts_list` (from aap-mcp-inventory-management)
**Parameters**:
- `search`: `"<inventory_name>"`
- `page_size`: `1`

**Transparency note**: Per execution-governance.md, inventory risk classification is this agent's implementation of Red Hat's recommendation to "use separate inventories for production and development environments" (Controller Best Practices).

### Step 5: Pre-Execution Context Analysis (Scenario-Driven)

Per the "Pre-Execution Context Analysis" section of execution-governance.md, examine the template's operational context. These queries adapt the risk assessment to the specific scenario.

**5a. Job History** (always check):

**MCP Tool**: `jobs_list` (from aap-mcp-job-management)
**Parameters**:
- `job_template`: `"<template_id>"`
- `order_by`: `"-finished"`
- `page_size`: `5`

Examine the most recent 5 runs. Report:
- If all successful → "Clear history"
- If most recent failed → **WARN**: "Last run of this template failed. Investigate before re-executing."
- If 2+ consecutive failures → **ELEVATED**: "Template has failed [N] consecutive times."
- If 0 runs → **INFO**: "First execution of this template -- extra caution recommended."

**5b. Launch Configuration** (always check -- data available from Step 3):

From the `job_templates_launch_retrieve` response (Step 3), examine:
- `ask_job_type_on_launch`: If `false` AND risk is CRITICAL/HIGH → Warn that check mode cannot be enforced at launch time
- `ask_limit_on_launch`: If `false` AND risk is CRITICAL → Warn that phased rollout is not possible
- `ask_diff_mode_on_launch`: If `false` → Note that diff mode cannot be enabled at launch

**5c. Notification Bindings** (check for CRITICAL/HIGH risk):

**MCP Tool**: `job_templates_retrieve` (from aap-mcp-job-management)
**Parameters**:
- `id`: `"<template_id>"`

Check notification association fields. If no failure notifications are bound:
Report: "Per Red Hat's Notifications documentation (Ch. 25), this template has no failure notification. If execution fails, no one will be automatically alerted."

**5d. Workflow Coverage** (check for CRITICAL/HIGH risk):

**MCP Tool**: `workflow_job_templates_list` (from aap-mcp-job-management)
**Parameters**:
- `page_size`: `100`

If no workflows reference this template:
Report: "Per Red Hat's Workflow documentation (Ch. 9), this template runs standalone -- not wrapped in a workflow with approval gates or failure paths."

**5e. Module Analysis** (check if job history exists):

If Step 5a found previous runs, examine events from the most recent job:

**MCP Tool**: `jobs_job_events_list` (from aap-mcp-job-management)
**Parameters**:
- `id`: `"<most_recent_job_id>"`
- `page_size`: `50`

If events show `ansible.builtin.shell` or `ansible.builtin.command` usage:
Report specific warning: "This playbook uses shell/command modules ([X] tasks). Check mode will SKIP these tasks entirely."

**5f. Adaptive Risk Adjustment**:

Based on collected signals, adjust the base risk level per execution-governance.md's "Adaptive Risk Enhancement" table:
- HIGH + never run + check mode not overridable → elevate to **CRITICAL**
- LOW + recent failures → elevate to **MEDIUM**
- Any risk + no notifications on production target → add advisory flag

### Step 6: Scan Extra Vars for Secrets

Inspect the extra_vars that would be passed to the job. Check both:
1. Default extra_vars from the template (from Step 3)
2. User-provided extra_vars overrides

**Secret detection** (per execution-governance.md):
- Key names containing (case-insensitive): `password`, `secret`, `token`, `api_key`, `apikey`, `private_key`, `ssh_key`, `access_key`, `auth`
- Values that look like tokens: long alphanumeric strings, base64, prefixes like `sk-`, `ghp_`, `Bearer`

**Transparency note**: Per execution-governance.md, secret scanning implements Red Hat's recommendation to "Remove user access to credentials" (Ch. 15, Sec. 15.1.4) by detecting plain-text secrets in extra_vars that should be managed via AAP credentials.

### Step 7: Generate Risk Report

**Output format**:

```
## Execution Risk Analysis

**Job Template**: [name] (ID: [id])
**Target Inventory**: [name]
**Base Risk Level**: [CRITICAL / HIGH / MEDIUM / LOW]
**Adjusted Risk Level**: [same or elevated, with rationale if different]

### Risk Classification

Per Red Hat's *Controller Best Practices*: "Use separate inventories for production and development environments."

**Inventory signal**: [name pattern match or host count]
**Risk level**: [CRITICAL/HIGH/MEDIUM/LOW]
**Governance required**: [check mode + approval / confirmation only / direct execution]

### Operational Context [section only appears when signals found]

| Signal | Finding | Impact |
|---|---|---|
| Job History | [clear / last run failed / N consecutive failures / first run] | [proceed / investigate / elevated caution] |
| Check Mode Override | [available / not overridable] | [governance enforceable / template modification needed] |
| Phased Rollout | [available / not overridable] | [limit parameter works / all-or-nothing execution] |
| Notifications | [failure notifications bound / none configured] | [team will be alerted / silent failures] |
| Workflow Coverage | [wrapped in workflow / standalone] | [approval gates available / no governance gates] |
| Playbook Modules | [standard modules / shell/command detected ([X] tasks)] | [check mode reliable / partial dry-run coverage] |

### Extra Vars Safety Scan

Per Red Hat's *Security Best Practices* (Ch. 15, Sec. 15.1.4): "Remove user access to credentials."

| Check | Status | Detail |
|---|---|---|
| Secret-like key names | [PASS/FAIL] | [findings] |
| Plain-text values | [PASS/FAIL] | [findings] |

### Recommendation

[Based on risk level AND operational context, what governance controls should be applied]
[If risk was elevated: explain why and cite the triggering signals]
```

**If secrets are found**: BLOCK the execution and recommend using AAP credentials instead.

**If CRITICAL/HIGH risk**: Recommend check mode execution before full run.

**If risk was elevated** by operational signals: Explain the elevation clearly (e.g., "Risk elevated from HIGH to CRITICAL because this template has never been run and check mode cannot be overridden").

**If LOW risk with no signals**: Approve for direct execution with user confirmation.

## Dependencies

### Required MCP Servers
- `aap-mcp-job-management` - Job template data
- `aap-mcp-inventory-management` - Inventory and host data

### Required MCP Tools
- `job_templates_list` (from job-management) - Find template by name
- `job_templates_retrieve` (from job-management) - Get template details and notification bindings
- `job_templates_launch_retrieve` (from job-management) - Get launch parameters and prompt-on-launch config
- `jobs_list` (from job-management) - Check recent job history for the template
- `jobs_job_events_list` (from job-management) - Analyze previous run's module usage
- `workflow_job_templates_list` (from job-management) - Check workflow coverage
- `inventories_list` (from inventory-management) - List inventories
- `hosts_list` (from inventory-management) - Host count for unclassifiable inventories

### Related Skills
- `aap-mcp-validator` - Prerequisite validation
- `governed-job-launcher` - Next step after risk analysis passes
- `execution-summary` - Audit trail

### Reference Documentation
- [execution-governance.md](../../docs/aap/execution-governance.md) - Risk classification and safety scanning reference

## Example Usage

**User**: "Execute the security patch on production"

**Agent**:
1. Reads execution-governance.md
2. Reports: "I consulted execution-governance.md which cites Red Hat's Security Best Practices and Controller Best Practices."
3. Finds "Security Patch" template via `job_templates_list`
4. Inspects launch parameters via `job_templates_launch_retrieve`
5. Identifies "Production" inventory → CRITICAL base risk
6. **Adapts**: Checks job history → last run failed → adds WARN signal
7. **Adapts**: Checks launch config → `ask_job_type_on_launch: true` → check mode enforceable
8. **Adapts**: Checks notifications → no failure notifications → flags gap
9. **Adapts**: Checks previous run events → finds shell/command tasks → elevates check mode warning
10. Scans extra_vars → no secrets found
11. Reports: "Risk Level: CRITICAL (confirmed). Operational context: last run failed, no failure notifications configured, playbook uses 2 shell tasks that check mode will skip. Recommend investigating last failure before proceeding."
