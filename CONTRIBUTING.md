# Contributing to Agentic Collections

Add skills to the Red Hat Agentic Collections marketplace.

## How to Contribute

The fastest way to contribute is using `/agentic-contribution-skill` in Claude Code. It guides you through everything: discovery, definition, generation, validation, and git workflow.

### Two paths

**Have an idea for a new skill?**

```
/agentic-contribution-skill
# Choose "Create" → answer discovery questions → skill is generated and validated
```

**Already have a SKILL.md?**

```
/agentic-contribution-skill
# Choose "Import" → point to your file → skill is analyzed, adapted, and validated
```

### Quick start

1. Fork and clone the repository
2. Open the project in Claude Code
3. Run `/agentic-contribution-skill` and follow the prompts

The skill handles pack selection, CLAUDE.md routing, validation (Tier 1 + Tier 2), and git workflow automatically.

## Pack Selection

Each pack targets a specific persona. Choose the one that matches your skill:

| Pack | Persona | Use when |
|------|---------|----------|
| `rh-sre` | Site Reliability Engineers | CVE remediation, system compliance, RHEL automation |
| `rh-developer` | Application Developers | App deployment, S2I builds, Helm charts |
| `rh-virt` | Virtualization Admins | VM lifecycle, snapshots, migrations |
| `ocp-admin` | OpenShift Administrators | Cluster management, health reports, monitoring |
| `rh-ai-engineer` | AI/ML Engineers | Model serving, vLLM, KServe, NVIDIA NIM |
| `rh-automation` | Automation Leads | Ansible AAP governance, safety checks |
| `rh-basic` | General Red Hat Users | CVE diagnostics, lifecycle, patching |
| `rh-support-engineer` | Support Engineers | Technical support, troubleshooting |

Not sure which pack? The skill will suggest one based on your skill's content.

## Manual Contribution

If you prefer to create skills manually:

1. Read the standards: [SKILL_DESIGN_PRINCIPLES.md](SKILL_DESIGN_PRINCIPLES.md)
2. Create `<pack>/skills/<skill-name>/SKILL.md` following the template
3. Update `<pack>/CLAUDE.md` intent routing table
4. Validate Tier 1: `./scripts/run-skill-linter.sh <pack>/skills/<skill-name>/`
5. Validate Tier 2: `make validate-skill-design-changed`

Both tiers must pass before submitting a PR.

## Before You Submit

- [ ] Tier 1 validation passed (agentskills.io spec)
- [ ] Tier 2 validation passed (design principles)
- [ ] Skill doc links validated: `uv run python scripts/validate_skill_doc_links.py <pack>/skills/<skill-name>/SKILL.md`
- [ ] Skill doc tree links validated: `uv run python scripts/validate_docs_tree_links.py <pack>/skills/<skill-name>/SKILL.md`
- [ ] Pack CLAUDE.md intent routing updated
- [ ] Tested skill locally by invoking it in Claude Code
- [ ] No credentials hardcoded (use `${ENV_VAR}` format)
- [ ] Human-in-the-loop confirmation for destructive operations

## Resources

- [SKILL_DESIGN_PRINCIPLES.md](SKILL_DESIGN_PRINCIPLES.md) -- Design principles and templates
- [Federation Review Guide](FEDERATION_REVIEW_GUIDE.md) -- How external packs are evaluated for federation
- [agentskills.io specification](https://agentskills.io/specification) -- Base skill standard
- [Documentation site](https://rhecosystemappeng.github.io/agentic-collections) -- Browse all collections
- [GitHub Issues](https://github.com/RHEcosystemAppEng/agentic-collections/issues) -- Report bugs or ask questions

## License

By contributing, you agree your contributions are licensed under [Apache License 2.0](LICENSE).
