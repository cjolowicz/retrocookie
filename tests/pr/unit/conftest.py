"""Fixtures for retrocookie.pr."""
from pathlib import Path
from typing import Callable
from typing import Iterator

import pytest
from tests.pr.unit.fakes.github import API as FakeAPI  # noqa: N811
from tests.pr.unit.fakes.retrocookie import retrocookie

from retrocookie.pr.base.bus import Bus
from retrocookie.pr.cache import Cache
from retrocookie.pr.protocols import github
from retrocookie.pr.protocols.retrocookie import Retrocookie
from retrocookie.pr.repository import Repository


@pytest.fixture
def bus() -> Iterator[Bus]:
    """Return the bus."""
    bus = Bus()
    with bus.events.errorhandler():
        yield bus


@pytest.fixture
def cache(tmp_path: Path) -> Cache:
    """Return a cache."""
    return Cache(tmp_path / "cache")


@pytest.fixture
def api(tmp_path: Path) -> github.API:
    """Return a fake GitHub API."""
    return FakeAPI(_backend=tmp_path / "github")


@pytest.fixture(name="retrocookie")
def fixture_retrocookie() -> Retrocookie:
    """Return a fake retrocookie function."""
    return retrocookie


@pytest.fixture
def repository(api: github.API, cache: Cache) -> Callable[[str], Repository]:
    """Return a repository factory."""

    def _repository(fullname: str) -> Repository:
        return Repository.load(fullname, api=api, cache=cache)

    return _repository
