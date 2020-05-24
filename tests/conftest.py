"""Fixtures."""
import json
import textwrap
from pathlib import Path
from typing import Dict

import pytest

from retrocookie import git


@pytest.fixture
def context() -> Dict[str, str]:
    return {"project_slug": "example"}


@pytest.fixture
def cookiecutter_path(tmp_path: Path) -> Path:
    path = tmp_path / "cookiecutter-example"
    path.mkdir()
    return path


@pytest.fixture
def cookiecutter_json(cookiecutter_path: Path, context: Dict[str, str]) -> Path:
    path = cookiecutter_path / "cookiecutter.json"
    text = json.dumps(context)
    path.write_text(text)
    return path


@pytest.fixture
def cookiecutter_subdirectory(cookiecutter_path: Path) -> Path:
    path = cookiecutter_path / "{{ cookiecutter.project_slug }}"
    path.mkdir()
    return path


@pytest.fixture
def cookiecutter_readme(cookiecutter_subdirectory: Path) -> Path:
    path = cookiecutter_subdirectory / "README.md"
    text = """\
    # {{ cookiecutter.project_slug }}

    Welcome to `{{ cookiecutter.project_slug }}`!
    """
    path.write_text(textwrap.dedent(text))
    return path


@pytest.fixture
def cookiecutter_project(
    cookiecutter_path: Path, cookiecutter_json: Path, cookiecutter_readme: Path
) -> Path:
    return cookiecutter_path


@pytest.fixture
def cookiecutter_repository(cookiecutter_project: Path) -> git.Repository:
    repository = git.Repository.init(cookiecutter_project)
    repository.add()
    repository.commit(
        author="user", author_email="user@example.com", message="Initial commit"
    )
    return repository
