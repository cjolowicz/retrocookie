"""Fixtures for functional tests."""
import json
import os
import secrets
import time
from itertools import count
from pathlib import Path
from typing import Callable
from typing import Iterator

import github3
import pytest
from github3.pulls import PullRequest
from github3.repos.repo import Repository

from retrocookie.pr import appname


session_fixture = pytest.fixture(scope="session")
skip_without_token = pytest.mark.skipif(
    "TEST_GITHUB_TOKEN" not in os.environ,
    reason="TEST_GITHUB_TOKEN is not set",
)


@session_fixture
def token() -> str:
    """Return the GitHub API token for functional tests."""
    return os.environ["TEST_GITHUB_TOKEN"]


@session_fixture
def github(token: str) -> github3.GitHub:
    """Return a GitHub API client."""
    return github3.login(token=token)


CreateRepository = Callable[[str], Repository]


@session_fixture
def create_repository(github: github3.GitHub) -> CreateRepository:
    """Create a GitHub repository."""
    owner: str = github.me().login
    random = secrets.token_hex(nbytes=3)

    def _create(slug: str) -> Repository:
        name = f"{appname}-test-{slug}-{random}"
        github.create_repository(
            name,
            description=f"Generated repository for {appname} tests",
            has_wiki=False,
        )

        for retry in count(start=1):
            try:
                return github.repository(owner, name)
            except github3.exceptions.NotFoundError:
                if retry >= 3:
                    raise

            time.sleep(4)

        raise AssertionError("unreachable")

    return _create


@session_fixture
def _template(create_repository: CreateRepository) -> Iterator[Repository]:
    repository = create_repository("template")
    yield repository
    repository.delete()


@session_fixture
def _project(create_repository: CreateRepository) -> Iterator[Repository]:
    repository = create_repository("project")
    yield repository
    repository.delete()


@session_fixture
def template(_template: Repository) -> Repository:
    """Create a GitHub repository for a Cookiecutter template."""
    _template.create_file(
        path="cookiecutter.json",
        message="Create cookiecutter.json",
        content=json.dumps({"project": "example"}).encode(),
    )
    _template.create_file(
        path="{{cookiecutter.project}}/.cookiecutter.json",
        message="Create .cookiecutter.json in project",
        content=b"{{cookiecutter | jsonify}}",
    )
    _template.create_file(
        path="{{cookiecutter.project}}/README.md",
        message="Create README.md in project",
        content=b"# {{cookiecutter.project}}",
    )
    return _template


@session_fixture
def project(_project: Repository, template: Repository) -> Repository:
    """Create a GitHub repository for a Cookiecutter template project."""
    _project.create_file(
        path=".cookiecutter.json",
        message="Create .cookiecutter.json",
        content=json.dumps(
            {"_template": f"gh:{template.full_name}", "project": "example"}
        ).encode(),
    )
    _project.create_file(
        path="README.md",
        message="Create README",
        content=b"# example",
    )
    return _project


@pytest.fixture
def branch() -> str:
    """Return a branch name that is unique for every test case."""
    random = secrets.token_hex(nbytes=3)
    return f"branch-{random}"


CreatePullRequest = Callable[[Path, str], PullRequest]


@pytest.fixture
def create_project_pull_request(project: Repository, branch: str) -> CreatePullRequest:
    """Return a pull request for the template project."""

    def _create(path: Path, content: str) -> PullRequest:
        # Wait four seconds before creating each pull request. GitHub requests one
        # second between each request for a single user, but we run these tests
        # concurrently for two platforms and two event types (pull_request and push).
        # See https://docs.github.com/en/rest/guides/best-practices-for-integrators
        time.sleep(4)

        project_default_branch = project.branch(project.default_branch)
        project.create_ref(f"refs/heads/{branch}", project_default_branch.commit.sha)

        project_file = project.file_contents(str(path))
        project_file.update(
            message=f"Update {path}",
            content=content.encode(),
            branch=branch,
        )

        return project.create_pull(
            title=f"Update {path}",
            head=f"{project.owner}:{branch}",
            base=project.default_branch,
        )

    return _create


FindPullRequest = Callable[[], PullRequest]


@pytest.fixture
def find_template_pull_request(
    template: Repository,
    branch: str,
) -> FindPullRequest:
    """Find the generated pull request in the template repository."""

    def _find() -> PullRequest:
        [template_pull] = template.pull_requests(
            head=f"{template.owner}:{appname}/{branch}"
        )
        return template_pull

    return _find
