# Sasta Claude Code

## Description

A coding assistant built for working with small (~7B) LLMs hosted locally.


## Setup

```bash
uv pip install -e ".[dev]"
```

## Test

```bash
# all tests
uv run pytest

# specific test
uv run pytest tests/unit/sastac/ast/test_parser.py
```

## Updating dependencies

```bash
# Add project dependency
uv add tree-sitter

# Add dev dependency
uv add --dev pytest

# Create lockfile from pyproject.toml
uv lock

# Install packages from lock file
uv sync --all-extras
```
