"""Tests for retrocookie.pr.repository."""
from retrocookie.pr.cache import Cache
from retrocookie.pr.protocols import github
from retrocookie.pr.repository import Repository


def test_repository(api: github.API, cache: Cache) -> None:
    """It loads the repository."""
    repository = Repository.load("owner/name", api=api, cache=cache)
    assert repository.clone.path.exists()
