"""Fixtures for retrocookie.pr."""
from pathlib import Path

import pytest
from tests.pr.unit.fakes.github import API as FakeAPI  # noqa: N811

from retrocookie.pr.cache import Cache
from retrocookie.pr.protocols import github


@pytest.fixture
def cache(tmp_path: Path) -> Cache:
    """Return a cache."""
    return Cache(tmp_path / "cache")


@pytest.fixture
def api(tmp_path: Path) -> github.API:
    """Return a fake GitHub API."""
    return FakeAPI(_backend=tmp_path / "github")
