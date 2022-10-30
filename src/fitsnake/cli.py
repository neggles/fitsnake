import sys
from pathlib import Path

import click


@click.command()
@click.version_option(package_name="fitsnake")
@click.option("-v", "--verbose", is_flag=True, default=False, help="Enable verbose console output.")
@click.option(
    "-o",
    "--option",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    required=False,
    default="./option.ini",
    help="Path to a file",
)
@click.argument(
    "argument",
    type=str,
    required=False,
    default="",
)
def cli(verbose: bool, option: Path, argument: str):
    """
    Main entrypoint for your application.
    """
    click.echo(f"verbose: {verbose}")
    click.echo(f"option: {option}")
    click.echo(f"argument: {argument}")
    click.echo("done")
    sys.exit(0)
