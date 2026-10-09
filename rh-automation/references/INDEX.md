# Documentation Index

Navigation guide for the rh-automation knowledge base. Runtime copies live under each skill's `references/` directory (canonical files plus shared-pool symlinks). This plugin index maps those files for repository navigation.

## How Documents Are Used

```
User Request → Agent → Skill reads document → Skill queries MCP tools → Skill interprets with document knowledge → Output with Red Hat citations
```

Paths in `.ai-index/` are plugin-relative (from `rh-automation/`).

## Document Map

### AAP Category

Platform governance, execution, and troubleshooting references for Ansible Automation Platform.

| Document | Purpose | Skills That Read It | Red Hat Sources |
|----------|---------|-------------------|----------------|
| [governance-readiness.md](../skills/governance-readiness-assessor/references/aap/governance-readiness.md) | 7-domain platform governance assessment | `governance-readiness-assessor` | 8 sources (Security Best Practices, Workflows, Notifications, RBAC, Instance Groups, Activity Stream, EE Guide, Hardening Guide) |
| [execution-governance.md](../skills/execution-risk-analyzer/references/aap/execution-governance.md) | Risk classification, check mode, rollback, phased rollout | `execution-risk-analyzer`, `governed-job-launcher` | 5 sources (Job Templates, Security Best Practices, Workflows, Check Mode, Controller Best Practices) |
| [job-troubleshooting.md](../skills/job-failure-analyzer/references/aap/job-troubleshooting.md) | Event parsing, host correlation, failure patterns | `job-failure-analyzer`, `host-fact-inspector` | 3 sources (Troubleshooting Guide, Job Events, Administration Guide) |

### Error classification

Cross-cutting reference material used across multiple use cases.

| Document | Purpose | Skills That Read It | Red Hat Sources |
|----------|---------|-------------------|----------------|
| [error-classification.md](../skills/resolution-advisor/references/error-classification.md) | Error taxonomy, classification trees, resolution paths | `resolution-advisor` | 3 sources (Troubleshooting Guide, Ansible Module docs, Administration Guide) |

## Task-to-Document Mapping

| User Task | Primary Document | Secondary Document |
|-----------|-----------------|-------------------|
| "Assess governance readiness" | governance-readiness.md | -- |
| "Execute on production" | execution-governance.md | governance-readiness.md (optional pre-check) |
| "Analyze failed job" | job-troubleshooting.md | error-classification.md |
| "How to fix this error?" | error-classification.md | job-troubleshooting.md |

## Semantic Indexing

The `.ai-index/` directory contains pre-computed indexes for efficient document discovery:

- `semantic-index.json` -- Document metadata with semantic keywords
- `task-to-docs-mapping.json` -- Pre-computed document sets for common workflows
- `cross-reference-graph.json` -- Document relationship graph

See [SOURCES.md](SOURCES.md) for official Red Hat source attribution.
