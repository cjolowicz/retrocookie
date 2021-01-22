"""Test data."""
from tests.pr.unit.fakes import github


EXAMPLE_PROJECT = github.Repository("owner", "project")
EXAMPLE_TEMPLATE = github.Repository("owner", "template")
EXAMPLE_PROJECT_PULL = github.PullRequest(
    1,
    "title",
    "body",
    "branch",
    "owner",
    "https://github.com/owner/project/pull/1",
)
EXAMPLE_TEMPLATE_PULL = github.PullRequest(
    1,
    "title",
    "body",
    "retrocookie-pr/branch",
    "owner",
    "https://github.com/owner/template/pull/1",
)
