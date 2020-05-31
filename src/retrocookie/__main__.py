"""Command-line interface."""
from pathlib import Path
from typing import Container
from typing import Optional

import click

from .core import retrocookie


@click.command()
@click.option(
    "--ref", "-r", metavar="REF", required=True, help="Remote reference to fetch",
)
@click.option(
    "--base",
    metavar="REF",
    default="master",
    help="Remote reference to rebase from",
    show_default=True,
)
@click.option(
    "--local", metavar="REF", help="Local branch name  [default: same as --ref]",
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
@click.argument("repository", required=False)
@click.version_option()
def main(
    ref: str,
    base: str,
    local: Optional[str],
    whitelist: Container[str],
    blacklist: Container[str],
    directory: Optional[str],
    repository: Optional[str],
) -> None:
    """Retrocookie imports commits into Cookiecutter templates.

    The source repository is passed as a non-optional argument. This can
    be the repository URL or filesystem path of an instance of the
    Cookiecutter template. If omitted, the repository URL is constructed
    from origin, by appending `-instance` to the repository name.
    """
    path = Path(directory) if directory else None
    retrocookie(
        ref,
        base=base,
        branch=local,
        url=repository,
        whitelist=whitelist,
        blacklist=blacklist,
        path=path,
    )


if __name__ == "__main__":
    main(prog_name="retrocookie")  # pragma: no cover
