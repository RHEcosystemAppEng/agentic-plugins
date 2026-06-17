# Examples - Agentic Contribution Skill

## Example 1: Creating a VM Backup Skill for rh-virt

**User Query**: "Create skill for rh-virt to backup VMs"

**Skill Interaction**:

```
Agentic-Contribution-Skill:
What does it do? For which Red Hat product(s) is this skill targeted?
> "Create VM backups using snapshots for OpenShift Virtualization"

What role uses it?
> "Virt admins"

✅ Detected pack: rh-virt. Use it? (yes/no)
> yes

What MCP tools does this skill need?

Reading rh-virt/mcps.json...

Available MCPs in rh-virt:
- openshift-virtualization (VM management, snapshots)
- openshift-administration (cluster resources, pods, namespaces)

Will you use existing MCPs, need new ones, or both?
> "Use openshift-virtualization: vm-snapshot-create, vm-snapshot-get"

Verifying tools exist in openshift-virtualization MCP...
✅ Verified: virtualmachinesnapshot_create, virtualmachinesnapshot_get exist

Operation type? (read-only/additive/destructive)
> "additive"

Color mapping:
🔵 cyan - Read-only: list VMs, view snapshot status
🟢 green - Additive: create snapshot, create VM, add backup
🔵 blue - Reversible: restart VM, pause snapshot
🟡 yellow - Destructive but recoverable: delete old snapshot
🔴 red - Critical: restore VM from snapshot, delete VM

For "create VM snapshot": green (additive operation)

✅ Color: green

Skill name? (kebab-case)
> "vm-backup-create"

✅ Name is representative of purpose (VM backup using snapshots for OpenShift Virtualization)
✅ Unique in rh-virt

3-5 user phrases for 'Use when':
> - "Backup VM database-01"
> - "Create snapshot before upgrade"
> - "Save VM state for recovery"

NOT for?
> "NOT for restoring (use vm-snapshot-restore)"

Workflow steps with MCP tools:
> 1. Validate VM exists - resources_get
> 2. Check storage supports snapshots - storageclasses_list
> 3. Create snapshot - virtualmachinesnapshot_create
> 4. Monitor until ready - virtualmachinesnapshot_get

3+ common issues:
> "Snapshot fails: Storage doesn't support: Use snapshot-capable storage"
> "VM not found: Wrong namespace: Verify with oc project"
> "Stuck pending: CSI driver issue: Check openshift-storage pods"

## Review Before Generation

**Pack**: rh-virt | **Skill**: vm-backup-create | **Color**: green

**Purpose**: Create VM backups using snapshots for OpenShift Virtualization
**Red Hat Product**: OpenShift Virtualization

**Use When**:
- "Backup VM database-01"
- "Create snapshot before upgrade"
- "Save VM state for recovery"

**NOT for**: Restoring (use vm-snapshot-restore)

**Workflow**: 4 steps
**Common Issues**: 3 documented
**MCP Tools**: 2 tools (verified to exist)
**Human-in-the-Loop**: Yes

Proceed? (yes/no)
> yes

Reading SKILL_DESIGN_PRINCIPLES.md for compliant generation...
✅ I consulted SKILL_DESIGN_PRINCIPLES.md to ensure compliant generation.

Generating skill with production-ready quality...

✅ Generated: rh-virt/skills/vm-backup-create/SKILL.md
✅ Updated: rh-virt/AGENTS.md (intent routing)

Running validation...

✅ Tier 1: PASSED
✅ Tier 2: PASSED

## ✅ Skill Created
Production-ready quality

Ready to commit? (yes/no)
> yes

[Git workflow with confirmations]

🎉 Complete! PR created at: github.com/...

Thank you for contributing!
```

## Example 2: Non-representative Name Triggers AI Suggestions

```
Skill name? (kebab-case)
> "check-stuff"

⚠️ Not representative of purpose (monitor cluster health for OpenShift).

Suggestions:
1. cluster-health-monitor
2. ocp-health-check  
3. cluster-metrics-monitor

Choose (1-3) or provide your own:
> 1

✅ Using "cluster-health-monitor"
```

