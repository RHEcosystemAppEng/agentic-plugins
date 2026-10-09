---
name: red-hat-get-started
description: Bootstrap installer. Fetches and installs all Red Hat agent skills into this project.
license: Apache-2.0
user_invocable: true
model: inherit
color: yellow
allowed-tools:
---

# Red Hat Skills Installer

SKILLS_REPO = https://github.com/RHEcosystemAppEng/agentic-plugins/tree/main/rh-basic/skills

Install all Red Hat agent skills into the appropriate skills directory for the
current agentic tool. Work through skills in order. Do not stop on a single
fetch failure -- continue and report failures at the end.

## Prerequisites

Network access to GitHub to download skill files.

## When to Use This Skill

When setting up Agent plugin for Red Hat customers for the first time in a project.

## Workflow

1. Download each skill's SKILL.md from SKILLS_REPO into the appropriate skills directory.
2. Report any failures for manual recovery.
3. Deliver post-install summary and remove itself.

## Dependencies

None.

## Skills to Install

| Skill directory              | Invocation                      |
|------------------------------|---------------------------------|
| red-hat-cve-explainer        | /red-hat-cve-explainer          |
| red-hat-diagnostics          | /red-hat-diagnostics            |
| red-hat-product-lifecycle    | /red-hat-product-lifecycle      |
| red-hat-security-mcp-setup   | /red-hat-security-mcp-setup     |
| red-hat-support-severity     | /red-hat-support-severity       |

## Install Sequence

Browse SKILLS_REPO to find the raw SKILL.md URL for each skill directory.

For each skill:

1. Create the skill directory inside the appropriate skills directory for the current tool.
2. Download the raw file directly into that directory as `SKILL.md` using a
   native file fetch or download tool. Do not read the content and re-write it
   -- this risks truncation or reformatting.

On failure: print URL and target path, tell user to download manually, continue.

## Post-Install Summary

After all 5 skills are processed, tell the user:

```
Red Hat agent skills installed.

Available commands:
  /red-hat-cve-explainer      -- Explain a CVE and recommended action
  /red-hat-diagnostics        -- Gather diagnostic data for Red Hat support
  /red-hat-product-lifecycle  -- Check lifecycle status for any Red Hat product
  /red-hat-security-mcp-setup -- Add the Red Hat Security MCP server (CVE/advisory data)
  /red-hat-support-severity   -- Determine support ticket severity and SLA

[List any skills that failed to download and their manual URLs.]

Type /red-hat-security-mcp-setup to configure the Security MCP server.
```

## Self-Destruct

After delivering the summary, delete this skill's directory from the skills
directory of the current agentic tool.

Tell the user: "This installer has removed itself."
