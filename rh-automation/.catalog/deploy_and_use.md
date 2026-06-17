<!--
  Catalog fragment — maintain via create-collection workflow (assistant + maintainer + PR review).
  Golden sources: skills/*/SKILL.md, README.md, AGENTS.md, marketplace/rh-agentic-collection.yml
-->

### Prerequisites

- Claude Code CLI or IDE extension (if using Claude Code)
- Ansible Automation Platform **controller** reachable over HTTPS from the workstation running the assistant
- API token with permissions appropriate for job, inventory, configuration, security, monitoring, and user APIs used by the pack

### Environment setup

All HTTP MCP endpoints in **`mcps.json`** derive from the same host and bearer token. **Names must match `mcps.json` exactly.**

```bash
export AAP_MCP_SERVER="your-aap-controller-hostname.example.com"
export AAP_API_TOKEN="your-controller-api-token"
```

Do **not** commit real hostnames or tokens; **`mcps.json`** must keep **`${AAP_MCP_SERVER}`** and **`${AAP_API_TOKEN}`** placeholders only.

### Installation (Lola)

```bash
lola install -f rh-automation
```

Module path: **`rh-automation`** in **`marketplace/rh-agentic-collection.yml`**. See the root [README.md](../../README.md) for marketplace setup.

### Installation (Claude Code)

```bash
lola install -f rh-automation -a claude-code
```

### Installation (Cursor)

```bash
lola install -f rh-automation -a cursor
```

### MCP configuration

Six **HTTP** MCP servers are listed under **`mcpServers`** in **`mcps.json`** (job, inventory, configuration, security-compliance, system-monitoring, user-management). Each uses **`https://${AAP_MCP_SERVER}/...`** and **`Bearer ${AAP_API_TOKEN}`**. Skills wrap these endpoints—do not call them directly from the assistant.
