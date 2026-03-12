# Sasta Claude

## Description

This project is an attempt at building a coding assistant built for working with small (~7B) LLMs hosted locally. The hypothesis is that you can get a _reasonable_ setup in place by just tweaking context and limiting your intents and constraints.


## Setup

```bash
# Embedding model
ollama pull nomic-embed-text
```
```bash
uv pip install -e ".[dev]"
```

## Configuration

The application configuration limits and logging preferences can be controlled via environment variables. By default, the application specifies the active environment using the `SASTAC_ENV` variable which defaults to `local`. It then attempts to load an environment configuration file dynamically from `env/{SASTAC_ENV}.env` relative to the project root. The `SASTAC_CONFIG_FILE` variable defined inside the targeted `.env` file explicitly tells the application which system defaults to load.

You can override the entire working environment or individually override specific settings via your terminal:

```bash
# Override the active targeted environment (loads `env/production.env` instead)
SASTAC_ENV=production python scripts/chat.py

# Manually override the environment file path entirely
SASTAC_ENV_FILE=/custom_path/custom.env python scripts/chat.py

# Override the log level (default: INFO)
SASTAC_LOG_LEVEL=DEBUG python scripts/chat.py
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

### Running task workflow
```bash
python -m sastac.llm.workflow
```

### System Requirements

* OS: Ubuntu 24.04.2 LTS
* CPU: 11th Gen Intel® Core™ i7-11800H × 16
* Memory: 16 GB
* GPU: NVIDIA GeForce RTX 3050 Laptop GPU (4GB VRAM)
