# Agentic skill pack for Red Hat customers

Essential Red Hat skills for IT professionals working with Red Hat products. This pack covers everyday tasks: understanding CVEs, gathering diagnostics, checking product lifecycle status, and filing support cases at the right severity.

**Persona**: IT Professional / Red Hat Customer
**Marketplaces**: Claude Code, Cursor

## Overview

Agentic skill pack for Red Hat customers provides lightweight, self-contained skills that work with or without a configured MCP server. Each skill falls back to web sources when MCP tools are unavailable.

- **6 skills** covering the most common Red Hat support and operations workflows
- **1 MCP server integration** (Red Hat Security MCP) for live CVE and advisory data
- **Self-installing** via the `red-hat-get-started` skill

## Quick Start

### Prerequisites

- Claude Code CLI or IDE extension
- A Red Hat account ([console.redhat.com](https://console.redhat.com)) for MCP authentication (optional)

### Installation (Lola)

```bash
lola market add rh-agentic-collections https://raw.githubusercontent.com/RHEcosystemAppEng/agentic-collections/main/marketplace/rh-agentic-collection.yml
lola install -f rh-basic
```

### MCP Setup (optional but recommended)

Skills work without MCP configured, falling back to public Red Hat documentation. To enable live CVE and advisory data, run `/red-hat-security-mcp-setup` after installation — it uses Red Hat Customer Portal browser SSO and requires no API credentials.

## Skills

### 1. **red-hat-cve-explainer** - CVE Explanation and Severity

Explains a CVE using Red Hat's severity rating system and recommends a course of action.

**Use when:**
- "What is CVE-2024-1234?"
- "How severe is this CVE?"
- "Should I patch CVE-X immediately?"

**What it does:**
- Looks up CVE metadata via the Red Hat Security MCP or Red Hat CVE pages
- Maps to Red Hat severity (Critical/Important/Moderate/Low)
- Links to applicable security advisories (RHSA/RHBA/RHEA)
- Gives a concrete action recommendation per severity

### 2. **red-hat-diagnostics** - Diagnostic Data Gathering

Provides the correct commands and upload instructions for gathering diagnostics across Red Hat products.

**Use when:**
- "How do I collect a sos report?"
- "What must-gather do I run for OpenShift?"
- "How do I gather AAP logs for a support case?"

**What it does:**
- Identifies product and deployment type (RPM, containerized, OCP operator)
- Provides exact commands for RHEL, OpenShift, AAP, and Satellite
- Explains how to upload archives to Red Hat Support

### 3. **red-hat-product-lifecycle** - Lifecycle Status

Reports the current lifecycle phase and support dates for any Red Hat product or version.

**Use when:**
- "Is RHEL 8.6 still supported?"
- "When does OpenShift 4.14 reach end of maintenance?"
- "What App Streams are available for RHEL 9?"

**What it does:**
- Retrieves lifecycle dates via the Red Hat Security MCP or Red Hat lifecycle pages
- Explains what updates each phase receives (security, bug, features)
- Gives a concrete action recommendation (upgrade, EUS, patch normally)
- Explains Red Hat's backporting model

### 4. **red-hat-support-severity** - Support Ticket Severity

Determines the correct severity for a Red Hat support ticket and explains the SLA.

**Use when:**
- "What severity should I file this case as?"
- "Is this a Sev 1 or Sev 2?"
- "What's the SLA for my support tier?"

**What it does:**
- Maps your situation (outage, impairment, workaround) to Sev 1-4
- Shows SLA response times for Premium and Standard support
- Lists what to include in the ticket for fastest resolution
- Adjusts recommendation when a CVE is involved

### 5. **red-hat-get-started** - Bootstrap Installer

Fetches and installs all skills from Agentic skill pack for Red Hat customers into the current project. Removes itself after running.

**Use when:**
- Setting up Red Hat skills for the first time in a project

### 6. **red-hat-security-mcp-setup** - Red Hat Security MCP Configuration

Adds the Red Hat Security MCP server to the current project's `.mcp.json` using HTTP transport and browser SSO.

**Use when:**
- "Set up the Red Hat Security MCP server"
- "Add red-hat-security to my MCP config"

**What it does:**
- Locates or creates `.mcp.json` in the project root
- Merges the `red-hat-security` HTTP transport entry without removing existing servers
- Explains the Red Hat Customer Portal SSO browser login flow
- Advises the user to restart Claude Code for the new server to take effect

## Skills Decision Guide

| User Request | Skill | Reason |
|---|---|---|
| "Explain this CVE" | **red-hat-cve-explainer** | CVE lookup and severity |
| "How do I collect diagnostics?" | **red-hat-diagnostics** | Support case preparation |
| "Is RHEL 8 still supported?" | **red-hat-product-lifecycle** | Lifecycle date lookup |
| "What severity is my support case?" | **red-hat-support-severity** | SLA guidance |
| "Install Red Hat skills" | **red-hat-get-started** | First-time setup |
| "Set up the Red Hat Security MCP server" | **red-hat-security-mcp-setup** | MCP server configuration |

## MCP Server Integration

### **red-hat-security** - Red Hat Security MCP

Provides CVE, advisory, and errata data from the Red Hat Security API.

- CVE metadata and severity — used by `red-hat-cve-explainer` and `red-hat-support-severity`
- Advisory details (RHSA/RHBA/RHEA)
- **Transport:** HTTP (`https://security-mcp.api.redhat.com/mcp`)
- **Authentication:** Red Hat Customer Portal SSO (browser login, no env vars required)

**Skills fall back to `WebFetch` on Red Hat documentation if MCP is unavailable** — you do not need MCP configured to use this pack.

## Security Model

- **No hardcoded credentials** — the Red Hat Security MCP uses browser-based SSO
- **No credential echo** — skills never print authentication tokens or session data

## Architecture

```
rh-basic/
├── README.md
├── AGENTS.md
├── mcps.json
└── skills/
    ├── red-hat-cve-explainer/SKILL.md
    ├── red-hat-diagnostics/SKILL.md
    ├── red-hat-get-started/SKILL.md
    ├── red-hat-product-lifecycle/SKILL.md
    ├── red-hat-security-mcp-setup/SKILL.md
    └── red-hat-support-severity/SKILL.md
```

## References

- [Red Hat Customer Portal](https://access.redhat.com/)
- [Red Hat Product Lifecycle](https://access.redhat.com/product-life-cycles/)
- [Red Hat CVE Database](https://access.redhat.com/security/security-updates/#/cve)
- [Lola Package Manager](https://github.com/LobsterTrap/lola)
- [Main Repository](https://github.com/RHEcosystemAppEng/agentic-collections)
