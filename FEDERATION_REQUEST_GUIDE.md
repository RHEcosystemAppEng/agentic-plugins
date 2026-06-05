# Federation Request Guide

How to register your external agentic pack in the Red Hat Agentic Collections marketplace.

Federation lets you **list your pack in our catalog without moving code into this repository**. Your pack stays in your repo — you own it, maintain it, and release it. Users discover it here and install it directly from your repository via [Lola](https://github.com/LobsterTrap/lola).

**Install scope:** `lola install -f <name>` installs the **entire Lola pack** — every skill in the pack, the same as for in-repo modules such as `rh-sre` or `rh-developer`. There is no marketplace field to install a subset of skills.

For how maintainers evaluate federation PRs, see [FEDERATION_REVIEW_GUIDE.md](FEDERATION_REVIEW_GUIDE.md).

> **Lola `ref` field:** Federated entries **must** include `ref` (40-character commit SHA) for CI validation and catalog pinning in this repository. **Lola currently ignores `ref`** on `lola install` / `lola mod add` and installs from the repository default branch until [LobsterTrap/lola#180](https://github.com/LobsterTrap/lola/issues/180) is fixed.

## Two ways to request federation

| Method | When to use |
|--------|-------------|
| **`/federation-request` skill** | Recommended. Clone this repo in Claude Code, run `/federation-request`, provide your repository URL and pack path — metadata is inferred and a PR is prepared interactively. |
| **Manual (this guide)** | Step-by-step when you prefer to open the PR yourself or work outside Claude Code. |

Direct contributions (adding skills inside this repo) use `/agentic-contribution-skill` instead — see [CONTRIBUTING.md](CONTRIBUTING.md).

---

## Requirements

Before requesting federation, your pack must meet these criteria:

| Requirement | Details |
|-------------|---------|
| **Lola-compatible structure** | Valid Lola pack with `CLAUDE.md`, `README.md`, and `skills/` directory at the declared `path` |
| **License** | LICENSE file in your repo, compatible with Apache 2.0 (Apache-2.0, MIT, BSD-2-Clause, BSD-3-Clause) |
| **Tier 1 compliance** | All skills pass the [agentskills.io specification](https://agentskills.io/specification) linter |
| **Tier 2 compliance** | All skills follow [SKILL_DESIGN_PRINCIPLES.md](SKILL_DESIGN_PRINCIPLES.md) |
| **No hardcoded credentials** | MCP servers in `mcps.json` use `${ENV_VAR}` references only |
| **No `:latest` tags** | Container images pinned by version or SHA256 digest |
| **Public repository** | Must be cloneable without authentication |
| **Pinned commit** | Marketplace entry must include `ref` as a **40-character commit SHA** (not a branch or tag name) |

Validate your pack locally before opening a PR:

```bash
# From your pack directory (or use --pack-path for a subdirectory)
uv run python scripts/validate_federation.py <repo-url> --ref <40-character-commit-sha>
uv run python scripts/validate_federation.py <repo-url> --ref <commit-sha> --pack-path <path>
```

---

## What you provide vs what we infer

The `/federation-request` skill asks for **only two inputs**:

1. **repository** — public Git URL (must not be this repo; that is a direct contribution)
2. **path** — path to the Lola pack inside the repo (use `.` when the pack is at the repo root)

Everything else is **inferred from a clone** of your repository, then shown in a summary table for your confirmation:

| Field | How it is determined |
|-------|----------------------|
| **name** | `plugin.json` name, basename of `path`, or sole `skills/` folder — must be unique kebab-case in the marketplace |
| **title** | README heading, title-case of `name`, or plugin description — used in `docs/plugins.json` and catalog `name:` |
| **description** | `plugin.json`, README, or first skill description (≤200 chars) |
| **version** | `plugin.json` semver, or default `0.1.0` |
| **ref** | Default-branch HEAD commit SHA (40 hex characters) |
| **tags** | Derived from skills, README, and path; always includes `federation` |
| **maturity** | Defaults to **`ORANGE`** (not promoted on GitHub Pages until **`GREEN`**) |

You may override any inferred value before the PR is created.

---

## Marketplace entry format

Your PR adds a module entry to `marketplace/rh-agentic-collection.yml`:

```yaml
  - name: "<name>"
    description: "<description>"
    version: "<version>"
    repository: "<repository>"
    ref: "<commit-sha>"         # required: 40-character commit SHA (Lola ignores until lola#180)
    path: "<path>"
    tags:
      - "<tag1>"
      - "<tag2>"
      - "federation"
```

| Field | Required | Notes |
|-------|----------|-------|
| `name` | Yes | Kebab-case module identifier; used by `lola install -f <name>` |
| `description` | Yes | One or two sentences |
| `version` | Yes | Semver (`X.Y.Z`) |
| `repository` | Yes | Public Git URL of your pack repo |
| `ref` | Yes | **40-character commit SHA** for CI/catalog pinning in this repo (Lola ignores until [lola#180](https://github.com/LobsterTrap/lola/issues/180)) |
| `path` | Yes | Subdirectory of the pack (`.` for repo root). **All skills under this path are installed.** |
| `tags` | Yes | Include `federation` plus discoverability keywords |

---

## What your PR must include

A complete federation PR contains:

1. **`marketplace/rh-agentic-collection.yml`** — module entry (above)
2. **`docs/plugins.json`** — display title for the documentation site:

   ```json
   "<name>": {
     "title": "<human-readable title>"
   }
   ```

3. **`federation/modules/<name>/.catalog/`** — collection catalog generated from your external pack at `ref` (via `/create-collection` or equivalent). Set `id:` to the module `name` and catalog `name:` to the confirmed `title`.

Stage and commit:

```bash
git checkout -b feat/federate-<name>
git add marketplace/rh-agentic-collection.yml docs/plugins.json federation/modules/<name>/
git commit -m "feat: federate <name> module from <repository>"
git push -u origin feat/federate-<name>
gh pr create --title "feat: federate <name> module" --label "federation"
```

The **`federation`** label triggers automated CI validation.

---

## Automated validation (CI)

When your PR has the `federation` label, CI (`.github/workflows/federation-validation.yml`) runs on each new or changed federated module:

| Check | Description |
|-------|-------------|
| **Commit SHA** | `ref` is present and a valid 40-character hex SHA |
| **Clone & access** | Repository reachable at the pinned commit |
| **Lola module schema** | Required marketplace fields present |
| **Tier 1** | agentskills.io spec (skill linter) |
| **Tier 2** | Design principles |
| **MCP pinning** | No `:latest`; no hardcoded credentials in `mcps.json` |
| **Credential scan** | gitleaks |
| **Catalog cross-check** | `federation/modules/<name>/.catalog/` matches the external pack roster, title, and marketplace metadata at `ref` |

Results are posted as a comment on your PR.

---

## Maintainer review

After CI passes, a maintainer reviews using `/federation-review` and [FEDERATION_REVIEW_GUIDE.md](FEDERATION_REVIEW_GUIDE.md). Review covers license compatibility, AI agent compatibility (Claude Code, Cursor, ChatGPT), and catalog quality.

---

## After merge

Once merged, users can install your pack — **all skills in the pack at `path`**, like any other marketplace module:

```bash
lola market add rh-agentic-collections https://raw.githubusercontent.com/RHEcosystemAppEng/agentic-collections/main/marketplace/rh-agentic-collection.yml
lola install -f <name>
```

Federated modules default to **`ORANGE`** maturity. Promotion to **`GREEN`** lists the pack on the [documentation site](https://rhecosystemappeng.github.io/agentic-collections).

### Maintaining your federated pack

You own your pack — updates happen in **your** repository. When you release changes that should appear in the marketplace:

- Bump **`version`** in `marketplace/rh-agentic-collection.yml`
- Update **`ref`** to a new **40-character commit SHA** (not a tag name)
- Refresh **`federation/modules/<name>/.catalog/`** if skills or metadata changed
- Open a PR here with the `federation` label

Breaking changes (renamed skills, restructured pack) require an updated marketplace entry and catalog refresh.

---

## FAQ

**Can I expose only some skills from a larger repo?**  
Yes — structure your external repo so the skills you want live in a **dedicated Lola pack directory**, then set marketplace **`path`** to that directory (for example `packages/network-diagnostics`). Lola installs every skill under that path; there is no per-skill filter in the marketplace YAML.

**What if my repo is private?**  
Federation requires a public repository so users and CI can clone it.

**Can I use a monorepo?**  
Yes. Set `path` to the subdirectory where your Lola pack lives (e.g., `packages/my-agentic-pack`).

**Why commit SHA instead of a tag?**  
This repo requires an immutable pin for supply-chain reproducibility. Resolve a tag to a SHA in your repo (`git rev-parse v1.0.0`) and use that SHA as `ref`.

**What license is required?**  
Any license compatible with Apache 2.0: Apache-2.0, MIT, BSD-2-Clause, BSD-3-Clause. GPL and AGPL are not compatible.

**Federation vs direct contribution?**  
- **Federation** — complete external pack; code stays in your repo  
- **Direct contribution** — add skills to an existing pack in this repo via `/agentic-contribution-skill`

---

## Resources

- [FEDERATION_REVIEW_GUIDE.md](FEDERATION_REVIEW_GUIDE.md) — How maintainers evaluate federation requests
- [CONTRIBUTING.md](CONTRIBUTING.md) — Direct contribution guide
- [SKILL_DESIGN_PRINCIPLES.md](SKILL_DESIGN_PRINCIPLES.md) — Skill quality standards
- [COLLECTION_SPEC.md](COLLECTION_SPEC.md) — Collection catalog specification
- [Lola Package Manager](https://github.com/LobsterTrap/lola) — Install and manage agentic packs
