"""Tests for core module."""
from pathlib import Path

import pytest

from .helpers import append
from .helpers import branch
from .helpers import touch
from retrocookie import core
from retrocookie import git
from retrocookie import retrocookie


def in_template(path: Path) -> Path:
    """Prepend the template directory to the path."""
    return "{{ cookiecutter.project_slug }}" / path


class Example:
    """Example data for the test cases."""

    path = Path("README.md")
    text = "Lorem Ipsum\n"
    template_path = in_template(path)


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
def test_rewrite(
    cookiecutter_repository: git.Repository,
    cookiecutter_instance_repository: git.Repository,
    text: str,
    expected: str,
) -> None:
    """It rewrites the file contents as expected."""
    cookiecutter, instance = cookiecutter_repository, cookiecutter_instance_repository

    with branch(instance, "topic", create=True):
        append(instance, Example.path, text)

    retrocookie(
        instance.path, path=cookiecutter.path, branch="topic", create_branch="topic",
    )

    with branch(cookiecutter, "topic"):
        assert expected in cookiecutter.read_text(Example.template_path)


def test_branch(
    cookiecutter_repository: git.Repository,
    cookiecutter_instance_repository: git.Repository,
) -> None:
    """It creates the specified branch."""
    cookiecutter, instance = cookiecutter_repository, cookiecutter_instance_repository

    with branch(instance, "topic", create=True):
        append(instance, Example.path, Example.text)

    retrocookie(
        instance.path,
        path=cookiecutter.path,
        branch="topic",
        create_branch="just-another-branch",
    )

    with branch(cookiecutter, "just-another-branch"):
        assert Example.text in cookiecutter.read_text(Example.template_path)


def test_single_commit(
    cookiecutter_repository: git.Repository,
    cookiecutter_instance_repository: git.Repository,
) -> None:
    """It cherry-picks the specified commit."""
    cookiecutter, instance = cookiecutter_repository, cookiecutter_instance_repository

    append(instance, Example.path, Example.text)
    retrocookie(instance.path, ["HEAD"], path=cookiecutter.path)

    assert Example.text in cookiecutter.read_text(Example.template_path)


def test_multiple_commits_sequential(
    cookiecutter_repository: git.Repository,
    cookiecutter_instance_repository: git.Repository,
) -> None:
    """It cherry-picks the specified commits."""
    cookiecutter, instance = cookiecutter_repository, cookiecutter_instance_repository
    names = "first", "second"

    for name in names:
        touch(instance, Path(name))

    retrocookie(instance.path, ["HEAD~2.."], path=cookiecutter.path)

    for name in names:
        path = in_template(Path(name))
        assert cookiecutter.exists(path)


def test_multiple_commits_parallel(
    cookiecutter_repository: git.Repository,
    cookiecutter_instance_repository: git.Repository,
) -> None:
    """It cherry-picks the specified commits."""
    cookiecutter, instance = cookiecutter_repository, cookiecutter_instance_repository
    names = "first", "second"

    for name in names:
        with branch(instance, name, create=True):
            touch(instance, Path(name))

    retrocookie(instance.path, names, path=cookiecutter.path)

    for name in names:
        path = in_template(Path(name))
        assert cookiecutter.exists(path)


def test_find_template_directory_fails(tmp_path: Path) -> None:
    """It raises an exception when there is no template directory."""
    repository = git.Repository.init(tmp_path)
    with pytest.raises(Exception):
        core.find_template_directory(repository)
