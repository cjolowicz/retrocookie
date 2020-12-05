"""Command-line interface."""
import contextlib
import subprocess  # noqa: S404
import webbrowser
from pathlib import Path
from typing import Collection
from typing import Iterator
from typing import List
from typing import NoReturn
from typing import Optional

import appdirs
import click

from retrocookie.pr import appname
from retrocookie.pr import console
from retrocookie.pr import events
from retrocookie.pr.adapters import github
from retrocookie.pr.adapters.retrocookie import retrocookie
from retrocookie.pr.base.bus import Bus
from retrocookie.pr.base.bus import Error
from retrocookie.pr.base.exceptionhandlers import ExceptionHandler
from retrocookie.pr.base.exceptionhandlers import exceptionhandler
from retrocookie.pr.base.exceptionhandlers import nullhandler
from retrocookie.pr.cache import Cache
from retrocookie.pr.compat.contextlib import contextmanager
from retrocookie.pr.core import import_pull_requests


def get_token(cache: Cache) -> str:
    """Obtain the token from the cache or by prompting the user."""
    with contextlib.suppress(FileNotFoundError):
        return cache.load_token()

    token: str = click.prompt("Please enter a personal access token for the GitHub API")
    cache.save_token(token)
    return token


def giterrorhandler(*, bus: Bus) -> ExceptionHandler:
    """Handle errors from a git subprocess."""

    @exceptionhandler
    def _(error: subprocess.CalledProcessError) -> None:
        if isinstance(error.cmd, list) and len(error.cmd) >= 2:
            command = Path(error.cmd[0]).name
            subcommand, *args = error.cmd[1:]
            if command == "git":
                bus.events.raise_(
                    events.GitFailed(
                        subcommand, args, error.returncode, error.stdout, error.stderr
                    )
                )
        return None

    return _


@exceptionhandler
def exithandler(exception: Error) -> NoReturn:
    """Exit on application errors."""
    raise SystemExit(1)


def collect(errors: List[Error]) -> ExceptionHandler:
    """Collect errors."""

    @exceptionhandler
    def _(error: Error) -> bool:
        errors.append(error)
        return True

    return _


def register_pull_request_viewer(*, bus: Bus) -> None:
    """Register an event handler for viewing pull requests in a browser."""

    @bus.events.subscribe
    def _(event: events.PullRequestCreated) -> None:
        webbrowser.open(event.template_pull.html_url)

    @bus.contexts.subscribe  # type: ignore[no-redef]
    @contextmanager
    def _(event: events.UpdatePullRequest) -> Iterator[None]:
        yield
        webbrowser.open(event.template_pull.html_url)


@click.command()
@click.argument("pull_requests", metavar="pull-request", nargs=-1)
@click.option(
    "-R",
    "--repository",
    help="GitHub repository containing the pull requests.",
)
@click.option(
    "--token",
    metavar="token",
    envvar="GITHUB_TOKEN",
    help="GitHub token",
)
@click.option("-u", "--user", help="Import pull requests opened by this GitHub user.")
@click.option("--all", is_flag=True, help="Import all pull requests.")
@click.option("--force", is_flag=True, help="Overwrite existing pull requests.")
@click.option(
    "--keep-going",
    "-k",
    is_flag=True,
    help="Keep going when some pull requests cannot be imported.",
)
@click.option(
    "--open", is_flag=True, help="View imported pull requests in a web browser."
)
@click.option("--debug", is_flag=True, help="Print tracebacks for all errors.")
@click.version_option()
def main(
    pull_requests: Collection[str],
    repository: Optional[str],
    token: Optional[str],
    user: Optional[str],
    all: bool,
    force: bool,
    keep_going: bool,
    open: bool,
    debug: bool,
) -> None:
    """Import pull requests from generated projects into their template.

    Command-line arguments specify pull requests to import, by number or by
    branch. Alternatively, select pull requests by specifying the user that
    opened them, via the --user option. Use the --all option to import all open
    pull requests in the generated project.

    Use the --repository option to specify the GitHub repository of the
    generated project from which the pull requests should be imported. Provide
    the full name of the repository on GitHub in the form owner/name. The owner
    can be omitted if the repository is owned by the authenticated user. This
    option can be omitted when the command is invoked from a local clone.

    Update previously imported pull requests by specifying --force. By default,
    this program refuses to overwrite existing pull requests.

    The program needs a personal access token (PAT) to access the GitHub API,
    and prompts for the token when invoked for the first time. Subsequent
    invocations read the token from the application cache. Alternatively, you
    can specify the token using the --token option or the GITHUB_TOKEN
    environment variable; both of these methods bypass the cache.
    """
    if not (pull_requests or user or all):
        raise click.UsageError("Please specify which pull requests to import.")

    if all and pull_requests:
        raise click.UsageError("Do not specify --all with individual pull requests.")

    bus = Bus()
    console.start(bus=bus)

    if open:  # pragma: no cover
        register_pull_request_viewer(bus=bus)

    errors: List[Error] = []

    corehandler = (
        giterrorhandler(bus=bus)
        >> github.errorhandler(bus=bus)
        >> bus.events.errorhandler()
    )
    mainerrorhandler = corehandler >> (exithandler if not debug else nullhandler)
    nestederrorhandler = (corehandler >> collect(errors)) if keep_going else nullhandler

    with mainerrorhandler:
        user_cache_dir = appdirs.user_cache_dir(appauthor=appname, appname=appname)
        cache = Cache(Path(user_cache_dir))
        api = github.API.login(token or get_token(cache), bus=bus)

        import_pull_requests(
            pull_requests,
            api=api,
            bus=bus,
            cache=cache,
            errorhandler=nestederrorhandler,
            retrocookie=retrocookie,
            repository=repository,
            user=user,
            force=force,
        )

    if errors:
        raise SystemExit(1)  # pragma: no cover


if __name__ == "__main__":  # pragma: no cover
    main()
