"""Functional tests for retrocookie.pr.__main__."""
from pathlib import Path
from typing import Callable
from typing import List

import pytest
from github3.repos.repo import Repository
from tests.pr.functional.conftest import CreatePullRequest
from tests.pr.functional.conftest import FindPullRequest
from tests.pr.functional.conftest import skip_without_token

from retrocookie.pr import __main__
from retrocookie.pr import appname


InvokeMain = Callable[[List[str]], None]


@pytest.fixture
def invoke_main(project: Repository, token: str) -> InvokeMain:
    """Invoke the main function."""

    def _main(args: List[str]) -> None:
        args = [
            f"--repository={project.full_name}",
            f"--token={token}",
            *args,
        ]

        __main__.main.main(
            args=args,
            prog_name=__main__.main.name,
            standalone_mode=False,
        )

    return _main


# This test connects to the real API. Skip it if we don't have a token (even
# though the test does not actually use it).
@skip_without_token
def test_invalid_token() -> None:
    """It fails."""
    with pytest.raises(SystemExit):
        __main__.main.main(
            args=["--repository=REPOSITORY", "--token=INVALID", "1"],
            prog_name=__main__.main.name,
            standalone_mode=False,
        )


@skip_without_token
def test_number(
    create_project_pull_request: CreatePullRequest,
    invoke_main: InvokeMain,
    find_template_pull_request: FindPullRequest,
) -> None:
    """It imports the pull request with the given number."""
    project_pull = create_project_pull_request(
        Path("README.md"),
        "# Welcome to example",
    )

    invoke_main([str(project_pull.number)])

    template_pull = find_template_pull_request()
    assert project_pull.title == template_pull.title


@skip_without_token
def test_rewrite(
    create_project_pull_request: CreatePullRequest,
    invoke_main: InvokeMain,
    template: Repository,
) -> None:
    """It rewrites the commits associated with the pull request."""
    project_pull = create_project_pull_request(
        Path("README.md"),
        "# Welcome to example",
    )

    invoke_main([str(project_pull.number)])

    template_file = template.file_contents(
        "{{cookiecutter.project}}/README.md",
        ref=f"refs/heads/{appname}/{project_pull.head.ref}",
    )
    assert "# Welcome to {{cookiecutter.project}}" == template_file.decoded.decode()


@skip_without_token
def test_force(
    create_project_pull_request: CreatePullRequest,
    invoke_main: InvokeMain,
) -> None:
    """It updates the pull request."""
    project_pull = create_project_pull_request(
        Path("README.md"),
        "# Welcome to example",
    )

    invoke_main([str(project_pull.number)])
    invoke_main(["--force", "--all"])


@skip_without_token
def test_user(
    create_project_pull_request: CreatePullRequest,
    invoke_main: InvokeMain,
    find_template_pull_request: FindPullRequest,
) -> None:
    """It imports pull requests of the given user."""
    project_pull = create_project_pull_request(
        Path("README.md"),
        "# Welcome to example",
    )

    invoke_main([f"--user={project_pull.user.login}", str(project_pull.number)])

    template_pull = find_template_pull_request()
    assert project_pull.title == template_pull.title
