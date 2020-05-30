"""Test cases for the __main__ module."""
from pathlib import Path
from typing import Iterable

import pytest
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


def test_help(runner: CliRunner) -> None:
    """It exits with a status code of zero."""
    result = runner.invoke(__main__.main, ["--help"])
    assert result.exit_code == 0


@pytest.mark.parametrize(
    "options", [["--ref=topic"], ["--ref=topic", "--local=other"]],
)
def test_main(
    runner: CliRunner,
    cookiecutter_repository: git.Repository,
    cookiecutter_instance_repository: git.Repository,
    options: Iterable[str],
) -> None:
    """It exits with a status code of zero."""
    cookiecutter, instance = cookiecutter_repository, cookiecutter_instance_repository
    path = Path("README.md")
    text = "Lorem Ipsum\n"

    with branch(instance, "topic"):
        append(instance, path, text)
        commit(instance, path)

    with utils.chdir(cookiecutter.path):
        result = runner.invoke(__main__.main, [*options, str(instance.path)])
        assert result.exit_code == 0
