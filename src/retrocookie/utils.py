"""Utilities."""
import contextlib
import os
import tempfile
from pathlib import Path
from typing import Iterator

from . import git


def removeprefix(string: str, prefix: str) -> str:
    """Remove prefix from string, if present."""
    return string[len(prefix) :] if string.startswith(prefix) else string


def removesuffix(string: str, suffix: str) -> str:
    """Remove suffix from string, if present."""
    return string[: -len(suffix)] if suffix and string.endswith(suffix) else string


@contextlib.contextmanager
def chdir(path: Path) -> Iterator[None]:
    """Context manager for changing the directory."""
    cwd = Path.cwd()
    os.chdir(path)

    try:
        yield
    finally:
        os.chdir(cwd)


@contextlib.contextmanager
def temporary_repository() -> Iterator[git.Repository]:
    """Create repository in temporary directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir)
        yield git.Repository.init(path)
