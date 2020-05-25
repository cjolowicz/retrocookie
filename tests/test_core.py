"""Tests for core module."""
from pathlib import Path
from typing import Optional

import pytest
from retrocookie import core
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


def test_guess_instance_url_fails(tmp_path: Path) -> None:
    """It raises an exception when there is no remote URL."""
    repository = git.Repository.init(tmp_path)
    with pytest.raises(Exception):
        core.guess_instance_url(repository)


@pytest.mark.parametrize(
    "url", ["https://example.com/user/repo.git", "https://example.com/user/repo",]
)
def test_guess_instance_url_succeeds(tmp_path: Path, url: str) -> None:
    """It returns an instance URL based on the cookiecutter's remote URL."""
    repository = git.Repository.init(tmp_path)
    repository.add_remote("origin", url)
    url = core.guess_instance_url(repository)
    assert url.endswith("-instance.git")


def test_find_template_directory_fails(tmp_path: Path) -> None:
    """It raises an exception when there is no template directory."""
    repository = git.Repository.init(tmp_path)
    with pytest.raises(Exception):
        core.find_template_directory(repository)


def test_temporary_remote_overwrites_existing(tmp_path: Path) -> None:
    """It replaces an existing remote."""
    repository = git.Repository.init(tmp_path)
    repository.add_remote("upstream", "stale")

    with core.temporary_remote(repository, "upstream", "location"):
        assert "location" == repository.get_remote_url("upstream")


def test_temporary_remote_skips_non_existing(tmp_path: Path) -> None:
    """It replaces an existing remote."""
    repository = git.Repository.init(tmp_path)

    with core.temporary_remote(repository, "upstream", "location"):
        repository.remove_remote("upstream")

    assert not repository.exists_remote("upstream")

