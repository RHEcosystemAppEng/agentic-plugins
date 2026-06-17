<!--
  Catalog fragment — maintain via create-collection workflow (assistant + maintainer + PR review).
  Golden sources: skills/*/SKILL.md, README.md, AGENTS.md, marketplace/rh-agentic-collection.yml
-->

### Why use this collection instead of calling MCP tools directly?

- **Reliability** — Skills apply validation gates (CVE IDs, inventory, AAP connectivity) before expensive operations.
- **Safety** — Human-in-the-loop for remediation plans, playbook execution, and broad job launches.
- **Consistency** — Documented workflows, error handling, and follow-up skills (for example `/remediation` vs ad hoc tool calls).
- **Troubleshooting** — Skills bundle recovery paths; use `/mcp-lightspeed-validator` and `/mcp-aap-validator` when prerequisites fail.

### In-repository documentation

This pack ships an AI-oriented knowledge base under **`docs/`**. Start at **[docs/INDEX.md](docs/INDEX.md)** and use **`docs/.ai-index/`** (semantic index, task mapping) for token-efficient discovery.

### Configuration and architecture

- Environment variables for Lightspeed and AAP are declared only as `${VAR}` placeholders in **`mcps.json`**.
- Orchestration (**`/remediation`**) chains impact, validation, context, playbook generation, execution, and verification; see pack **AGENTS.md** for routing when you need a single step only.
