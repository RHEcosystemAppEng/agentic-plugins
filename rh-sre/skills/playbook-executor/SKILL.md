---
name: playbook-executor
description: |
  **CRITICAL**: Use for Ansible playbook execution via AAP. DO NOT call AAP MCP tools directly.

  Execute remediation playbooks with job management, dry-run, and reporting. Use after playbook-generator.

  Use when:
  - "Execute the remediation playbook"
  - "Launch the playbook on AAP"
  - "Run the CVE remediation job"
  - "Dry-run the playbook first"

  **Git Flow**: If template playbook path ≠ generated playbook, perform Git Flow (commit, push, sync) BEFORE launch.
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

**Validation freshness**: Can skip if already validated in this session. See [Validation Freshness Policy](../mcp-aap-validator/SKILL.md#validation-freshness-policy).

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

### Phase 1: Job Template Selection and Playbook Preparation

**Goal**: Identify an AAP job template suitable for executing the remediation playbook. **Git Flow is MANDATORY** before Phase 3 when the template points to a different playbook or when content must be updated.

**Input**: Playbook content and metadata from playbook-generator (filename, CVE ID, target systems). The playbook YAML is already in context—do NOT regenerate it during Git Flow. Playbook path is derived from metadata: `playbooks/remediation/<filename>` (e.g., `playbooks/remediation/remediation-CVE-2025-49794.yml`).

**BLOCKING**: You MUST NOT launch any job (dry-run or production) until the playbook is in the Git repo and the user has confirmed "sync complete". AAP executes from the synced project—there is no "override at launch". Launching without Git Flow executes the WRONG playbook.

#### Step 1.1: Derive Playbook Path

From playbook metadata (filename from playbook-generator):
- Use convention `playbooks/remediation/<filename>`
- Support both `remediation-CVE-*.yml` and `remediation-CVE-*-playbook.yml` patterns.
- Example: CVE-2026-26103 → `playbooks/remediation/remediation-CVE-2026-26103.yml`

#### Step 1.2: List Templates and Validate Each Candidate

**MCP Tool**: `job_templates_list` (from aap-mcp-job-management)

**Parameters**:
- `page_size`: 50 (retrieve up to 50 templates)
- `search`: "" (search for all templates)

**REQUIRED**: For each template in results:
1. Call `job_templates_retrieve(id)` to get full details
2. **Invoke the `/job-template-remediation-validator` skill** with the template ID to verify it meets remediation requirements (inventory, project, playbook, credentials, become_enabled)
3. Only include templates that PASS validation in the lists below

Build two lists:
- **exact_match**: `template.playbook` equals `our_playbook_path` (normalize slashes; match if equal or basenames match)
- **compatible_other**: Passes job-template-remediation-validator but **different playbook path** (template points to e.g. `cve-remediation.yml` while we have `remediation-CVE-2026-26103.yml`)

**Path normalization**: Normalize slashes, handle `playbooks/remediation/` prefix. Match if `template.playbook` equals `our_playbook_path` or if basenames match. **Different filenames = different path = Scenario 2.**

#### Step 1.3: Scenario Selection (MANDATORY - Do Not Skip)

**Scenario 1 - Same playbook path** (exact_match not empty):

The template already points to our playbook path. The project may need the latest content. **Read [references/05-git-flow-prompts.md](references/05-git-flow-prompts.md)** for Scenario 1 prompt, options (A/B), and Git Flow steps.

- **If A**: Execute Git Flow (see Git Flow section below). **BLOCK Phase 3** until user confirms "sync complete" or "done".
- **If B**: Wait for user confirmation. **BLOCK Phase 3** until user confirms.

**Scenario 2 - Different playbook path** (compatible_other not empty, exact_match empty):

**CRITICAL**: The template points to a DIFFERENT playbook than our generated playbook. You MUST NOT launch the job without Git Flow—AAP executes from synced content; there is no override at launch. **Read [references/05-git-flow-prompts.md](references/05-git-flow-prompts.md)** for Scenario 2 prompt and Git Flow steps.

- **If yes**: Execute Git Flow. **BLOCK Phase 3** until Git Flow completes and user confirms "sync complete".
- **If no**: Fall through to Scenario 3.

**Anti-pattern**: Do NOT say "I'll override with our playbook" and then launch—that is impossible. The playbook MUST be in the repo before launch.

**Scenario 3 - No suitable template** (exact_match and compatible_other both empty, or user chose "no" in Scenario 2):

Execute the `/job-template-creator` skill with instruction:
```
"Create a job template for this remediation playbook. Playbook: [content]. Filename: [filename]. Path: [our_playbook_path]. CVE: [cve_id]. Target systems: [list]."
```

The job-template-creator skill guides the user through: (1) Adding playbook to Git repository, (2) Syncing AAP project, (3) Creating job template via AAP Web UI with correct path, inventory, credentials, privilege escalation.

After `/job-template-creator` completes, retrieve the template ID (from skill output or user confirmation). Execute `/job-template-remediation-validator` to validate the newly created template. If passed, proceed to Phase 3 (Dry-Run). If failed, report issues and ask user to fix in AAP Web UI.

**Multiple matches**: If multiple exact matches, present list and ask user to choose by number. If multiple different-path matches, prefer by project name containing "remediation" or "CVE", else first.

**Phase 1 Checkpoint** (BLOCKING - must pass before Phase 3):
- **Git Flow required**: If Scenario 1 or 2, you MUST complete Git Flow and receive "sync complete" from the user before proceeding. Do NOT skip.
- **No override**: There is no way to "override" the playbook at launch. AAP runs whatever is in the synced project.
- **Never launch** if the playbook has not been committed, pushed, and synced

#### Git Flow (for Scenario 1 Override and Scenario 2) - MANDATORY HITL

**When**: Scenario 1 (same path, update content) or Scenario 2 (different path, replace playbook). **Do not skip**—execution with wrong playbook content will remediate the wrong CVE.

**Target path**:
- Scenario 1: `our_playbook_path` (e.g. `playbooks/remediation/remediation-CVE-2026-26103.yml`)
- Scenario 2: `template.playbook` (e.g. `playbooks/remediation/cve-remediation.yml`)—we replace the template's playbook with our generated content

**Prerequisite**: Ask user for the local path to the Git repository. Use `projects_list` for project name and `scm_url`. **Read [references/05-git-flow-prompts.md](references/05-git-flow-prompts.md)** for repo path question, HITL checkpoint text, and after-push message.

**Steps** (execute in order; HITL at checkpoint):
1. **Write playbook to file** (FAST—do NOT regenerate):
   - The playbook content is ALREADY in context from playbook-generator (or remediation skill). Use it directly.
   - **⚠️ ABSOLUTE PATH REQUIRED**: The Write path MUST start with `/`. Use: `<user_provided_path>/<target_path>`. Example: `/Users/dmartino/projects/AI/ai5/ai5-demo/test-aap-project/playbooks/remediation/cve-remediation.yml`
   - **WRONG** (causes "Error writing file"): `test-aap-project/playbooks/...` or `playbooks/remediation/...` — these are relative and fail when repo is outside workspace.
   - **Before Write**: Confirm path starts with `/`. If not, prepend the user's repo path.
   - Do NOT invoke playbook-generator, do NOT call MCP tools, do NOT re-fetch. This should take seconds, not minutes.
2. Use Run tool: `git add <target_path>` (from repo root, e.g. `git add playbooks/remediation/cve-remediation.yml`)
3. **HITL Checkpoint** (REQUIRED): Display summary per reference file. Wait for "yes" or "proceed"
4. If confirmed: `git commit -m "Add/update remediation playbook for CVE-YYYY-NNNNN"`
5. `git push origin main` (or branch from project's scm_branch if available)

**Note**: Git must be configured. Use Run tool for git commands.

**Do NOT proceed to Phase 3 (Dry-Run) until user confirms sync complete.**

### Phase 2: Git Flow (MANDATORY before Phase 3)

**BLOCKING**: Git Flow must be complete before Phase 3. See Phase 1 Step 1.3. Confirm: playbook written, commit/push done, user confirmed "sync complete". If not, STOP.

### Phase 3: Dry-Run Execution (Recommended)

**Prerequisite**: Phase 2 (Git Flow) MUST be complete. User must have confirmed "sync complete".

**Goal**: Test playbook in check mode before actual execution to simulate changes.

**Read [references/04-dry-run-display-templates.md](references/04-dry-run-display-templates.md)** for: Playbook Preview, Dry-Run Offer, Dry-Run Results Display, Proceed prompt.

#### Step 3.1–3.2: Display Preview and Offer Dry-Run

Show playbook structure per reference. Offer dry-run with options: yes / no / abort. **ONLY if user confirms**, proceed.

#### Step 3.3: Launch Dry-Run Job

**Pre-launch check** (BLOCKING): If Scenario 1 or 2 applied, you MUST have completed Git Flow and received "sync complete" from the user. If not, STOP—do not launch. Return to Phase 2 / Git Flow.

**MCP Tool**: `job_templates_launch_retrieve` (from aap-mcp-job-management)

**Parameters**: `id`, `requestBody` with `job_type: "check"`, `extra_vars`, `limit`

**Key**: `job_type: "check"` - Runs Ansible in check mode (dry-run)

#### Step 3.4: Monitor Dry-Run Progress

Poll `jobs_retrieve` every 2 seconds. Use `jobs_job_events_list` for live task updates.

#### Step 3.5: Display Dry-Run Results

**MCP Tools**: `jobs_stdout_retrieve` (id, format: "txt"), `jobs_job_host_summaries_list` (id). Use display format from reference.

#### Step 3.6: Proceed to Actual Execution?

Ask per reference. Wait for "yes" or "execute".

### Phase 4: Actual Execution

**ONLY execute if user explicitly confirms** (either after dry-run or directly if they skipped dry-run).

#### Step 4.1: Final Confirmation

```
⚠️ CRITICAL: Playbook Execution Confirmation Required

This playbook will:
- Execute on: 3 production systems
- Update packages: httpd (2.4.53-7.el9 → 2.4.57-8.el9)
- Restart services: httpd
- Estimated downtime: ~10 seconds per system
- Requires reboot: No

Job Template: CVE Remediation Template (ID: 10)
AAP URL: https://aap.example.com/jobs/

❓ Execute this playbook now?

Options:
- "yes" or "execute" - Proceed with execution
- "abort" - Cancel execution

Please respond with your choice.
```

Wait for explicit "yes" or "execute" response.

#### Step 4.2: Launch Production Job

**Pre-launch check** (BLOCKING): Same as Phase 3—if Scenario 1 or 2 applied, Git Flow must be complete and user must have confirmed "sync complete". Do NOT launch without it.

**MCP Tool**: `job_templates_launch_retrieve` (from aap-mcp-job-management)

**Parameters**:
```json
{
  "id": "10",
  "requestBody": {
    "job_type": "run",
    "extra_vars": {
      "target_cve": "CVE-2025-49794",
      "remediation_mode": "automated",
      "verify_after": true
    },
    "limit": "prod-web-01,prod-web-02,prod-web-03"
  }
}
```

**Key Parameter**: `job_type: "run"` - Runs Ansible in execution mode (actual changes)

**Expected Output**:
```json
{
  "job": 1235,
  "status": "pending",
  "url": "/api/controller/v2/jobs/1235/"
}
```

#### Step 4.3: Monitor Execution Progress

**Polling Strategy**:
1. Call `jobs_retrieve(id=job_id)` every 2 seconds
2. Get task events with `jobs_job_events_list(id=job_id)` for progress updates
3. Display real-time task completion status
4. Continue until status is "successful", "failed", or "error"

**Progress Display**:
```
⏳ Execution in progress...

Job ID: 1235
Status: running
Elapsed: 1m 23s
AAP URL: https://aap.example.com/#/jobs/playbook/1235

Recent Events:
- ✓ Gathering Facts (completed - all hosts)
- ✓ Check Disk Space (completed - all hosts)
- ✓ Backup Configuration (completed - all hosts)
- ⏳ Update Package: httpd (running - prod-web-01, prod-web-02)
  └─ prod-web-01: Installing httpd-2.4.57-8.el9...
  └─ prod-web-02: Installing httpd-2.4.57-8.el9...
- ⏸  Restart Service: httpd (pending)
```

**Update every 2 seconds** until completion.

### Phase 5: Execution Report

**Goal**: Generate report with job details, per-host results, and full output.

**Read [references/01-execution-report-templates.md](references/01-execution-report-templates.md)** for JSON examples, report template, and Success/Partial Success/Failure output templates.

#### Step 5.1–5.4: Gather Data

**MCP Tools** (all from aap-mcp-job-management):
- `jobs_retrieve` (id) - Job details
- `jobs_job_host_summaries_list` (id) - Per-host stats
- `jobs_job_events_list` (id) - Task timeline
- `jobs_stdout_retrieve` (id, format: "txt") - Full console output

#### Step 5.5: Generate Report

Format all gathered data per reference. Use Success / Partial Success / Failure template based on job status.

#### Step 5.6: Validate Job Log for CVE Handling (MANDATORY)

**Goal**: Confirm from the job stdout that the playbook actually addressed the target CVE(s).

**Input**: Target CVE ID(s) from invocation (e.g. CVE-2025-49794). Job stdout from `jobs_stdout_retrieve` (already gathered in Step 5.4).

**Parse stdout for**:
- Target CVE ID(s) in output (vars, task names, audit logs, playbook metadata)
- Package update tasks for affected packages (dnf/yum install/update, package module)
- Remediation-related task names (e.g. "Update package", "Restart service", "remediation")

**Report** (add to execution report):
- **✓ Job log confirms CVE-XXXX-YYYY was addressed** — CVE ID or package updates found in stdout
- **⚠️ Job log did not show clear evidence of CVE handling** — No CVE ID or package updates found; recommend manual verification or `/remediation-verifier`

**Batch**: For multiple CVEs, validate each. Report per-CVE confirmation or warning.

### Phase 6: Error Handling

**If job status is "failed" or "error"**, provide detailed troubleshooting.

**Read [references/02-error-handling-guide.md](references/02-error-handling-guide.md)** for: Error categories, error report template, troubleshooting steps, relaunch parameters.

#### Step 6.1: Parse Error Output

**MCP Tool**: `jobs_stdout_retrieve`. Analyze output for error categories per reference.

#### Step 6.2: Generate Error Report

Use error report template from reference. Include per-host results, failed task details, troubleshooting steps, relaunch options.

#### Step 6.3: Offer Relaunch

If user chooses relaunch: **MCP Tool** `jobs_relaunch_retrieve` with `hosts: "failed"`, `job_type: "run"` per reference.

## Reference Files

| File | Use When |
|------|----------|
| [01-execution-report-templates.md](references/01-execution-report-templates.md) | Phase 5 reports, Success/Partial/Failure output |
| [02-error-handling-guide.md](references/02-error-handling-guide.md) | Phase 6 error reports, relaunch |
| [03-workflow-examples.md](references/03-workflow-examples.md) | Demo full workflow, failure handling, skip dry-run |
| [04-dry-run-display-templates.md](references/04-dry-run-display-templates.md) | Phase 3 preview, offer, results, proceed prompt |
| [05-git-flow-prompts.md](references/05-git-flow-prompts.md) | Scenario 1/2 prompts, Git Flow HITL, after-push |

## Dependencies

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
- [AAP Job Execution Guide](../../docs/ansible/aap-job-execution.md) - AAP job execution best practices
- [Playbook Integration with AAP](../../docs/ansible/playbook-integration-aap.md) - Playbook-to-AAP workflow

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
