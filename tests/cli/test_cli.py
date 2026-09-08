from pathlib import Path

import pytest
from typer.testing import CliRunner

from topoli import __version__
from topoli.cli import app, check_cache_dir, check_python

runner = CliRunner()


def test_version_flag() -> None:
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert __version__ in result.stdout


def test_doctor_offline_passes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TOPOLI_CACHE_DIR", str(tmp_path / "cache"))
    result = runner.invoke(app, ["doctor", "--skip-network"])
    assert result.exit_code == 0, result.stdout
    assert "All checks passed" in result.stdout
    assert (tmp_path / "cache").is_dir()


def test_python_check_is_ok_on_supported_interpreter() -> None:
    assert check_python().ok


def test_cache_check_reports_unwritable_dir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    blocker = tmp_path / "file"
    blocker.write_text("not a directory")
    monkeypatch.setenv("TOPOLI_CACHE_DIR", str(blocker / "cache"))
    assert not check_cache_dir().ok
