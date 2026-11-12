# Contributing to Agentic Plugins Skills

Add skills to the Red Hat Agentic Plugins.

## How to Contribute

The fastest way to contribute is using `/agentic-contribution-skill` in Claude Code. It guides you through everything: discovery, definition, generation, validation, and git workflow.

### Two paths

**Have an idea for a new skill?**

```
/agentic-contribution-skill
# Choose "Create" -> answer discovery questions -> skill is generated and validated
```

**Already have a SKILL.md?**

```
/agentic-contribution-skill
# Choose "Import" -> point to your file -> skill is analyzed, adapted, and validated
```

### Quick start

1. Fork and clone the repository
2. Open the project in Claude Code
3. Run `/agentic-contribution-skill` and follow the prompts

The skill handles plugin selection, AGENTS.md routing, validation (Tier 1 + Tier 2), and git workflow automatically.

## Plugin Selection

Each plugin targets a specific persona. Choose the one that matches your skill:

| Plugin | Persona | Use when |
|------|---------|----------|
| `rh-sre` | Site Reliability Engineers | CVE remediation, system compliance, RHEL automation |
| `rh-developer` | Application Developers | App deployment, S2I builds, Helm charts |
| `rh-virt` | Virtualization Admins | VM lifecycle, snapshots, migrations |
| `ocp-admin` | OpenShift Administrators | Cluster management, health reports, monitoring |
| `rh-ai-engineer` | AI/ML Engineers | Model serving, vLLM, KServe, NVIDIA NIM |
| `rh-automation` | Automation Leads | Ansible AAP governance, safety checks |
| `rh-basic` | General Red Hat Users | CVE diagnostics, lifecycle, patching, support cases, troubleshooting |

Not sure which plugin? The skill will suggest one based on your skill's content.

## Manual Contribution

If you prefer to create skills manually:

1. Read the standards: [SKILL_DESIGN_PRINCIPLES.md](SKILL_DESIGN_PRINCIPLES.md)
2. Create `<plugin>/skills/<skill-name>/SKILL.md` following the template
3. Update `<plugin>/AGENTS.md` intent routing table
4. Validate Tier 1: `uv run python scripts/validate_skills_tier1.py <plugin>/skills/<skill-name>/SKILL.md`
5. Validate Tier 2: `make validate-skill-design-changed`

Both tiers must pass before submitting a PR.

## Before You Submit

- [ ] Tier 1 validation passed (agentskills.io spec)
- [ ] Tier 2 validation passed (design principles)
- [ ] Compass manifests and references layout validated: `make validate-compass-manifests`
- [ ] Skill doc links validated: `uv run python scripts/validate_skill_doc_links.py <plugin>/skills/<skill-name>/SKILL.md`
- [ ] Skill doc tree links validated: `uv run python scripts/validate_docs_tree_links.py <plugin>/skills/<skill-name>/SKILL.md`
- [ ] Plugin AGENTS.md intent routing updated
- [ ] Tested skill locally by invoking it in Claude Code
- [ ] No credentials hardcoded (use `${ENV_VAR}` format)
- [ ] Human-in-the-loop confirmation for destructive operations
- [ ] PR description fills the template (CodeRabbit warns on thin descriptions)

## CodeRabbit reviews

PRs are auto-reviewed by [CodeRabbit](https://coderabbit.ai) using [`.coderabbit.yaml`](.coderabbit.yaml). Reviews are short and contract-focused (skills, `mcps.json`, Compass manifests, `AGENTS.md`, collection roster, secrets). They do **not** replace `make validate` or required human / CODEOWNERS approval.

**What CodeRabbit looks for**
- Skill frontmatter and skill-first / MCP encapsulation rules
- No hardcoded credentials (`${ENV_VAR}` only in `mcps.json`)
- Compass `dependsOn` / `dependencyOf` consistency and collection roster sync
- Secret leakage (including under `eval/`)

**How to work with it**
- Fill [`.github/pull_request_template.md`](.github/pull_request_template.md); description check is `warning` (not a merge blocker)
- Skip auto-review with a `hold` label, a WIP title (`wip:`, `[WIP]`), or a GitHub Draft PR
- Bot / Dependabot-style authors are ignored for auto-review
- Org members can chat with the bot on the PR; non-org members cannot (`allow_non_org_members: false`)
- Auto-review stays on for every push (`auto_pause_after_reviewed_commits: 0`)
- Useful comments: `@coderabbitai review`, `@coderabbitai full review`, `@coderabbitai summary`

When adding a new MCP server under `mcps/`, add a matching `path_instructions` entry in [`.coderabbit.yaml`](.coderabbit.yaml) for that manifest (do not use `mcps/*.yaml` — it would also match `mcps/catalog-info.yaml`).

Policy changes to `.coderabbit.yaml` are owned like other CI/config (see `CODEOWNERS`).

## Resources

- [SKILL_DESIGN_PRINCIPLES.md](SKILL_DESIGN_PRINCIPLES.md) -- Design principles and templates
- [agentskills.io specification](https://agentskills.io/specification) -- Base skill standard
- [Security Policy](SECURITY.md) -- Credential handling and vulnerability reporting
- [`.coderabbit.yaml`](.coderabbit.yaml) -- CodeRabbit review policy

## License

By contributing, you agree your contributions are licensed under [Apache License 2.0](LICENSE).
