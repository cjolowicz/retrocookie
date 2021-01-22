"""Tests for retrocookie.pr.github."""
from typing import Any

import github3.exceptions
import pytest
import requests.exceptions
from tests.pr.unit.utils import raises

from retrocookie.pr import events
from retrocookie.pr.adapters import github
from retrocookie.pr.base.bus import Bus


class FakeRequest:
    """A fake for requests.Request."""

    url = "https://api.github.com/repos/owner/name"
    method = "GET"


class FakeResponse:
    """A fake for requests.Response."""

    request = FakeRequest()
    status_code = 403

    def json(self) -> Any:
        """Return the JSON body."""
        return {"message": "Forbidden"}


def test_errorhandler_github_with_request(bus: Bus) -> None:
    """It raises a GitHubError event."""
    response = FakeResponse()

    with raises(events.GitHubError):
        with github.errorhandler(bus=bus):
            raise github3.exceptions.GitHubError(response)


def test_errorhandler_github_without_request(bus: Bus) -> None:
    """It reraises the exception."""
    with pytest.raises(github3.exceptions.GitHubError):
        with github.errorhandler(bus=bus):
            raise github3.exceptions.IncompleteResponse(json={}, exception=None)


def test_errorhandler_connection_with_requests_exception(bus: Bus) -> None:
    """It raises a ConnectionError event."""
    response = FakeResponse()
    cause = requests.RequestException(response=response)

    with raises(events.ConnectionError):
        with github.errorhandler(bus=bus):
            raise github3.exceptions.ConnectionError(cause)


def test_errorhandler_connection_without_requests_exception(bus: Bus) -> None:
    """It reraises the exception."""
    cause = Exception()

    with pytest.raises(github3.exceptions.ConnectionError):
        with github.errorhandler(bus=bus):
            raise github3.exceptions.ConnectionError(cause)
