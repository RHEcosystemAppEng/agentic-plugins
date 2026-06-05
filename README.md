# Red Hat Agentic Collections

**Production-ready AI skills and automation for Red Hat platforms** — install specialized plugins for SREs, developers, platform administrators, and AI engineers working with RHEL, OpenShift, and Red Hat automation platforms.

## Installation (Lola package manager)

Install collections using [Lola](https://github.com/LobsterTrap/lola), the AI skills package manager. **Installation applies to the current folder only** — run commands from your project directory.

### One-time setup: add marketplace

```bash
lola market add rh-agentic-collections https://raw.githubusercontent.com/RHEcosystemAppEng/agentic-collections/main/marketplace/rh-agentic-collection.yml
```

### Install individual module

```bash
lola install -f rh-sre
```

### Install all modules at once

```bash
for m in ocp-admin rh-ai-engineer rh-automation rh-developer rh-sre rh-virt; do lola install -f $m; done
```

### Install to a specific assistant only

Use the `-a` option to target Claude Code or Cursor:

```bash
lola install -f rh-sre -a claude-code   # Claude Code only
lola install -f rh-sre -a cursor        # Cursor only
```

[![Validate Agentic Collections](https://github.com/RHEcosystemAppEng/agentic-collections/actions/workflows/compliance-check.yml/badge.svg)](https://github.com/RHEcosystemAppEng/agentic-collections/actions/workflows/compliance-check.yml)
[![Skill Specification Linter](https://github.com/RHEcosystemAppEng/agentic-collections/actions/workflows/skill-spec-report.yml/badge.svg)](https://github.com/RHEcosystemAppEng/agentic-collections/actions/workflows/skill-spec-report.yml)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Marketplace](https://img.shields.io/badge/Claude%20Code-Marketplace-purple)](https://github.com/RHEcosystemAppEng/agentic-collections)

---

## 🚀 Quick Start

### 1. Add the Marketplace

```bash
lola market add rh-agentic-collections https://raw.githubusercontent.com/RHEcosystemAppEng/agentic-collections/main/marketplace/rh-agentic-collection.yml
```

### 2. Install a Module

```bash
# For Site Reliability Engineers
lola install -f rh-sre

# For Developers
lola install -f rh-developer

# For OpenShift Administrators
lola install -f ocp-admin

# For Virtualization Administrators
lola install -f rh-virt

# For AI/ML Engineers
lola install -f rh-ai-engineer

# For Ansible Automation Platform Engineers
lola install -f rh-automation
```

See each module's README for available skills and usage examples.

### 3. Install All Modules

```bash
for m in ocp-admin rh-ai-engineer rh-automation rh-developer rh-sre rh-virt; do lola install -f $m; done
```

**Note:** Re-run `lola install -f <module>` anytime to pick up newer module content after marketplace updates.

---

## 📦 Available Plugins

6 persona-focused plugins with **62 production-ready skills**:

| Plugin | Version | Skills | Description | Personas |
|--------|---------|--------|-------------|----------|
| **[rh-sre](rh-sre/README.md)** | 1.0.0 | 13 | CVE remediation, system compliance, RHEL automation | Site Reliability Engineers |
| **[rh-developer](rh-developer/README.md)** | 1.0.0 | 14 | Application deployment, S2I builds, Helm charts | Application Developers |
| **[openshift-virtualization](rh-virt/README.md)** | 1.0.0 | 10 | VM lifecycle, snapshots, migrations, cloning | Virtualization Admins |
| **[ocp-admin](ocp-admin/README.md)** | 1.0.0 | 3 | Multi-cluster management, health reports, monitoring | OpenShift Administrators |
| **[rh-ai-engineer](rh-ai-engineer/README.md)** | 1.0.0 | 11 | Model serving, vLLM, KServe, NVIDIA NIM | AI/ML Engineers |
| **[rh-automation](rh-automation/README.md)** | 1.0.0 | 11 | Ansible Automation Platform governance, safety checks | Automation Leads |

**Total:** 62 skills across 6 plugins | **Standalone Agents:** 0 | **Orchestration:** Delivered through orchestration skills where applicable | **License:** Apache 2.0 | **Status:** Production Ready

---

## 📋 Prerequisites

### General Requirements

1. **Claude Code** (latest version recommended)
   - Desktop app ([claude.ai/code](https://claude.ai/code))
   - VS Code extension, JetBrains extension, or Web app
   - CLI tool

2. **Container Runtime** (Podman or Docker)
   - Required for MCP servers used by most plugins
   - Podman (recommended for Linux): `sudo dnf install podman`
   - Docker Desktop (macOS/Windows): [docker.com](https://docker.com)

3. **Network Access**
   - Internet connectivity for marketplace installation
   - Access to container registries (quay.io, registry.redhat.io)
   - Access to Red Hat platforms (depending on plugins used)

### Plugin-Specific Requirements

Each plugin has additional requirements:
- **Credentials**: Red Hat API keys, cluster kubeconfigs, service tokens
- **Platform Access**: OpenShift clusters, RHEL systems, Ansible Automation Platform
- **Permissions**: Cluster admin, namespace edit, or view roles

**See each plugin's README for detailed requirements and setup instructions.**

---

### Key Features

- **🎯 Role-Specific**: Each plugin is designed for specific personas and workflows
- **🔒 Security First**: Credential handling, human-in-the-loop for destructive operations
- **🔧 Production Ready**: 60+ skills validated against [design principles](SKILL_DESIGN_PRINCIPLES.md)
- **📚 Documentation**: AI-optimized docs with semantic indexing (rh-sre reference)
- **🔌 MCP Integration**: Red Hat Lightspeed, Ansible Automation Platform servers
- **✅ Quality Assured**: Automated compliance checks and specification linting

---

## Contributing

**New skill idea?** Run `/agentic-contribution-skill` in Claude Code.
**Have an existing skill?** Run `/agentic-contribution-skill` and choose import mode.
**Want to federate your own pack?** Follow the [Federation Request Guide](FEDERATION_REQUEST_GUIDE.md).
**Full guide:** [CONTRIBUTING.md](CONTRIBUTING.md)

---

## Documentation Site

View the interactive documentation at: **https://rhecosystemappeng.github.io/agentic-collections**

The site provides:
- **Agentic Collections**: Browse all available collections, skills, and agents with detailed descriptions
- **MCP Servers**: Explore MCP server configurations and integration details
- **Search**: Find collection, skills, agents, and servers by keyword across all content

### Prerequisites

The documentation tools use [uv](https://github.com/astral-sh/uv) for fast, isolated Python environment management:

```bash
# Install uv (one-time setup)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or on macOS with Homebrew
brew install uv
```

### Local Development

Generate and view documentation locally:

```bash
# Install dependencies (first time only)
make install

# Validate pack structure + collection compliance (COLLECTION_SPEC.md, catalog/schema.yaml)
make validate

# Optional: collection-only targets
# make validate-collection-schema
# make validate-collection-compliance
# make catalog-mirror-json   # refresh .catalog/collection.json from YAML

# Validate skills against Design Principles (SKILL_DESIGN_PRINCIPLES.md)
# Validate only changed skills (staged + unstaged) - recommended for local dev:
make validate-skill-design-changed
# Or validate all skills / a specific pack:
make validate-skill-design
make validate-skill-design PACK=rh-sre

# Generate docs/data.json
make generate

# Start local server at http://localhost:8000
make serve

# Or run full test suite with auto-open
make test-full
```

Updates are automatically deployed to GitHub Pages when changes are pushed to main.

For more details, see [docs/README.md](docs/README.md).

### Skill Design Validation

Use the `validate-skill-design` and `validate-skill-design-changed` targets to check skills against the [Design Principles](SKILL_DESIGN_PRINCIPLES.md) referenced from CLAUDE.md. **CI runs this validation automatically** on pull requests and pushes to main, but only for changed skills. For local development, run `validate-skill-design-changed` to validate only your modified skills (staged + unstaged). To perform full validation or validate a specific pack, run `validate-skill-design`. Ensure compliance with:

- Document consultation transparency (DP1)
- Parameter specification and ordering (DP2)
- Description conciseness (DP3)
- Dependencies declaration (DP4)
- Human-in-the-loop requirements for critical operations (DP5)
- Mandatory sections (Prerequisites, When to Use, Workflow) (DP6)
- Credential security (no `echo $VAR` exposure) (DP7)
- Required frontmatter policy (`model` required: `inherit|sonnet|haiku`; `color` required: `cyan|green|blue|yellow|red|magenta`)

```bash
# Validate only changed skills (staged + unstaged) - recommended for local dev
make validate-skill-design-changed

# Validate all packs
make validate-skill-design

# Validate a specific pack only
make validate-skill-design PACK=rh-sre

# Treat warnings as errors
uv run python scripts/validate_skill_design.py --warnings-as-errors

```


## Security

This repository uses [gitleaks](https://github.com/gitleaks/gitleaks) and the [pre-commit](https://pre-commit.com/) framework to block accidental secrets and to run scoped validation before commits.

### Quick Start

```bash
# One-time: Python deps + dev tools (includes pre-commit), then install the git hook
make install
scripts/install-hooks.sh
```

`scripts/install-hooks.sh` runs `uv sync` / `uv sync --group dev`, ensures `gitleaks` is available when possible, then `uv run pre-commit install`. It backs up a **non–pre-commit** `.git/hooks/pre-commit` (for example an old gitleaks-only hook) before replacing it.

On commit, hooks defined in `.pre-commit-config.yaml` run: **gitleaks**, **`make validate`** when catalog/roster-related paths change, and **`make validate-skill-design-changed`** when pack `skills/*/SKILL.md` files change. CI still enforces the full checks in [`.github/workflows/compliance-check.yml`](.github/workflows/compliance-check.yml) (`make validate` and related jobs).

### What's Protected

- **API keys**: OpenAI, GitHub, AWS, Google Cloud
- **Private keys**: SSH, SSL/TLS certificates
- **Hardcoded credentials** in `mcps.json` files
- **Database connection strings** with passwords
- **JWT tokens** and authentication secrets

### MCP Configuration Rules

✅ **CORRECT** - Use environment variable references:
```json
{
  "env": {
    "LIGHTSPEED_CLIENT_ID": "${LIGHTSPEED_CLIENT_ID}",
    "LIGHTSPEED_CLIENT_SECRET": "${LIGHTSPEED_CLIENT_SECRET}"
  }
}
```

❌ **BLOCKED** - Hardcoded values:
```json
{
  "env": {
    "LIGHTSPEED_CLIENT_SECRET": "sk-proj-abc123..."
  }
}
```

### Manual Scanning

```bash
# Scan entire repository history
gitleaks detect --source . --verbose

# Scan only staged changes
gitleaks protect --staged
```

See [SECURITY.md](SECURITY.md) for details.

## Validation Severity Guide

Use validation outputs to prioritize fixes:

- **blocking**: must be fixed before merge; CI fails.
- **high**: warning in initial rollout; prioritize in same PR when practical.
- **medium**: warning; schedule near-term cleanup.
- **informational**: track for hygiene improvements.

Recommended remediation workflow:

1. Run `make validate`.
2. Review the validator output and resolve reported issues.
3. Fix all blocking findings first, then high findings related to changed files.
4. Re-run `make validate` before opening or updating a PR.

## Adding a New MCP Server

To add a new MCP server to an agentic pack and display it on the documentation site:

### Step 1: Add MCP Configuration to Pack

Add the server configuration to `<pack>/mcps.json`:

```json
{
  "mcpServers": {
    "your-server-name": {
      "command": "podman|docker|npx",
      "args": ["run", "--rm", "-i", "..."],
      "env": {
        "VAR_NAME": "${VAR_NAME}"  // Always use env var references
      },
      "description": "Brief description of the MCP server",
      "security": {
        "isolation": "container",
        "network": "local",
        "credentials": "env-only|none"
      }
    }
  }
}
```

**Security Requirements:**
- ✅ Always use `${ENV_VAR}` references for credentials
- ❌ Never hardcode API keys, tokens, or secrets
- ✅ Set appropriate security isolation level

**Platform Notes (Linux vs macOS):**

On **Linux**, you may want to add `--userns=keep-id:uid=65532,gid=65532` to the Podman `args` for proper UID/GID mapping inside the container. This ensures the container process runs with the correct non-root user identity.

On **macOS**, this flag is **not supported** because Podman runs inside a Linux VM where user namespace mapping behaves differently. Omit it on macOS or the container will fail to start.

### Step 2: Add Custom Metadata (Optional)

To display repository links and tool descriptions on the documentation site, add an entry to `docs/mcp.json`:

```json
{
  "your-server-name": {
    "repository": "https://github.com/org/repo",
    "tools": [
      {
        "name": "tool_name",
        "description": "What this tool does and when to use it"
      }
    ]
  }
}
```

**Fields:**
- `repository`: GitHub repository URL (appears as README badge on server card)
- `tools`: Array of tool objects with name and description (displayed in server details modal)

### Step 3: Generate Documentation

Regenerate the documentation site data:

```bash
make generate
```

This will:
1. Parse the `mcps.json` file from your pack
2. Merge it with custom data from `docs/mcp.json`
3. Update `docs/data.json` with the new server

### Step 4: Verify Locally

Test the changes locally:

```bash
make serve
```

Visit http://localhost:8000 and verify:
- Server appears in MCP Servers section
- Server card shows correct information
- README badge appears (if repository URL provided)
- Tools count displays (if tools provided)
- Details modal shows all configuration

### Step 5: Commit and Deploy

```bash
git add <pack>/mcps.json docs/mcp.json docs/data.json
git commit -m "feat: add <server-name> MCP server to <pack>"
git push
```

The documentation site will automatically update via GitHub Actions.

### Example: Adding Red Hat Lightspeed MCP Server

**File: `rh-sre/mcps.json`**
```json
{
  "mcpServers": {
    "lightspeed-mcp": {
      "command": "podman",
      "args": ["run", "--rm", "-i",
               "--env", "LIGHTSPEED_CLIENT_ID",
               "--env", "LIGHTSPEED_CLIENT_SECRET",
               "quay.io/redhat-services-prod/insights-mcp:latest"],
      "env": {
        "LIGHTSPEED_CLIENT_ID": "${LIGHTSPEED_CLIENT_ID}",
        "LIGHTSPEED_CLIENT_SECRET": "${LIGHTSPEED_CLIENT_SECRET}"
      },
      "description": "Red Hat Lightspeed MCP server for CVE data and remediation",
      "security": {
        "isolation": "container",
        "network": "local",
        "credentials": "env-only"
      }
    }
  }
}
```

**File: `docs/mcp.json`**
```json
{
  "lightspeed-mcp": {
    "repository": "https://github.com/RedHatInsights/insights-mcp",
    "tools": [
      {
        "name": "vulnerability__get_cves",
        "description": "Get list of CVEs affecting the account"
      },
      {
        "name": "vulnerability__get_cve",
        "description": "Get details about specific CVE"
      }
    ]
  }
}
```

### Troubleshooting

**Server not appearing:**
- Run `make validate` to check for JSON syntax errors
- Verify `mcps.json` file is in the pack directory
- Check that pack directory is listed in `scripts/generate_pack_data.py` PACK_DIRS

**Tools not showing:**
- Ensure `docs/mcp.json` has entry for your server
- Verify tool objects have both `name` and `description` fields
- Regenerate with `make generate`

**Security errors:**
- Check for hardcoded credentials with `gitleaks protect --staged`
- Ensure all env values use `${VAR}` format
- Review security isolation settings

---

## 🧪 Local Testing

Test the marketplace locally before publishing:

### Add Local Marketplace

```bash
cd /path/to/agentic-collections
lola market add rh-agentic-collections ./marketplace/rh-agentic-collection.yml
```

### Install Module Locally

```bash
lola install -f rh-sre
```

### Validate packs (recommended)

```bash
# Structure, mcps.json, CLAUDE.md, skill frontmatter; validates plugin.json only when present
make validate
```

### Optional: Claude Code plugin CLI

If you use the Claude Code `/plugin` marketplace workflow against a local checkout:

```bash
claude plugin validate .
# Or from within Claude Code
/plugin validate .
```

That CLI checks marketplace/plugin manifests for that workflow, including `plugin.json` when present under `.claude-plugin/`.


## 📚 Additional Resources

- **[Documentation Site](https://rhecosystemappeng.github.io/agentic-collections)**: Browse all collections, skills, and MCP servers
- **[CLAUDE.md](CLAUDE.md)**: Repository structure and development workflow
- **[Skill Design Principles](SKILL_DESIGN_PRINCIPLES.md)**: Quality guidelines for skills
- **[Federation Request Guide](FEDERATION_REQUEST_GUIDE.md)**: How to federate your external pack into the marketplace
- **[Federation Review Guide](FEDERATION_REVIEW_GUIDE.md)**: How we evaluate external packs for federation
- **[VALIDATION_REPORT.md](VALIDATION_REPORT.md)**: Marketplace compliance verification
- **[Security Policy](SECURITY.md)**: Credential handling and vulnerability reporting

---

## 📄 License

Apache License 2.0 - see [LICENSE](LICENSE) for details.

---

**Maintained by:** [Red Hat Ecosystem Engineering](https://github.com/RHEcosystemAppEng)

**Questions?** Open an [issue](https://github.com/RHEcosystemAppEng/agentic-collections/issues) or check the [documentation site](https://rhecosystemappeng.github.io/agentic-collections).
