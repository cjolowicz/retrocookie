"""Tests for git interface."""
from pathlib import Path

import pytest

from .helpers import branch
from .helpers import commit
from .helpers import write
from retrocookie import git


@pytest.fixture
def repository(tmp_path: Path) -> git.Repository:
    """Initialize repository in a temporary directory."""
    return git.Repository.init(tmp_path)


def test_commit(repository: git.Repository) -> None:
    """It creates a commit."""
    repository.commit("Empty")


def test_read_text(repository: git.Repository) -> None:
    """It returns the file contents."""
    path = repository.path / "README.md"
    path.write_text("# example\n")

    repository.add(path)
    repository.commit(f"Add {path}")

    assert path.read_text() == repository.read_text(path)


def test_cherrypick(repository: git.Repository) -> None:
    """It applies a commit from another branch."""
    # Add README on master.
    readme = repository.path / "README.md"
    readme.write_text("# example\n")

    repository.add()
    repository.commit("Initial")

    # Add .gitignore on topic.
    with branch(repository, "topic", create=True):
        ignore = repository.path / ".gitignore"
        ignore_text = "*.pyc\n"
        ignore.write_text(ignore_text)

        repository.add()
        repository.commit("Ignore *.pyc")

    # Append <message> to README, on master.
    with readme.open(mode="a") as io:
        message = "\nHello, world!\n"
        io.write(message)

    repository.add()
    repository.commit("Update")

    # Cherry-pick the .gitignore onto master.
    repository.cherrypick("topic")

    assert ignore_text == repository.read_text(ignore)
    assert message in repository.read_text(readme)


def test_cherrypick_index(repository: git.Repository) -> None:
    """It updates the index from the cherry-pick."""
    readme, install = map(Path, ("README", "INSTALL"))

    write(repository, readme, "")

    with branch(repository, "install", create=True):
        write(repository, install, "")

    repository.cherrypick("install")

    assert "INSTALL" in {e.path for e in repository.repo.index}


def test_cherrypick_worktree(repository: git.Repository) -> None:
    """It updates the worktree from the cherry-pick."""
    readme, install = map(Path, ("README", "INSTALL"))

    write(repository, readme, "")

    with branch(repository, "install", create=True):
        write(repository, install, "")

    repository.cherrypick("install")

    assert (repository.path / install).exists()


def test_cherrypick_conflict(repository: git.Repository) -> None:
    """It raises an exception if the cherry-pick results in conflicts."""
    path = Path("README")

    write(repository, path, "")

    with branch(repository, "topic", create=True):
        write(repository, path, "a")

    write(repository, path, "b")

    with pytest.raises(git.Conflict):
        repository.cherrypick("topic")


def test_parse_revisions(repository: git.Repository) -> None:
    """It returns the hashes on topic for the range expression ``..topic``."""
    commit(repository)

    with branch(repository, "topic", create=True):
        expected = [commit(repository), commit(repository)]

    revisions = repository.parse_revisions("..topic")

    assert revisions == expected


def test_lookup_replacement(repository: git.Repository) -> None:
    """It returns the replacement ref for a replaced ref."""
    first, second = commit(repository), commit(repository)

    repository.git("replace", second, first)

    assert first == repository.lookup_replacement(second)
