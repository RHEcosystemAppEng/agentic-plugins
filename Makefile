.PHONY: help install validate validate-collection-schema validate-collection-compliance catalog-mirror-json validate-skill-design validate-skill-design-changed validate-mcp-tools validate-federated generate serve clean test test-full check-uv

help:
	@echo "agentic-collections Documentation Generator"
	@echo ""
	@echo "Available targets:"
	@echo "  install                       - Install Python dependencies (requires uv)"
	@echo "  validate                      - Pack structure + collection compliance + federated catalog cross-check"
	@echo "  validate-collection-schema    - Schema + roster + banners (subset of compliance)"
	@echo "  validate-collection-compliance - Full .catalog compliance (includes collection.json drift)"
	@echo "  catalog-mirror-json           - Regenerate all .catalog/collection.json from YAML"
	@echo "  validate-skill-design         - Validate all skills (use PACK=rh-sre for a specific pack)"
	@echo "  validate-skill-design-changed - Validate only changed skills (staged + unstaged, for local dev)"
	@echo "  validate-federated            - Tier 1 skill lint on external federated packs (heavy; catalog cross-check is in validate)"
	@echo "  validate-mcp-tools            - Validate allowed-tools against live MCP servers (requires podman)"
	@echo "  generate    - Generate docs/data.json"
	@echo "  serve       - Start local server on http://localhost:8000"
	@echo "  test        - Quick test (validate + generate + verify)"
	@echo "  test-full   - Full test suite (test + serve with browser open)"
	@echo "  clean       - Remove generated files"
	@echo "  update      - Full update (validate + generate)"
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
	@echo "Validating agentic collection structure..."
	@uv run python scripts/validate_structure.py
	@echo "Validating skill docs links..."
	@uv run python scripts/validate_skill_doc_links.py
	@echo "Validating docs tree links..."
	@uv run python scripts/validate_docs_tree_links.py
	@echo "Validating collection compliance (.catalog/)..."
	@uv run python scripts/validate_collection_compliance.py
	@echo "Validating federated catalog cross-check (clone external repos at pinned ref)..."
	@uv run python scripts/validate_federation_catalog_all.py
	@echo "Validating MCP tool references (skips gracefully without podman)..."
	@uv run python scripts/validate_mcp_tools.py
	@echo "✓ Validation complete!"

validate-collection-schema: check-uv
	@uv run python scripts/validate_collection_schema.py

validate-collection-compliance: check-uv
	@uv run python scripts/validate_collection_compliance.py

catalog-mirror-json: check-uv
	@uv run python scripts/catalog_yaml_to_json.py --all

validate-skill-design: check-uv
	@uv run python scripts/validate_skill_design.py $(if $(PACK),$(PACK))

validate-skill-design-changed: check-uv
	@VALIDATE_INCLUDE_UNCOMMITTED=1 ./scripts/ci-validate-changed-skills.sh

validate-mcp-tools: check-uv
	@echo "Validating MCP tool references against live servers..."
	@uv run python scripts/validate_mcp_tools.py $(if $(PACK),$(PACK))
	@echo "✓ MCP tool validation complete!"

validate-federated: check-uv
	@echo "Validating federated module skills (Tier 1, external clone)..."
	@uv run python scripts/fetch_federated_skills.py

generate: check-uv
	@echo "Generating documentation..."
	@uv run python scripts/build_website.py
	@echo "✓ Documentation generated in docs/"

serve: check-uv
	@echo "Starting local server on http://localhost:8000"
	@echo "Press Ctrl+C to stop the server"
	@cd docs && uv run python -m http.server 8000

clean:
	@echo "Cleaning generated files..."
	@rm -f docs/data.json
	@echo "✓ Cleaned!"

test: validate generate
	@echo ""
	@echo "Running verification checks..."
	@./scripts/test_local.sh
	@echo ""
	@echo "✓ All tests passed!"
	@echo ""
	@echo "To view the site locally, run: make serve"

test-full: test
	@echo ""
	@echo "Opening browser and starting server..."
	@(sleep 2 && open http://localhost:8000) &
	@make serve

update: validate generate
	@echo "✓ Documentation updated successfully!"
