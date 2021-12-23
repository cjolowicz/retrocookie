"""Tests for retrocookie.pr.importer."""
from typing import Callable

import pytest

from retrocookie.pr import appname
from retrocookie.pr import events
from retrocookie.pr.base.bus import Bus
from retrocookie.pr.cache import Cache
from retrocookie.pr.importer import Importer
from retrocookie.pr.protocols.retrocookie import Retrocookie
from retrocookie.pr.repository import Repository
from tests.pr.unit.fakes import github
from tests.pr.unit.utils import raises


@pytest.fixture
def template(repository: Callable[[str], Repository]) -> Repository:
    """Return the template repository."""
    return repository("owner/template")


@pytest.fixture
def project(repository: Callable[[str], Repository]) -> Repository:
    """Return the project repository."""
    return repository("owner/project")


@pytest.fixture
def importer(
    project: Repository,
    template: Repository,
    bus: Bus,
    cache: Cache,
    retrocookie: Retrocookie,
) -> Importer:
    """Return an importer."""
    return Importer(
        project,
        template,
        bus=bus,
        cache=cache,
        retrocookie=retrocookie,
    )


@pytest.fixture
def pull_request() -> github.PullRequest:
    """Return the pull request."""
    return github.PullRequest(1, "title", "body", "branch", "user")


def test_import(
    importer: Importer,
    pull_request: github.PullRequest,
    template: Repository,
    cache: Cache,
) -> None:
    """It imports the branch."""
    cache.save_token("token")

    importer.import_(pull_request)

    [imported] = template.github.pull_requests()

    assert imported.branch == f"{appname}/{pull_request.branch}"


def test_import_exists_branch(
    importer: Importer,
    pull_request: github.PullRequest,
    template: Repository,
    cache: Cache,
) -> None:
    """It imports the branch."""
    cache.save_token("token")

    with raises(events.PullRequestAlreadyExists):
        for _ in range(2):
            importer.import_(pull_request)


def test_import_force(
    importer: Importer,
    pull_request: github.PullRequest,
    template: Repository,
    cache: Cache,
) -> None:
    """It imports the branch."""
    cache.save_token("token")

    for force in [False, True]:
        importer.import_(pull_request, force=force)

    [imported] = template.github.pull_requests()

    assert imported.branch == f"{appname}/{pull_request.branch}"
