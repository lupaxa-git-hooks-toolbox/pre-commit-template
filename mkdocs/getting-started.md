# Getting started

## Requirements

-   Python 3.13 or newer on `PATH`
-   A Git working tree
-   The [multiplexer](https://github.com/lupaxa-git-hooks-toolbox/git-hooks-multiplexer)
    installed as `.git/hooks/pre-commit` if you want this file run as a subhook

## Copy the template

```bash
mkdir -p hooks/pre-commit
cp /path/to/pre-commit-template/src/pre-commit-template hooks/pre-commit/01-ruff
chmod +x hooks/pre-commit/01-ruff
```

A later setup tool will copy this same file from a hook repo.

## Fill the header

Set `REQUIRED_COMMANDS`, `TOOL`, and `FILE_EXTENSIONS`. Example:

```python
REQUIRED_COMMANDS = ["ruff"]
TOOL = ["ruff", "check"]
FILE_EXTENSIONS = [".py"]
```

Do not edit below `# STOP HERE`.

## First check

```bash
hooks/pre-commit/01-ruff
```

With no matching staged files the hook exits 0.
