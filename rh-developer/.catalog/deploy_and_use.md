<!--
  Catalog fragment — maintain via create-collection workflow (assistant + maintainer + PR review).
  Golden sources: skills/*/SKILL.md, README.md, AGENTS.md, marketplace/rh-agentic-collection.yml
-->

### Prerequisites

- OpenShift cluster access (`oc`, valid `KUBECONFIG`) for OpenShift flows
- Podman (local builds and MCP)
- Optional: `GITHUB_PERSONAL_ACCESS_TOKEN` for GitHub-backed project detection
- Optional: Red Hat Lightspeed credentials for `/rhel-deploy` and `/debug-rhel` advisor paths

### Environment setup

Variable **names** must match **`mcps.json`**. Do not commit secrets or print values in assistant output.

**OpenShift + local tooling:**

```bash
export KUBECONFIG="/path/to/your/kubeconfig"
```

**GitHub MCP (optional):**

```bash
export GITHUB_PERSONAL_ACCESS_TOKEN="your-github-token"
```

**Red Hat Lightspeed MCP (optional):**

```bash
export LIGHTSPEED_CLIENT_ID="your-service-account-client-id"
export LIGHTSPEED_CLIENT_SECRET="your-service-account-client-secret"
```

### Install (Lola)

```bash
lola install -f rh-developer
```

Module path: `rh-developer` in `marketplace/rh-agentic-collection.yml`. See the root [README.md](../../README.md) for full prerequisites and MCP notes.

### Installation (Claude Code)

```bash
lola install -f rh-developer -a claude-code
```

### Installation (Cursor)

```bash
lola install -f rh-developer -a cursor
```

### MCP configuration

Servers are defined in **`mcps.json`** at the pack root. Use **`${VAR}`** placeholders only.

**Note (Linux vs macOS):** the OpenShift MCP `Podman` invocation may include user-namespace flags for `KUBECONFIG` readability; on macOS Podman-in-VM may require adjusting `mcps.json` per the pack README.
