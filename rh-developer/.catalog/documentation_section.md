<!--
  Catalog fragment — maintain via create-collection workflow (assistant + maintainer + PR review).
  Golden sources: skills/*/SKILL.md, README.md, AGENTS.md
-->

### Why use skills instead of raw MCP tools?

- **Safety** — skills enforce confirmation before creates/updates/deletes and redact secrets.
- **Recovery** — standardized debug skills (`/debug-pod`, `/debug-build`, …) chain to remediation steps.
- **Consistency** — workflows follow plugin docs (human-in-the-loop, image selection, RHEL patterns).

### Plugin documentation

Skill-local reference docs live under **`skills/*/references/`** (for example `skills/validate-environment/references/prerequisites.md`, `skills/recommend-image/references/image-selection-criteria.md`, `skills/debug-pod/references/debugging-patterns.md`).

### Routing

Use **`AGENTS.md`** intent routing to pick a single skill; use **`/containerize-deploy`** when the user wants an end-to-end guided path with checkpoints.
