"""Core module."""
import json
import subprocess  # noqa: S404
import tempfile
from pathlib import Path
from typing import cast
from typing import Container
from typing import Dict
from typing import Iterable
from typing import List
from typing import Optional
from typing import Tuple

from . import git


NAMESPACE = "retrocookie"
REMOTE = "retrocookie-instance"


def guess_remote_url() -> str:
    """Guess the URL of the template instance."""
    url = git.get_remote_url("origin")
    if url.endswith(".git"):
        url = url[: -len(".git")]
    return f"{url}-instance.git"


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


def filter_branch(
    refs: Iterable[str], subdirectory: str, replacements: List[Tuple[str, str]]
) -> None:
    """Rewrite commits from the template instance to use template variables."""
    command = [
        "git",
        "filter-repo",
        "--force",
        f"--to-subdirectory-filter={subdirectory}",
        *(f"--path-rename={old}:{new}" for old, new in replacements),
        *(f"--refs={ref}" for ref in refs),
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        replacements_file = Path(tmpdir) / "replacements.txt"
        replacements_file.write_text(
            "\n".join(f"{old}==>{new}" for old, new in replacements)
        )

        command.append(f"--replace-text={replacements_file}")
        subprocess.run(command, check=True)


def local(ref: str) -> str:
    return f"{NAMESPACE}/{ref}"


def remote(ref: str) -> str:
    return f"{REMOTE}/{ref}"


def fetch_commits(url: str, ref: str, base: str) -> None:
    """Fetch commits from the template instance."""
    if git.exists_remote(REMOTE):
        git.remove_remote(REMOTE)

    git.add_remote(REMOTE, url)
    git.fetch_remote(REMOTE, ref, base)
    git.create_branch(local(ref), remote(ref))
    git.create_branch(local(base), remote(base))
    git.remove_remote(REMOTE)


def rewrite_commits(
    ref: str,
    base: str,
    template_directory: Path,
    whitelist: Container[str],
    blacklist: Container[str],
) -> None:
    """Rewrite commits for template."""
    context = load_context()
    replacements = get_replacements(context, whitelist, blacklist)
    filter_branch(
        refs=(local(ref), local(base)),
        subdirectory=template_directory.name,
        replacements=replacements,
    )


def harvest_commits(branch: str, base: str, ref: str, onto: str) -> None:
    """Rebase commits and clean up."""
    git.rebase(local(base), local(ref), "--onto={onto}")
    git.move_branch(local(ref), branch)
    git.remove_branch(local(base))


def retrocookie(
    url: Optional[str],
    ref: str,
    whitelist: Container[str],
    blacklist: Container[str],
    base: str = "master",
    branch: Optional[str] = None,
) -> None:
    """Import commits from instance repository into template repository."""
    if url is None:
        url = guess_remote_url()

    if branch is None:
        branch = ref

    template_directory = find_template_directory()
    original_branch = git.get_current_branch()

    fetch_commits(url, ref, base)
    rewrite_commits(ref, base, template_directory, whitelist, blacklist)
    harvest_commits(branch, base, ref, onto=original_branch)


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
