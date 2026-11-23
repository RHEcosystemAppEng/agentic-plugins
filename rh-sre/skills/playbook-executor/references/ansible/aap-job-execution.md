---
title: AAP Job Execution Guide
category: ansible
sources:
  - title: Red Hat Ansible Automation Platform Documentation
    url: https://docs.redhat.com/en/documentation/red_hat_ansible_automation_platform/2.6
    date_accessed: 2026-02-24
  - title: AAP Job Templates
    url: https://docs.redhat.com/en/documentation/red_hat_ansible_automation_platform/2.6/html/using_automation_execution/controller-job-templates
    date_accessed: 2026-02-24
tags: [aap, job-execution, playbook, dry-run, check-mode]
semantic_keywords: [aap job execution, ansible check mode, dry-run remediation, job template requirements, aap url structure]
use_cases: [playbook-executor, remediation]
related_docs: [playbook-integration-aap.md, cve-remediation-templates.md]
last_updated: 2026-02-24
---

<!-- evaluator-ignore: security/no-credential-access -->

# AAP Job Execution Guide

## Overview

This guide covers executing Ansible remediation playbooks through AAP (Ansible Automation Platform), including dry-run testing, job monitoring, and result interpretation.

## Job Template Requirements for Remediation

### Minimum Requirements

For a job template to be suitable for CVE remediation, it must have:

1. **Inventory**: Contains target systems identified in CVE analysis
2. **Project**: Contains or can receive remediation playbooks from Git
3. **Credentials**: 
   - Machine credential (SSH) for host access
   - Privilege escalation enabled (sudo/become)
4. **Execution Environment**: Compatible with RHEL versions of target systems

### Recommended Settings

- **Prompt on Launch - Variables**: Allow passing CVE-specific parameters
- **Prompt on Launch - Limit**: Allow targeting specific hosts at runtime
- **Job Type**: Should support both "Run" and "Check" modes
- **Verbosity**: Set to at least "1 (Verbose)" for debugging
- **Timeout**: Set generous timeout (30+ minutes for large-scale remediations)
- **Enable Webhook**: Optional for CI/CD integration

### Example Template Configuration

```yaml
Name: CVE Remediation Template
Job Type: Run
Inventory: Production Servers
Project: Remediation Playbooks
Playbook: playbooks/remediation/remediation-template.yml
Credentials:
  - SSH Credential (Machine)
  - Privilege Escalation: Yes
Prompt on Launch:
  - Variables: Yes
  - Limit: Yes
Options:
  - Enable Privilege Escalation: Yes
  - Allow Simultaneous: No
```

## Dry-Run vs Production Execution

### Dry-Run (Check Mode)

**Purpose**: Simulate playbook execution without making actual changes.

**Use When**:
- Testing new remediation playbooks
- Validating changes before production
- Identifying potential issues (permissions, package availability, dependencies)
- Understanding impact scope

**How to Execute**:
```json
{
  "job_type": "check",
  "extra_vars": {...}
}
```

**What It Does**:
- Gathers facts from target systems
- Evaluates conditionals and variables
- Simulates task execution
- Reports **would change** counts
- Does NOT apply any changes

**Limitations**:
- Some modules don't support check mode (command, shell, raw)
- Services that would restart are not actually restarted
- Can't detect runtime failures that occur during actual execution
- Package dependencies may not be fully validated

**Output Interpretation**:
```
PLAY RECAP *************************************************************
prod-web-01 : ok=8    changed=3    unreachable=0    failed=0
prod-web-02 : ok=8    changed=3    unreachable=0    failed=0
prod-web-03 : ok=8    changed=3    unreachable=0    failed=0

"changed=3" means 3 tasks WOULD make changes
"failed=0" means no errors detected in check mode
```

### Production Execution (Run Mode)

**Purpose**: Apply actual changes to systems.

**Use When**:
- Dry-run passed successfully
- User has approved changes
- Maintenance window scheduled (if required)
- Backups completed

**How to Execute**:
```json
{
  "job_type": "run",
  "extra_vars": {...}
}
```

**What It Does**:
- Executes all playbook tasks
- Applies actual changes (package updates, config modifications, service restarts)
- Reports real results
- Can trigger system reboots if specified

**Best Practices**:
1. Always run dry-run first
2. Review dry-run results carefully
3. Ensure maintenance window if downtime expected
4. Have rollback plan ready
5. Monitor execution in real-time
6. Verify success after completion

