<p align="center">
    <a href="https://github.com/lupaxa-git-hooks-toolbox">
        <img src="https://raw.githubusercontent.com/the-lupaxa-project/brand-assets/master/logos/organisations/git-hooks-toolbox/readme-logo.png" alt="Organisation Logo" />
    </a>
</p>

<h1 align="center">Pre-Commit Template</h1>

One self-contained script. Copy it into `hooks/pre-commit/<name>`, edit the
header, and `chmod +x` it. No pip install. The
[multiplexer](https://github.com/lupaxa-git-hooks-toolbox/git-hooks-multiplexer)
runs it as a subhook.

Works as a silent lint (ruff, mypy, shellcheck, rubocop) or with optional
yes/no prompts on `/dev/tty`. Defaults make a copied file a strict, silent
no-op (require `git`, then exit 0) until `TOOL`, `run_check`, or
`UPFRONT_PROMPT` is set.

## Install

Python 3.13 or newer on `PATH`. The only file you need is
`src/pre-commit-template`. Install the multiplexer as `.git/hooks/pre-commit`
if you want this file run as a subhook.

```bash
mkdir -p hooks/pre-commit
cp src/pre-commit-template hooks/pre-commit/01-ruff
chmod +x hooks/pre-commit/01-ruff
```

Edit the header only. Leave everything below `# STOP HERE` alone.

```python
REQUIRED_COMMANDS = ["ruff"]
TOOL = ["ruff", "check"]
FILE_EXTENSIONS = [".py"]
```

With no matching staged files the hook exits 0. You can run it by hand:

```bash
hooks/pre-commit/01-ruff
```

## Header Knobs

| Name                      | Default     | Meaning                                                                              |
| :------------------------ | :---------- | :----------------------------------------------------------------------------------- |
| `REQUIRED_COMMANDS`       | `[]`        | Extra binaries that must exist on `PATH`. The engine always requires `git`.          |
| `TOOL`                    | `None`      | Argv prefix; matching files are appended. Empty list is unset.                       |
| `FILE_EXTENSIONS`         | `[]`        | Match suffix (e.g. `[".py", ".sh"]`). Empty means no extension filter.               |
| `SHEBANG_PATTERN`         | `None`      | Regex tested against the first line (e.g. `r"python3?"`).                            |
| `RUN_MODE`                | `"batch"`   | `"batch"`: one invocation with all files. `"each"`: one invocation per file.         |
| `UPFRONT_PROMPT`          | `None`      | Yes/no text on `/dev/tty` before the check. `None` = skip.                           |
| `UPFRONT_WHEN`            | `None`      | If a prompt is set: `None` means always; otherwise call the predicate.               |
| `CONFIRM_FINDINGS_PROMPT` | `None`      | Yes/no after a failed check. `None` = abort on failure.                              |
| `ON_MISSING_TOOL`         | `"abort"`   | `"abort"` or `"skip"` when a name in `REQUIRED_COMMANDS` is missing.                 |
| `ON_NO_TTY_UPFRONT`       | `"abort"`   | `"abort"` or `"skip"` when an upfront prompt cannot open `/dev/tty`.                 |
| `ON_NO_TTY_FINDINGS`      | `"abort"`   | `"abort"` or `"skip"` when a findings prompt cannot open `/dev/tty`.                 |
| `match_file`              | `None`      | `(path: str) -> bool` after the built-in filter; extra AND.                          |
| `run_check`               | `None`      | `(files: list[str]) -> int` instead of `TOOL`. Print your own output; return a code. |
| `should_upfront_prompt`   | `None`      | `() -> bool` instead of `UPFRONT_WHEN`.                                              |

A staged file is a candidate if it is readable. It then matches if:

-   `FILE_EXTENSIONS` and `SHEBANG_PATTERN` are both unset/empty → all readable
  staged files; or
-   its name ends with an extension **or** its shebang matches (either filter
  may be set alone).

`git` is never skipped. Missing `git` always aborts with exit 1, regardless
of `ON_MISSING_TOOL`. Unknown `RUN_MODE` or `ON_*` values print a message on
stderr and exit 1.

When-predicate order: `should_upfront_prompt` if set, else `UPFRONT_WHEN` if
set, else always (when `UPFRONT_PROMPT` is set). The engine exposes
`current_branch() -> str` for those callables.

Prompt-only hook: `TOOL` is unset or empty and `run_check` is unset. The
engine still requires `git`, runs the upfront prompt if configured, and does
not list or check staged files.

Staged paths come from `git diff --cached --name-only --diff-filter=ACM`,
split on newlines so names with spaces stay intact. Missing or unreadable
paths are skipped; they do not abort the hook.

## Prompts

Read yes/no answers from `/dev/tty`, never from stdin. Git and the
multiplexer may already be using stdin for a payload. Accept `y` / `yes` /
`n` / `no` (case-insensitive); re-ask on anything else. If `/dev/tty`
cannot be opened, apply that hook’s `ON_NO_TTY_*` knob — do not hang on a
pipe.

| Knob                 | `"abort"`                 | `"skip"`      |
| :------------------- | :------------------------ | :------------ |
| `ON_NO_TTY_UPFRONT`  | Message on stderr, exit 1 | Continue      |
| `ON_NO_TTY_FINDINGS` | Message on stderr, exit 1 | Treat as pass |

Exit `0` means no matching files, the check passed, the user confirmed
findings, prompt-only “yes”, or missing-tool skip. Exit `1` means no Git
work tree, missing tool (abort), the user said no, no-TTY abort, or a
failed check with no code. Otherwise the hook exits with the tool’s
non-zero code.

## Examples

Docs-only headers. This repo does not ship finished hook scripts.

### Silent Ruff

Strict lint default: require `ruff`, check staged Python files (and
shebang matches), abort on tool failure.

```python
REQUIRED_COMMANDS = ["ruff"]
TOOL = ["ruff", "check"]
FILE_EXTENSIONS = [".py"]
SHEBANG_PATTERN = r"python3?"
```

### Confirm Commits to Master

Prompt only on `master`. When `/dev/tty` is unavailable (IDE / Cursor),
skip the prompt so the commit is not blocked.

```python
UPFRONT_PROMPT = "Are you sure you want to commit to master? [Yes/No] "
UPFRONT_WHEN = lambda: current_branch() == "master"
ON_NO_TTY_UPFRONT = "skip"
```

Leave `TOOL` unset for a prompt-only hook.

## Development

These steps are only for changing this repository.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
python -m pytest
```

<a href="https://github.com/the-lupaxa-project">
  <img src="https://raw.githubusercontent.com/the-lupaxa-project/brand-assets/master/logos/components/footer-for-child-orgs.svg" alt="The Lupaxa Project Footer" width="100%" />
</a>
