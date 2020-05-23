"""Git interface."""
import subprocess  # noqa: S404
import tempfile
from pathlib import Path
from typing import List
from typing import Optional
from typing import Tuple


def clone(url: str, directory: Path) -> None:
    """Clone the repository."""
    subprocess.run(["git", "clone", url, str(directory)], check=True)


def exists_remote(remote: str) -> bool:
    """Return True if the remote exists."""
    process = subprocess.run(
        ["git", "remote"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
        check=True,
    )
    remotes = process.stdout.split()
    return remote in remotes


def add_remote(remote: str, url: str) -> None:
    """Add the remote with the given URL."""
    subprocess.run(["git", "remote", "add", remote, url], check=True)


def remove_remote(remote: str) -> None:
    """Remove the remote."""
    subprocess.run(["git", "remote", "remove", remote], check=True)


def get_remote_url(remote: str) -> str:
    """Return the URL of the remote."""
    process = subprocess.run(
        ["git", "remote", "get-url", remote],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
        check=True,
    )
    return process.stdout.strip()


def fetch_remote(remote: str, *refs: str) -> None:
    """Fetch ref from the remote."""
    subprocess.run(["git", "fetch", "--no-tags", remote, *refs], check=True)


def create_branch(branch: str, ref: str) -> None:
    """Create a branch."""
    subprocess.run(
        ["git", "switch", "--create", branch, ref], check=True,
    )


def exists_branch(branch: str) -> bool:
    """Return True if the branch exists."""
    process = subprocess.run(
        ["git", "show-ref", "--verify", "--quiet", "refs/heads/{branch}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
    )
    return process.returncode == 0


def remove_branch(branch: str) -> None:
    """Remove the branch."""
    subprocess.run(["git", "branch", "--delete", "--force", branch], check=True)


def get_current_branch() -> str:
    """Return the current branch."""
    process = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
        check=True,
    )
    return process.stdout.strip()


def switch_branch(branch: str) -> None:
    """Switch the current branch."""
    subprocess.run(["git", "switch", branch], check=True)


def move_branch(*args: str) -> None:
    """Move the branch."""
    subprocess.run(["git", "branch", "--move", *args], check=True)


def find_branches(namespace: str) -> List[str]:
    """Find branches under the given namespace."""
    process = subprocess.run(
        [
            "git",
            "for-each-ref",
            "--format=%(refname:short)",
            f"refs/heads/{namespace}/",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
        check=True,
    )
    return process.stdout.split()


def rebase(*args: str) -> None:
    """Rebase."""
    subprocess.run(["git", "rebase", *args], check=True)


def filter_branch(
    subdirectory: str, replacements: List[Tuple[str, str]], cwd: Optional[Path] = None,
) -> None:
    """Rewrite commits from the template instance to use template variables."""
    command = [
        "git",
        "filter-repo",
        f"--to-subdirectory-filter={subdirectory}",
        *(f"--path-rename={old}:{new}" for old, new in replacements),
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        replacements_file = Path(tmpdir) / "replacements.txt"
        replacements_file.write_text(
            "\n".join(f"{old}==>{new}" for old, new in replacements)
        )

        command.append(f"--replace-text={replacements_file}")
        subprocess.run(command, check=True, cwd=cwd)
