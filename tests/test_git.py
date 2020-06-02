"""Tests for git interface."""
from pathlib import Path

from retrocookie import git


def test_commit(tmp_path: Path) -> None:
    """It creates a commit."""
    repository = git.Repository.init(tmp_path)
    repository.commit("Empty")


def test_read_text(tmp_path: Path) -> None:
    """It returns the file contents."""
    path = tmp_path / "README.md"
    path.write_text("# example\n")

    repository = git.Repository.init(tmp_path)
    repository.add(path)
    repository.commit(f"Add {path}")

    assert path.read_text() == repository.read_text(path)
