#!/usr/bin/env bash
#
# Install the repository git pre-commit hook via the pre-commit framework.
#
# This replaces the legacy behavior that wrote a gitleaks-only hook into
# .git/hooks/pre-commit. The single hook now delegates to pre-commit, which
# runs gitleaks plus scoped validation (see .pre-commit-config.yaml).
#

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "========================================="
echo "Git hooks (pre-commit)"
echo "========================================="
echo ""

if [ ! -d ".git" ]; then
    echo -e "${RED}Error: Not a git repository${NC}"
    echo "Run this script from the repository root (or use: scripts/install-hooks.sh from root)."
    exit 1
fi

if ! command -v uv >/dev/null 2>&1; then
    echo -e "${RED}Error: uv not found${NC}"
    echo "Install uv: https://docs.astral.sh/uv/getting-started/installation/"
    exit 1
fi

echo "Syncing dependencies (includes dev group: pre-commit)..."
uv sync --group dev
echo ""

HOOK_FILE=".git/hooks/pre-commit"
if [ -f "$HOOK_FILE" ] && ! grep -q 'pre-commit' "$HOOK_FILE" 2>/dev/null; then
    BACKUP="${HOOK_FILE}.backup-$(date +%Y%m%d-%H%M%S)"
    echo -e "${YELLOW}Backing up existing pre-commit hook (non-pre-commit) to:${NC} $BACKUP"
    mv "$HOOK_FILE" "$BACKUP"
    echo "The previous hook (e.g. gitleaks-only) is preserved; pre-commit will own the hook now."
    echo ""
fi

if ! command -v gitleaks >/dev/null 2>&1; then
    echo -e "${YELLOW}Gitleaks not found on PATH.${NC} The gitleaks-system hook needs it."
    echo "Install one of:"
    echo "  - macOS: brew install gitleaks"
    echo "  - https://github.com/gitleaks/gitleaks#installation"
    echo ""
    if [[ "${OSTYPE:-}" == darwin* ]] && command -v brew >/dev/null 2>&1; then
        echo "Installing gitleaks via Homebrew..."
        brew install gitleaks
    else
        echo -e "${YELLOW}Skipping automatic gitleaks install (unsupported OS or no brew).${NC}"
        echo "Install gitleaks, then re-run: scripts/install-hooks.sh"
    fi
    echo ""
else
    echo -e "${GREEN}✓${NC} Gitleaks: $(gitleaks version 2>/dev/null || echo ok)"
    echo ""
fi

echo "Installing pre-commit hook (writes .git/hooks/pre-commit)..."
uv run pre-commit install
echo ""

if [ ! -f ".gitleaks.toml" ]; then
    echo -e "${YELLOW}Warning: .gitleaks.toml not found${NC}"
else
    echo -e "${GREEN}✓${NC} Configuration found: .gitleaks.toml"
fi

echo ""
echo "========================================="
echo "Done"
echo "========================================="
echo "On commit, pre-commit runs (see .pre-commit-config.yaml):"
echo "  - gitleaks (secrets)"
echo "  - make validate (when roster/catalog-related paths change)"
echo "  - make validate-skill-design-changed (when plugin SKILL.md files change)"
echo ""
echo "CI source of truth for collection checks: .github/workflows/compliance-check.yml (make validate)."
echo "Manual: pre-commit run --all-files"
echo ""
