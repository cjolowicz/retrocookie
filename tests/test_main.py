"""Test cases for the __main__ module."""
from pathlib import Path
from typing import Iterable

import pytest
from _pytest.monkeypatch import MonkeyPatch
from click.testing import CliRunner

from .helpers import append
from .helpers import branch
from .helpers import commit
from retrocookie import __main__
from retrocookie import git
from retrocookie import utils


@pytest.fixture
def runner() -> CliRunner:
    """Fixture for invoking command-line interfaces."""
    return CliRunner()


def test_main(
    runner: CliRunner,
    cookiecutter_repository: git.Repository,
    cookiecutter_instance_repository: git.Repository,
) -> None:
    """It exits with a status code of zero."""
    cookiecutter, instance = cookiecutter_repository, cookiecutter_instance_repository
    path = Path("README.md")
    text = "Lorem Ipsum\n"

    with branch(instance, "topic"):
        append(instance, path, text)
        commit(instance, path)

    with utils.chdir(cookiecutter.path):
        result = runner.invoke(__main__.main, ["--ref=topic", str(instance.path)])
        assert result.exit_code == 0


@pytest.fixture
def mock_retrocookie(monkeypatch: MonkeyPatch) -> None:
    """Replace retrocookie function by noop."""
    monkeypatch.setattr(__main__, "retrocookie", lambda *args, **kwargs: None)


@pytest.mark.parametrize(
    "args",
    [
        ["--help"],
        ["--ref=topic"],
        ["--ref=topic", "--local=other"],
        ["--ref=topic", "--whitelist=project_name", "--whitelist=package_name"],
        ["--ref=topic", "--blacklist=github_user"],
    ],
)
def test_accepted_invocations(
    runner: CliRunner, args: Iterable[str], mock_retrocookie: None
) -> None:
    """It succeeds when invoked with the given arguments."""
    result = runner.invoke(__main__.main, args)
    assert result.exit_code == 0, result.output


@pytest.mark.parametrize(
    "args", [[], ["--ref=topic", "first", "second"]],
)
def test_rejected_invocations(
    runner: CliRunner, args: Iterable[str], mock_retrocookie: None
) -> None:
    """It fails when invoked with the given arguments."""
    result = runner.invoke(__main__.main, args)
    assert result.exit_code == 2
