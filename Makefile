.PHONY: help install validate validate-structure validate-collection-schema validate-collection-compliance validate-skill-design validate-skill-design-changed validate-mcp-tools package clean check-uv

help:
	@echo "agentic-plugins"
	@echo ""
	@echo "Available targets:"
	@echo "  install                       - Install Python dependencies (requires uv)"
	@echo "  validate                      - Full validation: Tier 1 (agentskills.io) + Tier 2 (structure, compliance, design)"
	@echo "  validate-structure            - Structure, links, compliance, MCP tools (no per-skill tier checks)"
	@echo "  validate-collection-schema    - Schema + roster + banners (subset of compliance)"
	@echo "  validate-collection-compliance - Full .catalog compliance (includes collection.json drift)"
	@echo "  validate-skill-design         - Validate all skills (use PACK=rh-sre for a specific pack)"
	@echo "  validate-skill-design-changed - Validate only changed skills (staged + unstaged, for local dev)"
	@echo "  validate-mcp-tools            - Validate allowed-tools against live MCP servers (requires podman)"
	@echo "  package                       - Package skills into ZIPs (output: dist/)"
	@echo "  clean                         - Remove generated files"
	@echo ""
	@echo "Requirements:"
	@echo "  uv - Install with: curl -LsSf https://astral.sh/uv/install.sh | sh"

check-uv:
	@command -v uv >/dev/null 2>&1 || { \
		echo "Error: uv is not installed"; \
		echo ""; \
		echo "Install uv with:"; \
		echo "  curl -LsSf https://astral.sh/uv/install.sh | sh"; \
		echo ""; \
		echo "Or visit: https://github.com/astral-sh/uv"; \
		exit 1; \
	}

install: check-uv
	@echo "Installing Python dependencies with uv..."
	@uv sync --group dev
	@echo "Dependencies installed in isolated environment (includes dev: pre-commit for git hooks)!"

validate: check-uv
	@EXIT=0; \
	echo ""; \
	echo "======================================================================"; \
	echo "  Skill Check Tier 1 — agentskills.io spec"; \
	echo "======================================================================"; \
	echo ""; \
	echo "=== Validating skills against agentskills.io spec..."; \
	uv run python scripts/validate_skills_tier1.py || EXIT=1; \
	echo ""; \
	echo "======================================================================"; \
	echo "  Skill Check Tier 2 — Structure, compliance, design principles"; \
	echo "======================================================================"; \
	echo ""; \
	echo "=== Validating agentic collection structure..."; \
	uv run python scripts/validate_structure.py || EXIT=1; \
	echo "=== Validating skill docs links..."; \
	uv run python scripts/validate_skill_doc_links.py || EXIT=1; \
	echo "=== Validating docs tree links..."; \
	uv run python scripts/validate_docs_tree_links.py || EXIT=1; \
	echo "=== Validating collection compliance (.catalog/)..."; \
	uv run python scripts/validate_collection_compliance.py || EXIT=1; \
	echo "=== Validating MCP tool references (skips gracefully without podman)..."; \
	uv run python scripts/validate_mcp_tools.py --summary-only --log-file .validate/mcp-tools.log || EXIT=1; \
	echo "=== Validating skill design principles..."; \
	uv run python scripts/validate_skills_tier2.py || EXIT=1; \
	echo ""; \
	echo "======================================================================"; \
	echo "  Validation complete!"; \
	echo "======================================================================"; \
	exit $$EXIT

validate-structure: check-uv
	@EXIT=0; \
	echo "=== Validating agentic collection structure..."; \
	uv run python scripts/validate_structure.py || EXIT=1; \
	echo "=== Validating skill docs links..."; \
	uv run python scripts/validate_skill_doc_links.py || EXIT=1; \
	echo "=== Validating docs tree links..."; \
	uv run python scripts/validate_docs_tree_links.py || EXIT=1; \
	echo "=== Validating collection compliance (.catalog/)..."; \
	uv run python scripts/validate_collection_compliance.py || EXIT=1; \
	echo "=== Validating MCP tool references (skips gracefully without podman)..."; \
	uv run python scripts/validate_mcp_tools.py --summary-only --log-file .validate/mcp-tools.log || EXIT=1; \
	echo "=== Validation complete!"; \
	exit $$EXIT

validate-collection-schema: check-uv
	@uv run python scripts/validate_collection_schema.py

validate-collection-compliance: check-uv
	@uv run python scripts/validate_collection_compliance.py

validate-skill-design: check-uv
	@uv run python scripts/validate_skills_tier2.py $(if $(PACK),$(PACK))

validate-skill-design-changed: check-uv
	@VALIDATE_INCLUDE_UNCOMMITTED=1 ./scripts/ci-validate-changed-skills.sh

validate-mcp-tools: check-uv
	@echo "Validating MCP tool references against live servers..."
	@uv run python scripts/validate_mcp_tools.py $(if $(PACK),$(PACK))
	@echo "MCP tool validation complete!"

package: check-uv
	@uv run python scripts/package_skills.py

clean:
	@echo "Cleaning generated files..."
	@rm -rf .validate/ dist/
	@echo "Cleaned!"
