#!/bin/bash
# E2E Test for /red-hat-security-mcp-setup skill
# Automated test with programmatic skill installation

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"
PACK_DIR="$(cd "$SKILL_DIR/../.." && pwd)"
TEST_PROJECT_DIR="${SCRIPT_DIR}/test-project-claude"
EVAL_REPORT="${SCRIPT_DIR}/eval-report-claude.txt"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# Test state
TEST_PASSED=true

echo ""
echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BOLD}  Red Hat Security MCP Setup - E2E Test${NC}"
echo -e "${BOLD}  Automated skill validation${NC}"
echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Initialize report
cat > "$EVAL_REPORT" <<EOF
Red Hat Security MCP Setup - E2E Test Report
Generated: $(date)
Skill: /red-hat-security-mcp-setup
Test Type: End-to-End Automated

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

EOF

log_test() {
    echo "$1" >> "$EVAL_REPORT"
}

fail_test() {
    echo -e "${RED}✗ FAILED:${NC} $1"
    log_test "FAILED: $1"
    TEST_PASSED=false
}

pass_test() {
    echo -e "${GREEN}✓ PASSED:${NC} $1"
    log_test "PASSED: $1"
}

info() {
    echo -e "${CYAN}ℹ${NC} $1"
}

prompt_user() {
    echo -e "${YELLOW}➜${NC} $1"
    read -p "Press Enter to continue..."
    echo ""
}

ask_user() {
    echo -e "${YELLOW}?${NC} $1"
    read -p "Enter y/n: " response
    echo ""
    [[ "$response" =~ ^[Yy] ]]
}

# Check prerequisites
echo -e "${BOLD}Checking prerequisites...${NC}"
echo ""

if ! command -v claude &> /dev/null; then
    fail_test "Claude CLI not found. Install from: https://claude.ai/code"
    echo ""
    echo "Report saved to: $EVAL_REPORT"
    exit 1
fi
pass_test "Claude CLI detected"

if ! command -v git &> /dev/null; then
    fail_test "git not found"
    echo ""
    echo "Report saved to: $EVAL_REPORT"
    exit 1
fi
pass_test "git detected"

echo ""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TEST 1: Create Test Project
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

echo -e "${BOLD}━━━ Test 1: Create Test Project ━━━${NC}"
echo ""
log_test "━━━ Test 1: Create Test Project ━━━"
log_test ""

# Clean up any existing test project
if [ -d "$TEST_PROJECT_DIR" ]; then
    info "Removing existing test project..."
    rm -rf "$TEST_PROJECT_DIR"
fi

# Create test project
info "Creating test project at: $TEST_PROJECT_DIR"
mkdir -p "$TEST_PROJECT_DIR"
cd "$TEST_PROJECT_DIR"

git init -q
echo "# MCP Setup E2E Test Project" > README.md
git add .
git commit -q -m "Initial commit"

if [ -d "$TEST_PROJECT_DIR/.git" ] && [ -f "$TEST_PROJECT_DIR/README.md" ]; then
    pass_test "Test project created successfully"
    log_test "  Location: $TEST_PROJECT_DIR"
else
    fail_test "Test project creation failed"
fi

# Install the skill in the test project
info "Installing red-hat-security-mcp-setup skill..."

SKILLS_DIR="$TEST_PROJECT_DIR/.claude/skills"
mkdir -p "$SKILLS_DIR"

# Copy the skill
cp -r "$SKILL_DIR" "$SKILLS_DIR/red-hat-security-mcp-setup"

if [ -f "$SKILLS_DIR/red-hat-security-mcp-setup/SKILL.md" ]; then
    pass_test "Skill installed in test project"
    log_test "  Skill path: $SKILLS_DIR/red-hat-security-mcp-setup/"
else
    fail_test "Failed to install skill in test project"
fi

# Copy CLAUDE.md from rh-basic pack for context
if [ -f "$PACK_DIR/CLAUDE.md" ]; then
    cp "$PACK_DIR/CLAUDE.md" "$TEST_PROJECT_DIR/.claude/"
    info "Copied pack CLAUDE.md for skill routing"
fi

echo ""
log_test ""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TEST 2: Invoke Skill via Claude (Interactive)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

echo -e "${BOLD}━━━ Test 2: Invoke /red-hat-security-mcp-setup Skill ━━━${NC}"
echo ""
log_test "━━━ Test 2: Invoke /red-hat-security-mcp-setup Skill ━━━"
log_test ""

echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}  Interactive Skill Invocation Required${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
info "This skill requires interactive approval for:"
info "  - Tool permissions (claude mcp add command)"
info "  - SSO authentication (browser-based Red Hat login)"
echo ""
info "A new Terminal window will open automatically with Claude running."
info "The skill command will be sent automatically."
info "You just need to approve permissions and complete SSO authentication."
echo ""

cd "$TEST_PROJECT_DIR"

echo -e "${CYAN}─────────────────────────────────────────────────────────${NC}"
echo -e "${BOLD}Test Project Location:${NC} $TEST_PROJECT_DIR"
echo ""
echo -e "${BOLD}What will happen:${NC}"
echo "  1. New Terminal window opens"
echo "  2. Claude starts in the test project"
echo "  3. /red-hat-security-mcp-setup is invoked automatically"
echo "  4. You approve tool permissions"
echo "  5. You complete SSO authentication in browser"
echo "  6. Close the Claude session when done"
echo "  7. Return here and press Enter"
echo -e "${CYAN}─────────────────────────────────────────────────────────${NC}"
echo ""

prompt_user "Ready to launch the interactive Claude session?"

info "Opening new Terminal window with Claude..."

# Create expect script to automate the skill invocation
EXPECT_SCRIPT="$SCRIPT_DIR/invoke-skill.exp"
cat > "$EXPECT_SCRIPT" <<'EXPECTEOF'
#!/usr/bin/env expect
set timeout -1
spawn claude
expect {
    -re ".*" {
        send "/red-hat-security-mcp-setup\r"
        interact
    }
}
EXPECTEOF
chmod +x "$EXPECT_SCRIPT"

# Use AppleScript to open new Terminal window and run the expect script
osascript <<APPLESCRIPT
tell application "Terminal"
    activate
    set newTab to do script "cd '$TEST_PROJECT_DIR' && '$EXPECT_SCRIPT'; echo ''; echo 'Skill invocation complete. You can close this window.'; echo 'Return to the test script and press Enter to continue.'"
end tell
APPLESCRIPT

echo ""
info "Terminal window opened with Claude running in test project"
info "The skill command has been sent automatically"
echo ""
prompt_user "After completing the skill (approvals + SSO), close the Claude window and press Enter here"

echo ""

# Validate MCP server was added
info "Validating that skill added the MCP server..."

MCP_GET_OUTPUT=$(claude mcp get red-hat-security 2>&1)

if echo "$MCP_GET_OUTPUT" | grep -q "https://security-mcp.api.redhat.com/mcp"; then
    pass_test "Skill successfully added red-hat-security MCP server"
    log_test "  Verified via: claude mcp get red-hat-security"
    echo "$MCP_GET_OUTPUT" >> "$EVAL_REPORT"
else
    echo -e "${YELLOW}⚠${NC} MCP server not found in configuration"
    echo ""
    echo "$MCP_GET_OUTPUT"
    echo ""

    if ask_user "Did the skill successfully add the red-hat-security MCP server?"; then
        pass_test "User confirmed MCP server was added"
        log_test "  User confirmed: MCP server added successfully"
    else
        fail_test "Skill did not add the MCP server"
        log_test "ERROR: MCP server not found"
        log_test ""
        log_test "Output:"
        echo "$MCP_GET_OUTPUT" >> "$EVAL_REPORT"
        log_test ""
        echo ""
        echo "Report saved to: $EVAL_REPORT"
        exit 1
    fi
fi

echo ""
log_test ""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TEST 3: Verify MCP Server Configuration
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

echo -e "${BOLD}━━━ Test 3: Verify MCP Server Configuration ━━━${NC}"
echo ""
log_test "━━━ Test 3: Verify MCP Server Configuration ━━━"
log_test ""

info "Checking MCP server status and authentication..."
echo ""

MCP_GET_OUTPUT=$(claude mcp get red-hat-security 2>&1)

echo -e "${CYAN}─────────────────────────────────────────────────────────${NC}"
echo "$MCP_GET_OUTPUT"
echo -e "${CYAN}─────────────────────────────────────────────────────────${NC}"
echo ""

# Check if server is registered
if echo "$MCP_GET_OUTPUT" | grep -q "https://security-mcp.api.redhat.com/mcp"; then
    pass_test "red-hat-security MCP server is registered"
    log_test "  Verified via: claude mcp get red-hat-security"

    # Check for authentication failure
    if echo "$MCP_GET_OUTPUT" | grep -iq "needs authentication\|! Needs authentication"; then
        fail_test "MCP server authentication failed"
        log_test "  Error: Server shows '! Needs authentication'"
        log_test "  The SSO authentication was not completed successfully"
        echo ""
        echo -e "${RED}Authentication failed. The skill did not complete SSO authentication.${NC}"
        echo ""
        echo "Report saved to: $EVAL_REPORT"
        exit 1
    # Check status/authentication
    elif echo "$MCP_GET_OUTPUT" | grep -iq "connected\|enabled\|authenticated"; then
        pass_test "MCP server appears authenticated/connected"
        log_test "  Status: Server shows as connected/authenticated"
    else
        echo -e "${YELLOW}⚠${NC} Cannot determine authentication status from output"

        if ask_user "Does the MCP server appear to be authenticated/connected in the output above?"; then
            pass_test "User confirmed MCP server is authenticated"
            log_test "  User confirmed: MCP server authenticated"
        else
            fail_test "MCP server may not be authenticated"
            log_test "  User reported: MCP server not authenticated"
        fi
    fi
else
    fail_test "red-hat-security MCP server not found in configuration"
    log_test "ERROR: MCP server not found"
    log_test ""
    log_test "Output:"
    echo "$MCP_GET_OUTPUT" >> "$EVAL_REPORT"
    log_test ""
    echo ""
    echo "Report saved to: $EVAL_REPORT"
    exit 1
fi

echo ""
log_test ""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TEST 4: Cleanup Test Project
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

echo -e "${BOLD}━━━ Test 4: Cleanup Test Project ━━━${NC}"
echo ""
log_test "━━━ Test 4: Cleanup Test Project ━━━"
log_test ""

# Remove MCP server
info "Removing red-hat-security MCP server..."

if claude mcp remove red-hat-security 2>&1; then
    pass_test "MCP server removed successfully"
    log_test "  Executed: claude mcp remove red-hat-security"
else
    echo -e "${YELLOW}⚠${NC} Could not remove MCP server (may already be removed)"
    log_test "WARNING: Failed to remove MCP server"
fi

echo ""

# Remove test project directory
prompt_user "Ready to delete the test project and cleanup logs?"

cd "$SCRIPT_DIR"

if [ -d "$TEST_PROJECT_DIR" ]; then
    rm -rf "$TEST_PROJECT_DIR"
    if [ ! -d "$TEST_PROJECT_DIR" ]; then
        pass_test "Test project deleted"
        log_test "  Deleted: $TEST_PROJECT_DIR"
    else
        fail_test "Failed to delete test project"
    fi
else
    info "Test project already removed"
fi

# Remove log files
info "Cleaning up log files..."

LOG_FILES=(
    "$EXPECT_SCRIPT"
    "$SCRIPT_DIR/skill-execution.log"
    "$SCRIPT_DIR/auth-test.log"
    "$SCRIPT_DIR/verify-auth.log"
)

for log_file in "${LOG_FILES[@]}"; do
    if [ -f "$log_file" ]; then
        rm -f "$log_file"
    fi
done

if [ ${#LOG_FILES[@]} -gt 0 ]; then
    pass_test "Log files cleaned up"
    log_test "  Removed expect script and test logs"
fi

echo ""
log_test ""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Final Summary
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BOLD}  E2E Test Summary${NC}"
echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

log_test ""
log_test "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log_test "SUMMARY"
log_test "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log_test ""

if [ "$TEST_PASSED" = true ]; then
    echo -e "${GREEN}${BOLD}✓ ALL TESTS PASSED${NC}"
    log_test "Result: ALL TESTS PASSED"
    echo ""
    echo "The /red-hat-security-mcp-setup skill successfully:"
    echo "  1. ✓ Installed in test project"
    echo "  2. ✓ Invoked interactively with user approvals"
    echo "  3. ✓ Registered and authenticated red-hat-security MCP server"
    EXIT_CODE=0
else
    echo -e "${RED}${BOLD}✗ SOME TESTS FAILED${NC}"
    log_test "Result: SOME TESTS FAILED"
    echo ""
    echo "Review the evaluation report for details:"
    echo "  - $EVAL_REPORT"
    EXIT_CODE=1
fi

echo ""
log_test ""
log_test "Report location:"
log_test "  - $EVAL_REPORT"

echo "Detailed report saved to: $EVAL_REPORT"
echo ""

exit $EXIT_CODE
