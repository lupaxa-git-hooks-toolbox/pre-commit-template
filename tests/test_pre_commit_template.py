#!/usr/bin/env python3
"""Tests for src/pre-commit-template."""

from __future__ import annotations

import importlib.util
import os
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from importlib.machinery import SourceFileLoader
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "src" / "pre-commit-template"


def _load_script():
    loader = SourceFileLoader("pre_commit_template", str(SCRIPT))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


@contextmanager
def _git_repo() -> Iterator[Path]:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "t@example.com"], cwd=root, check=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=root, check=True)
        subprocess.run(
            ["git", "commit", "--allow-empty", "-m", "init"],
            cwd=root,
            check=True,
            capture_output=True,
        )
        yield root


@contextmanager
def _unborn_git_repo() -> Iterator[Path]:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "t@example.com"], cwd=root, check=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=root, check=True)
        yield root


@contextmanager
def _preserve_cwd() -> Iterator[None]:
    try:
        previous = os.getcwd()
    except FileNotFoundError:
        previous = str(REPO_ROOT)
        os.chdir(previous)
    try:
        yield
    finally:
        try:
            os.chdir(previous)
        except OSError:
            os.chdir(REPO_ROOT)


@pytest.fixture(autouse=True)
def _reset_cwd_after_test():
    try:
        start = os.getcwd()
    except FileNotFoundError:
        start = str(REPO_ROOT)
        os.chdir(start)
    yield
    try:
        os.chdir(start)
    except (OSError, FileNotFoundError):
        os.chdir(REPO_ROOT)


def test_header_defaults():
    mod = _load_script()
    assert SCRIPT.read_text(encoding="utf-8").splitlines()[0] == "#!/usr/bin/env python3"
    assert "# STOP HERE" in SCRIPT.read_text(encoding="utf-8")
    assert mod.REQUIRED_COMMANDS == []
    assert mod.TOOL is None
    assert mod.FILE_EXTENSIONS == []
    assert mod.SHEBANG_PATTERN is None
    assert mod.RUN_MODE == "batch"
    assert mod.UPFRONT_PROMPT is None
    assert mod.UPFRONT_WHEN is None
    assert mod.CONFIRM_FINDINGS_PROMPT is None
    assert mod.ON_MISSING_TOOL == "abort"
    assert mod.ON_NO_TTY_UPFRONT == "abort"
    assert mod.ON_NO_TTY_FINDINGS == "abort"
    assert mod.match_file is None
    assert mod.run_check is None
    assert mod.should_upfront_prompt is None


def test_validate_knobs_accepts_defaults():
    mod = _load_script()
    mod.validate_knobs()


def test_validate_knobs_rejects_unknown_run_mode(capsys):
    mod = _load_script()
    mod.RUN_MODE = "parallel"
    with pytest.raises(SystemExit) as exc:
        mod.validate_knobs()
    assert exc.value.code == 1
    assert "RUN_MODE" in capsys.readouterr().err


def test_resolve_git_finds_git():
    mod = _load_script()
    path = mod.resolve_git()
    assert os.path.isfile(path)
    assert os.access(path, os.X_OK)


def test_resolve_git_missing_exits(monkeypatch, capsys):
    mod = _load_script()
    monkeypatch.setattr(mod.shutil, "which", lambda name: None if name == "git" else "/bin/true")
    with pytest.raises(SystemExit) as exc:
        mod.resolve_git()
    assert exc.value.code == 1
    assert "git" in capsys.readouterr().err.lower()


def test_required_command_missing_aborts(monkeypatch, capsys):
    mod = _load_script()
    mod.REQUIRED_COMMANDS = ["definitely-not-installed-xyz"]
    real_which = shutil.which

    def fake_which(name):
        if name == "definitely-not-installed-xyz":
            return None
        return real_which(name)

    monkeypatch.setattr(mod.shutil, "which", fake_which)
    with pytest.raises(SystemExit) as exc:
        mod.resolve_required_commands()
    assert exc.value.code == 1
    assert "definitely-not-installed-xyz" in capsys.readouterr().err


