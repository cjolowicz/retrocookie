"""Retrocookie interface."""
from pathlib import Path

from retrocookie import retrocookie as _retrocookie


def retrocookie(repository: Path, *, branch: str, upstream: str, path: Path) -> None:
    """Wrap retrocookie.retrocookie with protocols.Retrocookie signature."""
    _retrocookie(repository, branch=branch, upstream=upstream, path=path)
