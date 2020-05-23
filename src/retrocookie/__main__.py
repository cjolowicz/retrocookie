"""Command-line interface."""
from typing import Container
from typing import Optional

import click

from .core import cleanup as _cleanup
from .core import retrocookie


@click.command()
@click.option(
    "--url",
    metavar="URL",
    help=(
        "Repository URL of template instance" "  [default: <originurl>-instance.git]"
    ),
)
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
@click.version_option()
def main(
    url: Optional[str],
    ref: str,
    base: str,
    local: Optional[str],
    whitelist: Container[str],
    blacklist: Container[str],
) -> None:
    """Retrocookie imports commits into Cookiecutter templates."""
    retrocookie(
        ref, base=base, local=local, url=url, whitelist=whitelist, blacklist=blacklist,
    )


if __name__ == "__main__":
    main(prog_name="retrocookie")  # pragma: no cover
