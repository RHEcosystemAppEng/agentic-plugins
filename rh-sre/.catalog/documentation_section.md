<!--
  Catalog fragment — maintain via create-collection workflow (assistant + maintainer + PR review).
  Golden sources: skills/*/SKILL.md, README.md, AGENTS.md
-->

### Why use this collection instead of calling MCP tools directly?

- **Reliability** — Skills apply validation gates (CVE IDs, inventory, AAP connectivity) before expensive operations.
- **Safety** — Human-in-the-loop for remediation plans, playbook execution, and broad job launches.
- **Consistency** — Documented workflows, error handling, and follow-up skills (for example `/remediation` vs ad hoc tool calls).
- **Troubleshooting** — Skills bundle recovery paths; use `/mcp-lightspeed-validator` and `/mcp-aap-validator` when prerequisites fail.

### In-repository documentation

This plugin ships an AI-oriented knowledge base under **`references/`** (index and source attribution) and **`skills/*/references/`** (runtime skill docs). Start at **[references/INDEX.md](references/INDEX.md)** and use **`references/.ai-index/`** (semantic index, task mapping) for token-efficient discovery.

### Configuration and architecture

- Environment variables for Lightspeed and AAP are declared only as `${VAR}` placeholders in **`mcps.json`**.
- Orchestration (**`/remediation`**) chains impact, validation, context, playbook generation, execution, and verification; see plugin **AGENTS.md** for routing when you need a single step only.
