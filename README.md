<p align="center">
    <a href="https://github.com/lupaxa-git-hooks-toolbox">
        <img src="https://raw.githubusercontent.com/the-lupaxa-project/brand-assets/master/logos/organisations/git-hooks-toolbox/readme-logo.png" alt="Organisation Logo" />
    </a>
</p>

<h1 align="center">Pre-commit template</h1>

One self-contained script. Copy it into `hooks/pre-commit/<name>`, edit the
header, and `chmod +x` it. No pip install. The multiplexer runs it as a
subhook.

Works as a silent lint (ruff, mypy, shellcheck, rubocop) or with optional
yes/no prompts on `/dev/tty`.

## Install

Python 3.13 or newer on `PATH`. The only file you need is
`src/pre-commit-template`.

```bash
cp src/pre-commit-template hooks/pre-commit/01-ruff
chmod +x hooks/pre-commit/01-ruff
```

Edit the header: `REQUIRED_COMMANDS`, `TOOL`, `FILE_EXTENSIONS`. Leave
everything below `# STOP HERE` alone.

## Development

These steps are only for changing this repository.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
python -m pytest
```

## Documentation

The guide is in [`mkdocs/`](mkdocs/index.md). After installing the `dev`
extras:

```bash
mkdocs serve
```

<a href="https://github.com/the-lupaxa-project">
  <img src="https://raw.githubusercontent.com/the-lupaxa-project/brand-assets/master/logos/components/footer-for-child-orgs.svg" alt="The Lupaxa Project Footer" width="100%" />
</a>