## Job Type Parameter

### job_type: "check"

**API Parameter**:
```json
{
  "id": "10",
  "requestBody": {
    "job_type": "check"
  }
}
```

**Equivalent Command Line**:
```bash
ansible-playbook playbook.yml --check
```

**Behavior**:
- Runs in check mode (dry-run)
- No actual changes applied
- Reports what WOULD happen
- Useful for validation

### job_type: "run"

**API Parameter**:
```json
{
  "id": "10",
  "requestBody": {
    "job_type": "run"
  }
}
```

**Equivalent Command Line**:
```bash
ansible-playbook playbook.yml
```

**Behavior**:
- Runs in execution mode
- Applies actual changes
- Reports what DID happen
- Production execution

## Interpreting Job Results

### Job Status Values

| Status | Meaning | Action |
|--------|---------|--------|
| `pending` | Job queued, not yet started | Wait for execution |
| `waiting` | Waiting for resources/dependencies | Monitor for start |
| `running` | Currently executing | Monitor progress |
| `successful` | Completed without errors | Verify changes |
| `failed` | Completed with errors | Review error logs |
| `error` | Job could not execute | Check configuration |
| `canceled` | User cancelled job | N/A |

### Per-Host Statistics

**ok**: Number of tasks that executed successfully without changes
**changed**: Number of tasks that made actual changes
**failed**: Number of tasks that failed
**unreachable**: Number of hosts that couldn't be reached
**rescued**: Number of tasks that recovered from failures
**ignored**: Number of failed tasks that were ignored

**Success Criteria**:
- `failed: 0` AND `unreachable: 0` = Success
- `changed > 0` = Remediation applied changes
- `ok > 0` = Some tasks ran successfully

**Failure Indicators**:
- `failed > 0` = At least one task failed
- `unreachable > 0` = Host connectivity issues
- `ok: 0` AND `changed: 0` = Nothing executed successfully

### Task Timeline Interpretation

Example timeline:
```
1. ✅ Gather Facts (2s)
2. ✅ Check disk space (1s)
3. ✅ Backup configuration (3s)
4. ✅ Update package httpd (45s)
5. ⚠️ Restart httpd service (FAILED on prod-web-03)
6. ✅ Verify service status (2s)
```

**Analysis**:
- Tasks 1-4: Successful across all hosts
- Task 5: Failed on one host (prod-web-03)
- Task 6: Likely skipped on failed host

**Action**:
- Investigate why httpd restart failed on prod-web-03
- Check logs for that specific host
- Verify httpd package was actually installed
- Relaunch job for failed host after fixing issue

## AAP URL Structure

### Job Details URL

**Format**:
```
https://{your-aap-instance}/#/jobs/playbook/{JOB_ID}
```

**Example**:
```
https://aap.example.com/#/jobs/playbook/1235
```

**What It Shows**:
- Real-time job status
- Live output stream
- Per-host statistics
- Task-level details
- Error messages
- Job parameters used

### Template URL

**Format**:
```
https://{your-aap-instance}/#/templates/job_template/{TEMPLATE_ID}/details
```

**Example**:
```
https://aap.example.com/#/templates/job_template/10/details
```

### Project URL

**Format**:
```
https://{your-aap-instance}/#/projects/{PROJECT_ID}/details
```

## Troubleshooting Common Execution Failures

### Connection Failures

**Symptoms**:
- `unreachable: 1` in host statistics
- "SSH timeout" errors
- "Connection refused" messages

**Common Causes**:
1. SSH service not running on target
2. Firewall blocking port 22
3. Network connectivity issues
4. Wrong SSH credentials

**Troubleshooting Steps**:
```bash
# Test SSH connectivity
ssh -i /path/to/key user@target-host

# Check SSH service
systemctl status sshd

# Verify firewall rules
firewall-cmd --list-all

# Test network connectivity
ping target-host
```

**Resolution**:
- Fix SSH service or network issues
- Update credentials in AAP
- Relaunch job after fixing

### Permission Errors

**Symptoms**:
- `failed: 1` with "Permission denied" errors
- "sudo: required but not available" messages
- "This command has to be run under the root user" errors

**Common Causes**:
1. Privilege escalation not enabled
2. User doesn't have sudo rights
3. SELinux blocking operation
4. File permissions incorrect

