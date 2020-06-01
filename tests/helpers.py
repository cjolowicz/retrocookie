"""Utilities for testing."""
import contextlib
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

from retrocookie import git


def read(repository: git.Repository, path: Path) -> str:
    """Read file in repository."""
    path = repository.path / path
    return path.read_text()


def commit(repository: git.Repository, path: Path) -> None:
    """Create a commit with the path."""
    repository.add(path)
    repository.commit(f"Update {path}")


def write(repository: git.Repository, path: Path, text: str) -> None:
    """Write file in repository."""
    path = repository.path / path
    path.write_text(text)
    commit(repository, path)


def append(repository: git.Repository, path: Path, text: str) -> None:
    """Append to file in repository."""
    text = read(repository, path) + text
    write(repository, path, text)


@dataclass
class Append:
    """Append text to the file located at path."""

    path: Path
    text: str


def apply(repository: git.Repository, change: Append) -> None:
    """Apply the change to the repository."""
    append(repository, change.path, change.text)


@contextlib.contextmanager
def branch(
    repository: git.Repository, branch: str, *, create: bool = False
) -> Iterator[None]:
    """Switch to branch."""
    original = repository.get_current_branch()

    if create and not repository.exists_branch(branch):
        repository.create_branch(branch)

    repository.switch_branch(branch)

    try:
        yield
    finally:
        repository.switch_branch(original)


def in_template(path: Path) -> Path:
    """Prepend the template directory to the path."""
    return "{{ cookiecutter.project_slug }}" / path
