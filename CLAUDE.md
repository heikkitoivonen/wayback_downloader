# Claude Code Project Guide

This file contains important rules and workflows for maintaining the Wayback Machine Downloader project.

## Package Management

**ALWAYS use `uv` for all Python operations:**
- Installing dependencies: `uv sync --dev`
- Running scripts: `uv run python wayback_downloader.py`
- Adding dependencies: `uv add <package>` or `uv add --dev <package>`

**Never use pip directly** - all dependencies are managed through `pyproject.toml` and `uv.lock`.

## Before Every Commit

**Run `make check` before every commit. No exceptions.**

This runs linting, type checking, and all tests in sequence.

## Makefile Targets

| Target | Description |
|--------|-------------|
| `make test` | Run unit tests |
| `make types` | Run pyright type checker |
| `make lint` | Run ruff linter |
| `make format` | Format code with ruff |
| `make check` | Run lint, types, and test (required before commits) |

## Project Principles

1. **Generic, not specific:** Tool downloads any archived website, not just blogs
2. **No "blog" references:** Use generic terms like "site", "website", "content"
3. **Rate limiting:** Respect Internet Archive's servers (default 1s delay)
4. **MIT Licensed:** Code is open source under MIT
5. **Copyright holder:** Heikki Toivonen

## Code Style

- Follow Ruff's formatting (runs automatically via `make format`)
- Use double quotes for strings
- Specific exception types (no bare `except:`)
- Type hints encouraged but not required
- Descriptive variable and function names

## Important Files

- `wayback_downloader.py` - Main application code
- `test_wayback_downloader.py` - Unit tests
- `pyproject.toml` - Project metadata and dependencies
- `Makefile` - Build and quality check targets
- `LICENSE.txt` - MIT License
- `README.md` - User documentation

## What NOT to Do

- Don't use pip directly
- Don't create requirements.txt
- Don't commit without running `make check`
- Don't add "blog" references
- Don't skip the rate limiting
- Don't commit downloaded content (blog/, downloaded_site/)
