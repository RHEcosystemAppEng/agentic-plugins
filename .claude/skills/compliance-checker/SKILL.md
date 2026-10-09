---
name: compliance-checker
description: |
  Run skill design compliance validation for agentic collections. Use when the user asks to:
  - "Check skill compliance" / "Validate skill design" / "Run compliance check"
  - "Verify my skills follow design principles"
  - Before committing skill changes

  Runs the validate_skills_tier2.py script against SKILL_DESIGN_PRINCIPLES.md.
---

# Skill Design Compliance Checker

Run the programmatic compliance check for skills in this agentic-plugins repository.

## When to Use This Skill

Invoke this skill when the user wants to:
- Validate skills against [SKILL_DESIGN_PRINCIPLES.md](SKILL_DESIGN_PRINCIPLES.md)
- Check compliance before committing or opening a PR
- Verify design principle adherence (DP1–DP7)

## Workflow

1. **Run from project root** (the workspace root).

2. **Preferred: validate only changed skills** (recommended for local dev):
   ```bash
   make validate-skill-design-changed
   ```
   This validates only staged and unstaged skill changes.

3. **Alternative: validate all skills or a specific plugin**:
   ```bash
   make validate-skill-design
   # Or validate a specific plugin:
   make validate-skill-design PLUGIN=rh-sre
   ```

4. **Report results** to the user:
   - If validation passes: report success
   - If validation fails: list the errors and suggest fixes per the design principles

## Dependencies

- `uv` must be installed (run `make install` if needed)
- Script: `scripts/validate_skills_tier2.py`
- Reference: [SKILL_DESIGN_PRINCIPLES.md](../../../SKILL_DESIGN_PRINCIPLES.md)

## Design Principles Checked

- DP1: Document consultation transparency
- DP2: Parameter specification and ordering
- DP3: Description conciseness (≤500 tokens)
- DP4: Dependencies declaration
- DP5: Human-in-the-loop for critical skills
- DP6: Mandatory sections (Prerequisites, When to Use, Workflow)
- DP7: Credential security (avoid echoing env vars)
