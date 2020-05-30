"""Tests for utils module."""
from pathlib import Path

from retrocookie import git
from retrocookie.utils import temporary_remote


def test_temporary_remote_overwrites_existing(tmp_path: Path) -> None:
    """It replaces an existing remote."""
    repository = git.Repository.init(tmp_path)
    repository.add_remote("upstream", "stale")

    with temporary_remote(repository, "upstream", "location"):
        assert "location" == repository.get_remote_url("upstream")


def test_temporary_remote_skips_non_existing(tmp_path: Path) -> None:
    """It replaces an existing remote."""
    repository = git.Repository.init(tmp_path)

    with temporary_remote(repository, "upstream", "location"):
        repository.remove_remote("upstream")

    assert not repository.exists_remote("upstream")
