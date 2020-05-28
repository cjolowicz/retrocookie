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
def temporary_repository(url: str) -> Iterator[git.Repository]:
    """Clone URL to temporary directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        directory = Path(tmpdir) / "instance"
        yield git.Repository.clone(url, directory)


@contextlib.contextmanager
def temporary_remote(
    repository: git.Repository, remote: str, url: str
) -> Iterator[None]:
    """Add remote on entry, remove it on exit."""
    if repository.exists_remote(remote):
        repository.remove_remote(remote)

    repository.add_remote(remote, url)

    try:
        yield
    finally:
        if repository.exists_remote(remote):
            repository.remove_remote(remote)
