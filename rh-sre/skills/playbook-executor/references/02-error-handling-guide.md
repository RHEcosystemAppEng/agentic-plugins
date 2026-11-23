# Step 02: Error Handling Guide

Read this reference when generating Phase 6 error reports or troubleshooting.

## Error Categories

**Parse error output** from `jobs_stdout_retrieve` for these common patterns:

1. **Connection Failures**: SSH timeout, host unreachable, authentication failed
2. **Permission Errors**: elevated privileges required, insufficient permissions, SELinux denials
3. **Package Manager Issues**: repo unavailable, package not found, dependency conflicts
4. **Service Failures**: service not found, restart failed, timeout
5. **Disk Space**: insufficient space for updates
6. **General Failures**: playbook syntax errors, task failures

## Error Report Template

```markdown
# Playbook Execution Failed

## Job Summary
**Job ID**: 1235
**Status**: ❌ Failed
**Duration**: 2m 45s
**Started**: 2026-02-24 15:35:02 UTC
**Failed At**: 2026-02-24 15:37:47 UTC
**Job Template**: CVE Remediation Template
**AAP URL**: [View in AAP](https://aap.example.com/#/jobs/playbook/1235)

## Per-Host Results
| Host | OK | Changed | Failed | Unreachable | Status |
|------|-----|---------|--------|-------------|--------|
| prod-web-01 | 8 | 3 | 0 | 0 | ✅ Success |
| prod-web-02 | 8 | 3 | 0 | 0 | ✅ Success |
| prod-web-03 | 5 | 0 | 1 | 0 | ❌ Failed |

**Summary**: 2 of 3 hosts succeeded, 1 failed

## Failed Tasks Details

### Host: prod-web-03

**Task**: Restart httpd service
**Error**: "Failed to restart httpd.service: Unit httpd.service not found."

**Error Category**: Service Failure

**Root Cause**: The httpd service is not installed or not recognized by systemd.

**Troubleshooting Steps**:
1. Check if httpd is installed:
   ```bash
   ssh prod-web-03 'rpm -q httpd'
   ```
2. If not installed, the package update may have failed:
   ```bash
   ssh prod-web-03 'dnf info httpd'
   ```
3. Check systemd service status:
   ```bash
   ssh prod-web-03 'systemctl status httpd'
   ```
4. Review package manager logs:
   ```bash
   ssh prod-web-03 'tail -50 /var/log/dnf.log'
   ```

**Recommended Action**: 
- Verify httpd package installation on prod-web-03
- Check if package update completed successfully
- Manually install httpd if needed: `dnf install httpd`
- Relaunch job for failed host only

## Console Output (Last 50 Lines)
<details>
<summary>Click to expand error context</summary>

[Relevant error output from jobs_stdout_retrieve]

</details>

## Relaunch Options

Would you like to:
1. **Relaunch for failed hosts only** - Run job again with limit="prod-web-03"
2. **Fix issues manually and relaunch** - Resolve problems first, then relaunch
3. **View full job output** - See complete execution logs
4. **Abort** - Stop remediation workflow

Please choose an option (1-4):
```

## Relaunch Parameters

**MCP Tool**: `jobs_relaunch_retrieve` (from aap-mcp-job-management)

**Parameters**:
```json
{
  "id": "1235",
  "requestBody": {
    "hosts": "failed",
    "job_type": "run"
  }
}
```

This relaunches the job for only the failed hosts.
