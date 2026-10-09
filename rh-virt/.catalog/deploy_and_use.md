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
- [Podman](https://podman.io/) (or Docker) — the MCP server runs as a container
- OpenShift cluster (**>= 4.19**) with the **OpenShift Virtualization** operator installed
- A kubeconfig with RBAC sufficient for VirtualMachine and related KubeVirt resources in target namespaces

### Step 1: Install the agent plugin

```bash
# Add the Red Hat Agentic marketplace (one-time setup)
lola market add rh-agentic-plugins https://raw.githubusercontent.com/RHEcosystemAppEng/agentic-catalog/main/marketplace/rh-agentic-collection.yml

# Install the rh-virt plugin (replace claude-code with your AI assistant)
# Valid targets: claude-code, copilot-cli, copilot-vscode, cursor, opencode
lola install rh-virt -a claude-code
```

This installs the skills, the instructions file, and the MCP server definitions into your project.

Verify the installation:

```bash
lola list
```

### Step 2: Configure environment variables

The plugin uses an MCP server that requires a kubeconfig passed as an environment variable. **Never hardcode kubeconfig contents — always use environment variables.**

**For cluster operations** (`openshift-virtualization`):

```bash
export KUBECONFIG="/path/to/your/kubeconfig"
```

Verify the API sees KubeVirt / VM objects (optional smoke check):

```bash
oc get virtualmachines -A
```

### Step 3: Use the skills

The plugin provides 10 skills. See the [rh-virt README](../README.md) for the full list with descriptions and usage examples.

### Uninstall

Remove the agent plugin from your project:

```bash
lola uninstall rh-virt
```

To also remove the marketplace registry:

```bash
lola market rm rh-agentic-plugins
```
