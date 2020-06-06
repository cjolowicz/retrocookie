"""Tests for core module."""
from pathlib import Path

import pytest

from .helpers import append
from .helpers import branch
from .helpers import in_template
from .helpers import touch
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
def test_rewrite(
    cookiecutter_repository: git.Repository,
    cookiecutter_instance_repository: git.Repository,
    text: str,
    expected: str,
) -> None:
    """It rewrites the file contents as expected."""
    cookiecutter, instance = cookiecutter_repository, cookiecutter_instance_repository
    path = Path("README.md")

    with branch(instance, "topic", create=True):
        append(instance, path, text)

    retrocookie(
        instance.path, path=cookiecutter.path, branch="topic", create_branch="topic",
    )

    with branch(cookiecutter, "topic"):
        assert expected in cookiecutter.read_text(in_template(path))


def test_branch(
    cookiecutter_repository: git.Repository,
    cookiecutter_instance_repository: git.Repository,
) -> None:
    """It creates the specified branch."""
    cookiecutter, instance = cookiecutter_repository, cookiecutter_instance_repository
    path = Path("README.md")
    text = "Lorem Ipsum\n"

    with branch(instance, "topic", create=True):
        append(instance, path, text)

    retrocookie(
        instance.path,
        path=cookiecutter.path,
        branch="topic",
        create_branch="just-another-branch",
    )

    with branch(cookiecutter, "just-another-branch"):
        assert text in cookiecutter.read_text(in_template(path))


def test_single_commit(
    cookiecutter_repository: git.Repository,
    cookiecutter_instance_repository: git.Repository,
) -> None:
    """It cherry-picks the specified commit."""
    cookiecutter, instance = cookiecutter_repository, cookiecutter_instance_repository
    path = Path("README.md")
    text = "Lorem Ipsum\n"

    append(instance, path, text)
    retrocookie(instance.path, ["HEAD"], path=cookiecutter.path)

    assert text in cookiecutter.read_text(in_template(path))


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
