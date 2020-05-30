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

    with branch(instance, "topic"):
        apply(instance, change)

    retrocookie("topic", path=cookiecutter.path, url=str(instance.path))

    with branch(cookiecutter, "topic"):
        assert expected in read(cookiecutter, in_template(change.path))


def test_branch(
    cookiecutter_repository: git.Repository,
    cookiecutter_instance_repository: git.Repository,
) -> None:
    """It creates the specified branch."""
    cookiecutter, instance = cookiecutter_repository, cookiecutter_instance_repository
    change = Append(Path("README.md"), "Lorem Ipsum\n")

    with branch(instance, "topic"):
        apply(instance, change)

    retrocookie(
        "topic",
        path=cookiecutter.path,
        url=str(instance.path),
        branch="just-another-branch",
    )

    with branch(cookiecutter, "just-another-branch"):
        assert change.text in read(cookiecutter, in_template(change.path))


def test_guess_succeeds(
    cookiecutter_repository: git.Repository,
    cookiecutter_instance_repository: git.Repository,
    tmp_path: Path,
) -> None:
    """It guesses the repository URL of the template instance."""
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


def test_guess_fails(tmp_path: Path) -> None:
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
def test_guess_expected(tmp_path: Path, url: str, expected: str) -> None:
    """It returns an instance URL based on the cookiecutter's remote URL."""
    repository = git.Repository.init(tmp_path)
    repository.add_remote("origin", url)
    assert expected == core.guess_instance_url(repository)


def test_find_template_directory_fails(tmp_path: Path) -> None:
    """It raises an exception when there is no template directory."""
    repository = git.Repository.init(tmp_path)
    with pytest.raises(Exception):
        core.find_template_directory(repository)
