<!--
  Catalog fragment — maintain via create-collection workflow (assistant + maintainer + PR review).
  Golden sources: skills/*/SKILL.md, README.md, AGENTS.md, marketplace/rh-agentic-collection.yml
-->

- **Credentials:** Browser SSO only for `red-hat-security`; no API keys or client secrets are required for `mcps.json`.
- **Transport security:** MCP access uses HTTPS to `https://security-mcp.api.redhat.com/mcp` and relies on Red Hat Customer Portal authentication.
- **No write operations:** All skills are read-only with respect to Red Hat platform data. No remediation playbooks are generated or executed by this pack.
- **Self-removing setup skill:** `red-hat-get-started` deletes itself from the project after completing its one-time task.
