"""Git interface."""
import subprocess  # noqa: S404
from pathlib import Path
from typing import Any
from typing import Optional

import pygit2


class Repository:
    """Git repository."""

    def __init__(
        self, path: Optional[Path] = None, *, repo: Optional[pygit2.Repository] = None
    ) -> None:
        """Initialize."""
        self.path = path or Path.cwd() if repo is None else Path(repo.path).parent
        self.repo = repo or pygit2.Repository(self.path)

    def git(
        self, *args: str, check: bool = True, **kwargs: Any
    ) -> "subprocess.CompletedProcess[str]":
        """Invoke git."""
        # FIXME: Use `from __future__ import annotations` instead of quoting.
        # This requires Python 3.7+.
        return subprocess.run(  # noqa: S603,S607
            ["git", *args], check=check, cwd=self.path, **kwargs
        )

    @classmethod
    def init(cls, path: Path) -> "Repository":
        """Create a repository."""
        repo = pygit2.init_repository(path)
        return cls(path, repo=repo)

    @classmethod
    def clone(cls, url: str, path: Path) -> "Repository":
        """Clone the repository."""
        # pygit2 wheels for Windows and macOS lack SSH support.
        # https://github.com/libgit2/pygit2/issues/994
        subprocess.run(  # noqa: S603,S607
            ["git", "clone", url, str(path)], check=True,
        )
        return cls(path)

    def exists_remote(self, remote: str) -> bool:
        """Return True if the remote exists."""
        return remote in {r.name for r in self.repo.remotes}

    def add_remote(self, remote: str, url: str) -> None:
        """Add the remote with the given URL."""
        self.repo.remotes.create(remote, url)

    def remove_remote(self, remote: str) -> None:
        """Remove the remote."""
        self.repo.remotes.delete(remote)

    def get_remote_url(self, remote: str) -> str:
        """Return the URL of the remote."""
        return self.repo.remotes[remote].url  # type: ignore[no-any-return]

    def fetch_remote(self, remote: str, *refs: str) -> None:
        """Fetch ref from the remote."""
        self.repo.remotes[remote].fetch(refspecs=list(refs))  # FIXME: --no-tags?

    def create_branch(self, branch: str, ref: Optional[str] = None) -> None:
        """Create a branch."""
        if ref is None:
            commit = self.repo[self.repo.head.target]
        else:
            commit = self.repo.branches[ref].peel()
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

    def rebase(self, upstream: str, branch: str, onto: str) -> None:
        """Rebase."""
        self.git("rebase", upstream, branch, f"--onto={onto}")

    def add(self, *paths: Path) -> None:
        """Add paths to the index."""
        for path in paths:
            self.repo.index.add(
                path.relative_to(self.path) if path.is_absolute() else path
            )
        else:
            self.repo.index.add_all()
        self.repo.index.write()

    def commit(
        self,
        *,
        author: str,
        author_email: str,
        message: str,
        committer: Optional[str] = None,
        committer_email: Optional[str] = None,
    ) -> None:
        """Create a commit."""
        if committer is None:
            committer = author

        if committer_email is None:
            committer_email = author_email

        author_signature = pygit2.Signature(author, author_email)
        committer_signature = pygit2.Signature(committer, committer_email)

        try:
            head = self.repo.head
            refname = head.name
            parents = [head.target]
        except pygit2.GitError:
            refname = "refs/heads/master"
            parents = []

        tree = self.repo.index.write_tree()

        self.repo.create_commit(
            refname, author_signature, committer_signature, message, tree, parents
        )
