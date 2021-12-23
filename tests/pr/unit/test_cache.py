"""Tests for retrocookie.pr.cache."""
from pathlib import Path

import pytest

from retrocookie import git
from retrocookie.pr.cache import Cache
from tests.helpers import commit


@pytest.fixture
def repository(tmp_path: Path) -> git.Repository:
    """Return a repository."""
    repository = git.Repository.init(tmp_path / "repository")
    repository.commit("")
    return repository


@pytest.fixture
def url(repository: git.Repository) -> str:
    """Return a repository URL."""
    return f"file://{repository.path.resolve()}"


def test_repository_clone(cache: Cache, url: str) -> None:
    """It clones the repository within the cache directory."""
    clone = cache.repository(url)
    assert cache.path in clone.path.parents


def test_repository_idempotent(cache: Cache, url: str) -> None:
    """It returns the same repository as before."""
    clone1 = cache.repository(url)
    clone2 = cache.repository(url)
    assert clone1.path == clone2.path


def test_repository_update(cache: Cache, url: str, repository: git.Repository) -> None:
    """It updates the repository from its remote."""
    cache.repository(url)
    sha1 = commit(repository)
    clone = cache.repository(url)
    assert sha1 == clone.repo.head.target.hex


def test_worktree(cache: Cache, url: str) -> None:
    """It creates a worktree for the given branch."""
    repository = cache.repository(url)
    with cache.worktree(repository, "branch") as worktree:
        assert "branch" == worktree.get_current_branch()


def test_token_roundtrip(cache: Cache) -> None:
    """It saves and loads the token."""
    cache.save_token("token")
    assert "token" == cache.load_token()


def test_load_invalid_token(cache: Cache) -> None:
    """It rejects invalid tokens on load."""
    cache.save_token("token")
    path = cache.path / "token.json"
    path.write_text('{"token": 666}')
    with pytest.raises(TypeError):
        cache.load_token()
