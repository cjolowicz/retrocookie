"""Command-line interface."""
from typing import Container
from typing import Optional

import click

from .core import cleanup
from .core import retrocookie


@click.command()
@click.option(
    "--url",
    metavar="URL",
    help=(
        "Repository URL for the template instance"
        "  [default: <URL of origin>-instance]"
    ),
)
@click.option(
    "--ref",
    "-r",
    metavar="REF",
    required=True,
    help="Remote reference to fetch (required)",
)
@click.option(
    "--base",
    metavar="REF",
    default="master",
    help="Remote reference from which to rebase",
    show_default=True,
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
    "--delete", "-d", is_flag=True, help="Clean up the branches created by this tool"
)
@click.version_option()
def main(
    url: Optional[str],
    ref: str,
    base: str,
    whitelist: Container[str],
    blacklist: Container[str],
    delete: bool,
) -> None:
    """Retrocookie imports commits from template instances into the template."""
    if delete:
        cleanup(ref)
    else:
        retrocookie(url, ref, whitelist, blacklist, base)


if __name__ == "__main__":
    main(prog_name="retrocookie")  # pragma: no cover
