"""Functional tests for retrocookie.pr.adapters.github."""
from pathlib import Path

from tests.pr.functional.conftest import CreatePullRequest
from tests.pr.functional.conftest import skip_without_token

from retrocookie.pr.adapters import github


@skip_without_token
def test_html_url(
    create_project_pull_request: CreatePullRequest,
) -> None:
    """It imports pull requests of the given user."""
    project_pull = create_project_pull_request(
        Path("README.md"),
        "# Welcome to example",
    )

    pull_request = github.PullRequest(project_pull)

    assert pull_request.html_url.startswith("https://github.com/")
