"""Command-line interface."""
from pathlib import Path
from typing import Container
from typing import Iterable
from typing import Optional

import click

from .core import retrocookie


@click.command()
@click.option(
    "--branch",
    "-b",
    metavar="BRANCH",
    help="Remote branch to cherry-pick",
)
@click.option(
    "--upstream",
    metavar="REF",
    help="Remote upstream branch",
)
@click.option(
    "--create",
    "-c",
    is_flag=True,
    help="Create a local branch with the same name as --branch",
)
@click.option(
    "--create-branch",
    metavar="BRANCH",
    help="Create a local branch for the imported commits",
)
@click.option(
    "--include-variable",
    "include_variables",
    metavar="VAR",
    multiple=True,
    help="Only rewrite these Cookiecutter variables",
)
@click.option(
    "--exclude-variable",
    "exclude_variables",
    metavar="VAR",
    multiple=True,
    help="Do not rewrite these Cookiecutter variables",
)
@click.option(
    "--directory",
    "-C",
    metavar="DIR",
    help="Path to the repository  [default: working directory]",
)
@click.argument("repository")
@click.argument("commits", nargs=-1)
@click.version_option()
def main(
    branch: Optional[str],
    upstream: Optional[str],
    create: bool,
    create_branch: Optional[str],
    include_variables: Container[str],
    exclude_variables: Container[str],
    directory: Optional[str],
    repository: str,
    commits: Iterable[str],
) -> None:
    """Retrocookie imports commits into Cookiecutter templates.

    The path to the source repository is passed as a positional argument.
    This should be an instance of the Cookiecutter template with a
    .cookiecutter.json file.

    Additional positional arguments are the commits to be imported.
    See gitrevisions(7) for a list of ways to spell commits and commit
    ranges. These arguments are interpreted in the same way as
    git-cherry-pick(1) does. If no commits are specified, the HEAD
    commit is imported.

    Specifying --branch is equivalent to passing master..<branch>
    as a positional argument. Use --upstream to specify a different
    upstream branch. Use --create to create the same branch in the
    target repository.

    By default, commits are cherry-picked onto the current branch.
    Use --create-branch to specify a different branch, which must
    not exist yet. As a shorthand, --create is equivalent to passing
    --create-branch with the same argument as --branch.

    Commits are rewritten in the following way:

    \b
      - Files are moved to the template directory
      - Tokens with special meaning in Jinja are escaped
      - Values from .cookiecutter.json are replaced by templating tags
        with the corresponding variable name

    Use the --include-variable and --exclude-variable options to include or
    exclude specific variables from .cookiecutter.json.
    """
    if create:
        if create_branch:
            raise click.UsageError(
                "--create and --create-branch are mutually exclusive"
            )

        if branch is None:
            raise click.UsageError("--create requires --branch")

        create_branch = branch

    if not commits and branch is None:
        commits = ["HEAD"]

    path = Path(directory) if directory else None
    retrocookie(
        Path(repository),
        commits,
        branch=branch,
        upstream=upstream,
        create_branch=create_branch,
        include_variables=include_variables,
        exclude_variables=exclude_variables,
        path=path,
    )


if __name__ == "__main__":
    main(prog_name="retrocookie")  # pragma: no cover
