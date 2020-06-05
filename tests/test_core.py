"""Tests for core module."""
from pathlib import Path

import pytest

from .helpers import Append
from .helpers import apply
from .helpers import branch
from .helpers import in_template
from retrocookie import core
from retrocookie import git
from retrocookie import retrocookie


@pytest.mark.parametrize(
    "text, expected",
    [
        ("Lorem Ipsum\n", "Lorem Ipsum\n"),
        (
            "This project is called example.\n",
            "This project is called {{ cookiecutter.project_slug }}.\n",
        ),
        (
            "python-version: ${{ matrix.python-version }}",
            'python-version: ${{ "{{" }} matrix.python-version {{ "}}" }}',
        ),
    ],
)
def test_verbatim(
    cookiecutter_repository: git.Repository,
    cookiecutter_instance_repository: git.Repository,
    text: str,
    expected: str,
) -> None:
    """It inserts text verbatim."""
    cookiecutter, instance = cookiecutter_repository, cookiecutter_instance_repository
    change = Append(Path("README.md"), text)

    with branch(instance, "topic", create=True):
        apply(instance, change)

    retrocookie(
        instance.path, path=cookiecutter.path, branch="topic", create_branch="topic",
    )

    with branch(cookiecutter, "topic"):
        assert expected in cookiecutter.read_text(in_template(change.path))


def test_branch(
    cookiecutter_repository: git.Repository,
    cookiecutter_instance_repository: git.Repository,
) -> None:
    """It creates the specified branch."""
    cookiecutter, instance = cookiecutter_repository, cookiecutter_instance_repository
    change = Append(Path("README.md"), "Lorem Ipsum\n")

    with branch(instance, "topic", create=True):
        apply(instance, change)

    retrocookie(
        instance.path,
        path=cookiecutter.path,
        branch="topic",
        create_branch="just-another-branch",
    )

    with branch(cookiecutter, "just-another-branch"):
        assert change.text in cookiecutter.read_text(in_template(change.path))


def test_commits(
    cookiecutter_repository: git.Repository,
    cookiecutter_instance_repository: git.Repository,
) -> None:
    """It cherry-picks the specified commits."""
    cookiecutter, instance = cookiecutter_repository, cookiecutter_instance_repository
    change = Append(Path("README.md"), "Lorem Ipsum\n")
    apply(instance, change)

    retrocookie(instance.path, ["HEAD"], path=cookiecutter.path)

    assert change.text in cookiecutter.read_text(in_template(change.path))


def test_find_template_directory_fails(tmp_path: Path) -> None:
    """It raises an exception when there is no template directory."""
    repository = git.Repository.init(tmp_path)
    with pytest.raises(Exception):
        core.find_template_directory(repository)
