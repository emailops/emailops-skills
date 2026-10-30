.PHONY: check test version hooks

# Check every skill: the EmailOps app's SKILL.md rules, allowed files, example-only addresses
check:
	python3 scripts/check.py

# The validator's own tests
test:
	uv run --no-project --with pytest pytest -q scripts/tests

# Agent skills changed since BASE (default main)? Then the plugin's version must be higher
version:
	python3 scripts/check_version.py $(or $(BASE),main)

# Run check before every commit and the version check before every push
hooks:
	git config core.hooksPath .githooks
