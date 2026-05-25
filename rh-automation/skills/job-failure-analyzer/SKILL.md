---
name: job-failure-analyzer
description: |
  Extract and analyze failure events from AAP jobs to classify errors and reconstruct failure timelines.

  Use when:
  - "Job #X failed", "Why did the execution fail?"
  - "Analyze the failed job", "What went wrong?"
  - "Show me the failure details"

  NOT for: host fact correlation (use host-fact-inspector) or resolution recommendations (use resolution-advisor).
model: inherit
color: yellow
license: Apache-2.0
allowed-tools: jobs_retrieve jobs_job_events_list jobs_job_host_summaries_list jobs_stdout_retrieve
---

# Job Failure Analyzer

## Prerequisites

**Required MCP Servers**:
- `aap-mcp-job-management` - Job details, events, host summaries, stdout

**Verification**: Run the `aap-mcp-validator` skill with `aap-mcp-job-management` before proceeding.

## When to Use This Skill

Use this skill when:
- User reports a failed job and wants analysis
- As the first step in the forensic-troubleshooter workflow
- User asks to understand what went wrong with a job

Do NOT use when:
- User wants to execute a job (use `execution-risk-analyzer` + `governed-job-launcher`)
- User wants host fact correlation (use `host-fact-inspector` after this skill)
- User wants resolution recommendations (use `resolution-advisor` after this skill)

## Workflow

### Step 1: Consult Troubleshooting Documentation

**CRITICAL**: Document consultation MUST happen BEFORE any MCP tool invocations.

**Document Consultation** (REQUIRED - Execute FIRST):
1. **Action**: Read [job-troubleshooting.md](../../docs/aap/job-troubleshooting.md) using the Read tool to understand event extraction, failure patterns, host summary interpretation, and root cause classification
2. **Output to user**: "I consulted [job-troubleshooting.md](docs/aap/job-troubleshooting.md) which references Red Hat's AAP 2.6 Troubleshooting Guide for failure analysis patterns."

### Step 2: Retrieve Job Status

**MCP Tool**: `jobs_retrieve` (from aap-mcp-job-management)
**Parameters**:
- `id`: `"<job_id>"`

Extract: `status`, `failed`, `job_type`, `elapsed`, `launch_type`.

Per job-troubleshooting.md, the status determines the analysis path:
- `failed` → Analyze events for `runner_on_failed`
- `error` → Platform-level failure (check capacity, EE, credentials)
- `canceled` → Check timeout or manual cancellation

### Step 3: Extract Failure Events

**MCP Tool**: `jobs_job_events_list` (from aap-mcp-job-management)
**Parameters**:
- `id`: `"<job_id>"`
- `page_size`: `100`

Filter for failure-related events:
- `runner_on_failed` -- task failures (PRIMARY)
- `runner_on_unreachable` -- host connectivity failures (PRIMARY)
- `playbook_on_stats` -- final summary

From each failure event, extract:
- `host`: which host failed
- `task`: which task failed
- `event_data.res.msg`: error message
- `event_data.task_action`: Ansible module
- `counter`: sequence number for timeline

### Step 4: Retrieve Host Summaries

**MCP Tool**: `jobs_job_host_summaries_list` (from aap-mcp-job-management)
**Parameters**:
- `id`: `"<job_id>"`

Map each host's `ok`, `changed`, `failures`, `dark`, `skipped` counts.

### Step 5: Classify the Failure

Apply the classification from job-troubleshooting.md:

| dark > 0 | failures > 0 | Classification |
|---|---|---|
| Yes | No | **Platform issue**: Host connectivity |
| No | Yes | **Code/Config issue**: Task failure |
| Yes | Yes | **Mixed**: Both connectivity and task issues |

For each `runner_on_failed` event, match against the failure patterns in job-troubleshooting.md:
- Pattern 1: Host Unreachable
- Pattern 2: Module Failure (Package Operations)
- Pattern 3: Privilege Escalation Timeout
- Pattern 4: Service Start Failure
- Pattern 5: Template Rendering Error
- Pattern 6: Execution Environment Issue

### Step 6: Reconstruct Failure Timeline

Sort events by `counter` and produce a chronological failure narrative:

1. First failure event (root cause candidate)
2. Subsequent failures (cascade effects)
3. Final stats (scope of impact)

### Step 7: Generate Failure Analysis Report

**Output format** (per job-troubleshooting.md template):

```
## Job Failure Analysis: Job #[job_id]

**Job Status**: [status]
**Elapsed Time**: [elapsed]s
**Launch Type**: [launch_type]

### Failure Timeline

1. [counter] - Task "[task_name]" on host "[hostname]": [event_type]
   Error: "[error_message]"
   Module: [module_name]
2. [subsequent failure events]

### Host Summary

| Host | OK | Changed | Failed | Unreachable |
|---|---|---|---|---|
| [host1] | [ok] | [changed] | [failures] | [dark] |

### Preliminary Classification

**Type**: [Platform / Code / Configuration] Issue
**Pattern Match**: [Pattern name from failure patterns reference]
**Evidence**: Per Red Hat's Troubleshooting Guide: "[relevant guidance from job-troubleshooting.md]"
**Root Cause Candidate**: [first failure event analysis]

### Next Steps

- Host fact correlation recommended: [yes/no, with affected hostnames]
- Resolution advisory recommended: [yes/no, with error pattern]
```

## Dependencies

### Required MCP Servers
- `aap-mcp-job-management` - Job data and events

### Required MCP Tools
- `jobs_retrieve` (from job-management) - Job status
- `jobs_job_events_list` (from job-management) - Event stream
- `jobs_job_host_summaries_list` (from job-management) - Per-host summary
- `jobs_stdout_retrieve` (from job-management) - Full stdout (supplementary)

### Related Skills
- `aap-mcp-validator` - Prerequisite validation
- `host-fact-inspector` - Next step: correlate with host facts
- `resolution-advisor` - Next step: get resolution recommendations
- `execution-summary` - Audit trail

### Reference Documentation
- [job-troubleshooting.md](../../docs/aap/job-troubleshooting.md) - Event parsing and failure patterns

## Example Usage

**User**: "Job #4451 failed halfway through. Analyze the logs."

**Agent**:
1. Reads job-troubleshooting.md
2. Reports: "I consulted job-troubleshooting.md which references Red Hat's AAP 2.6 Troubleshooting Guide."
3. Retrieves job #4451 → status: `failed`
4. Extracts events → finds `runner_on_failed` on task "Install security package" with `ansible.builtin.dnf`, msg: "No package matching 'nonexistent-package'"
5. Retrieves host summaries → 1 host with failures=1
6. Classifies: Code Error (Pattern 2: Module Failure - Package Operations)
7. Reports structured analysis with timeline, classification, and next steps
