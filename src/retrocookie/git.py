"""Git interface."""
from __future__ import annotations

import functools
import operator
import subprocess  # noqa: S404
from pathlib import Path
from typing import Any
from typing import cast
from typing import List
from typing import Optional

import pygit2
from pygit2.index import ConflictCollection


def git(
    *args: str, check: bool = True, **kwargs: Any
) -> subprocess.CompletedProcess[str]:
    """Invoke git."""
    return subprocess.run(["git", *args], check=check, **kwargs)  # noqa: S603,S607


class Conflict(Exception):
    """Exception raised if the index has conflicts."""

    def __init__(self, conflicts: ConflictCollection):
        """Initialize."""
        super().__init__(conflicts)


class Repository:
    """Git repository."""

    def __init__(
        self, path: Optional[Path] = None, *, repo: Optional[pygit2.Repository] = None
    ) -> None:
        """Initialize."""
        self.path = path or Path.cwd() if repo is None else Path(repo.path).parent
        self.repo = repo or pygit2.Repository(self.path)

    def git(self, *args: str, **kwargs: Any) -> subprocess.CompletedProcess[str]:
        """Invoke git."""
        return git(*args, cwd=self.path, **kwargs)

    @classmethod
    def init(cls, path: Path) -> Repository:
        """Create a repository."""
        repo = pygit2.init_repository(path)
        return cls(path, repo=repo)

    def create_branch(self, branch: str, ref: str = "HEAD") -> None:
        """Create a branch."""
        commit = self.repo.revparse_single(ref)
        self.repo.branches.create(branch, commit)

    def get_current_branch(self) -> str:
        """Return the current branch."""
        return self.repo.head.shorthand  # type: ignore[no-any-return]

    def exists_branch(self, branch: str) -> bool:
        """Return True if the branch exists."""
        return branch in self.repo.branches

    def switch_branch(self, branch: str) -> None:
        """Switch the current branch."""
        self.repo.checkout(self.repo.branches[branch])

    def fetch_commits(self, source: Repository, *commits: str) -> None:
        """Fetch the given commits and their immediate parents."""
        self.git("fetch", "--no-tags", "--depth=2", str(source.path), *commits)

    def parse_revisions(self, *revisions: str) -> List[str]:
        """Parse revisions using the format specified in gitrevisions(7)."""
        process = self.git(
            "rev-list", "--no-walk", *revisions, text=True, capture_output=True
        )
        result = process.stdout.split()
        result.reverse()
        return result

    def lookup_replacement(self, commit: str) -> str:
        """Lookup the replace ref for the given commit."""
        refname = f"refs/replace/{commit}"
        ref = self.repo.lookup_reference(refname)
        return cast(str, ref.target.hex)

    def _ensure_relative(self, path: Path) -> Path:
        """Interpret the path relative to the repository root."""
        return path.relative_to(self.path) if path.is_absolute() else path

    def read_text(self, path: Path, *, ref: str = "HEAD") -> str:
        """Return the contents of the blob at the given path."""
        commit = self.repo.revparse_single(ref)
        path = self._ensure_relative(path)
        blob = functools.reduce(operator.truediv, path.parts, commit.tree)
        return cast(str, blob.data.decode())

    def add(self, *paths: Path) -> None:
        """Add paths to the index."""
        for path in paths:
            path = self._ensure_relative(path)
            self.repo.index.add(path)
        else:
            self.repo.index.add_all()
        self.repo.index.write()

    def commit(self, message: str) -> None:
        """Create a commit."""
        try:
            head = self.repo.head
            refname = head.name
            parents = [head.target]
        except pygit2.GitError:
            refname = "refs/heads/master"
            parents = []

        tree = self.repo.index.write_tree()
        author = committer = self.repo.default_signature

        self.repo.create_commit(refname, author, committer, message, tree, parents)

    def cherrypick(self, ref: str) -> None:
        """Cherry-pick the commit <ref>."""
        commit = self.repo.revparse_single(ref)
        head = self.repo.head

        self.repo.cherrypick(commit.id)
        if self.repo.index.conflicts is not None:
            raise Conflict(self.repo.index.conflicts)

        tree = self.repo.index.write_tree()
        committer = self.repo.default_signature

        self.repo.create_commit(
            head.name, commit.author, committer, commit.message, tree, [head.target],
        )

        self.repo.state_cleanup()
