"""Tests for retrocookie.pr.__main__."""
import subprocess  # noqa: S404
from typing import List

import pytest
from click.testing import CliRunner
from pytest import MonkeyPatch
from tests.pr.unit.data import EXAMPLE_PROJECT_PULL
from tests.pr.unit.data import EXAMPLE_TEMPLATE
from tests.pr.unit.data import EXAMPLE_TEMPLATE_PULL
from tests.pr.unit.utils import raises

from retrocookie.pr import __main__
from retrocookie.pr import events
from retrocookie.pr.base.bus import Bus
from retrocookie.pr.base.bus import Error
from retrocookie.pr.base.bus import Event
from retrocookie.pr.cache import Cache


def test_get_token_from_cache(cache: Cache) -> None:
    """It loads the token from the cache."""
    cache.save_token("token")
    assert "token" == __main__.get_token(cache)


def test_get_token_from_user(cache: Cache) -> None:
    """It prompts the user for the token."""
    runner = CliRunner()
    with runner.isolation(input="token"):
        assert "token" == __main__.get_token(cache)


def test_all_with_arguments() -> None:
    """It fails when --all is used with arguments."""
    runner = CliRunner()
    result = runner.invoke(__main__.main, ["--all", "1"])
    assert result.exit_code == 2


def test_without_arguments() -> None:
    """It fails when no pull requests are specified."""
    runner = CliRunner()
    result = runner.invoke(__main__.main, [])
    assert result.exit_code == 2


def test_giterrorhandler_with_git_error(bus: Bus) -> None:
    """It raises a GitFailed event."""
    with raises(events.GitFailed):
        with __main__.giterrorhandler(bus=bus):
            raise subprocess.CalledProcessError(1, ["git", "rev-parse", "HEAD"], "", "")


def test_collect() -> None:
    """It collects errors."""
    error = Error(Event())
    errors: List[Error] = []
    with __main__.collect(errors):
        raise error
    [caught] = errors  # type: ignore[unreachable]
    assert error is caught


@pytest.mark.parametrize(
    "error",
    [
        subprocess.CalledProcessError(1, "false", "", ""),
        subprocess.CalledProcessError(1, ["echo", "hello"], "", ""),
    ],
)
def test_giterrorhandler_without_git_error(bus: Bus, error: Exception) -> None:
    """It reraises the original exception."""
    with pytest.raises(subprocess.CalledProcessError):
        with __main__.giterrorhandler(bus=bus):
            raise error


def test_open_after_create(bus: Bus, monkeypatch: MonkeyPatch) -> None:
    """It opens the URL in a browser."""
    event = events.PullRequestCreated(
        EXAMPLE_TEMPLATE,
        EXAMPLE_TEMPLATE_PULL,
        EXAMPLE_PROJECT_PULL,
    )

    urls = []

    def _webbrowser_open(url: str) -> None:
        urls.append(url)

    monkeypatch.setattr("webbrowser.open", _webbrowser_open)

    __main__.register_pull_request_viewer(bus=bus)

    bus.events.publish(event)

    assert urls == [event.template_pull.html_url]


def test_open_after_update(bus: Bus, monkeypatch: MonkeyPatch) -> None:
    """It opens the URL in a browser."""
    event = events.UpdatePullRequest(
        EXAMPLE_TEMPLATE,
        EXAMPLE_TEMPLATE_PULL,
        EXAMPLE_PROJECT_PULL,
    )

    urls = []

    def _webbrowser_open(url: str) -> None:
        urls.append(url)

    monkeypatch.setattr("webbrowser.open", _webbrowser_open)

    __main__.register_pull_request_viewer(bus=bus)

    with bus.contexts.publish(event):
        pass

    assert urls == [event.template_pull.html_url]
