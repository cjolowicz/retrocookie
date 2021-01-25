"""Protocols for retrocookie.pr.github."""
from __future__ import annotations

from typing import AbstractSet
from typing import Iterable
from typing import Optional
from typing import Set

from retrocookie.pr.compat.typing import Protocol


class PullRequest(Protocol):
    """Pull request."""

    @property
    def number(self) -> int:
        """The number of the pull request."""

    @property
    def title(self) -> str:
        """The title of the pull request."""

    @property
    def body(self) -> Optional[str]:
        """The body of the pull request."""

    @property
    def branch(self) -> str:
        """The branch merged by the pull request."""

    @property
    def user(self) -> str:
        """The user who opened the pull request."""

    @property
    def html_url(self) -> str:
        """URL for viewing the pull request in a browser."""

    @property
    def labels(self) -> Set[str]:
        """Labels applied to the pull request."""

    def update(self, title: str, body: Optional[str], labels: AbstractSet[str]) -> None:
        """Update the pull request."""


class Repository(Protocol):
    """GitHub repository."""

    @property
    def owner(self) -> str:
        """The user who owns the repository."""

    @property
    def full_name(self) -> str:
        """The full name of the repository."""

    @property
    def clone_url(self) -> str:
        """URL for cloning the repository."""

    @property
    def push_url(self) -> str:
        """URL for pushing to the repository."""

    @property
    def default_branch(self) -> str:
        """The default branch of the repository."""

    def pull_requests(self) -> Iterable[PullRequest]:
        """Pull requests open in the repository."""

    def pull_request(self, number: int) -> PullRequest:
        """Return pull request identified by the given number."""

    def pull_request_by_head(self, head: str) -> Optional[PullRequest]:
        """Return pull request for the given head."""

    def create_pull_request(
        self,
        *,
        head: str,
        title: str,
        body: Optional[str],
        labels: AbstractSet[str],
    ) -> PullRequest:
        """Create a pull request."""


class API(Protocol):
    """GitHub API."""

    @property
    def me(self) -> str:
        """Return the login of the authenticated user."""

    def repository(self, owner: str, name: str) -> Repository:
        """Return the repository with the given owner and name."""
