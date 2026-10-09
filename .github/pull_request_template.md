<!--
  TIP: Run /agentic-contribution-skill in Claude Code to create or import skills.
  It handles validation, plugin selection, and AGENTS.md routing automatically.
  See CONTRIBUTING.md for details.
-->

## Summary

<!-- What does this PR do and why? -->

## Plugin(s) affected

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
- [ ] New plugin
- [ ] Update existing skill / agent
- [ ] MCP server config (`mcps.json`)
- [ ] Docs / README
- [ ] CI / tooling

## Contribution method

- [ ] Created/imported with `/agentic-contribution-skill`
- [ ] Manual contribution (validated with `make validate` + `make validate-skill-design-changed`)

## Plugin-persona alignment (new skills only)

<!-- Why does this skill belong in the selected plugin? (1-2 sentences) -->

## AGENTS.md compliance

- [ ] Agents orchestrate skills; no direct MCP/tool calls in agents
- [ ] Skills are single-purpose task executors
- [ ] Skills encapsulate all tool access (MCP tools invoked only inside skills)
- [ ] Document consultation: file is **read** with the Read tool, then declared to the user
- [ ] No credentials hardcoded; env vars used via `${VAR}` references
- [ ] Human-in-the-loop confirmation added for any destructive or critical operations

## Validation

- [ ] `make validate` passes locally
- [ ] New/changed skills have valid YAML frontmatter (`name`, `description`)
- [ ] New/changed agents have valid YAML frontmatter (`name`, `description`)
