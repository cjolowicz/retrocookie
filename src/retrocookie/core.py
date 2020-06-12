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


def rewrite_commits(
    repository: git.Repository,
    source: git.Repository,
    template_directory: Path,
    include_variables: Container[str],
    exclude_variables: Container[str],
    commits: Iterable[str],
) -> List[str]:
    """Rewrite the repository using template variables."""
    commits = list(commits)
    with_parents = source.parse_revisions(
        *[f"{commit}^" for commit in commits], *commits
    )
    context = load_context(source, commits[-1])
    RepositoryFilter(
        repository=repository,
        source=source,
        commits=with_parents,
        template_directory=template_directory,
        context=context,
        include_variables=include_variables,
        exclude_variables=exclude_variables,
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
    include_variables: Container[str] = (),
    exclude_variables: Container[str] = (),
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

        include_variables: The Cookiecutter variables which should be
            rewritten. If this is not specified, all variables from
            cookiecutter.json are rewritten.

        exclude_variables: Any Cookiecutter variables which should not be
            rewritten.

    """
    repository = git.Repository(path)
    instance = git.Repository(instance_path)
    template_directory = find_template_directory(repository)
    commits = get_commits(instance, commits, branch, upstream)

    with temporary_repository() as scratch:
        commits = rewrite_commits(
            scratch,
            instance,
            template_directory,
            include_variables,
            exclude_variables,
            commits,
        )

        apply_commits(repository, scratch, commits, create_branch)
