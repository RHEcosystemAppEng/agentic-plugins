<!--
  Catalog fragment — maintain via create-collection workflow (assistant + maintainer + PR review).
  Golden sources: skills/*/SKILL.md, README.md, AGENTS.md, marketplace/rh-agentic-collection.yml
-->

Skills source authoritative content from official Red Hat documentation at runtime using `WebFetch`. No offline doc corpus is bundled; the pack stays lean and always reflects current Red Hat guidance.

Key reference sources used by skills:

- [Red Hat Product Life Cycles](https://access.redhat.com/product-life-cycles/) — lifecycle phases and dates
- [Red Hat CVE Database](https://access.redhat.com/security/security-updates/#/cve) — CVE metadata and severity ratings
- [Red Hat Security Advisories](https://access.redhat.com/errata/) — RHSA/RHBA/RHEA advisory detail
- [sos tool documentation](https://access.redhat.com/solutions/3592) — diagnostic collection
- [OCP must-gather](https://docs.redhat.com/en/documentation/openshift_container_platform/4.17/html/support/gathering-cluster-data) — OpenShift diagnostic data
- [AAP troubleshooting](https://docs.redhat.com/en/documentation/red_hat_ansible_automation_platform/2.6/html/troubleshooting_ansible_automation_platform/diagnosing-the-problem) — AAP log gathering
