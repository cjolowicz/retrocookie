"""Tests for core module."""
from retrocookie import git


def test_core(cookiecutter_repository: git.Repository) -> None:
    """It succeeds."""
    cookiecutter_repository.git("show")
    cookiecutter_repository.git("status")
