"""Utilities."""
import contextlib
import os
import tempfile
from pathlib import Path
from typing import Iterator

from . import git


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
