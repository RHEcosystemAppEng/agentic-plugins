<!--
  Catalog fragment — maintain via create-collection workflow (assistant + maintainer + PR review).
  Golden sources: skills/*/SKILL.md, README.md, AGENTS.md, marketplace/rh-agentic-collection.yml
-->

### Prerequisites

- Claude Code CLI or IDE extension (if using Claude Code)
- Podman or Docker installed (for container-based MCP servers)
- Red Hat Lightspeed service account ([console](https://console.redhat.com/))

### Environment setup

Configure Red Hat Lightspeed credentials (names must match **`mcps.json`**):

```bash
export LIGHTSPEED_CLIENT_ID="your-service-account-client-id"
export LIGHTSPEED_CLIENT_SECRET="your-service-account-client-secret"
```

For Ansible Automation Platform MCP (optional, for playbook execution flows):

```bash
export AAP_MCP_SERVER="your-aap-controller-hostname"
export AAP_API_TOKEN="your-api-token"
```

### Installation (Lola)

From a checkout of this repository, install the pack with [Lola](https://github.com/LobsterTrap/lola) using the registry file at the repo root:

```bash
lola install -f rh-sre
```

The module is declared in **`marketplace/rh-agentic-collection.yml`** (`path: rh-sre`). See the root [README.md](../../README.md) for marketplace setup.

### Installation (Claude Code)

```bash
lola install -f rh-sre -a claude-code
```

### Installation (Cursor)

```bash
lola install -f rh-sre -a cursor
```

### MCP configuration

Server definitions live in **`mcps.json`** at the pack root. Use **`${VAR}`** placeholders only; never commit secrets.
