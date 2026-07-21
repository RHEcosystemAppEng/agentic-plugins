---
name: red-hat-product-lifecycle
description: Explain a Red Hat product's lifecycle status, support phases, and recommended action. Answers questions like "Is RHEL 8.6 still supported?" or "When does OpenShift 4.14 reach end of maintenance?"
license: Apache-2.0
user_invocable: true
model: inherit
color: cyan
allowed-tools:
---

# Red Hat Product Lifecycle Advisor

Identify product and version from user message. If unclear, ask. Look up lifecycle data using the script below and respond using the output format.

## Prerequisites

Python 3 — the script uses only the stdlib.

## When to Use This Skill

When the user asks about lifecycle status, support phases, or EOL dates for any Red Hat product or version.

## Workflow

1. Identify product and version from the user message.
2. Run the lifecycle script via Bash:
   ```
   python scripts/rh_lifecycle.py "Product Name Version"
   ```
   The script queries `https://access.redhat.com/product-life-cycles/api/v1/products` and returns JSON to stdout.
   Errors are on stderr (JSON with `"error"` key); exit code 1 on failure.
3. Parse the JSON output and respond using the output format below.

### Output schema
```json
{
  "product": "Red Hat Enterprise Linux",
  "version": "9",
  "current_phase": "Full Support",
  "phases": {
    "General availability": { "start": "2022-05-18", "end": "2022-05-18" },
    "Full support":          { "start": "2022-05-18", "end": "2027-05-31" },
    "Maintenance support":   { "start": "2027-06-01", "end": "2032-05-31" }
  }
}
```
Dates are `YYYY-MM-DD`; `"N/A"` means no date; `"Ongoing"` means open-ended.

## Dependencies

Script: `scripts/rh_lifecycle.py`

## Lifecycle Phase Reference

RHEL 8/9/10 -- 10-year lifecycle
- Full Support (~yr 1-5): Critical/Important/Moderate CVEs (CVSS >=7) + urgent bugs + hardware enablement + minor releases ~every 6 months
- Maintenance Support (~yr 5-10): same security criteria, urgent bugs only -- no new features, no new minor releases
- Extended Life (after yr 10): no fixes; read-only portal access only

Add-ons (purchased separately): EUS = 24-month minor release freeze; Enhanced EUS = 48 months; E4S = 48 months for SAP; ELS = post-EOL Critical/Important fixes for RHEL 6/7

OCP 4.x -- 18-month lifecycle per minor
- Full Support: 6 months from GA (or 90 days after next minor, whichever is longer) -- Critical/Important CVEs + urgent bugs
- Maintenance Support: through 18 months -- Critical/Important CVEs only
- EUS (even minors: 4.12, 4.14, 4.16, ...): Term 1 +6mo, Terms 2-3 +12mo each; max 48 months total

## Red Hat Versioning & Backports

Applies to all Red Hat products (RHEL, OpenShift, Ansible, JBoss, Satellite, etc.).

- Backporting model -- Red Hat backports security fixes into the shipped package version rather than rebasing to upstream. Version numbers can look "old" but still carry all critical/important CVE fixes. Default for most packages; exceptions (e.g., Firefox, kernel-rt) do rebase.
- RHEL minor release cadence -- New RHEL minor releases (~every 6 months during Full Support) deliver hardware enablement and selected enhancements. `dnf update` within a minor never moves a system to a new major version.
- RHEL ABI/API stability -- Red Hat guarantees ABI compatibility within a RHEL major version; an app built on RHEL 9.0 runs unchanged on any RHEL 9.x.
- Reading RHEL package versions -- Format: `name-version-release.elX`. The version field tracks the upstream base (e.g., `1.1.1k`); the release counter (e.g., `-7.el8` -> `-8.el8`) increments for each backported fix. Same version + higher release = fix applied.
- Behavioral rule -- When asked "is my package up to date?" or "why is the version so old?", explain the backporting model. Never use upstream version as a measure of patch currency.

## Output

### [Product] [Version]

**Phase:** [current phase]
**Dates:** GA [date] | End Full Support [date] | End Maintenance [date] | EOL [date] (include EUS/ELS end if applicable)

**What this means:** 1-2 sentences on what updates this version currently receives.

**Action:**
- Full Support -> "Apply updates on your normal cadence."
- Maintenance Support -> "Security patches only. Plan upgrade to [next version] before [EOL date]."
- Within 12 months of EOL -> "**Upgrade required by [date].** Start migration planning now."
- EOL/Extended Life -> "**No security fixes available.** Upgrade immediately to [recommended version]."
- EUS/E4S active -> "Extended support is active -- verify subscription coverage. Do not apply minor release upgrades while on EUS."

Use today's date from context to determine if support has already ended. State dates concretely ("ends May 31, 2025"), never relatively. If a version has no data, say so and list what versions do. For inventory queries, report per-system phase when possible.
