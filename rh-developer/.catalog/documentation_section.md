<!--
  Catalog fragment — maintain via create-collection workflow (assistant + maintainer + PR review).
  Golden sources: skills/*/SKILL.md, README.md, AGENTS.md, marketplace/rh-agentic-collection.yml
-->

### Why use skills instead of raw MCP tools?

- **Safety** — skills enforce confirmation before creates/updates/deletes and redact secrets.
- **Recovery** — standardized debug skills (`/debug-pod`, `/debug-build`, …) chain to remediation steps.
- **Consistency** — workflows follow pack docs (human-in-the-loop, image selection, RHEL patterns).

### Pack documentation

See **`docs/`** for deep dives: `prerequisites.md`, `human-in-the-loop.md`, `image-selection-criteria.md`, `builder-images.md`, `rhel-deployment.md`, `debugging-patterns.md`.

### Routing

Use **`AGENTS.md`** intent routing to pick a single skill; use **`/containerize-deploy`** when the user wants an end-to-end guided path with checkpoints.
