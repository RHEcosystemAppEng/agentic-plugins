<!--
  Catalog fragment — maintain via create-collection workflow (assistant + maintainer + PR review).
  Golden sources: skills/*/SKILL.md, README.md, CLAUDE.md, marketplace/rh-agentic-collection.yml
-->

### Prerequisites

- Claude Code CLI or IDE extension (if using Claude Code)
- Red Hat service account ([console.redhat.com](https://console.redhat.com/iam/service-accounts))

Skills fall back to WebFetch on public Red Hat documentation if the MCP server is not configured.

### Environment setup

No environment variables are required for this pack's MCP server. Authentication uses Red Hat Customer Portal browser SSO.

### Installation (Lola)

From a checkout of this repository, install the pack with [Lola](https://github.com/LobsterTrap/lola):

```bash
lola install -f rh-basic
```

The module is declared in **`marketplace/rh-agentic-collection.yml`** (`path: rh-basic`). See the root [README.md](../../README.md) for marketplace setup.

### Installation (Claude Code)

```bash
lola install -f rh-basic -a claude-code
```

### Installation (Cursor)

```bash
lola install -f rh-basic -a cursor
```

### MCP configuration

Server definitions live in **`mcps.json`** at the pack root and use HTTP transport:

- `red-hat-security` -> `https://security-mcp.api.redhat.com/mcp`

After installation, run `/red-hat-security-mcp-setup` to add the server to your project's `.mcp.json` and complete browser SSO authentication.
