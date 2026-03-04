# Sasta Claude Code

## Description

A coding assistant built for working with small (~7B) LLMs hosted locally.


## Setup

```bash
# Embedding model
ollama pull nomic-embed-text
```
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

## Verify indexing
```bash
# index a workspace
python -m sastac.index_workspace booklore ~/code/booklore

# verify the index
python scripts/verify_workspace_index.py booklore > index_verification.txt

# evaluate the index
python scripts/diagnose_index.py booklore > diagnostic.txt

# clear the index
python scripts/clear_workspace_index.py booklore
```


### System Requirements

* OS: Ubuntu 24.04.2 LTS
* CPU: 11th Gen Intel® Core™ i7-11800H × 16
* Memory: 16 GB
* GPU: NVIDIA GeForce RTX 3050 Laptop GPU (4GB VRAM)



