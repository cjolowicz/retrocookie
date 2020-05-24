"""Core module."""
import contextlib
import json
import tempfile
from pathlib import Path
from typing import cast
from typing import Container
from typing import Dict
from typing import Iterator
from typing import List
from typing import Optional
from typing import Tuple

from . import git


NAMESPACE = "retrocookie"
REMOTE = "retrocookie-instance"


def guess_remote_url(repository: git.Repository) -> str:
    """Guess the URL of the template instance."""
    url = repository.get_remote_url("origin")
    if url.endswith(".git"):
        url = url[: -len(".git")]
    return f"{url}-instance.git"


def find_template_directory(repository: git.Repository) -> Path:
    """Locate the subdirectory with the project template."""
    tokens = "{{", "cookiecutter", "}}"
    for path in repository.path.iterdir():
        if path.is_dir() and all(x in path.name for x in tokens):
            return path
    raise Exception("cannot find template directory")


def load_context(repository: git.Repository) -> Dict[str, str]:
    """Load the context from the .cookiecutter.json file."""
    path = repository.path / ".cookiecutter.json"
    with path.open() as io:
        return cast(Dict[str, str], json.load(io))


def get_replacements(
    context: Dict[str, str], whitelist: Container[str], blacklist: Container[str],
) -> List[Tuple[str, str]]:
    """Create replacements to be applied to commits from the template instance."""

    def ref(key: str) -> str:
        return f"{{{{cookiecutter.{key}}}}}"

    replacements = [
        (value, ref(key))
        for key, value in context.items()
        if key not in blacklist and not (whitelist and key not in whitelist)
    ]
    replacements.extend(
        [(token, token.join(('{{ "', '" }}'))) for token in ("{{", "}}")]
    )

    return replacements


def _local(ref: str) -> str:
    """Prefix ref by NAMESPACE."""
    return f"{NAMESPACE}/{ref}"


def _remote(ref: str) -> str:
    """Prefix ref by REMOTE."""
    return f"{REMOTE}/{ref}"


def rewrite_commits(
    repository: git.Repository,
    template_directory: Path,
    whitelist: Container[str],
    blacklist: Container[str],
) -> None:
    """Rewrite the repository using template variables."""
    context = load_context(repository)
    replacements = get_replacements(context, whitelist, blacklist)
    repository.filter_repo(
        subdirectory=template_directory.name, replacements=replacements
    )


def fetch_commits(
    repository: git.Repository, remote: git.Repository, base: str, ref: str
) -> None:
    """Fetch the rewritten commits."""
    repository.add_remote(REMOTE, str(remote.path))
    repository.fetch_remote(REMOTE, base, ref)


def harvest_commits(
    repository: git.Repository, branch: str, base: str, ref: str
) -> None:
    """Rebase commits onto branch and fast-forward."""
    repository.create_branch(_local(ref), _remote(ref))
    repository.rebase(_remote(base), _local(ref), onto=branch)
    repository.switch_branch(branch)
    repository.merge_ff(_local(ref))


@contextlib.contextmanager
def temporary_repository(url: str) -> Iterator[git.Repository]:
    """Clone URL to temporary directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        directory = Path(tmpdir) / "instance"
        yield git.Repository.clone(url, directory)


@contextlib.contextmanager
def temporary_worktree(
    repository: git.Repository, branch: str
) -> Iterator[git.Repository]:
    """Use a temporary worktree creating the given branch."""
    with tempfile.TemporaryDirectory() as tmpdir:
        directory = Path(tmpdir) / branch
        repository.add_worktree(branch, directory)

        try:
            yield git.Repository(directory)
        finally:
            repository.remove_worktree(directory)


def cleanup() -> None:
    """Remove branches and remotes created by this program."""
    repository = git.Repository()

    if repository.get_current_branch().startswith(NAMESPACE):
        repository.switch_branch("master")

    for branch in repository.find_branches(NAMESPACE):
        repository.remove_branch(branch)

    if repository.exists_remote(REMOTE):
        repository.remove_remote(REMOTE)


@contextlib.contextmanager
def cleaning() -> Iterator[None]:
    """Invoke cleanup on enter and exit."""
    cleanup()
    try:
        yield
    finally:
        cleanup()


def retrocookie(
    ref: str,
    *,
    base: str = "master",
    branch: Optional[str] = None,
    url: Optional[str],
    whitelist: Container[str] = (),
    blacklist: Container[str] = (),
) -> None:
    """Import commits from instance repository into template repository."""
    repository = git.Repository()
    template_directory = find_template_directory(repository)

    if url is None:
        url = guess_remote_url(repository)

    if branch is None:
        branch = ref

    with temporary_repository(url) as remote:
        rewrite_commits(remote, template_directory, whitelist, blacklist)

        with cleaning():
            fetch_commits(repository, remote, base, ref)

            with temporary_worktree(repository, branch) as worktree:
                harvest_commits(worktree, branch, base, ref)
