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


def guess_remote_url() -> str:
    """Guess the URL of the template instance."""
    url = git.get_remote_url("origin")
    if url.endswith(".git"):
        url = url[: -len(".git")]
    return f"{url}-instance.git"


def find_template_directory() -> Path:
    """Locate the subdirectory with the project template."""
    tokens = "{{", "cookiecutter", "}}"
    for path in Path.cwd().iterdir():
        if path.is_dir() and all(x in path.name for x in tokens):
            return path
    raise Exception("cannot find template directory")


def load_context(repository: Path) -> Dict[str, str]:
    """Load the context from the .cookiecutter.json file."""
    path = repository / ".cookiecutter.json"
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


def local(ref: str) -> str:
    """Prefix ref by NAMESPACE."""
    return f"{NAMESPACE}/{ref}"


def remote(ref: str) -> str:
    """Prefix ref by REMOTE."""
    return f"{REMOTE}/{ref}"


def fetch_commits(url: str, ref: str, base: str) -> None:
    """Fetch commits from the template instance."""
    git.add_remote(REMOTE, url)
    git.fetch_remote(REMOTE, ref, base)
    git.create_branch(local(ref), remote(ref))
    git.create_branch(local(base), remote(base))
    git.remove_remote(REMOTE)


def rewrite_commits(
    template_directory: Path,
    whitelist: Container[str],
    blacklist: Container[str],
    directory: Path,
) -> None:
    """Rewrite commits for template."""
    context = load_context(directory)
    replacements = get_replacements(context, whitelist, blacklist)
    git.filter_branch(
        subdirectory=template_directory.name, replacements=replacements, cwd=directory,
    )


def harvest_commits(branch: str, base: str, ref: str, onto: str) -> None:
    """Rebase commits and clean up."""
    git.rebase(local(base), local(ref), f"--onto={onto}")
    git.move_branch(local(ref), branch)
    git.remove_branch(local(base))


@contextlib.contextmanager
def temporary_repository(url: str) -> Iterator[Path]:
    """Clone URL to temporary directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        directory = Path(tmpdir) / "instance"
        git.clone(url, directory)
        yield directory


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
    cleanup()

    if url is None:
        url = guess_remote_url()

    if branch is None:
        branch = ref

    template_directory = find_template_directory()
    onto = git.get_current_branch()

    with temporary_repository(url) as directory:
        rewrite_commits(template_directory, whitelist, blacklist, directory)
        fetch_commits(str(directory), ref, base)

    harvest_commits(branch, base, ref, onto)


def cleanup() -> None:
    """Remove branches and remotes created by this program."""
    if git.get_current_branch().startswith(NAMESPACE):
        git.switch_branch("master")

    for branch in git.find_branches(NAMESPACE):
        git.remove_branch(branch)

    if git.exists_remote(REMOTE):
        git.remove_remote(REMOTE)
