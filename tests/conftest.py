"""Fixtures."""
from __future__ import annotations

import json
import textwrap
from pathlib import Path
from typing import Dict
from typing import Optional
from typing import TYPE_CHECKING

import pytest
from cookiecutter.main import cookiecutter


if TYPE_CHECKING:
    from retrocookie import git


@pytest.fixture
def context() -> Dict[str, str]:
    """Cookiecutter context dictionary."""
    return {"project_slug": "example"}


@pytest.fixture(params=["vanilla", "cruft"])
def flavor(request: pytest.FixtureRequest) -> str:
    """Test flavor, either vanilla cookiecutter or cruft."""
    out: str = request.param  # type: ignore[attr-defined]
    return out


@pytest.fixture
def flavor_path(tmp_path: Path, flavor: str) -> Path:
    """Temporary path to given flavor of test."""
    path = tmp_path / flavor
    path.mkdir()
    return path


@pytest.fixture
def cookiecutter_path(flavor_path: Path) -> Path:
    """Cookiecutter path."""
    path = flavor_path / "cookiecutter"
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
def dot_cookiecutter_json(
    cookiecutter_subdirectory: Path, flavor: str
) -> Optional[Path]:
    """The .cookiecutter.json file in the cookiecutter."""
    if flavor == "vanilla":
        path = cookiecutter_subdirectory / ".cookiecutter.json"
        text = """\
        {{cookiecutter | jsonify}}
        """
        path.write_text(textwrap.dedent(text))
        return path
    return None


@pytest.fixture
def cookiecutter_project(
    cookiecutter_path: Path,
    cookiecutter_json: Path,
    cookiecutter_readme: Path,
    dot_cookiecutter_json: Path,
) -> Path:
    """The cookiecutter."""
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
def cookiecutter_instance(
    cookiecutter_repository: git.Repository,
    context: Dict[str, str],
    flavor_path: Path,
    flavor: str,
) -> Path:
    """The cookiecutter instance."""
    template = str(cookiecutter_repository.path)
    if flavor == "vanilla":
        cookiecutter(template, no_input=True, output_dir=str(flavor_path))
        return flavor_path / context["project_slug"]
    elif flavor == "cruft":
        import cruft  # type: ignore[import]

        path: Path = cruft.create(
            template_git_url=template, no_input=True, output_dir=flavor_path
        )
        return path
    raise ValueError


@pytest.fixture
def cookiecutter_instance_repository(cookiecutter_instance: Path) -> git.Repository:
    """The vanilla cookiecutter instance repository."""
    return make_repository(cookiecutter_instance)
