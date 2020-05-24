"""Fixtures."""
import json
import textwrap
from pathlib import Path
from typing import Dict

import pytest
from cookiecutter.main import cookiecutter

from retrocookie import git


AUTHOR = "user"
AUTHOR_EMAIL = "user@example.com"


@pytest.fixture
def context() -> Dict[str, str]:
    return {"project_slug": "example"}


@pytest.fixture
def cookiecutter_path(tmp_path: Path) -> Path:
    path = tmp_path / "cookiecutter"
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
def dot_cookiecutter_json(cookiecutter_subdirectory: Path) -> Path:
    path = cookiecutter_subdirectory / ".cookiecutter.json"
    text = """\
    {{ cookiecutter | jsonify }}
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
    return cookiecutter_path


def make_repository(path: Path) -> git.Repository:
    repository = git.Repository.init(path)
    repository.add()
    repository.commit(
        author=AUTHOR, author_email=AUTHOR_EMAIL, message="Initial commit"
    )
    return repository


@pytest.fixture
def cookiecutter_repository(cookiecutter_project: Path) -> git.Repository:
    return make_repository(cookiecutter_project)


@pytest.fixture
def cookiecutter_instance(
    cookiecutter_repository: git.Repository, tmp_path: Path
) -> Path:
    path = tmp_path / "instance"
    template = str(cookiecutter_repository.path)
    cookiecutter(template, no_input=True, output_dir=str(path))
    return path


@pytest.fixture
def cookiecutter_instance_repository(cookiecutter_instance: Path) -> git.Repository:
    return make_repository(cookiecutter_instance)


@pytest.fixture
def cookiecutter_instance_repository_with_topic(
    cookiecutter_instance_repository: git.Repository
) -> git.Repository:
    repository = cookiecutter_instance_repository
    readme = repository.path / "README.md"
    with readme.open(mode="w+") as io:
        io.write("Lorem ipsum\n")

    repository.create_branch("topic")
    repository.switch_branch("topic")
    repository.add(readme)
    repository.commit(
        author=AUTHOR, author_email=AUTHOR_EMAIL, message="Update README.md"
    )
    return repository
