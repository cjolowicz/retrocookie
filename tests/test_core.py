"""Tests for core module."""
from pathlib import Path

from retrocookie import git
from retrocookie import retrocookie

from .helpers import *


def test_append(
    cookiecutter_repository: git.Repository,
    cookiecutter_instance_repository: git.Repository,
) -> None:
    """It succeeds."""
    cookiecutter, instance = cookiecutter_repository, cookiecutter_instance_repository
    path = Path("README.md")
    text = "Lorem Ipsum\n"

    with branch(instance, "topic"):
        append(instance, path, text)
        commit(instance, path)

    retrocookie("topic", path=cookiecutter.path, url=str(instance.path))

    with branch(cookiecutter, "topic"):
        assert text in read(cookiecutter, in_template(path))
