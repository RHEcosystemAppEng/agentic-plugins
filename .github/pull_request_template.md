<!--
  TIP: Run /agentic-contribution-skill in Claude Code to create or import skills.
  It handles validation, pack selection, and CLAUDE.md routing automatically.
  See CONTRIBUTING.md for details.
-->

## Summary

<!-- What does this PR do and why? -->

## Pack(s) affected

- [ ] `ocp-admin`
- [ ] `rh-ai-engineer`
- [ ] `rh-automation`
- [ ] `rh-basic`
- [ ] `rh-developer`
- [ ] `rh-sre`
- [ ] `rh-virt`
- [ ] Other / repo-wide

## Change type

- [ ] New skill
- [ ] New agent
- [ ] New pack
- [ ] Update existing skill / agent
- [ ] MCP server config (`mcps.json`)
- [ ] Docs / README
- [ ] CI / tooling
- [ ] Federation (external pack)

## Contribution method

- [ ] Created/imported with `/agentic-contribution-skill`
- [ ] Manual contribution (validated with `make validate` + `make validate-skill-design-changed`)

## Pack-persona alignment (new skills only)

<!-- Why does this skill belong in the selected pack? (1-2 sentences) -->

## CLAUDE.md compliance

- [ ] Agents orchestrate skills; no direct MCP/tool calls in agents
- [ ] Skills are single-purpose task executors
- [ ] Skills encapsulate all tool access (MCP tools invoked only inside skills)
- [ ] Document consultation: file is **read** with the Read tool, then declared to the user
- [ ] No credentials hardcoded; env vars used via `${VAR}` references
- [ ] Human-in-the-loop confirmation added for any destructive or critical operations

## Federation request (external pack)

<!-- Fill this section ONLY if this PR adds or updates a federated module. Delete it otherwise. -->

- **Repository URL:** <!-- https://github.com/org/repo -->
- **Pack path:** <!-- Subdirectory within the repo, or "." for root -->
- **Ref:** <!-- Required 40-character commit SHA (not a branch or tag) -->
- **License:** <!-- Verified from repo LICENSE during review; must be compatible with Apache 2.0 -->
- **Contact:** <!-- @github-handle or email of the pack owner -->

## Validation

- [ ] `make validate` passes locally
- [ ] New/changed skills have valid YAML frontmatter (`name`, `description`)
- [ ] New/changed agents have valid YAML frontmatter (`name`, `description`)