def test_required_command_missing_skip(monkeypatch):
    mod = _load_script()
    mod.REQUIRED_COMMANDS = ["definitely-not-installed-xyz"]
    mod.ON_MISSING_TOOL = "skip"
    real_which = shutil.which

    def fake_which(name):
        if name == "definitely-not-installed-xyz":
            return None
        return real_which(name)

    monkeypatch.setattr(mod.shutil, "which", fake_which)
    with pytest.raises(SystemExit) as exc:
        mod.resolve_required_commands()
    assert exc.value.code == 0


def test_on_missing_tool_invalid(monkeypatch, capsys):
    mod = _load_script()
    mod.REQUIRED_COMMANDS = ["definitely-not-installed-xyz"]
    mod.ON_MISSING_TOOL = "warn"
    monkeypatch.setattr(mod.shutil, "which", lambda name: None)
    with pytest.raises(SystemExit) as exc:
        mod.resolve_required_commands()
    assert exc.value.code == 1
    assert "ON_MISSING_TOOL" in capsys.readouterr().err


def test_find_repo_root_inside_work_tree():
    mod = _load_script()
    with _git_repo() as root:
        os.chdir(root)
        got = Path(mod.find_repo_root(mod.resolve_git())).resolve()
        assert got == root.resolve()


def test_find_repo_root_without_git_exits(tmp_path, capsys):
    mod = _load_script()
    os.chdir(tmp_path)
    with pytest.raises(SystemExit) as exc:
        mod.find_repo_root(mod.resolve_git())
    assert exc.value.code == 1
    assert capsys.readouterr().err


def test_list_staged_files_acm_and_spaces():
    mod = _load_script()
    with _git_repo() as root:
        (root / "ok.py").write_text("x\n", encoding="utf-8")
        (root / "my file.py").write_text("y\n", encoding="utf-8")
        (root / "skip.py").write_text("z\n", encoding="utf-8")
        subprocess.run(["git", "add", "ok.py", "my file.py"], cwd=root, check=True)
        os.chdir(root)
        staged = mod.list_staged_files(mod.resolve_git())
        assert set(staged) == {"ok.py", "my file.py"}


def test_file_matches_all_when_filters_empty(tmp_path):
    mod = _load_script()
    target = tmp_path / "notes.txt"
    target.write_text("hi\n", encoding="utf-8")
    assert mod.file_matches(str(target)) is True


def test_file_matches_extension_or_shebang(tmp_path):
    mod = _load_script()
    mod.FILE_EXTENSIONS = [".py"]
    mod.SHEBANG_PATTERN = r"python3?"
    py = tmp_path / "app.py"
    py.write_text("x\n", encoding="utf-8")
    sh = tmp_path / "run"
    sh.write_text("#!/usr/bin/env python3\nprint(1)\n", encoding="utf-8")
    txt = tmp_path / "readme.txt"
    txt.write_text("nope\n", encoding="utf-8")
    assert mod.file_matches(str(py)) is True
    assert mod.file_matches(str(sh)) is True
    assert mod.file_matches(str(txt)) is False


def test_filter_skips_unreadable_and_applies_match_file(tmp_path):
    mod = _load_script()
    good = tmp_path / "keep.py"
    good.write_text("x\n", encoding="utf-8")
    gone = tmp_path / "missing.py"
    extra = tmp_path / "drop.py"
    extra.write_text("y\n", encoding="utf-8")
    mod.FILE_EXTENSIONS = [".py"]
    mod.match_file = lambda path: Path(path).name != "drop.py"
    got = mod.filter_staged_files([str(good), str(gone), str(extra)])
    assert got == [str(good)]


def test_run_tool_batch_true():
    mod = _load_script()
    mod.TOOL = ["true"]
    assert mod.run_tool(["a.py"]) == 0


def test_run_tool_batch_false():
    mod = _load_script()
    mod.TOOL = ["false"]
    assert mod.run_tool(["a.py"]) == 1


def test_run_tool_each_uses_first_nonzero():
    mod = _load_script()
    mod.RUN_MODE = "each"
    mod.TOOL = [sys.executable, "-c", "import sys; sys.exit(0 if 'ok' in sys.argv[-1] else 3)"]
    with tempfile.TemporaryDirectory() as tmp:
        ok = Path(tmp) / "ok.py"
        bad = Path(tmp) / "bad.py"
        ok.write_text("x\n", encoding="utf-8")
        bad.write_text("y\n", encoding="utf-8")
        assert mod.run_tool([str(ok), str(bad)]) == 3


