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
- [Podman](https://podman.io/) (or Docker) — the MCP servers run as containers
- A Red Hat account with access to [cloud.redhat.com](https://cloud.redhat.com)
- For security skills (`/container-cve-validator`, `/coreos-cve-validator`, `/image-inspect`):
  - [Python requests](https://pypi.org/project/requests/) (`pip install requests`)
  - [regctl](https://github.com/regclient/regclient)
  - [cosign](https://github.com/sigstore/cosign)
  - [syft](https://github.com/anchore/syft) (optional, fallback SBOM generation)

### Step 1: Install the agent plugin

```bash
# Add the Red Hat Agentic marketplace (one-time setup)
lola market add rh-agentic-plugins https://raw.githubusercontent.com/RHEcosystemAppEng/agentic-catalog/main/marketplace/rh-agentic-collection.yml

# Install the ocp-admin plugin (replace claude-code with your AI assistant)
# Valid targets: claude-code, copilot-cli, copilot-vscode, cursor, opencode
lola install ocp-admin -a claude-code
```

This installs the skills, the instructions file, and the MCP server definitions into your project.

Verify the installation:

```bash
lola list
```

### Step 2: Configure environment variables

The plugin uses three MCP servers, each requiring specific credentials passed as environment variables. **Never hardcode tokens or paths — always use environment variables.**

**For cluster creation and inventory** (`openshift-self-managed`, `openshift-ocm-managed`):

1. Go to [https://cloud.redhat.com/openshift/token](https://cloud.redhat.com/openshift/token)
2. Click **Load token** → **Copy to clipboard**
3. Export it:

```bash
export OFFLINE_TOKEN="<your-token>"
```

**For cluster operations and reporting** (`openshift-administration`):

```bash
export KUBECONFIG="/path/to/your/kubeconfig"
```

### Step 3: Use the skills

The plugin provides 8 skills. See the [ocp-admin README](../README.md) for the full list with descriptions and usage examples.

### Uninstall

Remove the agent plugin from your project:

```bash
lola uninstall ocp-admin
```

To also remove the marketplace registry:

```bash
lola market rm rh-agentic-plugins
```
