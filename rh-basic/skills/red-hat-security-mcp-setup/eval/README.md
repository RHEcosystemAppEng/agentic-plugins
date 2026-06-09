# E2E Test for /red-hat-security-mcp-setup

Interactive end-to-end test that validates the complete skill workflow with human authentication.

## Overview

This E2E test **actually runs the skill** and verifies the entire MCP setup workflow including:
- ✅ Skill invocation via Claude Code
- ✅ MCP server registration
- ✅ SSO authentication (human-in-the-loop)
- ✅ Authenticated MCP tool access

## Running the Test

```bash
cd rh-basic/skills/red-hat-security-mcp-setup
./eval/claude-setup-eval.sh
```

**Requirements:**
- Claude Code CLI (`claude` command)
- Red Hat account for SSO authentication
- Internet connectivity

**Time:** ~5-10 minutes (includes human authentication steps)

## Test Flow

### Test 1: Create Test Project
- Creates a temporary Git project at `eval/test-project/`
- Initializes with README and initial commit

### Test 2: Invoke /red-hat-security-mcp-setup Skill
- Programmatically installs skill: copies to `.claude/skills/` in test project
- Invokes skill via: `echo '/red-hat-security-mcp-setup' | claude`
- Skill executes and performs MCP setup
- Output logged to `skill-execution.log`
- **Validates** skill added the MCP server (`claude mcp list`)
- **CRITICAL:** Test fails and exits if MCP server not added

### Test 3: Perform Authentication
- Sends CVE query via `echo "..." | claude` to trigger authentication
- **Human action required:** Complete Red Hat SSO login in browser
- Test waits for confirmation you completed login
- Output logged to `auth-test.log`

### Test 4: Verify Authenticated Access
- Sends test query requesting CVE data via MCP server
- Validates response contains CVE information (not auth errors)
- Output logged to `verify-auth.log`

### Test 5: Cleanup
- Preserves logs in `eval/` directory
- Deletes test project
- MCP server remains registered (user can remove manually if desired)

## Example Output

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Red Hat Security MCP Setup - E2E Test
  Human-in-the-loop skill validation
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Checking prerequisites...

✓ PASSED: Claude CLI detected
✓ PASSED: git detected

━━━ Test 1: Create Test Project ━━━

ℹ Creating test project at: eval/test-project
✓ PASSED: Test project created successfully

━━━ Test 2: Invoke /red-hat-security-mcp-setup Skill ━━━

ℹ Starting Claude Code with the skill invocation...
➜ Ready to invoke the skill? This will open Claude Code interactively.
Press Enter to continue...

ℹ Executing: claude prompt '/red-hat-security-mcp-setup'
─────────────────────────────────────────────────────────
[Skill output appears here...]
─────────────────────────────────────────────────────────

✓ PASSED: Skill execution completed

━━━ Test 3: Verify MCP Server & Authentication ━━━

ℹ Checking if red-hat-security MCP server was added...
✓ PASSED: red-hat-security MCP server is registered

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Authentication Required
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ℹ The next step requires SSO authentication with Red Hat Customer Portal.
➜ Ready to trigger authentication? (Browser will open for Red Hat SSO)
Press Enter to continue...

ℹ Executing: claude prompt 'List 5 CVEs for Red Hat Enterprise Linux 9'
─────────────────────────────────────────────────────────
[Authentication triggered, browser opens...]
─────────────────────────────────────────────────────────

➜ Did you complete the Red Hat SSO authentication? (Press Enter when done)

━━━ Test 4: Verify MCP is Authenticated ━━━

ℹ Sending a test query to verify authentication...
ℹ Executing: claude prompt 'Give me the latest CVE for Red Hat Enterprise Linux...'
─────────────────────────────────────────────────────────
[CVE data returned from MCP...]
─────────────────────────────────────────────────────────

✓ PASSED: MCP server is authenticated and responding with CVE data

━━━ Test 5: Cleanup Test Project ━━━

⚠ The MCP server 'red-hat-security' is still registered in Claude Code.
➜ Ready to delete the test project? Logs will be preserved in eval/
Press Enter to continue...

✓ PASSED: Test project deleted

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  E2E Test Summary
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✓ ALL TESTS PASSED

The /red-hat-security-mcp-setup skill successfully:
  1. ✓ Guided MCP server setup
  2. ✓ Registered red-hat-security MCP server
  3. ✓ Completed SSO authentication
  4. ✓ Verified authenticated access to CVE data

Detailed report saved to: eval/eval-report.txt
```

## Generated Artifacts

After running the test:

- **eval-report.txt** - Complete test results and validation log
- **skill-execution.log** - Output from `/red-hat-security-mcp-setup` skill invocation
- **auth-test.log** - Output from authentication trigger
- **verify-auth.log** - Output from authenticated access verification

## What Gets Tested

| Component | Validation |
|-----------|------------|
| **Skill invocation** | `/red-hat-security-mcp-setup` executes without errors |
| **MCP registration** | `claude mcp list` shows `red-hat-security` server |
| **Authentication** | Browser SSO flow completes (human verification) |
| **MCP tool access** | Queries return CVE data, not auth errors |
| **Cleanup** | Test artifacts removed, logs preserved |

## Human Interaction Required

This test requires human interaction at two points:

1. **Confirming readiness** - Before each test stage
2. **SSO authentication** - Completing Red Hat login in browser (Test 3)

The test will pause and wait for you to complete these steps.

## Cleanup

The test automatically:
- ✅ Deletes the test project directory
- ✅ Preserves all logs in `eval/` directory

The `red-hat-security` MCP server **remains registered** after the test. To remove it:

```bash
claude mcp remove red-hat-security
```

## Troubleshooting

### Authentication fails
- Verify you have an active Red Hat account at [console.redhat.com](https://console.redhat.com)
- Check your internet connection
- Ensure no corporate firewall blocks `security-mcp.api.redhat.com`

### Skill doesn't execute
- Verify Claude Code CLI is installed: `claude --version`
- Check you're in the correct directory
- Ensure the skill is available in your Claude environment

### Review logs for details
```bash
cat eval/skill-execution.log    # What the skill returned
cat eval/auth-test.log           # Authentication trigger output
cat eval/verify-auth.log         # Authenticated query output
cat eval/eval-report.txt         # Complete test report
```

## CI/CD Note

This test requires **human authentication** and is **not suitable for automated CI/CD**. It's designed for:
- Manual skill validation during development
- QA testing before releases
- Verifying the end-to-end user experience

For automated testing without human interaction, use structure validation tests instead.
