---
name: playbook-executor
description: >-
  Execute generated Ansible remediation playbooks through AAP, including template
  selection, dry-run, job monitoring, and reporting.
model: inherit
color: red
license: Apache-2.0
allowed-tools: job_templates_list job_templates_retrieve projects_list job_templates_launch_retrieve jobs_retrieve jobs_stdout_retrieve jobs_job_events_list jobs_job_host_summaries_list jobs_relaunch_retrieve inventories_list hosts_list
---

# AAP Playbook Executor Skill

This skill executes Ansible remediation playbooks through AAP (Ansible Automation Platform) with full job management capabilities.

**Integration with Remediation Skill**: The `/remediation` skill orchestrates this skill as part of its Step 5 (Execute Playbook) workflow. For standalone playbook execution, you can invoke this skill directly.

## Prerequisites

**Required MCP Servers**: `aap-mcp-job-management`, `aap-mcp-inventory-management` ([setup guide](https://docs.redhat.com/))

**Required MCP Tools**:
- `job_templates_list` (from aap-mcp-job-management) - List job templates
- `job_templates_retrieve` (from aap-mcp-job-management) - Get template details
- `projects_list` (from aap-mcp-job-management) - Get project name and scm_url for Git Flow
- `job_templates_launch_retrieve` (from aap-mcp-job-management) - Launch jobs
- `jobs_retrieve` (from aap-mcp-job-management) - Get job status
- `jobs_stdout_retrieve` (from aap-mcp-job-management) - Get console output
- `jobs_job_events_list` (from aap-mcp-job-management) - Get task events
- `jobs_job_host_summaries_list` (from aap-mcp-job-management) - Get host statistics
- `inventories_list` (from aap-mcp-inventory-management) - List inventories
- `hosts_list` (from aap-mcp-inventory-management) - List inventory hosts

**Required Environment Variables**:
- `AAP_MCP_SERVER` - Base URL for the MCP endpoint of the AAP server (must point to the AAP MCP gateway)
- `AAP_API_TOKEN` - AAP API authentication token

### Prerequisite Validation

**CRITICAL**: Before executing operations, execute the `/mcp-aap-validator` skill to verify AAP MCP server availability.

**Validation freshness**: Can skip if already validated in this session..

**How to invoke**: Execute the `/mcp-aap-validator` skill

**Handle validation result**:
- **If validation PASSED**: Continue with playbook execution workflow
- **If validation PARTIAL**: Warn user and ask to proceed
- **If validation FAILED**: Stop execution, provide setup instructions from validator

**Human Notification on Failure**:
If prerequisites are not met:
- ❌ "Cannot proceed: AAP MCP servers are not available"
- 📋 "Setup required: Configure AAP_MCP_SERVER and AAP_API_TOKEN environment variables"
- ❓ "How would you like to proceed? (setup now / skip / abort)"
- ⏸️ Wait for user decision

## When to Use This Skill

**Use this skill directly when you need**:
- Execute a previously generated Ansible playbook via AAP
- Track the status of a running AAP job
- Monitor playbook job completion
- Run dry-run (check mode) before production execution
- Verify playbook execution succeeded

**Use the `/remediation` skill when you need**:
- Full remediation workflow including playbook execution
- Integrated CVE analysis → playbook generation → execution → verification
- End-to-end remediation orchestration

**How they work together**: The `/remediation` skill invokes this skill after generating a remediation playbook, managing the full workflow from analysis to verification.

## Workflow

**Git Flow is MANDATORY**: When the job template's playbook path differs from the generated playbook (or content must be updated), you MUST perform Git Flow (write, commit, push, sync) and receive "sync complete" from the user BEFORE launching any job. Do NOT skip this—launching without it executes the wrong playbook.

### Phase 0: Validate AAP MCP Prerequisites

**Action**: Execute the `/mcp-aap-validator` skill

**Note**: Can skip if validation was performed earlier in this session and succeeded.

**How to invoke**: Execute the `/mcp-aap-validator` skill

**Handle validation result**:
- **If validation PASSED**: Continue to Phase 1
- **If validation PARTIAL**: Warn user and ask to proceed
- **If validation FAILED**: Stop execution, user must set up AAP MCP servers

### Phases 1–6: Select, Prepare, Execute, and Report

After prerequisite validation, follow [references/06-execution-workflow.md](references/06-execution-workflow.md) for template selection, the required user-approved Git Flow and sync checkpoint, dry-run, production confirmation, monitoring, reporting, and error handling. The linked reference points to the appropriate display and report templates. Do not launch before required sync and explicit user confirmation.

## Reference Files

| File | Use When |
|------|----------|
| [01-execution-report-templates.md](references/01-execution-report-templates.md) | Phase 5 reports, Success/Partial/Failure output |
| [02-error-handling-guide.md](references/02-error-handling-guide.md) | Phase 6 error reports, relaunch |
| [03-workflow-examples.md](references/03-workflow-examples.md) | Demo full workflow, failure handling, skip dry-run |
| [04-dry-run-display-templates.md](references/04-dry-run-display-templates.md) | Phase 3 preview, offer, results, proceed prompt |
| [05-git-flow-prompts.md](references/05-git-flow-prompts.md) | Scenario 1/2 prompts, Git Flow HITL, after-push |
| [06-execution-workflow.md](references/06-execution-workflow.md) | Detailed phases 1–6 execution procedure |

## Dependencies

Use these AAP MCP servers and tools to validate, launch, and monitor jobs.

### Required MCP Servers
- `aap-mcp-job-management` - AAP job management and execution
- `aap-mcp-inventory-management` - AAP inventory management

### Required MCP Tools
- `job_templates_list` (from aap-mcp-job-management) - List templates
- `job_templates_retrieve` (from aap-mcp-job-management) - Get template details
- `projects_list` (from aap-mcp-job-management) - Get project name and scm_url for Git Flow
- `job_templates_launch_retrieve` (from aap-mcp-job-management) - Launch jobs
- `jobs_retrieve` (from aap-mcp-job-management) - Get job status
- `jobs_stdout_retrieve` (from aap-mcp-job-management) - Get console output
- `jobs_job_events_list` (from aap-mcp-job-management) - Get task events
- `jobs_job_host_summaries_list` (from aap-mcp-job-management) - Get host statistics
- `inventories_list` (from aap-mcp-inventory-management) - List inventories
- `hosts_list` (from aap-mcp-inventory-management) - List hosts

### Related Skills
- `mcp-aap-validator` - **PREREQUISITE** - Validates AAP MCP servers (invoke in Phase 0)
- `job-template-remediation-validator` - **REQUIRED** - Invoke for each candidate template in Phase 1 Step 1.2 to verify remediation requirements
- `job-template-creator` - Creates/guides AAP job template setup
- `playbook-generator` - Generates playbooks for execution
- `remediation-verifier` - Verifies success after execution

### Reference Documentation
- [references/](references/) - Step-numbered reference files (01–05) for templates and examples
- [AAP Job Execution Guide](references/ansible/aap-job-execution.md) - AAP job execution best practices
- [Playbook Integration with AAP](references/ansible/playbook-integration-aap.md) - Playbook-to-AAP workflow

## Critical: Human-in-the-Loop Requirements

This skill executes code on production systems. **Explicit user confirmation is REQUIRED** at multiple stages.

**Before Git commit/push** (Scenario 1 Override, Scenario 2):
1. **Display change summary**: File path, diff or file size
2. **Ask for confirmation**: "Ready to commit and push these changes? Reply 'yes' or 'proceed' to continue, or 'abort' to cancel."
3. **Wait for explicit "yes" or "proceed"**: Do not commit/push without confirmation

**Before Dry-Run Execution** (if user chooses dry-run):
1. **Display Playbook Preview**: Show tasks and explain changes
2. **Ask for Dry-Run Confirmation**:
   ```
   ❓ Run dry-run to simulate changes?
   
   Options:
   - "yes" - Run dry-run (recommended)
   - "no" - Skip to actual execution
   - "abort" - Cancel

   Please respond with your choice.
   ```
3. **Wait for Explicit Response**: Do not proceed without confirmation

**Before Actual Execution** (REQUIRED):
1. **Display Execution Summary**: Show systems, changes, downtime estimate
2. **Ask for Final Confirmation**:
   ```
   ⚠️ CRITICAL: Execute playbook on production systems?
   
   This will make real changes to N systems.
   
   Options:
   - "yes" or "execute" - Proceed
   - "abort" - Cancel
   
   Please respond with your choice.
   ```
3. **Wait for Explicit "yes" or "execute"**: Do not proceed without confirmation

**Never assume approval** - always wait for explicit user confirmation before executing playbooks.

## Best Practices

1. **Write path must be absolute** - When Git Flow writes the playbook to the user's repo, use `<user_path>/playbooks/remediation/<filename>`. The path MUST start with `/`. Relative paths cause "Error writing file".
2. **Always validate AAP prerequisites** - Invoke mcp-aap-validator in Phase 0
3. **Validate each template** - Invoke job-template-remediation-validator for each candidate before selection
4. **Never skip Git Flow** - If template playbook path ≠ generated playbook path (Scenario 2) or content must be updated (Scenario 1), you MUST complete Git Flow and receive "sync complete" before Phase 3. Do NOT launch without it.
5. **Recommend dry-run** - Offer check mode before production execution
6. **Filter compatible templates** - Check inventory, project, and credentials match
7. **Monitor in real-time** - Display task progress during execution
8. **Full reporting** - Include per-host stats, task timeline, full output
9. **Error categorization** - Parse errors and provide specific troubleshooting
10. **Relaunch capability** - Offer to retry failed hosts
11. **Link to AAP** - Provide direct URL to job in AAP Web UI
12. **Suggest verification** - Always recommend remediation-verifier after success
13. **Document job details** - Save job ID and template info for audit trail

## Integration with Other Skills

- **playbook-generator**: Generates playbooks that this skill executes
- **job-template-creator**: Creates AAP job templates when needed
- **remediation-verifier**: Verifies success after this skill completes execution
- **`/remediation` skill**: Orchestrates full workflow including playbook execution

**Orchestration Example** (from `/remediation` skill):
1. Agent invokes playbook-generator skill → Creates playbook YAML
2. playbook-generator asks for confirmation → User approves playbook content
3. Agent invokes playbook-executor skill (this skill) → Execution workflow
4. Skill validates templates via job-template-remediation-validator → Filters valid candidates
5. Skill checks path match → If different path, offers Git Flow (HITL: commit/push, sync AAP)
6. Skill waits for "sync complete" before proceeding (if Git Flow was used)
7. Skill offers dry-run → User runs check mode
8. Skill asks for execution confirmation → User approves
9. Skill executes and monitors → Reports completion
10. Agent invokes remediation-verifier skill → Confirms CVE resolved

**Note**: Both playbook-generator and playbook-executor require separate confirmations for different purposes:
- playbook-generator: Confirms playbook content is acceptable
- playbook-executor: Confirms execution on production systems is approved

This two-step approval ensures user control over both what to run and when to run it.
