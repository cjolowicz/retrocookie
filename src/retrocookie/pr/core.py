"""Import pull requests."""
from typing import Collection
from typing import Optional
from urllib.parse import urlparse

from retrocookie import git
from retrocookie.core import load_context
from retrocookie.pr import events
from retrocookie.pr.base.bus import Bus
from retrocookie.pr.base.exceptionhandlers import ExceptionHandler
from retrocookie.pr.cache import Cache
from retrocookie.pr.importer import Importer
from retrocookie.pr.list import list_pull_requests
from retrocookie.pr.protocols import github
from retrocookie.pr.protocols.retrocookie import Retrocookie
from retrocookie.pr.repository import Repository
from retrocookie.utils import removeprefix
from retrocookie.utils import removesuffix


def parse_repository_name(url: str) -> Optional[str]:
    """Extract the repository name from the URL, if possible."""
    for prefix in ("gh:", "git@github.com:"):
        if url.startswith(prefix):
            path = removeprefix(url, prefix)
            return removesuffix(path, ".git")

    result = urlparse(url)
    if result.hostname == "github.com":
        return removesuffix(result.path[1:], ".git")

    return None


def get_project_name(*, bus: Bus) -> str:
    """Return the repository name of the project."""
    with bus.events.reraise(events.ProjectNotFound()):
        repository = git.Repository()

    for remote in repository.repo.remotes:
        name = parse_repository_name(remote.url)
        if name is not None:
            return name

    bus.events.raise_(events.ProjectNotFound())


def get_template_name(project: Repository, *, bus: Bus) -> str:
    """Return the repository name of the template, given the project."""
    with bus.events.reraise(
        events.TemplateNotFound(project.github),
        when=(KeyError, TypeError),
    ):
        context = load_context(project.clone, "HEAD")

    name = parse_repository_name(context["_template"])
    if name is not None:
        return name

    bus.events.raise_(events.TemplateNotFound(project.github))


def check_git_version(*, bus: Bus) -> None:
    """Check if we have a recent version of git."""
    # newren/git-filter-repo requires git >= 2.22.0
    minimum_version = git.Version.parse("2.22.0")

    with bus.events.reraise(events.GitNotFound()):
        version = git.version()

    if version < minimum_version:
        bus.events.raise_(events.BadGitVersion(version, minimum_version))


def import_pull_requests(
    pull_requests: Collection[str] = (),
    *,
    api: github.API,
    bus: Bus,
    cache: Cache,
    errorhandler: ExceptionHandler,
    retrocookie: Retrocookie,
    repository: Optional[str] = None,
    user: Optional[str] = None,
    force: bool = False,
) -> None:
    """Import pull requests from a repository into its Cookiecutter template."""
    check_git_version(bus=bus)

    if repository is None:
        repository = get_project_name(bus=bus)
    elif "/" not in repository:
        repository = "/".join([api.me, repository])

    with bus.contexts.publish(events.LoadProject(repository)):
        project = Repository.load(repository, api=api, cache=cache)

    template_name = get_template_name(project, bus=bus)

    with bus.contexts.publish(events.LoadTemplate(template_name)):
        template = Repository.load(template_name, api=api, cache=cache)

    importer = Importer(
        project,
        template,
        bus=bus,
        cache=cache,
        retrocookie=retrocookie,
    )

    for pull in list_pull_requests(project.github, pull_requests, user=user, bus=bus):
        with errorhandler:
            importer.import_(pull, force=force)
