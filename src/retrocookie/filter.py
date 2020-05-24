"""Interface for git-filter-repo."""
import contextlib
import os
from pathlib import Path
from typing import Iterator
from typing import List
from typing import Tuple

from git_filter_repo import Blob
from git_filter_repo import FilteringOptions
from git_filter_repo import RepoFilter

from . import git


class RepositoryFilter:
    """Perform path and blob replacements on repository."""

    def __init__(self, subdirectory: str, replacements: List[Tuple[str, str]]) -> None:
        self.subdirectory = subdirectory.encode()
        self.replacements = [(old.encode(), new.encode()) for old, new in replacements]

    def filename_callback(self, filename: bytes) -> bytes:
        for old, new in self.replacements:
            filename = filename.replace(old, new)
        return b"/".join((self.subdirectory, filename))

    def blob_callback(self, blob: Blob) -> None:
        for old, new in self.replacements:
            blob.data = blob.data.replace(old, new)

    def run(self) -> None:
        args = FilteringOptions.parse_args([], error_on_empty=False)
        self.repofilter = RepoFilter(
            args,
            filename_callback=self.filename_callback,
            blob_callback=self.blob_callback,
        )
        self.repofilter.run()


@contextlib.contextmanager
def chdir(path: Path) -> Iterator[None]:
    """Context manager for changing the directory."""
    old = Path.cwd()
    os.chdir(path)

    try:
        yield
    finally:
        os.chdir(old)


def filter_repository(
    repository: git.Repository, subdirectory: str, replacements: List[Tuple[str, str]]
) -> None:
    with chdir(repository.path):
        filter = RepositoryFilter(subdirectory, replacements)
        filter.run()
