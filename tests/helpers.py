"""Utilities for testing."""
import contextlib
from pathlib import Path
from typing import Iterator

from retrocookie import git


AUTHOR = "user"
AUTHOR_EMAIL = "user@example.com"


def read(repository: git.Repository, path: Path) -> str:
    path = repository.path / path
    return path.read_text()


def write(repository: git.Repository, path: Path, text: str) -> None:
    path = repository.path / path
    path.write_text(text)


def append(repository: git.Repository, path: Path, text: str) -> None:
    text = read(repository, path) + text
    write(repository, path, text)


@contextlib.contextmanager
def branch(repository: git.Repository, branch: str) -> Iterator[None]:
    original = repository.get_current_branch()

    if not repository.exists_branch(branch):
        repository.create_branch(branch)

    repository.switch_branch(branch)

    try:
        yield
    finally:
        repository.switch_branch(original)


def commit(repository: git.Repository, path: Path) -> None:
    repository.add(path)
    repository.commit(
        author=AUTHOR, author_email=AUTHOR_EMAIL, message=f"Update {path}"
    )


def in_template(path: Path) -> Path:
    return "{{ cookiecutter.project_slug }}" / path


