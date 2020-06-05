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
def temporary_repository(path: Path) -> Iterator[git.Repository]:
    """Clone repository to temporary directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        directory = Path(tmpdir) / "instance"
        yield git.Repository.clone(str(path), directory, mirror=True)
