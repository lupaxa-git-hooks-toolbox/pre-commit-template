# Reference

## Header defaults

| Name                      | Type                           | Default   |
| :------------------------ | :----------------------------- | :-------- |
| `REQUIRED_COMMANDS`       | `list[str]`                    | `[]`      |
| `TOOL`                    | `list[str] \| None`            | `None`    |
| `FILE_EXTENSIONS`         | `list[str]`                    | `[]`      |
| `SHEBANG_PATTERN`         | `str \| None`                  | `None`    |
| `RUN_MODE`                | `str`                          | `"batch"` |
| `UPFRONT_PROMPT`          | `str \| None`                  | `None`    |
| `UPFRONT_WHEN`            | `(() -> bool) \| None`         | `None`    |
| `CONFIRM_FINDINGS_PROMPT` | `str \| None`                  | `None`    |
| `ON_MISSING_TOOL`         | `str`                          | `"abort"` |
| `ON_NO_TTY_UPFRONT`       | `str`                          | `"abort"` |
| `ON_NO_TTY_FINDINGS`      | `str`                          | `"abort"` |
| `match_file`              | `((str) -> bool) \| None`      | `None`    |
| `run_check`               | `((list[str]) -> int) \| None` | `None`    |
| `should_upfront_prompt`   | `(() -> bool) \| None`         | `None`    |

Unknown `RUN_MODE`, `ON_MISSING_TOOL`, `ON_NO_TTY_UPFRONT`, or
`ON_NO_TTY_FINDINGS` values print a message on stderr and exit 1.

## Escape-hatch signatures

| Name                    | Signature                   | Role                                                      |
| :---------------------- | :-------------------------- | :-------------------------------------------------------- |
| `match_file`            | `(path: str) -> bool`       | Extra AND after extensions / shebang.                     |
| `run_check`             | `(files: list[str]) -> int` | Replaces `TOOL`; return the exit code.                    |
| `should_upfront_prompt` | `() -> bool`                | Replaces `UPFRONT_WHEN` when deciding whether to ask.     |
| `current_branch`        | `() -> str`                 | Engine helper for predicates (for example vs `"master"`). |

## No-TTY knobs

| Knob                 | When it applies                                      | `"abort"`                 | `"skip"`      |
| :------------------- | :--------------------------------------------------- | :------------------------ | :------------ |
| `ON_NO_TTY_UPFRONT`  | Upfront prompt cannot open `/dev/tty`                | Message on stderr, exit 1 | Continue      |
| `ON_NO_TTY_FINDINGS` | Findings confirm cannot open `/dev/tty` after a fail | Message on stderr, exit 1 | Treat as pass |

## Exit codes

| Code     | Meaning                                                                                          |
| :------- | :----------------------------------------------------------------------------------------------- |
| `0`      | No matching files; check passed; user confirmed findings; prompt-only “yes”; missing-tool skip   |
| `1`      | Not a Git work tree; missing tool (abort); user said no; no-TTY abort; failed check with no code |
| Tool `N` | Failed `TOOL` / `run_check` when we are not overriding the code via a findings “yes”             |

## Staged listing

Staged paths come from:

```bash
git diff --cached --name-only --diff-filter=ACM
```

The engine splits the output with `splitlines()` (newline-separated), not on
whitespace, so filenames with spaces stay intact. Paths that are missing or
unreadable are skipped; they do not abort the hook.

## Hook file

The product is the single file `src/pre-commit-template`. It uses the Python
standard library only. There is no package to install or import at runtime.

Copy it into `hooks/pre-commit/<name>`, edit the header, and `chmod +x`.
Python 3.13 or newer must be on `PATH`.
