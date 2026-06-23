# Fleet Inventory Output Templates

Read when completing a fleet inventory report to format the output.

## Template 1: Full Fleet Listing

**User Request**: "Show the managed fleet"

```markdown
# Managed Fleet Inventory

I consulted [fleet-management.md](../../../docs/insights/fleet-management.md) to structure this inventory report.

Retrieved from Red Hat Lightspeed on YYYY-MM-DDTHH:MM:SSZ

## Fleet Overview
- **Total Registered Systems**: N
- **Active (< 24h)**: N
- **Stale (> 7 days)**: N

## RHEL Version Distribution
| Version | Count | Percentage |

## Environment Breakdown
| Environment | Count | Systems |

## Top 20 Systems (by last check-in)
[Table: display_name, last_check_in, updated, groups or tags when present]

For RHEL version breakdown, call `inventory__get_host_system_profile` and use `system_profile.operating_system.version` or equivalent (`os_release`, `major`/`minor`).

**Would you like to**: Filter by environment/RHEL, view CVEs, create remediation plans
```

## Template 2: CVE-Affected Systems

**User Request**: "What systems are affected by CVE-X?"

```markdown
# CVE-X Impact Analysis

## Affected Systems Summary
- **Total Vulnerable**: N
- **Already Patched**: N
- **Impact Rate**: X% of fleet

## Vulnerable Systems
| System Name | RHEL Version | Environment | Remediation Available |

## Already Patched (No Action Needed)
[list]

## Next Steps
- Use `/remediation` skill for remediation
- Use cve-impact for severity analysis
```

## Template 3: Environment-Filtered View

**User Request**: "Show me production systems"

```markdown
# Production Systems Inventory

Filtered by tag: "production"

## Production Fleet Summary
- **Total**: N
- **RHEL 9.x / 8.x / 7.x** breakdown
- **Active / Stale** counts

## System Tiers
### Web Tier, Database Tier, Application Tier
[grouped lists]

## Stale System Alert ⚠️
[list with action: investigate Lightspeed client]

## Next Steps
- "Show CVEs affecting production systems"
- "Remediate CVE-X on production web tier"
```
