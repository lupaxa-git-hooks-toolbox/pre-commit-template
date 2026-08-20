# Usage

## Header knobs

Edit only the config block above `# STOP HERE`. Defaults make a copied
file a strict, silent no-op (require `git`, then exit 0) until `TOOL`,
`run_check`, or `UPFRONT_PROMPT` is set.

### Tool and files

| Name                | Meaning                                                                                          |
| :------------------ | :----------------------------------------------------------------------------------------------- |
| `REQUIRED_COMMANDS` | Extra binaries that must exist on `PATH`. The engine always requires `git`.                      |
| `TOOL`              | Argv prefix; matching files are appended. Example: `["ruff", "check"]`. Empty list is unset.     |
| `FILE_EXTENSIONS`   | Match suffix (e.g. `[".py", ".sh"]`). Empty means no extension filter.                           |
| `SHEBANG_PATTERN`   | Regex tested against the first line (e.g. `r"python3?"`).                                        |
| `RUN_MODE`          | `"batch"`: one invocation with all files. `"each"`: one invocation per file.                     |

A staged file is a candidate if it is readable. It then matches if:

- `FILE_EXTENSIONS` and `SHEBANG_PATTERN` are both unset/empty → all readable staged files; or
- its name ends with an extension **or** its shebang matches (either filter may be set alone).

### Prompts and acceptance

| Name                      | Meaning                                                                              |
| :------------------------ | :----------------------------------------------------------------------------------- |
| `UPFRONT_PROMPT`          | Yes/no text on `/dev/tty` before the check. `None` = skip.                           |
| `UPFRONT_WHEN`            | If a prompt is set: `None` means always; otherwise call the predicate.               |
| `CONFIRM_FINDINGS_PROMPT` | Yes/no after a failed check. `None` = abort on failure.                              |
| `ON_MISSING_TOOL`         | `"abort"` or `"skip"` when a name in `REQUIRED_COMMANDS` is missing.                 |
| `ON_NO_TTY_UPFRONT`       | `"abort"` or `"skip"` when an upfront prompt cannot open `/dev/tty`.                 |
| `ON_NO_TTY_FINDINGS`      | `"abort"` or `"skip"` when a findings prompt cannot open `/dev/tty`.                 |

`git` is never skipped. Missing `git` always aborts with exit 1, regardless
of `ON_MISSING_TOOL`.

### Escape hatches

Leave unset (`None`) unless needed.

| Name                    | Signature                   | When it runs                                                                |
| :---------------------- | :-------------------------- | :-------------------------------------------------------------------------- |
| `match_file`            | `(path: str) -> bool`       | After the built-in filter; extra AND.                                       |
| `run_check`             | `(files: list[str]) -> int` | If set, used instead of `TOOL`. Print your own output; return an exit code. |
| `should_upfront_prompt` | `() -> bool`                | If set, used instead of `UPFRONT_WHEN`.                                     |

When-predicate order: `should_upfront_prompt` if set, else `UPFRONT_WHEN` if
set, else always (when `UPFRONT_PROMPT` is set). The engine exposes
`current_branch() -> str` for those callables.

Prompt-only hook: `TOOL` is unset or empty and `run_check` is unset. The
engine still requires `git`, runs the upfront prompt if configured, and does
not list or check staged files.

## Run loop

1.   Resolve `git` via `shutil.which`. Missing `git` → message on stderr, exit 1
     (not subject to `ON_MISSING_TOOL`).
2.   Resolve every name in `REQUIRED_COMMANDS`. Any missing → list them, then
     apply `ON_MISSING_TOOL`.
3.   `chdir` to the work-tree root (`git rev-parse --show-toplevel`). No work
     tree → exit 1.
4.   If `UPFRONT_PROMPT` is set and the when-predicate is true: ask on
     `/dev/tty`. Cannot open TTY → `ON_NO_TTY_UPFRONT`. “No” → exit 1.
5.   If `TOOL` is unset or empty and `run_check` is unset: exit 0 (prompt-only
     path after step 4).
6.   List staged paths: `git diff --cached --name-only --diff-filter=ACM`,
     split on newlines (not whitespace).
7.   Filter: skip missing or unreadable paths; apply extensions / shebang /
     `match_file`. None left → exit 0.
8.   If `run_check` is set: `code = run_check(files)`. Else inherit stdout and
     stderr of `TOOL`. `batch`: one process, `code` is that exit code. `each`:
     one process per file; run every file; `code` is 0 if all succeeded,
     otherwise the first non-zero exit.
9.   `code == 0` → exit 0. Otherwise, if `CONFIRM_FINDINGS_PROMPT` is set: ask
     on `/dev/tty`; cannot open TTY → `ON_NO_TTY_FINDINGS`. “Yes” → exit 0.
     “No” or no prompt configured → exit `code` if it is non-zero, else 1.

## `/dev/tty` vs stdin

Read yes/no answers from `/dev/tty`, never from stdin. Git and the
multiplexer may already be using stdin for a payload. Accept `y` / `yes` /
`n` / `no` (case-insensitive); re-ask on anything else. If `/dev/tty`
cannot be opened, apply that hook’s `ON_NO_TTY_*` knob — do not hang on a
pipe.
