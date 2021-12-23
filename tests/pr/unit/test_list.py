"""Tests for retrocookie.pr.list."""
from typing import cast
from typing import Iterable
from typing import List

import pytest

from retrocookie.pr.base.bus import Bus
from retrocookie.pr.list import list_pull_requests
from retrocookie.pr.protocols.github import PullRequest as AbstractPullRequest
from tests.pr.unit.fakes import github


@pytest.fixture
def repository(api: github.API) -> github.Repository:
    """Return a fake repository."""
    return api.repository("owner", "name")


pr1 = github.PullRequest(1, "title1", "body1", "branch1", "user1")
pr2 = github.PullRequest(2, "title2", "body2", "branch2", "user2")


def equal(
    expected: Iterable[github.PullRequest], actual: Iterable[AbstractPullRequest]
) -> bool:
    """Return True if both iterables contain the same pull requests."""
    actual_ = [cast(github.PullRequest, item) for item in actual]
    return sorted(actual_) == sorted(expected)


@pytest.mark.parametrize(
    "pull_requests",
    [
        [],
        [pr1, pr2],
    ],
)
def test_list_all(
    repository: github.Repository,
    bus: Bus,
    pull_requests: List[github.PullRequest],
) -> None:
    """It lists all pull requests."""
    repository._pull_requests = pull_requests
    actual = list_pull_requests(repository, bus=bus)
    assert equal(pull_requests, actual)


@pytest.mark.parametrize(
    "pull_requests, user, expected",
    [
        ([], pr1.user, []),
        ([pr1, pr2], pr2.user, [pr2]),
        ([pr1, pr2], "unknown", []),
    ],
)
def test_list_by_user(
    repository: github.Repository,
    bus: Bus,
    pull_requests: List[github.PullRequest],
    user: str,
    expected: List[github.PullRequest],
) -> None:
    """It lists all pull requests."""
    repository._pull_requests = pull_requests
    actual = list_pull_requests(repository, user=user, bus=bus)
    assert equal(expected, actual)


@pytest.mark.parametrize(
    "pull_requests, specs, expected",
    [
        ([pr1, pr2], ["1"], [pr1]),
        ([pr1, pr2], ["2"], [pr2]),
        ([pr1, pr2], ["1", "2"], [pr1, pr2]),
    ],
)
def test_list_by_number(
    repository: github.Repository,
    bus: Bus,
    pull_requests: List[github.PullRequest],
    specs: List[str],
    expected: List[github.PullRequest],
) -> None:
    """It lists all pull requests."""
    repository._pull_requests = pull_requests
    actual = list_pull_requests(repository, specs, bus=bus)
    assert equal(expected, actual)


@pytest.mark.parametrize(
    "pull_requests, specs, expected",
    [
        ([pr1, pr2], ["branch1"], [pr1]),
        ([pr1, pr2], ["branch2"], [pr2]),
        ([pr1, pr2], ["branch1", "branch2"], [pr1, pr2]),
    ],
)
def test_list_by_head(
    repository: github.Repository,
    bus: Bus,
    pull_requests: List[github.PullRequest],
    specs: List[str],
    expected: List[github.PullRequest],
) -> None:
    """It lists all pull requests."""
    repository._pull_requests = pull_requests
    actual = list_pull_requests(repository, specs, bus=bus)
    assert equal(expected, actual)


@pytest.mark.parametrize(
    "pull_requests, specs",
    [
        ([], ["branch1"]),
        ([pr1, pr2], ["unknown"]),
    ],
)
def test_list_not_found(
    repository: github.Repository,
    bus: Bus,
    pull_requests: List[github.PullRequest],
    specs: List[str],
) -> None:
    """It lists all pull requests."""
    repository._pull_requests = pull_requests
    with pytest.raises(Exception):
        for _ in list_pull_requests(repository, specs, bus=bus):
            pass