def test_run_check_overrides_tool():
    mod = _load_script()
    mod.TOOL = ["false"]
    mod.run_check = lambda files: 0
    assert mod.run_tool(["a.py"]) == 0


def test_should_ask_upfront_none_means_always_when_prompt_set():
    mod = _load_script()
    mod.UPFRONT_PROMPT = "Go? [Yes/No] "
    assert mod.should_ask_upfront() is True


def test_should_ask_upfront_uses_when_then_override():
    mod = _load_script()
    mod.UPFRONT_PROMPT = "Go? [Yes/No] "
    mod.UPFRONT_WHEN = lambda: False
    assert mod.should_ask_upfront() is False
    mod.should_upfront_prompt = lambda: True
    assert mod.should_ask_upfront() is True


def test_apply_no_tty_skip_returns_true():
    mod = _load_script()
    assert mod.apply_no_tty_policy("skip") is True


def test_apply_no_tty_abort_exits(capsys):
    mod = _load_script()
    with pytest.raises(SystemExit) as exc:
        mod.apply_no_tty_policy("abort")
    assert exc.value.code == 1
    assert capsys.readouterr().err


def test_prompt_yes_no_accepts_yes_and_rejects_then_no():
    mod = _load_script()
    master_fd, slave_fd = os.openpty()
    try:
        reader = os.fdopen(os.dup(slave_fd), "r", buffering=1)
        writer = os.fdopen(os.dup(slave_fd), "w", buffering=1)

        class TtyIO:
            def write(self, text: str) -> None:
                writer.write(text)

            def flush(self) -> None:
                writer.flush()

            def readline(self) -> str:
                return reader.readline()

        tty = TtyIO()
        os.write(master_fd, b"maybe\ny\n")
        assert mod.prompt_yes_no("Continue? [Yes/No] ", tty) is True
        os.write(master_fd, b"n\n")
        assert mod.prompt_yes_no("Continue? [Yes/No] ", tty) is False
    finally:
        os.close(master_fd)


def test_prompt_yes_no_eof_returns_false():
    mod = _load_script()

    class TtyIO:
        def write(self, text: str) -> None:
            pass

        def flush(self) -> None:
            pass

        def readline(self) -> str:
            return ""

    assert mod.prompt_yes_no("Continue? [Yes/No] ", TtyIO()) is False


def test_current_branch_master():
    mod = _load_script()
    with _git_repo() as root:
        os.chdir(root)
        branch = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        assert mod.current_branch() == branch