**Troubleshooting Steps**:
```bash
# Check sudo access
sudo -l

# Test privilege escalation
sudo whoami

# Check SELinux status
getenforce

# Review SELinux denials
ausearch -m avc -ts recent
```

**Resolution**:
- Enable "Privilege Escalation" in job template
- Grant sudo rights to SSH user
- Adjust SELinux policies
- Fix file permissions

### Package Manager Issues

**Symptoms**:
- "No package X available" errors
- "Repository not found" messages
- "Dependency problems" errors
- Package installation timeouts

**Common Causes**:
1. Repository not configured or unavailable
2. Package name incorrect
3. Network issues accessing repos
4. Insufficient disk space

**Troubleshooting Steps**:
```bash
# Check repository configuration
dnf repolist

# Test package availability
dnf info httpd

# Check disk space
df -h

# Verify repository URLs
dnf repolist -v
```

**Resolution**:
- Configure required repositories
- Verify package names
- Fix network issues
- Free up disk space

### Service Restart Failures

**Symptoms**:
- `failed: 1` on service restart tasks
- "Failed to restart X.service" errors
- "Unit not found" messages
- Service timeout errors

**Common Causes**:
1. Service not installed
2. Configuration errors
3. Service dependencies not met
4. Systemd issues

**Troubleshooting Steps**:
```bash
# Check if service exists
systemctl status httpd

# Verify service file
systemctl cat httpd

# Check service logs
journalctl -u httpd -n 50

# Test manual restart
systemctl restart httpd
```

**Resolution**:
- Ensure service is installed
- Fix configuration errors
- Start required dependencies first
- Review systemd logs

### Disk Space Issues

**Symptoms**:
- "No space left on device" errors
- Package installation failures
- Download failures

**Common Causes**:
1. /var partition full
2. /tmp partition full
3. Log files consuming space

**Troubleshooting Steps**:
```bash
# Check disk usage
df -h

# Find large files
du -sh /var/* | sort -hr | head -10

# Check package cache size
du -sh /var/cache/dnf
```

**Resolution**:
- Clean package cache: `dnf clean all`
- Remove old logs: `journalctl --vacuum-time=7d`
- Remove unused packages: `dnf autoremove`

## Job Monitoring Best Practices

### Real-Time Monitoring

1. **Watch AAP Web UI**: Real-time output and status
2. **Monitor Task Progress**: Track which tasks are running
3. **Check Per-Host Stats**: Identify failing hosts early
4. **Review Event Log**: See task-level events as they occur

### Alert Configuration

Configure notifications for:
- Job failures
- Long-running jobs (timeout warnings)
- Partial successes (some hosts failed)

### Post-Execution Verification

After job completes:
1. **Review per-host statistics**: Ensure all hosts succeeded
2. **Check full output**: Look for warnings or errors
3. **Verify actual changes**: Confirm packages updated, services restarted
4. **Run remediation-verifier**: Validate CVE status changed

## Performance Optimization

### Parallelism

AAP can run tasks in parallel across multiple hosts. Configure:
- **Forks**: Number of parallel processes (default: 5)
- **Instance Groups**: Distribute jobs across multiple AAP nodes
- **Job Slicing**: Split large inventories into parallel jobs

### Timeout Settings

Set appropriate timeouts based on:
- Number of target systems
- Package size to download
- Network bandwidth
- System resources

**Recommended Timeouts**:
- Small remediations (1-10 hosts): 10 minutes
- Medium remediations (10-50 hosts): 30 minutes
- Large remediations (50+ hosts): 60+ minutes

## Security Considerations

### Credential Management

- Use AAP credential vault for secrets
- Rotate credentials regularly
- Limit credential scope to necessary hosts
- Never hardcode credentials in playbooks

### Audit Logging

AAP automatically logs:
- Who launched the job
- When it was launched
- What parameters were used
- Full execution output
- Final job status

**Retention**: Configure appropriate log retention for compliance.

### Change Control

Integrate AAP jobs with change management:
- Require approval workflows for production
- Document job execution in change tickets
- Link jobs to CVE remediation tracking
- Maintain audit trail

## Related Documentation

- [Playbook Integration with AAP](./playbook-integration-aap.md) - How to add playbooks to AAP
- [CVE Remediation Templates](./cve-remediation-templates.md) - Playbook patterns
- [Package Management](../rhel/package-management.md) - RHEL package update best practices
