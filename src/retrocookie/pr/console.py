"""Application console."""
from typing import ContextManager
from typing import Iterator

import rich.console
import rich.theme
import rich.traceback
from rich.markup import escape

from retrocookie.pr import events
from retrocookie.pr.base.bus import Bus
from retrocookie.pr.compat import contextlib
from retrocookie.pr.compat import shlex


class Console:
    """Console."""

    def __init__(self) -> None:
        """Create the console."""
        theme = rich.theme.Theme(
            {
                "success": "green",
                "failure": "red",
                "hint": "yellow",
                "repository": "blue",
                "pull": "bold bright_white",
                "oldpull": "bright_black",
                "title": "cyan",
                "command": "bold",
                "status": "bold",
                "stdout": "bright_black",
                "stderr": "red",
                "version": "green",
                "http.method": "blue",
                "http.status": "bright_blue",
            }
        )
        self.console = rich.console.Console(stderr=True, highlight=False, theme=theme)

    def success(self, message: str) -> None:
        """Display a success message."""
        self.console.print(f"[success]✓[/] {message}")

    def failure(self, message: str) -> None:
        """Display a failure message."""
        self.console.print(f"[failure]⨯[/] {message}")

    def hint(self, message: str) -> None:
        """Display a hint for the user."""
        self.console.print(f"[hint]☞ {message}[/]")

    def highlight(self, text: str) -> None:
        """Output a text with highlighting."""
        console = rich.console.Console(stderr=True)
        console.print(text)

    @contextlib.contextmanager
    def progress(self, message: str) -> Iterator[None]:
        """Display a status message with a spinner."""
        try:
            with self.console.status(message):
                yield
        except Exception:
            self.failure(message)
            raise


def start(*, bus: Bus) -> None:
    """Create the console and subscribe to events."""
    rich.traceback.install()

    console = Console()

    _subscribe(console, bus)


def _subscribe(console: Console, bus: Bus) -> None:  # noqa: C901
    _ = None  # Ignoring redefinitions of this name below.

    @bus.events.subscribe  # type: ignore[no-redef]
    def _(event: events.GitNotFound) -> None:
        console.failure("git not found")
        console.hint("Do you have git installed?")
        console.hint("Is git on your PATH?")
        console.hint("Can you run [command]git version[/]?")

    @bus.events.subscribe  # type: ignore[no-redef]
    def _(event: events.BadGitVersion) -> None:
        console.failure(f"This program requires git [version]{event.expected}[/].")
        console.hint(f"You have git [version]{event.version}[/], which is too old.")

    @bus.events.subscribe  # type: ignore[no-redef]
    def _(event: events.GitFailed) -> None:
        def _lines() -> Iterator[str]:
            yield (
                f"The command [command]git {event.command}[/] failed"
                f" with status [status]{event.status}[/]."
            )

            command = escape(shlex.join(["git", event.command, *event.options]))

            yield ""
            yield f"❯ {command}"

            for stream in ["stdout", "stderr"]:
                output = getattr(event, stream)
                if output:
                    yield ""
                    for line in output.splitlines():
                        line = escape(line)
                        yield f"[{stream}]{line}[/]"

            yield ""

        console.failure("\n".join(_lines()))

        if event.command == "cherry-pick":
            console.hint("Looks like the changes did not apply cleanly.")
            console.hint(
                "Try running [command]retrocookie[/] on a local clone instead."
            )

    @bus.events.subscribe  # type: ignore[no-redef]
    def _(event: events.GitHubError) -> None:
        def _lines() -> Iterator[str]:
            yield "The GitHub API returned an error response."
            yield f"[http.method]{event.method}[/] [repr.url]{event.url}[/]"
            yield f"[http.status]{event.code}[/] {event.message}"
            yield from event.errors

        console.failure("\n".join(_lines()))

    @bus.events.subscribe  # type: ignore[no-redef]
    def _(event: events.ConnectionError) -> None:
        def _lines() -> Iterator[str]:
            yield "Connection to GitHub API could not be established."
            yield f"[http.method]{event.method}[/] [repr.url]{event.url}[/]"

        console.failure("\n".join(_lines()))
        console.highlight(event.error)

    @bus.events.subscribe  # type: ignore[no-redef]
    def _(event: events.ProjectNotFound) -> None:
        console.failure("Project not found")
        console.hint("Does the current directory contain a repository?")
        console.hint("Is the repository on GitHub?")

    @bus.events.subscribe  # type: ignore[no-redef]
    def _(event: events.TemplateNotFound) -> None:
        console.failure(
            f"Project template for [repository]{event.project.full_name}[/] not found"
        )
        console.hint("Does the project contain a .cookiecutter.json file?")
        console.hint(
            'Does the .cookiecutter.json contain the repository URL under "_template"?'
        )
        console.hint("Is the template repository on GitHub?")

    @bus.contexts.subscribe  # type: ignore[no-redef]
    def _(event: events.LoadProject) -> ContextManager[None]:
        return console.progress(f"Loading project [repository]{event.repository}[/]")

    @bus.contexts.subscribe  # type: ignore[no-redef]
    def _(event: events.LoadTemplate) -> ContextManager[None]:
        return console.progress(f"Loading template [repository]{event.repository}[/]")

    @bus.events.subscribe  # type: ignore[no-redef]
    def _(event: events.RepositoryNotFound) -> None:
        console.failure(f"Repository [repository]{event.repository}[/] not found")

    @bus.events.subscribe  # type: ignore[no-redef]
    def _(event: events.PullRequestNotFound) -> None:
        spec = event.pull_request
        if spec.isnumeric():
            spec = f"#{spec}"
        console.failure(f"Pull request [pull]{spec}[/] not found")

    @bus.events.subscribe  # type: ignore[no-redef]
    def _(event: events.PullRequestAlreadyExists) -> None:
        console.failure(
            "Already imported"
            f" [pull]#{event.project_pull.number}[/]"
            f" [title]{escape(event.project_pull.title)}[/]"
        )
        console.hint(f"See [pull]#{event.template_pull.number}[/]")
        console.hint("Use --force to update an existing pull request.")

    @bus.contexts.subscribe  # type: ignore[no-redef]
    def _(event: events.CreatePullRequest) -> ContextManager[None]:
        return console.progress(
            f"[pull]#{event.project_pull.number}[/]"
            f" [title]{escape(event.project_pull.title)}[/]"
        )

    @bus.contexts.subscribe  # type: ignore[no-redef]
    @contextlib.contextmanager
    def _(event: events.UpdatePullRequest) -> Iterator[None]:
        with console.progress(
            f"[pull]#{event.project_pull.number}[/]"
            f" [title]{escape(event.project_pull.title)}[/]"
            f" [oldpull]#{event.template_pull.number}[/]"
        ):
            yield

        console.success(
            f"[pull]#{event.project_pull.number}[/]"
            f" [title]{escape(event.project_pull.title)}[/]"
            f" [pull]#{event.template_pull.number}[/]"
        )

    @bus.events.subscribe  # type: ignore[no-redef]
    def _(event: events.PullRequestCreated) -> None:
        console.success(
            f"[pull]#{event.project_pull.number}[/]"
            f" [title]{escape(event.project_pull.title)}[/]"
            f" [pull]#{event.template_pull.number}[/]"
        )
