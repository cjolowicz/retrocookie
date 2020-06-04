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


def get_commits(
    repository: git.Repository, commits: Iterable[str], branch: str, upstream: str
) -> Iterable[str]:
    """Return hashes of the commits to be picked."""
    revisions = [f"{upstream}..{branch}", *commits]
    return [
        commit
        for revision in revisions
        for commit in repository.parse_revisions(revision)
    ]


def rewrite_commits(
    repository: git.Repository,
    template_directory: Path,
    whitelist: Container[str],
    blacklist: Container[str],
    commits: Iterable[str],
) -> List[str]:
    """Rewrite the repository using template variables."""
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
    repository: git.Repository,
    remote: str,
    commits: Iterable[str],
    create_branch: Optional[str],
) -> None:
    """Create <branch> with the specified commits from <remote>."""
    repository.git("fetch", "--no-tags", "--depth=2", remote, *commits)

    if create_branch:
        repository.create_branch(create_branch)
        repository.switch_branch(create_branch)

    for commit in commits:
        repository.cherrypick(commit)


def retrocookie(
    url: str,
    branch: str,
    *,
    commits: Iterable[str] = (),
    upstream: str = "master",
    create_branch: Optional[str] = None,
    whitelist: Container[str] = (),
    blacklist: Container[str] = (),
    path: Optional[Path] = None,
) -> None:
    """Import commits from instance repository into template repository."""
    repository = git.Repository(path)
    template_directory = find_template_directory(repository)
    remote = "retrocookie"

    with temporary_repository(url) as instance:
        commits = get_commits(instance, commits, branch, upstream)
        commits = rewrite_commits(
            instance, template_directory, whitelist, blacklist, commits
        )

        with temporary_remote(repository, remote, str(instance.path)):
            apply_commits(repository, remote, commits, create_branch)
