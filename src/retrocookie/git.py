"""Git interface."""
from __future__ import annotations

import contextlib
import functools
import operator
import re
import subprocess  # noqa: S404
from dataclasses import dataclass
from dataclasses import field
from pathlib import Path
from typing import Any
from typing import cast
from typing import Iterator
from typing import List
from typing import Optional

import pygit2

from retrocookie.utils import removeprefix


def git(
    *args: str, check: bool = True, **kwargs: Any
) -> subprocess.CompletedProcess[str]:
    """Invoke git."""
    return subprocess.run(  # noqa: S603,S607
        ["git", *args], check=check, text=True, capture_output=True, **kwargs
    )


VERSION_PATTERN = re.compile(
    r"""
    (?P<major>\d+)\.
    (?P<minor>\d+)
    (\.(?P<patch>\d+))?
    """,
    re.VERBOSE,
)


@dataclass(frozen=True, order=True)
class Version:
    """Simplistic representation of git versions."""

    major: int
    minor: int
    patch: int
    _text: Optional[str] = field(default=None, compare=False)

    @classmethod
    def parse(cls, text: str) -> Version:
        """Extract major.minor[.patch] from the start of the text."""
        match = VERSION_PATTERN.match(text)

        if match is None:
            raise ValueError(f"invalid version {text!r}")

        parts = match.groupdict(default="0")

        return cls(
            int(parts["major"]), int(parts["minor"]), int(parts["patch"]), _text=text
        )

    def __str__(self) -> str:
        """Return the original representation."""
        return (
            self._text
            if self._text is not None
            else f"{self.major}.{self.minor}.{self.patch}"
        )


def version() -> Version:
    """Return the git version."""
    text = git("version").stdout.strip()
    text = removeprefix(text, "git version ")
    return Version.parse(text)


def get_default_branch() -> str:
    """Return the default branch for new repositories."""
    get_configs = [
        pygit2.Config.get_global_config,
        pygit2.Config.get_system_config,
    ]
    for get_config in get_configs:
        with contextlib.suppress(IOError, KeyError):
            config = get_config()
            branch = config["init.defaultBranch"]
            assert isinstance(branch, str)  # noqa: S101
            return branch

    return "master"


class Repository:
    """Git repository."""

    def __init__(
        self, path: Optional[Path] = None, *, repo: Optional[pygit2.Repository] = None
    ) -> None:
        """Initialize."""
        if repo is None:
            self.path = path or Path.cwd()
            self.repo = pygit2.Repository(self.path)
        else:
            self.path = Path(repo.workdir or repo.path)
            self.repo = repo

    def git(self, *args: str, **kwargs: Any) -> subprocess.CompletedProcess[str]:
        """Invoke git."""
        return git(*args, cwd=self.path, **kwargs)

    @classmethod
    def init(cls, path: Path, *, bare: bool = False) -> Repository:
        """Create a repository."""
        # https://github.com/libgit2/libgit2/issues/2849
        path.parent.mkdir(exist_ok=True, parents=True)
        repo = pygit2.init_repository(path, bare=bare)
        return cls(path, repo=repo)

    @classmethod
    def clone(cls, url: str, path: Path, *, mirror: bool = False) -> Repository:
        """Clone a repository."""
        options = ["--mirror"] if mirror else []
        git("clone", *options, url, str(path))
        return cls(path)

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

    def update_remote(self) -> None:
        """Update the remotes."""
        self.git("remote", "update")

    def fetch_commits(self, source: Repository, *commits: str) -> None:
        """Fetch the given commits and their immediate parents."""
        path = source.path.resolve()
        self.git("fetch", "--no-tags", "--depth=2", str(path), *commits)

    def push(self, remote: str, *refs: str, force: bool = False) -> None:
        """Update remote refs."""
        options = ["--force-with-lease"] if force else []
        self.git("push", *options, remote, *refs)

    def parse_revisions(self, *revisions: str) -> List[str]:
        """Parse revisions using the format specified in gitrevisions(7)."""
        process = self.git("rev-list", "--no-walk", *revisions)
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

    def exists(self, path: Path, *, ref: str = "HEAD") -> bool:
        """Return True if a blob exists at the given path."""
        commit = self.repo.revparse_single(ref)
        path = self._ensure_relative(path)
        try:
            functools.reduce(operator.truediv, path.parts, commit.tree)
            return True
        except KeyError:
            return False

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
            branch = get_default_branch()
            refname = f"refs/heads/{branch}"
            parents = []

        tree = self.repo.index.write_tree()
        author = committer = self.repo.default_signature

        self.repo.create_commit(refname, author, committer, message, tree, parents)

    def cherrypick(self, *refs: str) -> None:
        """Cherry-pick the given commits."""
        self.git("cherry-pick", *refs)

    @contextlib.contextmanager
    def worktree(
        self,
        branch: str,
        path: Path,
        *,
        base: str = "HEAD",
        force: bool = False,
        force_remove: bool = False,
    ) -> Iterator[Repository]:
        """Context manager to add and remove a worktree."""
        repository = self.add_worktree(branch, path, base=base, force=force)
        try:
            yield repository
        finally:
            self.remove_worktree(path, force=force_remove)

    def add_worktree(
        self,
        branch: str,
        path: Path,
        *,
        base: str = "HEAD",
        force: bool = False,
    ) -> Repository:
        """Add a worktree."""
        self.git(
            "worktree",
            "add",
            str(path),
            "--no-track",
            "-B" if force else "-b",
            branch,
            base,
        )

        return Repository(path)

    def remove_worktree(self, path: Path, *, force: bool = False) -> None:
        """Remove a worktree."""
        if force:
            self.git("worktree", "remove", "--force", str(path))
        else:
            self.git("worktree", "remove", str(path))
