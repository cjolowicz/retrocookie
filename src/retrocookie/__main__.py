"""Command-line interface."""
import click


@click.command()
@click.version_option()
def main() -> None:
    """Retrocookie."""


if __name__ == "__main__":
    main(prog_name="retrocookie")  # pragma: no cover
