"""Tests for git interface."""
from pathlib import Path
from typing import Dict

import pytest
from pytest import MonkeyPatch

from retrocookie import git
from retrocookie.utils import chdir

from .helpers import branch
from .helpers import commit
from .helpers import touch
from .helpers import write


@pytest.fixture
def repository(tmp_path: Path) -> git.Repository:
    """Initialize repository in a temporary directory."""
    return git.Repository.init(tmp_path / "repository")


@pytest.mark.parametrize(
    "config,expected",
    [
        ({}, "master"),
        ({"init.defaultBranch": "main"}, "main"),
    ],
)
def test_get_default_branch(
    config: Dict[str, str], expected: str, monkeypatch: MonkeyPatch
) -> None:
    """It returns the default branch."""
    monkeypatch.setattr("pygit2.Config.get_global_config", dict)
    monkeypatch.setattr("pygit2.Config.get_system_config", lambda: config)

    assert expected == git.get_default_branch()


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


def test_exists_true(repository: git.Repository) -> None:
    """It returns True if the file exists."""
    path = Path("README.md")
    touch(repository, path)

    assert repository.exists(path)


def test_exists_false(repository: git.Repository) -> None:
    """It returns False if the file does not exist."""
    path = Path("README.md")
    commit(repository)  # ensure HEAD exists

    assert not repository.exists(path)


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

    touch(repository, readme)

    with branch(repository, "install", create=True):
        touch(repository, install)

    repository.cherrypick("install")

    repository.repo.index.read()  # refresh stale index
    assert "INSTALL" in {e.path for e in repository.repo.index}


def test_cherrypick_worktree(repository: git.Repository) -> None:
    """It updates the worktree from the cherry-pick."""
    readme, install = map(Path, ("README", "INSTALL"))

    touch(repository, readme)

    with branch(repository, "install", create=True):
        touch(repository, install)

    repository.cherrypick("install")

    assert (repository.path / install).exists()


def test_cherrypick_conflict(repository: git.Repository) -> None:
    """It raises an exception if the cherry-pick results in conflicts."""
    path = Path("README")

    touch(repository, path)

    with branch(repository, "topic", create=True):
        write(repository, path, "a")

    write(repository, path, "b")

    with pytest.raises(Exception, match="conflict"):
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


def test_fetch_relative_path(repository: git.Repository) -> None:
    """It fetches from a relative path."""
    source_path = Path("..") / "another"
    path = Path("README")

    with chdir(repository.path):
        source = git.Repository.init(source_path)
        commit = touch(source, path)

        repository.fetch_commits(source, commit)

    assert repository.read_text(path, ref=commit) == ""


def test_add_worktree(repository: git.Repository, tmp_path: Path) -> None:
    """It creates a worktree."""
    commit(repository)

    path = tmp_path / "worktree"
    repository.add_worktree("branch", path)

    assert path.exists()


@pytest.mark.parametrize("force", [False, True])
def test_remove_worktree(
    repository: git.Repository, tmp_path: Path, force: bool
) -> None:
    """It removes the worktree."""
    commit(repository)

    path = tmp_path / "worktree"
    repository.add_worktree("branch", path)
    repository.remove_worktree(path, force=force)

    assert not path.exists()


def test_worktree(repository: git.Repository, tmp_path: Path) -> None:
    """It creates and removes a worktree."""
    commit(repository)

    path = tmp_path / "worktree"
    with repository.worktree("branch", path):
        assert path.exists()

    assert not path.exists()


@pytest.mark.parametrize(
    "version,expected",
    [
        # fmt: off
        ("0.99",             git.Version(major=0, minor=99, patch=0)),
        ("0.99.9n",          git.Version(major=0, minor=99, patch=9)),
        ("1.0rc6",           git.Version(major=1, minor=0,  patch=0)),
        ("1.0.0",            git.Version(major=1, minor=0,  patch=0)),
        ("1.0.0b",           git.Version(major=1, minor=0,  patch=0)),
        ("1.8.5.6",          git.Version(major=1, minor=8,  patch=5)),
        ("1.9-rc2",          git.Version(major=1, minor=9,  patch=0)),
        ("2.4.12",           git.Version(major=2, minor=4,  patch=12)),
        ("2.29.2.windows.3", git.Version(major=2, minor=29, patch=2)),  # GitHub Actions
        ("2.30.0",           git.Version(major=2, minor=30, patch=0)),
        ("2.30.0-rc0",       git.Version(major=2, minor=30, patch=0)),
        ("2.30.0-rc2",       git.Version(major=2, minor=30, patch=0)),
        # fmt: on
    ],
)
def test_valid_version(version: str, expected: git.Version) -> None:
    """It produces the expected version."""
    assert expected == git.Version.parse(version)


@pytest.mark.parametrize(
    "version",
    [
        "",
        "0",
        "1",
        "a",
        "1a",
        "1.a",
        "1a.0.0",
        "lorem.1.0.0",
        "1:1.0.0",
    ],
)
def test_invalid_version(version: str) -> None:
    """It raises an exception."""
    with pytest.raises(ValueError):
        git.Version.parse(version)
