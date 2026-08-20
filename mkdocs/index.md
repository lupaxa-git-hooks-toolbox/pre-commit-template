# Pre-commit template

One self-contained script. Copy `src/pre-commit-template` into
`hooks/pre-commit/<name>` — no pip install, no package. Edit the header.
Leave the engine below `# STOP HERE` alone.

The multiplexer runs that file as a pre-commit subhook.

## What it does

- Checks that `git` and `REQUIRED_COMMANDS` exist
- Optionally asks a yes/no question on `/dev/tty`
- Runs a tool (or `run_check`) on matching staged files
- Optionally asks whether to continue after a failed check
- Lets each hook set its own missing-tool and no-TTY rules

## Next steps

- [Getting started](getting-started.md) — copy the script
- [Usage](usage.md) — header knobs and the run loop
- [Reference](reference.md) — names, exits, prompts
- [Examples](examples.md) — silent ruff and confirm-on-master
