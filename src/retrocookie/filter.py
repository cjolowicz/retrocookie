"""Interface for git-filter-repo."""
import contextlib
import os
from pathlib import Path
from typing import Iterator
from typing import Iterable
from typing import Tuple

from git_filter_repo import Blob
from git_filter_repo import FilteringOptions
from git_filter_repo import RepoFilter

from . import git


@contextlib.contextmanager
def chdir(path: Path) -> Iterator[None]:
    """Context manager for changing the directory."""
    old = Path.cwd()
    os.chdir(path)

    try:
        yield
    finally:
        os.chdir(old)


class RepositoryFilter:
    """Perform path and blob replacements on repository."""

    def __init__(
        self,
        repository: git.Repository,
        path: Path,
        replacements: Iterable[Tuple[str, str]],
    ) -> None:
        self.repository = repository
        self.path = str(path).encode()
        self.replacements = [(old.encode(), new.encode()) for old, new in replacements]

    def filename_callback(self, filename: bytes) -> bytes:
        for old, new in self.replacements:
            filename = filename.replace(old, new)
        return b"/".join((self.path, filename))

    def blob_callback(self, blob: Blob) -> None:
        for old, new in self.replacements:
            blob.data = blob.data.replace(old, new)

    def _create_filter(self) -> RepoFilter:
        args = FilteringOptions.parse_args([], error_on_empty=False)
        return RepoFilter(
            args,
            filename_callback=self.filename_callback,
            blob_callback=self.blob_callback,
        )

    def run(self) -> None:
        with chdir(self.repository.path):
            repofilter = self._create_filter()
            repofilter.run()


def filter_repository(
    repository: git.Repository, path: Path, replacements: Iterable[Tuple[str, str]],
) -> None:
    repofilter = RepositoryFilter(repository, path, replacements)
    repofilter.run()
