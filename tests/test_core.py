"""Tests for core module."""
from pathlib import Path

import pytest

from .helpers import Append
from .helpers import apply
from .helpers import branch
from .helpers import in_template
from .helpers import read
from retrocookie import core
from retrocookie import git
from retrocookie import retrocookie


def test_append(
    cookiecutter_repository: git.Repository,
    cookiecutter_instance_repository: git.Repository,
) -> None:
    """It succeeds."""
    cookiecutter, instance = cookiecutter_repository, cookiecutter_instance_repository
    change = Append(Path("README.md"), "Lorem Ipsum\n")

    with branch(instance, "topic"):
        apply(instance, change)

    retrocookie("topic", path=cookiecutter.path, url=str(instance.path))

    with branch(cookiecutter, "topic"):
        assert change.text in read(cookiecutter, in_template(change.path))


def test_append_with_local(
    cookiecutter_repository: git.Repository,
    cookiecutter_instance_repository: git.Repository,
) -> None:
    """It succeeds."""
    cookiecutter, instance = cookiecutter_repository, cookiecutter_instance_repository
    change = Append(Path("README.md"), "Lorem Ipsum\n")

    with branch(instance, "topic"):
        apply(instance, change)

    retrocookie("topic", path=cookiecutter.path, url=str(instance.path), branch="other")

    with branch(cookiecutter, "other"):
        assert change.text in read(cookiecutter, in_template(change.path))


def test_append_with_guess(
    cookiecutter_repository: git.Repository,
    cookiecutter_instance_repository: git.Repository,
    tmp_path: Path,
) -> None:
    """It succeeds."""
    cookiecutter = git.Repository.clone(
        url=str(cookiecutter_repository.path), path=tmp_path / "clone"
    )
    instance = git.Repository.clone(
        url=str(cookiecutter_instance_repository.path),
        path=Path(f"{cookiecutter_repository.path}-instance"),
    )
    change = Append(Path("README.md"), "Lorem Ipsum\n")

    with branch(instance, "topic"):
        apply(instance, change)

    retrocookie("topic", path=cookiecutter.path)

    with branch(cookiecutter, "topic"):
        assert change.text in read(cookiecutter, in_template(change.path))


def test_guess_instance_url_fails(tmp_path: Path) -> None:
    """It raises an exception when there is no remote URL."""
    repository = git.Repository.init(tmp_path)
    with pytest.raises(Exception):
        core.guess_instance_url(repository)


@pytest.mark.parametrize(
    "url, expected",
    [
        (
            "https://example.com/user/repository.git",
            "https://example.com/user/repository-instance.git",
        ),
        (
            "https://example.com/user/repository",
            "https://example.com/user/repository-instance",
        ),
    ],
)
def test_guess_instance_url_succeeds(tmp_path: Path, url: str, expected: str) -> None:
    """It returns an instance URL based on the cookiecutter's remote URL."""
    repository = git.Repository.init(tmp_path)
    repository.add_remote("origin", url)
    assert expected == core.guess_instance_url(repository)


def test_find_template_directory_fails(tmp_path: Path) -> None:
    """It raises an exception when there is no template directory."""
    repository = git.Repository.init(tmp_path)
    with pytest.raises(Exception):
        core.find_template_directory(repository)