def test_current_branch_unborn_head():
    mod = _load_script()
    with _unborn_git_repo() as root, _preserve_cwd():
        os.chdir(root)
        expected = subprocess.run(
            ["git", "symbolic-ref", "--short", "HEAD"],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        assert mod.current_branch() == expected


def test_main_no_matching_files_succeeds():
    mod = _load_script()
    mod.TOOL = ["false"]
    mod.FILE_EXTENSIONS = [".py"]
    with _git_repo() as root:
        (root / "readme.txt").write_text("x\n", encoding="utf-8")
        subprocess.run(["git", "add", "readme.txt"], cwd=root, check=True)
        os.chdir(root)
        assert mod.main() == 0


def test_main_tool_success():
    mod = _load_script()
    mod.REQUIRED_COMMANDS = ["true"]
    mod.TOOL = ["true"]
    mod.FILE_EXTENSIONS = [".py"]
    with _git_repo() as root:
        (root / "app.py").write_text("x\n", encoding="utf-8")
        subprocess.run(["git", "add", "app.py"], cwd=root, check=True)
        os.chdir(root)
        assert mod.main() == 0


def test_main_tool_failure_aborts():
    mod = _load_script()
    mod.REQUIRED_COMMANDS = ["true"]
    mod.TOOL = ["false"]
    mod.FILE_EXTENSIONS = [".py"]
    with _git_repo() as root:
        (root / "app.py").write_text("x\n", encoding="utf-8")
        subprocess.run(["git", "add", "app.py"], cwd=root, check=True)
        os.chdir(root)
        assert mod.main() == 1


def test_main_prompt_only_no_tty_skip():
    mod = _load_script()
    mod.UPFRONT_PROMPT = "Commit to master? [Yes/No] "
    mod.ON_NO_TTY_UPFRONT = "skip"
    mod.open_tty = lambda: None
    with _git_repo() as root:
        os.chdir(root)
        assert mod.main() == 0


def test_main_prompt_only_no_tty_abort(capsys):
    mod = _load_script()
    mod.UPFRONT_PROMPT = "Commit to master? [Yes/No] "
    mod.ON_NO_TTY_UPFRONT = "abort"
    mod.open_tty = lambda: None
    with _git_repo() as root:
        os.chdir(root)
        with pytest.raises(SystemExit) as exc:
            mod.main()
        assert exc.value.code == 1
    assert capsys.readouterr().err


def test_main_confirm_findings_no_tty_abort():
    mod = _load_script()
    mod.TOOL = ["false"]
    mod.FILE_EXTENSIONS = [".py"]
    mod.CONFIRM_FINDINGS_PROMPT = "Commit anyway? [Yes/No] "
    mod.ON_NO_TTY_FINDINGS = "abort"
    mod.open_tty = lambda: None
    with _git_repo() as root:
        (root / "app.py").write_text("x\n", encoding="utf-8")
        subprocess.run(["git", "add", "app.py"], cwd=root, check=True)
        os.chdir(root)
        with pytest.raises(SystemExit) as exc:
            mod.main()
        assert exc.value.code == 1


def test_main_confirm_findings_no_tty_skip():
    mod = _load_script()
    mod.TOOL = ["false"]
    mod.FILE_EXTENSIONS = [".py"]
    mod.CONFIRM_FINDINGS_PROMPT = "Commit anyway? [Yes/No] "
    mod.ON_NO_TTY_FINDINGS = "skip"
    mod.open_tty = lambda: None
    with _git_repo() as root:
        (root / "app.py").write_text("x\n", encoding="utf-8")
        subprocess.run(["git", "add", "app.py"], cwd=root, check=True)
        os.chdir(root)
        assert mod.main() == 0


def test_main_prompt_only_outside_git_repo_exits():
    mod = _load_script()
    mod.UPFRONT_PROMPT = "Commit to master? [Yes/No] "
    with tempfile.TemporaryDirectory() as tmp, _preserve_cwd():
        os.chdir(tmp)
        with pytest.raises(SystemExit) as exc:
            mod.main()
        assert exc.value.code == 1


def test_main_confirm_findings_no_exits_tool_code():
    mod = _load_script()
    mod.TOOL = [sys.executable, "-c", "import sys; sys.exit(3)"]
    mod.FILE_EXTENSIONS = [".py"]
    mod.CONFIRM_FINDINGS_PROMPT = "Commit anyway? [Yes/No] "

    class TtyIO:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def write(self, text: str) -> None:
            pass

        def flush(self) -> None:
            pass

        def readline(self) -> str:
            return "n\n"

    mod.open_tty = lambda: TtyIO()
    with _git_repo() as root, _preserve_cwd():
        (root / "app.py").write_text("x\n", encoding="utf-8")
        subprocess.run(["git", "add", "app.py"], cwd=root, check=True)
        os.chdir(root)
        assert mod.main() == 3


def test_main_does_not_treat_stdin_as_yes(monkeypatch):
    mod = _load_script()
    mod.UPFRONT_PROMPT = "Go? [Yes/No] "
    mod.ON_NO_TTY_UPFRONT = "abort"
    mod.open_tty = lambda: None
    monkeypatch.setattr(sys, "stdin", type("S", (), {"read": lambda self: "yes\n"})())
    with _git_repo() as root:
        os.chdir(root)
        with pytest.raises(SystemExit) as exc:
            mod.main()
        assert exc.value.code == 1


def test_docs_name_the_header_and_worked_examples():
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    assert "src/pre-commit-template" in readme
    assert "Licence" not in readme and "License" not in readme
    usage = (REPO_ROOT / "mkdocs" / "usage.md").read_text(encoding="utf-8")
    assert "REQUIRED_COMMANDS" in usage
    examples = (REPO_ROOT / "mkdocs" / "examples.md").read_text(encoding="utf-8")
    assert 'TOOL = ["ruff", "check"]' in examples
    assert "ON_NO_TTY_UPFRONT" in examples
