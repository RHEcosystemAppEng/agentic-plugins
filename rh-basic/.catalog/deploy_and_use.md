<!--
  Catalog fragment — maintain via create-collection workflow (assistant + maintainer + PR review).
  Golden sources: skills/*/SKILL.md, README.md, AGENTS.md
-->

## Deploy and use
**Note:** This agent plugin is released as Developer Preview. Developer Preview features provide early access to functionality in advance of possible inclusion in a Red Hat product offering. For more information about the support scope of Red Hat Developer Preview features, see [Developer Preview Support Scope](https://access.redhat.com/support/offerings/devpreview).

### Prerequisites

- At least one supported AI coding assistant:
  - [Claude Code](https://claude.com/product/claude-code) (CLI or IDE extension)
  - [GitHub Copilot](https://github.com/features/copilot) (CLI or VS Code)
  - [Cursor](https://www.cursor.com/)
  - [OpenCode](https://opencode.ai/)
- [Lola](https://github.com/LobsterTrap/lola) CLI installed

### Step 1: Install the agent plugin

```bash
# Add the Red Hat Agentic marketplace (one-time setup)
lola market add rh-agentic-plugins https://raw.githubusercontent.com/RHEcosystemAppEng/agentic-catalog/main/marketplace/rh-agentic-collection.yml

# Install the rh-basic plugin (replace claude-code with your AI assistant)
# Valid targets: claude-code, copilot-cli, copilot-vscode, cursor, opencode
lola install rh-basic -a claude-code
```

This installs the skills, the instructions file, and the MCP server definitions into your project.

Verify the installation:

```bash
lola list
```

### Step 2: Set up the MCP server

This plugin uses the Red Hat Security MCP server, which authenticates via browser SSO — no environment variables are required.

After installation, run the setup skill to configure the server:

```
/red-hat-security-mcp-setup
```

This adds the Red Hat Security MCP server to your project's `.mcp.json` and guides you through browser SSO authentication.

### Step 3: Use the skills

The plugin provides 6 skills. See the [rh-basic README](../README.md) for the full list with descriptions and usage examples.

### Uninstall

Remove the agent plugin from your project:

```bash
lola uninstall rh-basic
```

To also remove the marketplace registry:

```bash
lola market rm rh-agentic-plugins
```
