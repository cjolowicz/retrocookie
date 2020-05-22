"""Core module."""
import json
import subprocess  # noqa: S404
import tempfile
from pathlib import Path
from typing import cast, Container, Dict, List, Optional


NAMESPACE = "retrocookie"
REMOTE = "retrocookie-instance"


def exists_remote(remote: str) -> bool:
    process = subprocess.run(
        ["git", "remote"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=True,
    )
    remotes = process.stdout.split()
    return remote in remotes


def add_remote(remote: str, url: str) -> None:
    subprocess.run(["git", "remote", "add", remote, url], check=True)
    subprocess.run(["git", "remote", "set-url", "--push", remote, "none"], check=True)


def remove_remote(remote: str) -> None:
    subprocess.run(["git", "remote", "remove", remote], check=True)


def get_remote_url(remote: str) -> str:
    process = subprocess.run(
        ["git", "remote", "get-url", remote],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=True,
    )
    return process.stdout.strip()


def fetch_remote(remote: str, ref: str) -> None:
    subprocess.run(["git", "fetch", "--no-tags", remote, ref], check=True)


def create_branch(branch: str, remote: str, ref: str) -> None:
    subprocess.run(
        ["git", "switch", "--force-create", branch, f"{REMOTE}/{ref}"], check=True,
    )


def load_context(
    whitelist: Container[str], blacklist: Container[str]
) -> Dict[str, str]:
    with Path(".cookiecutter.json").open() as io:
        data = cast(Dict[str, str], json.load(io))

    return {
        key: value
        for key, value in data.items()
        if key not in blacklist and not (whitelist and key not in whitelist)
    }


def find_template_directory() -> Path:
    tokens = "{{", "cookiecutter", "}}"
    for path in Path.cwd().iterdir():
        if path.is_dir() and all(x in path.name for x in tokens):
            return path
    raise Exception("cannot find template directory")


def filter_branch(
    branch: str, template_directory: Path, context: Dict[str, str]
) -> None:
    def ref(key: str) -> str:
        return f"{{{{cookiecutter.{key}}}}}"

    command = [
        "git",
        "filter-repo",
        "--force",
        f"--refs={branch}",
        f"--to-subdirectory-filter={template_directory.name}",
        *(f"--path-rename={value}:{ref(key)}" for key, value in context.items()),
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        replacements = Path(tmpdir) / "replacements.txt"
        replacements.write_text(
            "\n".join(f"{value}==>{ref(key)}" for key, value in context.items())
        )

        command.append(f"--replace-text={replacements}")
        subprocess.run(command, check=True)


def get_current_branch() -> str:
    process = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=True,
    )
    return process.stdout.strip()


def switch_branch(branch: str) -> None:
    subprocess.run(["git", "switch", branch], check=True)


def guess_remote_url() -> str:
    url = get_remote_url("origin")
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
    original_branch = get_current_branch()
    branch = f"{NAMESPACE}/{ref}"

    if exists_remote(REMOTE):
        remove_remote(REMOTE)

    try:
        add_remote(REMOTE, url)
        fetch_remote(REMOTE, ref)
        create_branch(branch, REMOTE, ref)
        context = load_context(whitelist, blacklist)
        filter_branch(branch, template_directory, context)
        switch_branch(original_branch)
    finally:
        if exists_remote(REMOTE):
            remove_remote(REMOTE)


def exists_branch(branch: str) -> bool:
    process = subprocess.run(
        ["git", "show-ref", "--verify", "--quiet", "refs/heads/{branch}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return process.returncode == 0


def remove_branch(branch: str) -> None:
    subprocess.run(["git", "branch", "--delete", "--force", branch], check=True)


def find_branches() -> List[str]:
    process = subprocess.run(
        [
            "git",
            "for-each-ref",
            "--format=%(refname:short)",
            f"refs/heads/{NAMESPACE}/",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=True,
    )
    return process.stdout.split()


def cleanup(branch: Optional[str]) -> None:
    branches = (
        [branch] if branch is not None and exists_branch(branch) else find_branches()
    )

    for branch in branches:
        remove_branch(branch)

    if exists_remote(REMOTE):
        remove_remote(REMOTE)
