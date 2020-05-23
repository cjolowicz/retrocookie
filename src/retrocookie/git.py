"""Git interface."""
import subprocess  # noqa: S404
import tempfile
from pathlib import Path
from typing import Any
from typing import List
from typing import Optional
from typing import Tuple


class Repository:
    """Git repository."""

    def __init__(self, path: Optional[Path] = None) -> None:
        """Initialize."""
        self.path = path or Path.cwd()

    def _git(
        self, *args: str, check: bool = True, **kwargs: Any
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(["git", *args], check=check, cwd=self.path, **kwargs)

    def add_worktree(self, branch: str, directory: Path) -> None:
        """Add a worktree at the given directory, creating the given branch."""
        self._git("worktree", "add", "-b", branch, str(directory))

    def remove_worktree(self, directory: Path) -> None:
        """Remove the worktree located at the given directory."""
        self._git("worktree", "remove", str(directory))

    def merge_ff(self, ref: str) -> None:
        """Fast-forward to ref."""
        self._git("merge", "--ff-only", ref)

    @classmethod
    def clone(cls, url: str, directory: Path) -> "Repository":
        """Clone the repository."""
        repository = cls(directory)
        subprocess.run(["git", "clone", url, str(directory)], check=True)
        return repository

    def exists_remote(self, remote: str) -> bool:
        """Return True if the remote exists."""
        process = self._git(
            "remote",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
        )
        remotes = process.stdout.split()
        return remote in remotes

    def add_remote(self, remote: str, url: str) -> None:
        """Add the remote with the given URL."""
        self._git("remote", "add", remote, url)

    def remove_remote(self, remote: str) -> None:
        """Remove the remote."""
        self._git("remote", "remove", remote)

    def get_remote_url(self, remote: str) -> str:
        """Return the URL of the remote."""
        process = self._git(
            "remote",
            "get-url",
            remote,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
        )
        return process.stdout.strip()

    def fetch_remote(self, remote: str, *refs: str) -> None:
        """Fetch ref from the remote."""
        self._git("fetch", "--no-tags", remote, *refs)

    def create_branch(self, branch: str, ref: str) -> None:
        """Create a branch."""
        self._git("switch", "--create", branch, ref)

    def remove_branch(self, branch: str) -> None:
        """Remove the branch."""
        self._git("branch", "--delete", "--force", branch)

    def get_current_branch(self) -> str:
        """Return the current branch."""
        process = self._git(
            "rev-parse",
            "--abbrev-ref",
            "HEAD",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
        )
        return process.stdout.strip()

    def switch_branch(self, branch: str) -> None:
        """Switch the current branch."""
        self._git("switch", branch)

    def move_branch(self, *args: str) -> None:
        """Move the branch."""
        self._git("branch", "--move", *args)

    def find_branches(self, namespace: str) -> List[str]:
        """Find branches under the given namespace."""
        process = self._git(
            "for-each-ref",
            "--format=%(refname:short)",
            f"refs/heads/{namespace}/",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
        )
        return process.stdout.split()

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
