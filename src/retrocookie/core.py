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
from .filter import filter_repository


def guess_instance_url(repository: git.Repository) -> str:
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
            return path.relative_to(repository.path)
    raise Exception("cannot find template directory")


def load_context(repository: git.Repository) -> Dict[str, str]:
    """Load the context from the .cookiecutter.json file."""
    path = repository.path / ".cookiecutter.json"
    with path.open() as io:
        return cast(Dict[str, str], json.load(io))


def get_replacements(
    context: Dict[str, str], whitelist: Container[str], blacklist: Container[str],
) -> List[Tuple[str, str]]:
    """Return replacements to be applied to commits from the template instance."""

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


def rewrite_commits(
    repository: git.Repository,
    template_directory: Path,
    whitelist: Container[str],
    blacklist: Container[str],
) -> None:
    """Rewrite the repository using template variables."""
    context = load_context(repository)
    replacements = get_replacements(context, whitelist, blacklist)
    filter_repository(
        repository=repository, path=template_directory, replacements=replacements,
    )


def apply_commits(
    repository: git.Repository, remote: str, base: str, ref: str, branch: Optional[str],
) -> None:
    """Create <branch> with commits from <remote>/<base>..<remote>/<ref>."""
    if branch is None:
        branch = ref

    current = repository.get_current_branch()
    repository.fetch_remote(remote, base, ref)
    repository.create_branch(branch, f"{remote}/{ref}")
    repository.rebase(upstream=f"{remote}/{base}", branch=branch, onto=current)


@contextlib.contextmanager
def temporary_repository(url: str) -> Iterator[git.Repository]:
    """Clone URL to temporary directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        directory = Path(tmpdir) / "instance"
        yield git.Repository.clone(url, directory)


@contextlib.contextmanager
def temporary_remote(
    repository: git.Repository, remote: str, url: str
) -> Iterator[None]:
    """Add remote on entry, remove it on exit."""
    if repository.exists_remote(remote):
        repository.remove_remote(remote)

    repository.add_remote(remote, url)

    try:
        yield
    finally:
        if repository.exists_remote(remote):
            repository.remove_remote(remote)


def retrocookie(
    ref: str,
    *,
    base: str = "master",
    branch: Optional[str] = None,
    url: Optional[str] = None,
    whitelist: Container[str] = (),
    blacklist: Container[str] = (),
    path: Optional[Path] = None,
) -> None:
    """Import commits from instance repository into template repository."""
    repository = git.Repository(path)
    template_directory = find_template_directory(repository)
    remote = "retrocookie"

    if url is None:
        url = guess_instance_url(repository)

    with temporary_repository(url) as instance:
        rewrite_commits(instance, template_directory, whitelist, blacklist)

        with temporary_remote(repository, remote, str(instance.path)):
            apply_commits(repository, remote, base, ref, branch)
