"""Git interface."""
import subprocess  # noqa: S404
import tempfile
from pathlib import Path
from typing import Any
from typing import List
from typing import Optional
from typing import Tuple

import pygit2


class Repository:
    """Git repository."""

    def __init__(self, path: Optional[Path] = None) -> None:
        """Initialize."""
        self.path = path or Path.cwd()
        self.repo = pygit2.Repository(self.path)

    def git(
        self, *args: str, check: bool = True, **kwargs: Any
    ) -> "subprocess.CompletedProcess[str]":
        # FIXME: Use `from __future__ import annotations` instead of quoting.
        # This requires Python 3.7+.
        return subprocess.run(["git", *args], check=check, cwd=self.path, **kwargs)

    @classmethod
    def clone(cls, url: str, path: Path) -> "Repository":
        """Clone the repository."""
        # pygit2 wheels for Windows and macOS lack SSH support.
        subprocess.run(["git", "clone", url, str(path)], check=True)
        return cls(path)

    def exists_remote(self, remote: str) -> bool:
        """Return True if the remote exists."""
        return remote in self.repo.remotes

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

    def create_branch(self, branch: str, ref: str) -> None:
        """Create a branch."""
        commit = self.repo.branches[ref].peel()
        self.repo.branches.create(branch, commit)

    def get_current_branch(self) -> str:
        """Return the current branch."""
        return self.repo.head.shorthand  # type: ignore[no-any-return]

    def switch_branch(self, branch: str) -> None:
        """Switch the current branch."""
        self.repo.checkout(self.repo.branches[branch])

    def rebase(self, upstream: str, branch: str, onto: str) -> None:
        """Rebase."""
        self.git("rebase", upstream, branch, f"--onto={onto}")

    def filter_repo(
        self, subdirectory: str, replacements: List[Tuple[str, str]]
    ) -> None:
        """Rewrite commits from the template instance to use template variables."""
        options = [
            f"--to-subdirectory-filter={subdirectory}",
            *(f"--path-rename={old}:{new}" for old, new in replacements),
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            replacements_file = Path(tmpdir) / "replacements.txt"
            replacements_file.write_text(
                "\n".join(f"{old}==>{new}" for old, new in replacements)
            )

            options.append(f"--replace-text={replacements_file}")
            self.git("filter-repo", *options)
