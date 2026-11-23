# Detailed Execution Workflow

This reference contains the job selection, Git Flow, dry-run, execution, reporting, and error-handling steps used by the playbook executor.

### Phase 1: Job Template Selection and Playbook Preparation

**Goal**: Identify an AAP job template suitable for executing the remediation playbook. **Git Flow is MANDATORY** before Phase 3 when the template points to a different playbook or when content must be updated.

**Input**: Playbook content and metadata from playbook-generator (filename, CVE ID, target systems). The playbook YAML is already in context—do NOT regenerate it during Git Flow. Derive the playbook path from its generated filename using the `playbooks/remediation/` directory convention.

**BLOCKING**: You MUST NOT launch any job (dry-run or production) until the playbook is in the Git repo and the user has confirmed "sync complete". AAP executes from the synced project—there is no "override at launch". Launching without Git Flow executes the WRONG playbook.

#### Step 1.1: Derive Playbook Path

From playbook metadata (filename from playbook-generator):
- Use convention `playbooks/remediation/<filename>`
- Support both `remediation-CVE-*.yml` and `remediation-CVE-*-playbook.yml` patterns.
- Use the generated filename and the `playbooks/remediation/` directory convention.

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
- **compatible_other**: Passes job-template-remediation-validator but **different playbook path** (template points to a different playbook than the generated playbook)

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
- Scenario 1: `our_playbook_path`
- Scenario 2: `template.playbook`—replace the template's playbook with the generated content

**Prerequisite**: Ask user for the local path to the Git repository. Use `projects_list` for project name and `scm_url`. **Read [references/05-git-flow-prompts.md](references/05-git-flow-prompts.md)** for repo path question, HITL checkpoint text, and after-push message.

**Steps** (execute in order; HITL at checkpoint):
1. **Write playbook to file** (FAST—do NOT regenerate):
   - The playbook content is ALREADY in context from playbook-generator (or remediation skill). Use it directly.
   - **⚠️ ABSOLUTE PATH REQUIRED**: The Write path MUST start with `/`. Use `<user_provided_path>/<target_path>`.
   - **WRONG** (causes "Error writing file"): `test-aap-project/playbooks/...` or `playbooks/remediation/...` — these are relative and fail when repo is outside workspace.
   - **Before Write**: Confirm path starts with `/`. If not, prepend the user's repo path.
   - Do NOT invoke playbook-generator, do NOT call MCP tools, do NOT re-fetch. This should take seconds, not minutes.
2. Use the Run tool to stage `<target_path>` from the repository root.
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
