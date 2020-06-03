"""Core module."""
import json
from pathlib import Path
from typing import cast
from typing import Container
from typing import Dict
from typing import Iterable
from typing import List
from typing import Optional

from . import git
from .filter import RepositoryFilter
from .utils import temporary_remote
from .utils import temporary_repository


def find_template_directory(repository: git.Repository) -> Path:
    """Locate the subdirectory with the project template."""
    tokens = "{{", "cookiecutter", "}}"
    for path in repository.path.iterdir():
        if path.is_dir() and all(x in path.name for x in tokens):
            return path.relative_to(repository.path)
    raise Exception("cannot find template directory")


def load_context(repository: git.Repository) -> Dict[str, str]:
    """Load the context from the .cookiecutter.json file."""
    path = Path(".cookiecutter.json")
    text = repository.read_text(path)
    return cast(Dict[str, str], json.loads(text))


def rewrite_commits(
    repository: git.Repository,
    template_directory: Path,
    whitelist: Container[str],
    blacklist: Container[str],
    revision: str,
) -> List[str]:
    """Rewrite the repository using template variables."""
    commits = repository.parse_revisions(revision)
    context = load_context(repository)
    RepositoryFilter(
        repository=repository,
        path=template_directory,
        context=context,
        whitelist=whitelist,
        blacklist=blacklist,
    ).run()
    return [repository.lookup_replacement(commit) for commit in commits]


def apply_commits(
    repository: git.Repository, remote: str, commits: Iterable[str], branch: str,
) -> None:
    """Create <branch> with the specified commits from <remote>."""
    repository.git("fetch", "--no-tags", "--depth=2", remote, *commits)
    repository.create_branch(branch)
    for commit in commits:
        repository.cherrypick(commit, branch=branch)


def retrocookie(
    url: str,
    ref: str,
    *,
    base: str = "master",
    branch: Optional[str] = None,
    whitelist: Container[str] = (),
    blacklist: Container[str] = (),
    path: Optional[Path] = None,
) -> None:
    """Import commits from instance repository into template repository."""
    repository = git.Repository(path)
    template_directory = find_template_directory(repository)
    remote = "retrocookie"

    with temporary_repository(url) as instance:
        commits = rewrite_commits(
            instance, template_directory, whitelist, blacklist, f"{base}..{ref}"
        )

        with temporary_remote(repository, remote, str(instance.path)):
            apply_commits(repository, remote, commits, branch or ref)