## Example 3: Importing an Existing Skill

```
User: "/agentic-contribution-skill"

Agentic-Contribution-Skill:
Are you creating a new skill from scratch, or importing an existing SKILL.md?
> "Import - I have a skill at ./my-skills/cluster-backup/SKILL.md"

Reading ./my-skills/cluster-backup/SKILL.md...

Analyzed: ./my-skills/cluster-backup/SKILL.md
Name: cluster-backup | Lines: 180 | Frontmatter: needs-fixes (missing model, color)
Suggested pack: ocp-admin (keywords: cluster, etcd, backup, restore)

No color in frontmatter. Analyzing operations...
Inferred color: red — Reason: skill performs etcd backup and restore, which are irreversible operations
Confirm? (yes/override)
> yes

Reading ocp-admin/mcps.json...
MCP tools referenced: resources_get, pods_exec, pods_log
✅ All 3 tools found in openshift-administration MCP server

Analyzed: ./my-skills/cluster-backup/SKILL.md
Name: cluster-backup | Lines: 180 | Frontmatter: needs-fixes (missing model, color)
Suggested pack: ocp-admin (keywords: cluster, etcd, backup, restore)
Color: red (inferred)
MCP tools: 3 verified, 0 not found
Missing sections: Prerequisites, Dependencies

Proceed with adaptation? (yes/no/try another file)
> yes

Reading SKILL_DESIGN_PRINCIPLES.md for compliant adaptation...
✅ I consulted SKILL_DESIGN_PRINCIPLES.md to ensure compliant adaptation.

Adapting skill:
✅ Added model: inherit
✅ Added color: red (confirmed by user)
✅ Added Prerequisites section with verification
✅ Added Dependencies section (MCP servers, tools)
✅ Fixed section ordering per DP7

Placing file: ocp-admin/skills/cluster-backup/SKILL.md
Updating: ocp-admin/AGENTS.md (intent routing)

Summary of changes:
- Frontmatter: added model, color, metadata
- Added 2 missing sections (Prerequisites, Dependencies)
- Reordered sections to match DP7
- Original content preserved

Confirm changes? (yes/no)
> yes

Running validation...

✅ Tier 1: PASSED
✅ Tier 2: PASSED

## ✅ Skill Imported

Files:
✅ ocp-admin/skills/cluster-backup/SKILL.md (210 lines)
✅ ocp-admin/AGENTS.md (intent routing updated)

Ready to commit? (yes/no)
> yes

[Git workflow with confirmations]
```

## Example 4: Large Skill Requires docs/ Folder

```
[After Phase 2 - Definition]

Workflow steps:
> 15 steps covering validation, backup, upgrade, monitoring, and rollback

💡 **Modularity Assessment**:
This skill has 15 steps. Options:
1. Single comprehensive skill (recommended for critical/cohesive workflows)
2. Subdivide into 3 modular skills (validation, execution, reporting)

For critical operations like cluster upgrades, option 1 keeps all HITL checkpoints in one place.

Default: Option 1. Subdivide? (yes/no)
> no

Proceeding with single comprehensive skill...

[Generation completes]

Running validation...

❌ Tier 1: FAILED - Line count exceeds 500 (got 1533)

**Iteration 1**: Moving detailed content to docs/ folder...

Creating docs/:
✅ docs/workflow-details.md (extended step explanations)
✅ docs/common-issues.md (full KB articles with solutions)
✅ docs/examples.md (comprehensive success/rollback scenarios)

Updating SKILL.md with references to docs/...

Running validation again...

✅ Tier 1: PASSED (323 lines)
✅ Tier 2: PASSED

## ✅ Skill Created (after 1 iteration)

**Files**:
✅ ocp-admin/skills/cluster-upgrade/SKILL.md (323 lines)
✅ ocp-admin/skills/cluster-upgrade/docs/workflow-details.md
✅ ocp-admin/skills/cluster-upgrade/docs/common-issues.md
✅ ocp-admin/skills/cluster-upgrade/docs/examples.md

**Quality**: Production-ready, comprehensive, validation compliant

Iterations: 1 (quality over speed achieved)
```
