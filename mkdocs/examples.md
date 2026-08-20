# Examples

Docs-only headers. This repo does not ship finished hook scripts.

## Silent ruff

Strict lint default: require `ruff`, check staged Python files (and
shebang matches), abort on tool failure.

```python
REQUIRED_COMMANDS = ["ruff"]
TOOL = ["ruff", "check"]
FILE_EXTENSIONS = [".py"]
SHEBANG_PATTERN = r"python3?"
```

## Confirm commits to master

Prompt only on `master`. When `/dev/tty` is unavailable (IDE / Cursor),
skip the prompt so the commit is not blocked.

```python
UPFRONT_PROMPT = "Are you sure you want to commit to master? [Yes/No] "
UPFRONT_WHEN = lambda: current_branch() == "master"
ON_NO_TTY_UPFRONT = "skip"
```

Leave `TOOL` unset for a prompt-only hook. The engine still requires
`git`, runs the upfront prompt when the predicate is true, and does not
list or check staged files.
