"""Core module."""
import json
from pathlib import Path
from typing import cast
from typing import Container
from typing import Dict
from typing import Iterable
from typing import Iterator
from typing import List
from typing import Optional

from . import git
from .filter import RepositoryFilter
from .utils import temporary_repository


def find_template_directory(repository: git.Repository) -> Path:
    """Locate the subdirectory with the project template."""
    tokens = "{{", "cookiecutter", "}}"
    for path in repository.path.iterdir():
        if path.is_dir() and all(x in path.name for x in tokens):
            return path.relative_to(repository.path)
    raise Exception("cannot find template directory")


def load_context(repository: git.Repository, ref: str) -> Dict[str, str]:
    """Load the context from the .cookiecutter.json file."""
    path = Path(".cookiecutter.json")
    text = repository.read_text(path, ref=ref)
    return cast(Dict[str, str], json.loads(text))


def get_commits(
    repository: git.Repository,
    commits: Iterable[str],
    branch: Optional[str],
    upstream: str,
) -> List[str]:
    """Return hashes of the commits to be picked."""

    def _generate() -> Iterator[str]:
        if branch is not None:
            yield from repository.parse_revisions(f"{upstream}..{branch}")

        if commits:
            yield from repository.parse_revisions(*commits)

    return list(_generate())


def fetch_commits(
    repository: git.Repository, source: git.Repository, commits: List[str],
) -> None:
    """Fetch commits into an empty repository."""
    repository.fetch_commits(source, *commits)
    repository.create_branch("master", commits[-1])


def rewrite_commits(
    repository: git.Repository,
    template_directory: Path,
    whitelist: Container[str],
    blacklist: Container[str],
    commits: Iterable[str],
) -> List[str]:
    """Rewrite the repository using template variables."""
    commits = list(commits)
    context = load_context(repository, commits[-1])
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
    source: git.Repository,
    commits: Iterable[str],
    create_branch: Optional[str],
) -> None:
    """Create <branch> with the specified commits from <remote>."""
    repository.fetch_commits(source, *commits)

    if create_branch:
        repository.create_branch(create_branch)
        repository.switch_branch(create_branch)

    for commit in commits:
        repository.cherrypick(commit)


def retrocookie(
    instance_path: Path,
    commits: Iterable[str] = (),
    *,
    path: Optional[Path] = None,
    branch: Optional[str] = None,
    upstream: str = "master",
    create_branch: Optional[str] = None,
    whitelist: Container[str] = (),
    blacklist: Container[str] = (),
) -> None:  # noqa: DAR101 https://github.com/terrencepreilly/darglint/issues/56
    """Import commits from instance repository into template repository.

    This function imports commits from an instance of the Cookiecutter
    template, rewriting occurrences of template variables back into the
    original templating tags, and prepending the template directory to
    filenames. Any tokens with special meaning in Jinja are escaped.

    Args:
        instance_path: The source repository, an instance of the Cookiecutter
            template with a ``.cookiecutter.json`` file.

        commits: The commits to be imported from the source repository.

        path: The target repository, a Cookiecutter template. This defaults to
            the current working directory.

        branch: The name of a branch to be imported from the source repository.
            This is equivalent to passing ``["master..branch"]`` in the
            ``commits`` parameter.

        upstream: The upstream for ``branch``, by default the master branch.

        create_branch: The name of the branch to be created in the target
            repository. By default, commits are imported onto the current
            branch.

        whitelist: The Cookiecutter variables which should be rewritten. If
            this is not specified, all variables from cookiecutter.json are
            rewritten.

        blacklist: Any Cookiecutter variables which should not be rewritten.

    """
    repository = git.Repository(path)
    instance = git.Repository(instance_path)
    template_directory = find_template_directory(repository)
    commits = get_commits(instance, commits, branch, upstream)

    with temporary_repository() as scratch:
        fetch_commits(scratch, instance, commits)
        commits = rewrite_commits(
            scratch, template_directory, whitelist, blacklist, commits
        )

        apply_commits(repository, scratch, commits, create_branch)
