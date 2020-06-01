"""Git interface."""
from __future__ import annotations

import subprocess  # noqa: S404
from pathlib import Path
from typing import Any
from typing import cast
from typing import List
from typing import Optional

import pygit2


def git(
    *args: str, check: bool = True, **kwargs: Any
) -> subprocess.CompletedProcess[str]:
    """Invoke git."""
    return subprocess.run(["git", *args], check=check, **kwargs)  # noqa: S603,S607


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

    @classmethod
    def clone(cls, url: str, path: Path, *, mirror: bool = False) -> Repository:
        """Clone the repository."""
        # pygit2 wheels for Windows and macOS lack SSH support.
        # https://github.com/libgit2/pygit2/issues/994
        options = ["--mirror"] if mirror else []
        git("clone", *options, url, str(path))
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

    def parse_revisions(self, *revisions: str) -> List[str]:
        """Parse revisions using the format specified in gitrevisions(7)."""
        process = self.git(
            "rev-list", "--no-walk", *revisions, text=True, capture_output=True
        )
        return process.stdout.split()

    def rebase(self, upstream: str, branch: str, onto: str) -> None:
        """Rebase."""
        self.git("rebase", upstream, branch, f"--onto={onto}")

    def _ensure_relative(self, path: Path) -> Path:
        """Interpret the path relative to the repository root."""
        return path.relative_to(self.path) if path.is_absolute() else path

    def read_text(self, path: Path, *, ref: str = "HEAD") -> str:
        """Return the contents of the blob at the given path."""
        commit = self.repo.references[ref].peel()
        path = self._ensure_relative(path)
        blob = commit.tree / str(path)
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

    def cherrypick(self, ref: str, *, branch: Optional[str] = None) -> None:
        """Cherry-pick the commit <ref> onto <branch>."""
        commit = self.repo.revparse_single(ref)
        head = self.repo.branches[branch] if branch is not None else self.repo.head
        index = self.repo.merge_trees(commit.parents[0].tree, head, commit)
        tree = index.write_tree(self.repo)
        committer = self.repo.default_signature

        self.repo.create_commit(
            head.name, commit.author, committer, commit.message, tree, [head.target],
        )
