"""GitHub interface."""
from __future__ import annotations

from typing import AbstractSet
from typing import cast
from typing import Iterable
from typing import Optional
from typing import Set
from typing import Union

import github3.exceptions
import requests
import tenacity

from retrocookie.pr import events
from retrocookie.pr.base.bus import Bus
from retrocookie.pr.base.exceptionhandlers import ExceptionHandler
from retrocookie.pr.base.exceptionhandlers import exceptionhandler


class PullRequest:
    """Pull request in a GitHub repository."""

    def __init__(
        self,
        pull_request: Union[
            github3.pulls.PullRequest,
            github3.pulls.ShortPullRequest,
        ],
    ) -> None:
        """Initialize."""
        self._pull_request = pull_request

    @property
    def number(self) -> int:
        """Number of the pull request."""
        return cast(int, self._pull_request.number)

    @property
    def title(self) -> str:
        """Title of the pull request description."""
        return cast(str, self._pull_request.title)

    @property
    def body(self) -> Optional[str]:
        """Body of the pull request description."""
        return cast(Optional[str], self._pull_request.body)

    @property
    def branch(self) -> str:
        """Branch merged by the pull request."""
        return cast(str, self._pull_request.head.ref)

    @property
    def user(self) -> str:
        """Login of the user that opened the pull request."""
        return cast(str, self._pull_request.user.login)

    @property
    def html_url(self) -> str:
        """URL for viewing the pull request in a browser."""
        return cast(str, self._pull_request.html_url)

    @property
    def labels(self) -> Set[str]:
        """The labels associated with the pull request."""
        issue = self._pull_request.issue()
        return {label.name for label in issue.labels()}

    def update(self, title: str, body: Optional[str], labels: AbstractSet[str]) -> None:
        """Update the pull request."""
        self._pull_request.update(title=title, body=body)
        self._pull_request.issue().replace_labels([*labels])


class Repository:
    """GitHub Repository."""

    def __init__(
        self, repository: github3.repos.repo.Repository, *, token: str, bus: Bus
    ) -> None:
        """Initialize."""
        self._repository = repository
        self._token = token
        self._bus = bus

    @property
    def owner(self) -> str:
        """The user who owns the repository."""
        return cast(str, self._repository.owner.login)

    @property
    def full_name(self) -> str:
        """The full name of the repository."""
        return cast(str, self._repository.full_name)

    @property
    def clone_url(self) -> str:
        """URL for cloning the repository."""
        return cast(str, self._repository.clone_url)

    @property
    def push_url(self) -> str:
        """URL for pushing to the repository."""
        return f"https://{self._token}:x-oauth-basic@github.com/{self.full_name}.git"

    @property
    def default_branch(self) -> str:
        """The default branch of the repository."""
        return cast(str, self._repository.default_branch)

    def pull_request(self, number: int) -> PullRequest:
        """Return pull request identified by the given number."""
        with self._bus.events.reraise(
            events.PullRequestNotFound(str(number)),
            when=github3.exceptions.NotFoundError,
        ):
            pull_request = self._repository.pull_request(number)

        return PullRequest(pull_request)

    def pull_request_by_head(self, head: str) -> Optional[PullRequest]:
        """Return pull request for the given head."""
        for pull_request in self._repository.pull_requests(head=head):
            return PullRequest(pull_request)
        return None

    def pull_requests(self) -> Iterable[PullRequest]:
        """Pull requests open in the repository."""
        for pull_request in self._repository.pull_requests(state="open"):
            yield PullRequest(pull_request)

    def create_pull_request(
        self,
        *,
        head: str,
        title: str,
        body: Optional[str],
        labels: AbstractSet[str],
    ) -> PullRequest:
        """Create a pull request."""
        pull_request = self._repository.create_pull(
            title=title,
            body=body,
            head=head,
            base=self._repository.default_branch,
        )

        # The GitHub API sometimes responds with 404 when the issue for
        # a newly created pull request is requested.
        for attempt in tenacity.Retrying(  # type: ignore[no-untyped-call]
            reraise=True,
            stop=tenacity.stop_after_attempt(3),  # type: ignore[attr-defined]
            wait=tenacity.wait_fixed(3),  # type: ignore[attr-defined]
        ):
            with attempt:
                pull_request.issue().add_labels(*labels)

        return PullRequest(pull_request)


class API:
    """GitHub API."""

    def __init__(self, github: github3.GitHub, *, token: str, bus: Bus) -> None:
        """Initialize."""
        self._github = github
        self._token = token
        self._bus = bus

    @classmethod
    def login(cls, token: str, *, bus: Bus) -> API:
        """Login to GitHub."""
        github = github3.login(token=token)
        return cls(github, token=token, bus=bus)

    @property
    def me(self) -> str:
        """Return the login of the authenticated user."""
        return cast(str, self._github.me().login)

    def repository(self, owner: str, name: str) -> Repository:
        """Return the repository with the given owner and name."""
        fullname = "/".join([owner, name])
        with self._bus.events.reraise(
            events.RepositoryNotFound(fullname),
            when=github3.exceptions.NotFoundError,
        ):
            _repository = self._github.repository(owner, name)

        return Repository(_repository, token=self._token, bus=self._bus)


def errorhandler(*, bus: Bus) -> ExceptionHandler:
    """Handle GitHub error responses."""

    @exceptionhandler
    def _handler1(error: github3.exceptions.GitHubError) -> None:
        if error.response is not None and error.response.request is not None:
            bus.events.raise_(
                events.GitHubError(
                    error.response.request.url,
                    error.response.request.method,
                    error.code,
                    error.message,  # noqa: B306
                    error.errors,
                )
            )
        return None

    @exceptionhandler
    def _handler2(error: github3.exceptions.ConnectionError) -> None:
        for arg in error.args:
            if isinstance(arg, requests.RequestException):
                bus.events.raise_(
                    events.ConnectionError(
                        arg.request.url,
                        arg.request.method,
                        str(error),
                    )
                )
        return None

    return _handler1 >> _handler2
