"""Fixtures for retrocookie.pr."""
from pathlib import Path

import pytest

from retrocookie.pr.cache import Cache


@pytest.fixture
def cache(tmp_path: Path) -> Cache:
    """Return a cache."""
    return Cache(tmp_path / "cache")
