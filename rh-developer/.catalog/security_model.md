<!--
  Catalog fragment — maintain via create-collection workflow (assistant + maintainer + PR review).
  Golden sources: skills/*/SKILL.md, README.md, AGENTS.md, marketplace/rh-agentic-collection.yml
-->

- Never echo tokens, kubeconfig contents, or registry passwords — only whether variables appear set.
- Confirm manifests and impact before mutating cluster or host resources; no silent deletes.
- Prefer **`/validate-environment`** before first deploy on a new machine or cluster context.
