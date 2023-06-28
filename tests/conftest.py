"""Fixtures."""
from __future__ import annotations

import json
import textwrap
from pathlib import Path
from typing import Dict
from typing import TYPE_CHECKING

import cruft  # type: ignore[import]
import pytest
from cookiecutter.main import cookiecutter


if TYPE_CHECKING:
    from retrocookie import git


@pytest.fixture
def context() -> Dict[str, str]:
    """Cookiecutter context dictionary."""
    return {"project_slug": "example"}


@pytest.fixture
def cookiecutter_path(tmp_path: Path) -> Path:
    """Cookiecutter path."""
    path = tmp_path / "cookiecutter"
    path.mkdir()
    return path


@pytest.fixture
def cookiecutter_json(cookiecutter_path: Path, context: Dict[str, str]) -> Path:
    """The cookiecutter.json file."""
    path = cookiecutter_path / "cookiecutter.json"
    text = json.dumps(context)
    path.write_text(text)
    return path


@pytest.fixture
def cookiecutter_subdirectory(cookiecutter_path: Path) -> Path:
    """The template directory in the cookiecutter."""
    path = cookiecutter_path / "{{cookiecutter.project_slug}}"
    path.mkdir()
    return path


@pytest.fixture
def cookiecutter_readme(cookiecutter_subdirectory: Path) -> Path:
    """The README file in the cookiecutter."""
    path = cookiecutter_subdirectory / "README.md"
    text = """\
    # {{cookiecutter.project_slug}}

    Welcome to `{{cookiecutter.project_slug}}`!
    """
    path.write_text(textwrap.dedent(text))
    return path


@pytest.fixture
def dot_cookiecutter_json(cookiecutter_subdirectory: Path) -> Path:
    """The .cookiecutter.json file in the cookiecutter."""
    path = cookiecutter_subdirectory / ".cookiecutter.json"
    text = """\
    {{cookiecutter | jsonify}}
    """
    path.write_text(textwrap.dedent(text))
    return path


@pytest.fixture
def cookiecutter_project(
    cookiecutter_path: Path,
    cookiecutter_json: Path,
    cookiecutter_readme: Path,
    dot_cookiecutter_json: Path,
) -> Path:
    """The cookiecutter."""
    return cookiecutter_path


@pytest.fixture
def cruft_project(
    cookiecutter_path: Path,
    cookiecutter_json: Path,
    cookiecutter_readme: Path,
) -> Path:
    """The cookiecutter using cruft."""
    # This still has `.cookiecutter.json` for some reason
    return cookiecutter_path


def make_repository(path: Path) -> git.Repository:
    """Turn a directory into a git repository."""
    from retrocookie import git

    repository = git.Repository.init(path)
    repository.add()
    repository.commit("Initial commit")
    return repository


@pytest.fixture
def cookiecutter_repository(cookiecutter_project: Path) -> git.Repository:
    """The cookiecutter repository."""
    return make_repository(cookiecutter_project)


@pytest.fixture
def cruft_repository(cruft_project: Path) -> git.Repository:
    """The cookiecutter repository using cruft."""
    return make_repository(cruft_project)


@pytest.fixture
def cookiecutter_instance(
    cookiecutter_repository: git.Repository,
    context: Dict[str, str],
    tmp_path: Path,
) -> Path:
    """The cookiecutter instance."""
    template = str(cookiecutter_repository.path)
    cookiecutter(template, no_input=True, output_dir=str(tmp_path))
    return tmp_path / context["project_slug"]


@pytest.fixture
def cruft_instance(
    cruft_repository: git.Repository,
    tmp_path: Path,
) -> Path:
    """The cookiecutter instance using cruft."""
    template = str(cruft_repository.path)
    path: Path = cruft.create(
        template_git_url=template, no_input=True, output_dir=tmp_path
    )
    return path


@pytest.fixture
def vanilla_instance_repository(cookiecutter_instance: Path) -> git.Repository:
    """The vanilla cookiecutter instance repository."""
    return make_repository(cookiecutter_instance)


@pytest.fixture
def cruft_instance_repository(cruft_instance: Path) -> git.Repository:
    """The cookiecutter instance repository using cruft."""
    return make_repository(cruft_instance)


@pytest.fixture(params=["vanilla_instance_repository", "cruft_instance_repository"])
def cookiecutter_instance_repository(request: pytest.FixtureRequest) -> git.Repository:
    """The cookiecutter instance repository."""
    param = request.param  # type: ignore[attr-defined]
    repo: git.Repository = request.getfixturevalue(param)
    return repo
