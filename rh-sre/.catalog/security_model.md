<!--
  Catalog fragment — maintain via create-collection workflow (assistant + maintainer + PR review).
  Golden sources: skills/*/SKILL.md, README.md, AGENTS.md, marketplace/rh-agentic-collection.yml
-->

- Do **not** expose `LIGHTSPEED_CLIENT_ID`, `LIGHTSPEED_CLIENT_SECRET`, AAP tokens, or any API credentials in chat—only whether they appear configured.
- Require explicit user approval before running remediation playbooks or destructive changes at scale.
- Prefer **`/remediation`** for end-to-end CVE response so validation and verification steps are not skipped accidentally.
