"""Events and contexts for the message bus."""
from dataclasses import dataclass
from typing import List

from retrocookie import git
from retrocookie.pr.base import bus
from retrocookie.pr.protocols import github


@dataclass
class GitNotFound(bus.Event):
    """Cannot find an installation of git."""


@dataclass
class BadGitVersion(bus.Event):
    """The installed version of git is too old."""

    version: git.Version
    expected: git.Version


@dataclass
class ProjectNotFound(bus.Event):
    """The generated project could not be identified."""


@dataclass
class TemplateNotFound(bus.Event):
    """The project template could not be identified."""

    project: github.Repository


@dataclass
class LoadProject(bus.Context):
    """The project repository is being loaded."""

    repository: str


@dataclass
class LoadTemplate(bus.Context):
    """A template repository is being loaded."""

    repository: str


@dataclass
class RepositoryNotFound(bus.Event):
    """The repository was not found."""

    repository: str


@dataclass
class PullRequestNotFound(bus.Event):
    """The pull request was not found."""

    pull_request: str


@dataclass
class PullRequestAlreadyExists(bus.Event):
    """The pull request already exists."""

    template: github.Repository
    template_pull: github.PullRequest
    project_pull: github.PullRequest


@dataclass
class GitFailed(bus.Event):
    """The git command exited with a non-zero status."""

    command: str
    options: List[str]
    status: int
    stdout: str
    stderr: str


@dataclass
class GitHubError(bus.Event):
    """The GitHub API returned an error response."""

    url: str
    method: str
    code: int
    message: str
    errors: List[str]


@dataclass
class ConnectionError(bus.Event):
    """A connection to the GitHub API could not be established."""

    url: str
    method: str
    error: str


@dataclass
class CreatePullRequest(bus.Context):
    """A pull request is being created."""

    template: github.Repository
    template_branch: str
    project_pull: github.PullRequest


@dataclass
class UpdatePullRequest(bus.Context):
    """A pull request is being updated."""

    template: github.Repository
    template_pull: github.PullRequest
    project_pull: github.PullRequest


@dataclass
class PullRequestCreated(bus.Event):
    """A pull request was created."""

    template: github.Repository
    template_pull: github.PullRequest
    project_pull: github.PullRequest
