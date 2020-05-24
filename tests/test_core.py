"""Tests for core module."""
from retrocookie import git
from retrocookie import retrocookie


def test_cookiecutter_repository(cookiecutter_repository: git.Repository) -> None:
    """It succeeds."""
    repository = cookiecutter_repository
    repository.git("show")
    repository.git("status")


def test_cookiecutter_instance(
    cookiecutter_instance_repository: git.Repository,
) -> None:
    """It succeeds."""
    repository = cookiecutter_instance_repository
    repository.git("show")
    repository.git("status")


def test_cookiecutter_instance_commit(
    cookiecutter_repository: git.Repository,
    cookiecutter_instance_repository_with_topic: git.Repository,
) -> None:
    """It succeeds."""
    path = cookiecutter_repository.path
    url = str(cookiecutter_instance_repository_with_topic.path)

    retrocookie("topic", path=path, url=url)
    cookiecutter_repository.switch_branch("topic")

    readme = path / "README.md"
    assert "Lorem ipsum" in readme.read_text()
