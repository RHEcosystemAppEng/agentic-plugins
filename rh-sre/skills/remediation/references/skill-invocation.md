---
title: Skill Invocation Reference
category: references
tags: [skills, invocation, troubleshooting]
last_updated: 2026-03-02
---

# Skill Invocation Reference

Guidance for correctly invoking skills in the rh-sre plugin across different AI hosts (Cursor, Claude Code, etc.).

## Invoking Skills (All Sub-Skills)

When the remediation skill (or other orchestrators) invokes any sub-skill—validators, cve-validation, cve-impact, system-context, playbook-generator, playbook-executor, remediation-verifier:

- **Use the Skill tool** with the skill name. Format may vary by host:
  - Cursor: `Skill(rh-sre:mcp-lightspeed-validator)` or similar
  - Claude Code: `/mcp-lightspeed-validator` or `Skill(mcp-lightspeed-validator)`
- **Wait for the skill to complete**—skills typically return output directly. Do NOT proceed to the next step until you have the skill's actual result (e.g. validation PASSED/FAILED). "Successfully loaded skill" indicates the skill was loaded, not that it finished—wait for the validation outcome before continuing.
- **Do NOT use "Task Output" with the skill name as the task ID.** If you see "No task found with ID: mcp-lightspeed-validator" (or cve-validation, cve-impact, etc.), you are passing the skill name to a Task Output tool. Task Output expects the task ID returned from an async invocation (e.g. a UUID), NOT the skill name. Skill names are not task IDs.

## If Validator Invocation Fails

If validator invocation returns "No task found" or similar:

1. **Do NOT block the workflow.** Proceed with a warning.
2. **Inform the user**: "Validator invocation encountered an issue. Proceeding with remediation workflow—MCP operations in later steps will confirm connectivity."
3. **Continue to Step 2** (cve-validation). The `get_cve` call will fail if Lightspeed MCP is unavailable.
4. **Continue to Step 5** (playbook-executor). AAP MCP calls will fail if AAP is unavailable.

The workflow is resilient: actual MCP tool calls in later steps serve as implicit validation. Do not retry Task Output with the skill name.

## Validation Freshness

If validation was performed earlier in the same session and succeeded, you may skip re-invoking validators. See each validator skill's "Validation Freshness Policy" section.
