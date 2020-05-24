"""Tests for core module."""
from retrocookie import git
from retrocookie import retrocookie


def test_core(
    cookiecutter_repository: git.Repository,
    cookiecutter_instance_repository_with_topic: git.Repository,
) -> None:
    """It succeeds."""
    cookiecutter = cookiecutter_repository
    instance = cookiecutter_instance_repository_with_topic

    retrocookie("topic", path=cookiecutter.path, url=str(instance.path))
    cookiecutter.switch_branch("topic")

    readme = cookiecutter.path / "README.md"
    assert "Lorem ipsum" in readme.read_text()
