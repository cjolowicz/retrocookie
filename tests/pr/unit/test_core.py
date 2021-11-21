"""Tests for retrocookie.pr.core."""
import json
import os
from pathlib import Path
from typing import Iterator

import pytest
from pytest import MonkeyPatch
from tests.helpers import write
from tests.pr.unit.fakes.retrocookie import retrocookie
from tests.pr.unit.utils import raises

from retrocookie import git
from retrocookie.compat import contextlib
from retrocookie.pr import appname
from retrocookie.pr import events
from retrocookie.pr.base.bus import Bus
from retrocookie.pr.base.exceptionhandlers import nullhandler
from retrocookie.pr.cache import Cache
from retrocookie.pr.core import check_git_version
from retrocookie.pr.core import get_project_name
from retrocookie.pr.core import get_template_name
from retrocookie.pr.core import import_pull_requests
from retrocookie.pr.protocols import github
from retrocookie.pr.repository import Repository


def test_import(bus: Bus, cache: Cache, api: github.API) -> None:
    """It imports the pull request."""
    cache.save_token("token")

    template = Repository.load("owner/template", api=api, cache=cache)
    project = Repository.load("owner/project", api=api, cache=cache)

    main = project.clone.get_current_branch()

    with cache.worktree(project.clone, main, force=True) as worktree:
        write(
            worktree,
            Path(".cookiecutter.json"),
            json.dumps({"_template": "gh:owner/template"}),
        )

    with cache.worktree(project.clone, "readme") as worktree:
        write(
            worktree,
            Path("README.md"),
            "# project",
        )

    project.clone.git("push")
    project.github.create_pull_request(
        head="owner:readme", title="Add README.md", body="", labels=set()
    )

    import_pull_requests(
        api=api,
        bus=bus,
        cache=cache,
        errorhandler=nullhandler,
        retrocookie=retrocookie,
        repository="owner/project",
    )

    [pull_request] = template.github.pull_requests()

    assert pull_request.branch == f"{appname}/readme"


def test_import_no_project_name(
    api: github.API,
    bus: Bus,
    cache: Cache,
    repository: git.Repository,
) -> None:
    """It derives the project name."""
    cache.save_token("token")

    repository.repo.remotes.create("origin", "git@github.com:owner/project.git")

    with chdir(repository.path):
        template = Repository.load("owner/template", api=api, cache=cache)
        project = Repository.load("owner/project", api=api, cache=cache)

        main = project.clone.get_current_branch()

        with cache.worktree(project.clone, main, force=True) as worktree:
            write(
                worktree,
                Path(".cookiecutter.json"),
                json.dumps({"_template": "gh:owner/template"}),
            )

        with cache.worktree(project.clone, "readme") as worktree:
            write(
                worktree,
                Path("README.md"),
                "# project",
            )

        project.clone.git("push")
        project.github.create_pull_request(
            head="owner:readme", title="Add README.md", body="", labels=set()
        )

        import_pull_requests(
            api=api,
            bus=bus,
            cache=cache,
            errorhandler=nullhandler,
            retrocookie=retrocookie,
        )

        [pull_request] = template.github.pull_requests()

        assert pull_request.branch == f"{appname}/readme"


@pytest.fixture
def repository(tmp_path: Path) -> git.Repository:
    """Return a repository."""
    return git.Repository.init(tmp_path / "repository")


@contextlib.contextmanager
def chdir(path: Path) -> Iterator[None]:
    """Change the directory temporarily."""
    cwd = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(cwd)


@pytest.mark.parametrize(
    "remote",
    [
        "git@github.com:owner/name.git",
        "https://github.com/owner/name.git",
        "https://github.com/owner/name",
    ],
)
def test_get_project_name(repository: git.Repository, remote: str, bus: Bus) -> None:
    """It returns the project name."""
    repository.repo.remotes.create("origin", remote)
    with chdir(repository.path):
        assert get_project_name(bus=bus) == "owner/name"


@pytest.mark.parametrize(
    "remote",
    [
        "https://example.com/owner/name",
    ],
)
def test_get_project_name_fails(
    repository: git.Repository, remote: str, bus: Bus
) -> None:
    """It fails to return the project name."""
    repository.repo.remotes.create("origin", remote)
    with chdir(repository.path):
        with raises(events.ProjectNotFound):
            get_project_name(bus=bus)


@pytest.mark.parametrize(
    "remote",
    [
        "https://example.com/owner/name",
    ],
)
def test_get_template_name_fails(
    bus: Bus, cache: Cache, api: github.API, remote: str
) -> None:
    """It fails to return the template name."""
    project = Repository.load("owner/project", api=api, cache=cache)
    main = project.clone.get_current_branch()

    with cache.worktree(project.clone, main, force=True) as worktree:
        write(
            worktree,
            Path(".cookiecutter.json"),
            json.dumps({"_template": remote}),
        )

    with raises(events.TemplateNotFound):
        get_template_name(project, bus=bus)


def test_check_git_version(bus: Bus, monkeypatch: MonkeyPatch) -> None:
    """It raises an exception when git is too old."""
    monkeypatch.setattr(git, "version", lambda: git.Version.parse("0.99"))
    with raises(events.BadGitVersion):
        check_git_version(bus=bus)
