<!--
  Catalog fragment — maintain via create-collection workflow (assistant + maintainer + PR review).
  Golden sources: skills/*/SKILL.md, README.md, AGENTS.md, marketplace/rh-agentic-collection.yml
-->

### red-hat-security — Red Hat Security MCP

Provides CVE, advisory, and errata data directly from the Red Hat Security API.

- **CVE and advisory lookups** — used by `red-hat-cve-explainer` and `red-hat-support-severity`
- **Transport:** HTTP (`https://security-mcp.api.redhat.com/mcp`)
- **Authentication:** Red Hat Customer Portal SSO (browser-based, no env vars required)
- **Setup:** run `/red-hat-security-mcp-setup` to add the server entry to your project's `.mcp.json`

**All skills fall back to `WebFetch` on public Red Hat documentation when this MCP server is unavailable.** An active Red Hat subscription is required for full dataset access.
