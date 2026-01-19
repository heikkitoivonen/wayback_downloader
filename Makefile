.PHONY: test types lint format check

test:
	uv run pytest -v

types:
	uv run pyright

lint:
	uv run ruff check .

format:
	uv run ruff format .

check: lint types test
