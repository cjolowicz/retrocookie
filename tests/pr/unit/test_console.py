"""Tests for the console."""
import contextlib
import io
from typing import Callable
from typing import Iterator
from typing import Tuple

import pytest
from tests.pr.unit.data import EXAMPLE_PROJECT
from tests.pr.unit.data import EXAMPLE_PROJECT_PULL
from tests.pr.unit.data import EXAMPLE_TEMPLATE
from tests.pr.unit.data import EXAMPLE_TEMPLATE_PULL

from retrocookie import git
from retrocookie.compat.contextlib import contextmanager
from retrocookie.pr import console
from retrocookie.pr import events
from retrocookie.pr.base.bus import Bus
from retrocookie.pr.base.bus import Context
from retrocookie.pr.base.bus import Event


@pytest.fixture
def bus() -> Iterator[Bus]:
    """Fixture for a bus with console handlers."""
    bus = Bus()
    console.start(bus=bus)
    yield bus


@contextmanager
def redirect() -> Iterator[Tuple[io.StringIO, io.StringIO]]:
    """Redirect standard output and error."""
    stdout = io.StringIO()
    stderr = io.StringIO()
    with contextlib.redirect_stdout(stdout):
        with contextlib.redirect_stderr(stderr):
            yield stdout, stderr


PublishEvent = Callable[[Event], Tuple[str, str]]


@pytest.fixture
def publish_event(bus: Bus) -> PublishEvent:
    """Factory fixture for publishing a event."""

    def _(event: Event) -> Tuple[str, str]:
        with redirect() as (stdout, stderr):
            bus.events.publish(event)
        return stdout.getvalue(), stderr.getvalue()

    return _


def get_class_name(instance: object) -> str:
    """Return the class name."""
    return instance.__class__.__name__


@pytest.mark.parametrize(
    "event",
    [
        events.GitNotFound(),
        events.BadGitVersion(
            git.Version.parse("0.99"),
            git.Version.parse("2.22.0"),
        ),
        events.ProjectNotFound(),
        events.TemplateNotFound(EXAMPLE_PROJECT),
        events.RepositoryNotFound("owner/name"),
        events.PullRequestNotFound("1"),
        events.PullRequestNotFound("branch"),
        events.PullRequestAlreadyExists(
            EXAMPLE_TEMPLATE,
            EXAMPLE_TEMPLATE_PULL,
            EXAMPLE_PROJECT_PULL,
        ),
        events.PullRequestCreated(
            EXAMPLE_TEMPLATE,
            EXAMPLE_TEMPLATE_PULL,
            EXAMPLE_PROJECT_PULL,
        ),
        events.GitFailed("rev-parse", ["8beecafe"], 128, "8beecafe", "fatal: ..."),
        events.GitFailed("cherry-pick", [], 1, "", "could not apply 8beecafe"),
        events.GitFailed("foo", [], 1, "", ""),
        events.GitHubError(
            "https://api.github.com/repos/owner/name", "GET", 401, "Bad credentials", []
        ),
        events.ConnectionError(
            "https://api.github.com/repos/owner/name", "GET", "pigeon unavailable"
        ),
    ],
    ids=get_class_name,
)
def test_publish_event(publish_event: PublishEvent, event: Event) -> None:
    """It displays the event on standard error."""
    stdout, stderr = publish_event(event)
    assert not stdout and stderr


PublishContext = Callable[[Context], Tuple[str, str]]


@pytest.fixture
def publish_context(bus: Bus) -> PublishContext:
    """Factory fixture for publishing a context."""

    class _ExampleError(Exception):
        pass

    def _(context: Context) -> Tuple[str, str]:
        with redirect() as (stdout, stderr):
            with contextlib.suppress(_ExampleError):
                with bus.contexts.publish(context):
                    # The exception ensures that something is written to the
                    # console before control exits the context.
                    raise _ExampleError("Boom")
        return stdout.getvalue(), stderr.getvalue()

    return _


@pytest.mark.parametrize(
    "context",
    [
        events.LoadTemplate("owner/name"),
        events.LoadProject("owner/name"),
        events.CreatePullRequest(
            EXAMPLE_TEMPLATE, "retrocookie-pr/branch", EXAMPLE_PROJECT_PULL
        ),
        events.UpdatePullRequest(
            EXAMPLE_TEMPLATE, EXAMPLE_TEMPLATE_PULL, EXAMPLE_PROJECT_PULL
        ),
    ],
    ids=get_class_name,
)
def test_publish_context(publish_context: PublishContext, context: Context) -> None:
    """It displays the context on standard error."""
    stdout, stderr = publish_context(context)
    assert not stdout and stderr


def test_progress_failure() -> None:
    """It displays a failure message."""
    c = console.Console()
    with contextlib.suppress(Exception):
        with redirect() as (stdout, stderr):
            with c.progress("message"):
                raise Exception("Boom")
    assert "⨯" in stderr.getvalue()
