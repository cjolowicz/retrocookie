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

    def __init__(
        self, path: Optional[Path] = None, repo: Optional[pygit2.Repository] = None,
    ) -> None:
        """Initialize."""
        self.path = path or Path.cwd()
        self.repo = repo or pygit2.Repository(self.path)

    def _git(
        self, *args: str, check: bool = True, **kwargs: Any
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(["git", *args], check=check, cwd=self.path, **kwargs)

    @classmethod
    def clone(cls, url: str, path: Path) -> "Repository":
        """Clone the repository."""
        repo = pygit2.clone_repository(url, path)
        return cls(path, repo)

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

    def remove_branch(self, branch: str) -> None:
        """Remove the branch."""
        self.repo.branches.delete(branch)

    def get_current_branch(self) -> str:
        """Return the current branch."""
        return self.repo.head.shorthand  # type: ignore[no-any-return]

    def switch_branch(self, branch: str) -> None:
        """Switch the current branch."""
        self.repo.checkout(self.repo.branches[branch])

    def find_branches(self, namespace: str) -> List[str]:
        """Find branches under the given namespace."""
        return [
            branch
            for branch in self.repo.branches.local
            if branch.startswith(f"{namespace}/")
        ]

    def rebase(self, upstream: str, branch: str, onto: str) -> None:
        """Rebase."""
        self._git("rebase", upstream, branch, f"--onto={onto}")

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
            self._git("filter-repo", *options)
