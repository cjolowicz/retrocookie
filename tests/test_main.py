"""Test cases for the __main__ module."""
from pathlib import Path
from typing import Iterable

import pytest
from _pytest.monkeypatch import MonkeyPatch
from click.testing import CliRunner

from .helpers import Append
from .helpers import apply
from .helpers import branch
from retrocookie import __main__
from retrocookie import git
from retrocookie import utils


@pytest.fixture
def runner() -> CliRunner:
    """Fixture for invoking command-line interfaces."""
    return CliRunner()


@pytest.fixture
def mock_retrocookie(monkeypatch: MonkeyPatch) -> None:
    """Replace retrocookie function by noop."""
    monkeypatch.setattr(__main__, "retrocookie", lambda *args, **kwargs: None)


@pytest.mark.parametrize(
    "args",
    [
        ["--help"],
        ["/home/user/src/repo", "--branch=topic"],
        ["--branch=topic", "/home/user/src/repo"],
        ["--branch=topic", "/home/user/src/repo", "18240dd"],
        ["--branch=topic", "https://example.com/owner/repo.git"],
        ["--branch=topic", "--create", "repo"],
        ["--branch=topic", "--create-branch=other", "repo"],
        [
            "--branch=topic",
            "--whitelist=project_name",
            "--whitelist=package_name",
            "repo",
        ],
        ["--branch=topic", "--blacklist=github_user", "repo"],
        ["/home/user/src/repo"],
        ["/home/user/src/repo", "18240dd"],
        ["/home/user/src/repo", "--create-branch=topic"],
    ],
)
def test_usage_success(
    runner: CliRunner, args: Iterable[str], mock_retrocookie: None
) -> None:
    """It succeeds when invoked with the given arguments."""
    result = runner.invoke(__main__.main, args)
    assert result.exit_code == 0, result.output


@pytest.mark.parametrize(
    "args",
    [
        [],
        ["--create", "repo"],
        ["--branch=topic"],
        ["--branch=topic", "--create", "--create-branch=another", "repo"],
    ],
)
def test_usage_error(
    runner: CliRunner, args: Iterable[str], mock_retrocookie: None
) -> None:
    """It fails when invoked with the given arguments."""
    result = runner.invoke(__main__.main, args)
    assert result.exit_code == 2


def test_functional(
    runner: CliRunner,
    cookiecutter_repository: git.Repository,
    cookiecutter_instance_repository: git.Repository,
) -> None:
    """It succeeds when importing a topic branch with a README update."""
    cookiecutter, instance = cookiecutter_repository, cookiecutter_instance_repository
    change = Append(Path("README.md"), "Lorem Ipsum\n")

    with branch(instance, "topic", create=True):
        apply(instance, change)

    with utils.chdir(cookiecutter.path):
        result = runner.invoke(__main__.main, ["--branch=topic", str(instance.path)])
        assert result.exit_code == 0
