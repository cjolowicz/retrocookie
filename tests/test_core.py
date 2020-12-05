"""Tests for core module."""
from dataclasses import dataclass
from pathlib import Path

import pytest

from .helpers import append
from .helpers import branch
from .helpers import touch
from .helpers import write
from retrocookie import core
from retrocookie import git
from retrocookie import retrocookie


def in_template(path: Path) -> Path:
    """Prepend the template directory to the path."""
    return "{{cookiecutter.project_slug}}" / path


@dataclass
class Example:
    """Example data for the test cases."""

    path: Path = Path("README.md")
    text: str = "Lorem Ipsum\n"


@pytest.fixture
def example() -> Example:
    """Fixture with example data."""
    return Example()


@pytest.mark.parametrize(
    "text, expected",
    [
        ("Lorem Ipsum\n", "Lorem Ipsum\n"),
        (
            "This project is called example.\n",
            "This project is called {{cookiecutter.project_slug}}.\n",
        ),
        (
            "python-version: ${{ matrix.python-version }}",
            'python-version: ${{"{{"}} matrix.python-version {{"}}"}}',
        ),
    ],
)
def test_rewrite(
    cookiecutter_repository: git.Repository,
    cookiecutter_instance_repository: git.Repository,
    text: str,
    expected: str,
    example: Example,
) -> None:
    """It rewrites the file contents as expected."""
    cookiecutter, instance = cookiecutter_repository, cookiecutter_instance_repository

    with branch(instance, "topic", create=True):
        append(instance, example.path, text)

    retrocookie(
        instance.path,
        path=cookiecutter.path,
        branch="topic",
        create_branch="topic",
    )

    with branch(cookiecutter, "topic"):
        assert expected in cookiecutter.read_text(in_template(example.path))


def test_branch(
    cookiecutter_repository: git.Repository,
    cookiecutter_instance_repository: git.Repository,
    example: Example,
) -> None:
    """It creates the specified branch."""
    cookiecutter, instance = cookiecutter_repository, cookiecutter_instance_repository

    with branch(instance, "topic", create=True):
        append(instance, example.path, example.text)

    retrocookie(
        instance.path,
        path=cookiecutter.path,
        branch="topic",
        create_branch="just-another-branch",
    )

    with branch(cookiecutter, "just-another-branch"):
        assert example.text in cookiecutter.read_text(in_template(example.path))


def test_upstream(
    cookiecutter_repository: git.Repository,
    cookiecutter_instance_repository: git.Repository,
    example: Example,
) -> None:
    """It does not apply changes from the upstream branch."""
    cookiecutter, instance = cookiecutter_repository, cookiecutter_instance_repository

    another = Path("file.txt")

    with branch(instance, "upstream", create=True):
        touch(instance, another)
        with branch(instance, "topic", create=True):
            append(instance, example.path, example.text)

    retrocookie(
        instance.path,
        path=cookiecutter.path,
        upstream="upstream",
        branch="topic",
        create_branch="topic",
    )

    with branch(cookiecutter, "topic"):
        assert not cookiecutter.exists(another)
        assert example.text in cookiecutter.read_text(in_template(example.path))


def test_single_commit(
    cookiecutter_repository: git.Repository,
    cookiecutter_instance_repository: git.Repository,
    example: Example,
) -> None:
    """It cherry-picks the specified commit."""
    cookiecutter, instance = cookiecutter_repository, cookiecutter_instance_repository

    append(instance, example.path, example.text)
    retrocookie(instance.path, ["HEAD"], path=cookiecutter.path)

    assert example.text in cookiecutter.read_text(in_template(example.path))


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


def test_load_context_error(cookiecutter_instance_repository: git.Repository) -> None:
    """It raises an exception when .cookiecutter.json is not JSON dictionary."""
    write(cookiecutter_instance_repository, Path(".cookiecutter.json"), "[]")
    with pytest.raises(TypeError):
        core.load_context(cookiecutter_instance_repository, "HEAD")
