"""Tests for git interface."""
from pathlib import Path

from retrocookie import git


def test_commit(tmp_path: Path) -> None:
    """It creates a commit."""
    repository = git.Repository.init(tmp_path)
    repository.commit("Empty")
