"""Command-line interface."""
from pathlib import Path
from typing import Container
from typing import Optional

import click

from .core import retrocookie


@click.command()
@click.option(
    "--branch", metavar="BRANCH", required=True, help="Remote branch to cherry-pick",
)
@click.option(
    "--upstream",
    metavar="REF",
    default="master",
    help="Remote upstream branch",
    show_default=True,
)
@click.option(
    "--create/--no-create",
    help="Create a local branch with the same name as --branch",
    show_default=True,
)
@click.option(
    "--create-branch",
    metavar="BRANCH",
    help="Create a local branch for the imported commits",
)
@click.option(
    "--whitelist",
    "-w",
    metavar="VAR",
    multiple=True,
    help="Only rewrite these Cookiecutter variables",
)
@click.option(
    "--blacklist",
    "-b",
    metavar="VAR",
    multiple=True,
    help="Do not rewrite these Cookiecutter variables",
)
@click.option(
    "--directory", "-C", metavar="DIR", help="Repository directory",
)
@click.argument("repository")
@click.version_option()
def main(
    branch: str,
    upstream: str,
    create: bool,
    create_branch: Optional[str],
    whitelist: Container[str],
    blacklist: Container[str],
    directory: Optional[str],
    repository: str,
) -> None:
    """Retrocookie imports commits into Cookiecutter templates.

    The source repository is passed as a positional argument. This can
    be the repository URL or filesystem path of an instance of the
    Cookiecutter template.
    """
    if create:
        if create_branch:
            raise click.UsageError(
                "--create and --create-branch are mutually exclusive"
            )

        create_branch = branch

    path = Path(directory) if directory else None
    retrocookie(
        repository,
        branch,
        upstream=upstream,
        create_branch=create_branch,
        whitelist=whitelist,
        blacklist=blacklist,
        path=path,
    )


if __name__ == "__main__":
    main(prog_name="retrocookie")  # pragma: no cover
