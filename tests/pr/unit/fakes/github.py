"""Fake GitHub API."""
from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from pathlib import Path
from typing import AbstractSet
from typing import Iterable
from typing import List
from typing import Optional
from typing import Set

from retrocookie import git


@dataclass(order=True)
class PullRequest:
    """Fake pull request."""

    number: int
    title: str
    body: Optional[str]
    branch: str
    user: str
    html_url: str = ""
    labels: Set[str] = dataclasses.field(default_factory=set)

    def update(self, title: str, body: Optional[str], labels: AbstractSet[str]) -> None:
        """Update the pull request."""
        self.title = title
        self.body = body
        self.labels = set(labels)


@dataclass
class Repository:
    """Fake repository."""

    owner: str
    name: str
    _pull_requests: List[PullRequest] = dataclasses.field(default_factory=list)
    _repository: Optional[git.Repository] = None

    @classmethod
    def create(
        cls, owner: str, name: str, _backend: Optional[Path] = None
    ) -> Repository:
        """Create a fake repository."""
        if _backend is None:
            return cls(owner, name)

        path = _backend / owner / f"{name}.git"
        if path.exists():
            repository = git.Repository(path)
        else:
            repository = git.Repository.init(path, bare=True)
            repository.commit("Initial")

        return cls(owner, name, _repository=repository)

    @property
    def full_name(self) -> str:
        """The full name of the repository."""
        return "/".join([self.owner, self.name])

    @property
    def clone_url(self) -> str:
        """URL for cloning the repository."""
        if self._repository is None:
            return f"https://github.com/{self.full_name}.git"

        return f"file://{self._repository.path.resolve()}"

    @property
    def push_url(self) -> str:
        """URL for pushing to the repository."""
        return self.clone_url

    @property
    def default_branch(self) -> str:
        """The default branch of the repository."""
        return git.get_default_branch()

    def pull_requests(self) -> Iterable[PullRequest]:
        """Pull requests open in the repository."""
        return self._pull_requests

    def pull_request(self, number: int) -> PullRequest:
        """Return pull request identified by the given number."""
        for pull_request in self._pull_requests:
            if pull_request.number == number:
                return pull_request
        raise ValueError("not found")

    def pull_request_by_head(self, head: str) -> Optional[PullRequest]:
        """Return pull request for the given head."""
        user, _, branch = head.rpartition(":")
        for pull_request in self._pull_requests:
            if self.owner == user and pull_request.branch == branch:
                return pull_request
        return None

    def create_pull_request(
        self,
        *,
        head: str,
        title: str,
        body: Optional[str],
        labels: AbstractSet[str],
    ) -> PullRequest:
        """Create a pull request."""
        user, _, branch = head.rpartition(":")
        number = 1 + max((pr.number for pr in self._pull_requests), default=0)
        html_url = f"https://github.com/{self.full_name}/pull/{number}"
        pull_request = PullRequest(
            number=number,
            title=title,
            body=body,
            branch=branch,
            user=user or self.owner,
            html_url=html_url,
            labels=set(labels),
        )
        self._pull_requests.append(pull_request)
        return pull_request


@dataclass
class API:
    """Fake GitHub API."""

    _backend: Optional[Path] = None
    _repositories: List[Repository] = dataclasses.field(default_factory=list)

    @property
    def me(self) -> str:
        """Return the login of the authenticated user."""
        return "owner"

    def repository(self, owner: str, name: str) -> Repository:
        """Return the repository with the given owner and name."""
        for repository in self._repositories:
            if repository.owner == owner and repository.name == name:
                return repository

        repository = Repository.create(owner, name, _backend=self._backend)
        self._repositories.append(repository)
        return repository
