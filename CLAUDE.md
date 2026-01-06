# Claude Code Project Guide

This file contains important rules and workflows for maintaining the Wayback Machine Downloader project.

## Package Management

**ALWAYS use `uv` for all Python operations:**
- Installing dependencies: `uv sync` or `uv sync --dev`
- Running scripts: `uv run python wayback_downloader.py`
- Running tests: `uv run pytest`
- Running linter: `uv run ruff check .`
- Adding dependencies: `uv add <package>` or `uv add --dev <package>`

**Never use pip directly** - all dependencies are managed through `pyproject.toml` and `uv.lock`.

## Code Quality Requirements

### Before Every Commit

**1. Run the linter:**
```bash
uv run ruff check .
```

Auto-fix issues when possible:
```bash
uv run ruff check --fix .
```

**2. Format the code:**
```bash
uv run ruff format .
```

**3. Run all tests:**
```bash
uv run pytest -v
```

All three must pass before committing. No exceptions.

## Dependency Management

- **Single source of truth:** `pyproject.toml`
- Main dependencies go in `[project.dependencies]`
- Dev dependencies go in `[dependency-groups.dev]`
- **Never create requirements.txt** - it was removed in favor of pyproject.toml

## Testing

- All tests in `test_wayback_downloader.py`
- Use pytest with pytest-mock for mocking
- **Minimum requirement:** All 34 tests must pass
- Tests should be run after ANY code changes
- Use `uv run pytest -v` for verbose output

## Git Workflow

### Commit Message Format

Follow the established pattern:
```
Brief imperative summary line

Detailed explanation:
- Bullet points for changes
- Include important details
- Mention test results

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

### Before Committing

1. ✅ Check linting: `uv run ruff check .`
2. ✅ Format code: `uv run ruff format .`
3. ✅ Run tests: `uv run pytest`
4. ✅ Review changes: `git status` and `git diff`

## Project Principles

1. **Generic, not specific:** Tool downloads any archived website, not just blogs
2. **No "blog" references:** Use generic terms like "site", "website", "content"
3. **Rate limiting:** Respect Internet Archive's servers (default 1s delay)
4. **MIT Licensed:** Code is open source under MIT
5. **Copyright holder:** Heikki Toivonen

## Code Style

- Follow Ruff's formatting (runs automatically)
- Use double quotes for strings
- Specific exception types (no bare `except:`)
- Type hints encouraged but not required
- Descriptive variable and function names

## Common Tasks

**Run the tool:**
```bash
uv run wayback_downloader.py "WAYBACK_URL" -o output_dir
```

**Full quality check:**
```bash
uv run ruff check . && uv run ruff format . && uv run pytest -v
```

**Add a new dependency:**
```bash
uv add package-name        # Production dependency
uv add --dev package-name  # Development dependency
```

## Important Files

- `wayback_downloader.py` - Main application code
- `test_wayback_downloader.py` - Unit tests (34 tests)
- `pyproject.toml` - Project metadata and dependencies
- `LICENSE.txt` - MIT License
- `README.md` - User documentation
- `.gitignore` - Excludes downloaded_site/, test_output/, .venv/, etc.

## What NOT to Do

❌ Don't use pip directly
❌ Don't create requirements.txt
❌ Don't commit without running tests
❌ Don't commit with linting errors
❌ Don't add "blog" references
❌ Don't skip the rate limiting
❌ Don't commit downloaded content (blog/, downloaded_site/)

## Quick Reference

| Task | Command |
|------|---------|
| Install deps | `uv sync --dev` |
| Run linter | `uv run ruff check .` |
| Fix lint issues | `uv run ruff check --fix .` |
| Format code | `uv run ruff format .` |
| Run tests | `uv run pytest -v` |
| Add dependency | `uv add package-name` |
| Add dev dependency | `uv add --dev package-name` |
| Run the tool | `uv run wayback_downloader.py "URL"` |

---

**Remember:** Quality over speed. Always run linter and tests before committing!
