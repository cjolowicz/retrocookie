"""Fake for retrocookie.retrocookie."""
from pathlib import Path


def retrocookie(repository: Path, *, branch: str, upstream: str, path: Path) -> None:
    """Import commits from instance repository into template repository."""
