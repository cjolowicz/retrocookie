"""Utilities for testing."""
import contextlib
from pathlib import Path
from typing import cast
from typing import Iterator

from retrocookie import git


def commit(repository: git.Repository, message: str = "") -> str:
    """Create a commit and return the hash."""
    repository.commit(message)
    return cast(str, repository.repo.head.target.hex)


def write(repository: git.Repository, path: Path, text: str) -> str:
    """Write file in repository."""
    path = repository.path / path
    path.write_text(text)
    repository.add(path)
    return commit(repository, f"Update {path.name}")


def touch(repository: git.Repository, path: Path) -> str:
    """Create an empty file in a repository."""
    path = repository.path / path
    path.touch()
    repository.add(path)
    return commit(repository, f"Touch {path.name}")


def append(repository: git.Repository, path: Path, text: str) -> None:
    """Append to file in repository."""
    text = repository.read_text(path) + text
    write(repository, path, text)


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
