"""Listing pull requests."""
import contextlib
from typing import Collection
from typing import Iterator
from typing import Optional

from retrocookie.pr import events
from retrocookie.pr.base.bus import Bus
from retrocookie.pr.protocols import github


def get_pull_request(
    repository: github.Repository,
    spec: str,
    *,
    bus: Bus,
) -> github.PullRequest:
    """Return the pull request matching the provided spec."""
    with contextlib.suppress(ValueError):
        number = int(spec)
        return repository.pull_request(number)

    pull = repository.pull_request_by_head(f"{repository.owner}:{spec}")
    if pull is not None:
        return pull

    bus.events.raise_(events.PullRequestNotFound(spec))


def get_pull_requests(
    repository: github.Repository,
    specs: Collection[str] = (),
    *,
    bus: Bus,
) -> Iterator[github.PullRequest]:
    """Return pull requests. With specs, filter those matching specs."""
    if specs:
        for spec in specs:
            yield get_pull_request(repository, spec, bus=bus)
    else:
        yield from repository.pull_requests()


def list_pull_requests(
    repository: github.Repository,
    specs: Collection[str] = (),
    *,
    user: Optional[str] = None,
    bus: Bus,
) -> Iterator[github.PullRequest]:
    """List matching pull requests in repository."""
    for pull in get_pull_requests(repository, specs, bus=bus):
        if user is None or pull.user == user:
            yield pull
