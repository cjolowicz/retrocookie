"""Core module."""
import json
import subprocess  # noqa: S404
import tempfile
from pathlib import Path
from typing import cast
from typing import Container
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple

from . import git


NAMESPACE = "retrocookie"
REMOTE = "retrocookie-instance"


def find_template_directory() -> Path:
    """Locate the subdirectory with the project template."""
    tokens = "{{", "cookiecutter", "}}"
    for path in Path.cwd().iterdir():
        if path.is_dir() and all(x in path.name for x in tokens):
            return path
    raise Exception("cannot find template directory")


def load_context() -> Dict[str, str]:
    """Load the context from the .cookiecutter.json file."""
    with Path(".cookiecutter.json").open() as io:
        return cast(Dict[str, str], json.load(io))


def get_replacements(
    context: Dict[str, str], whitelist: Container[str], blacklist: Container[str],
) -> List[Tuple[str, str]]:
    """Create replacements to be applied to commits from the template instance."""

    def ref(key: str) -> str:
        return f"{{{{cookiecutter.{key}}}}}"

    replacements = [
        (value, ref(key))
        for key, value in context.items()
        if key not in blacklist and not (whitelist and key not in whitelist)
    ]
    replacements.extend(
        [(token, token.join(('{{ "', '" }}'))) for token in ("{{", "}}")]
    )

    return replacements


def guess_remote_url() -> str:
    """Guess the URL of the template instance."""
    url = git.get_remote_url("origin")
    if url.endswith(".git"):
        url = url[: -len(".git")]
    return f"{url}-instance.git"


def retrocookie(
    url: Optional[str], ref: str, whitelist: Container[str], blacklist: Container[str],
) -> None:
    """Import commits from instance repository into template repository."""
    if url is None:
        url = guess_remote_url()

    template_directory = find_template_directory()
    original_branch = git.get_current_branch()
    branch = f"{NAMESPACE}/{ref}"

    if git.exists_remote(REMOTE):
        git.remove_remote(REMOTE)

    try:
        git.add_remote(REMOTE, url)
        git.fetch_remote(REMOTE, ref)
        git.create_branch(branch, REMOTE, ref)
        context = load_context()
        replacements = get_replacements(context, whitelist, blacklist)
        filter_branch(branch, template_directory, replacements)
        git.switch_branch(original_branch)
    finally:
        if git.exists_remote(REMOTE):
            git.remove_remote(REMOTE)


def filter_branch(
    branch: str, template_directory: Path, replacements: List[Tuple[str, str]]
) -> None:
    """Rewrite commits from the template instance to use template variables."""
    command = [
        "git",
        "filter-repo",
        "--force",
        f"--refs={branch}",
        f"--to-subdirectory-filter={template_directory.name}",
        *(f"--path-rename={old}:{new}" for old, new in replacements),
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        replacements_file = Path(tmpdir) / "replacements.txt"
        replacements_file.write_text(
            "\n".join(f"{old}==>{new}" for old, new in replacements)
        )

        command.append(f"--replace-text={replacements_file}")
        subprocess.run(command, check=True)


def cleanup(branch: Optional[str]) -> None:
    """Remove branches and remotes created by this program."""
    branches = (
        [branch]
        if branch is not None and git.exists_branch(branch)
        else git.find_branches(NAMESPACE)
    )

    for branch in branches:
        git.remove_branch(branch)

    if git.exists_remote(REMOTE):
        git.remove_remote(REMOTE)
