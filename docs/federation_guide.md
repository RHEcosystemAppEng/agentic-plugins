# Federation Guide

How to register your external agentic pack in the Red Hat Agentic Collections marketplace.

## What is federation?

Federation lets you **list your pack in our marketplace without moving code into this repository**. Your pack stays in your repo — you own it, maintain it, release it. Users discover it here and install it directly from your repository via [Lola](https://github.com/RedHatProductSecurity/lola).

## Requirements

Before requesting federation, your pack must meet these criteria:

| Requirement | Details |
|-------------|---------|
| **Lola-compatible structure** | Your repo must contain a valid Lola pack with `CLAUDE.md`, `README.md`, and `skills/` directory |
| **License** | Must be compatible with Apache 2.0 (Apache-2.0, MIT, BSD-2-Clause, BSD-3-Clause) |
| **Tier 1 compliance** | All skills pass the [agentskills.io specification](https://agentskills.io/specification) linter |
| **Tier 2 compliance** | All skills follow [SKILL_DESIGN_PRINCIPLES.md](../SKILL_DESIGN_PRINCIPLES.md) |
| **No hardcoded credentials** | MCP servers use `${ENV_VAR}` format only |
| **No `:latest` tags** | Container images must use pinned versions or SHAs |
| **Public repository** | The repo must be publicly accessible |

## Step-by-step process

### 1. Gather your module information

You will need the following details:

| Field | Description | Example |
|-------|-------------|---------|
| **name** | Module identifier (kebab-case) | `network-diagnostics` |
| **description** | What the pack does (1-2 sentences) | `Network troubleshooting skills for SDN and OVN diagnostics` |
| **version** | Semver version of your pack | `0.2.0` |
| **repository** | Your public Git repository URL | `https://github.com/org/repo` |
| **license** | License identifier | `MIT` |
| **ref** | *(optional)* Pinned commit SHA or tag | `v0.2.0` or `a1b2c3d4...` |
| **path** | *(optional)* Path to the pack inside your repo (default: `.`) | `my-pack` |
| **tags** | Keywords for discoverability | `networking, sdn, troubleshooting` |

### 2. Open the federation request

Clone or fork this repository, open it in Claude Code, and run:

```
/federation-request
```

The skill guides you through every step interactively — collecting your module data, creating the marketplace entry, generating catalog files, and opening the PR with the `federation` label.

### 3. Automated validation (CI)

When you open a PR with the `federation` label, CI automatically:

- Clones your repository at the declared ref
- Validates Lola module schema (name, description, version, repository)
- Runs Tier 1 linter on all skills
- Runs Tier 2 design principles validation
- Checks MCP version pinning (no `:latest`)
- Scans for hardcoded credentials (gitleaks)

Results are posted as a comment on your PR.

### 4. Maintainer review

A maintainer will review your PR using the `/federation-review` skill, which covers:

- License compatibility confirmation
- AI agent compatibility check (Claude Code, Cursor, ChatGPT)
- Collection catalog generation for your module
- Lola marketplace verification

### 5. After merge

Once merged, your pack is available in the marketplace:

```bash
# Users can install your pack directly
lola install -f <your-module-name>
```

Your pack will also appear on the [documentation site](https://rhecosystemappeng.github.io/agentic-collections) once promoted to `GREEN` maturity.

## Maintaining your federated pack

You own your pack — updates happen in your repository. A few things to keep in mind:

- **Version bumps**: Update the `version` field in the marketplace YAML when you release new versions (open a PR here)
- **Breaking changes**: If you rename skills or restructure the pack, update the marketplace entry
- **Ref pinning**: If your module entry uses a `ref`, update it to point to your latest stable commit or tag
- **Quality**: Your pack must continue to pass Tier 1 and Tier 2 validation

## FAQ

**Can I federate only some skills from my pack?**
By default, all skills in the pack at the declared path are included. If you want to federate a subset, structure your repo so the desired skills are in a dedicated subdirectory and set `path` accordingly.

**What if my repo is private?**
Federation requires a public repository. Users need to clone it to install the pack via Lola.

**Can I use a monorepo?**
Yes. Set the `path` field to the subdirectory where your Lola pack lives (e.g., `packages/my-agentic-pack`).

**What license is required?**
Any license compatible with Apache 2.0: Apache-2.0, MIT, BSD-2-Clause, BSD-3-Clause. GPL and AGPL are not compatible.

## Resources

- [CONTRIBUTING.md](../CONTRIBUTING.md) — Direct contribution guide (for adding skills to this repo)
- [Federation Review Guide](FEDERATION_REVIEW_GUIDE.md) — How maintainers evaluate federation requests
- [SKILL_DESIGN_PRINCIPLES.md](../SKILL_DESIGN_PRINCIPLES.md) — Skill quality standards
- [Lola Package Manager](https://github.com/RedHatProductSecurity/lola) — Install and manage agentic packs
