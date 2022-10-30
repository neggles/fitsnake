from datetime import datetime
import orjson
import readline
import subprocess
from pathlib import Path
from typing import List, Optional

import typer
from garmin_fit_sdk import Decoder, Stream
from garmin_fit_sdk.profile import Profile as FitProfile
from openpyxl import Workbook

from fitsnake import __version__
from fitsnake.console import console, err_console

app = typer.Typer()

FIT_PROFILE_MSGS = FitProfile["messages"]
FIT_MSG_TYPES = [FIT_PROFILE_MSGS[x]["messages_key"] for x in FIT_PROFILE_MSGS.keys()]


def version_callback(value: bool):
    if value:
        console.print(f"{__package__} v{__version__}")
        raise typer.Exit()


@app.callback()
def callback(
    version: Optional[bool] = typer.Option(
        None, "--version", "-v", callback=version_callback, is_eager=True, help="Show version"
    ),
):
    readline.parse_and_bind("tab: complete")
    pass


def decode_file(file: Path, filter: bool = True) -> dict:
    with file.open("rb") as f:
        stream: Stream = Stream.from_buffered_reader(f)
        decoder: Decoder = Decoder(stream)
        messages, errors = decoder.read()

    error_strings = "\n    ".join(errors)
    if errors:
        err_console.print(f"Errors decoding {file}: {error_strings}")

    if filter:
        messages = {k: v for k, v in messages.items() if k in FIT_MSG_TYPES}
    return messages, errors


@app.command()
def json(
    infile: List[Path] = typer.Argument(
        ...,
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="Source FIT data file(s)",
    ),
    outpath: Path = typer.Option(
        None,
        "--outpath",
        "-o",
        dir_okay=True,
        file_okay=True,
        writable=True,
        help="Output directory for CSV files. Default is the same directory as the input file.",
    ),
):

    for path in infile:
        if outpath is None:
            outfile = path.with_suffix(".json")
        elif outpath.is_dir():
            outfile = outpath / path.with_suffix(".json").name
        elif outpath.is_file() and len(infile) == 1:
            outfile = outpath
        else:
            raise typer.BadParameter("If output path is a file, only one input file can be specified")

        try:
            console.print(f"Converting [bold blue]{path}[/] to [bold yellow]{outfile}[/] ...", end="")
            messages, errors = decode_file(path)
            outfile.write_bytes(orjson.dumps(messages, option=orjson.OPT_INDENT_2 | orjson.OPT_NON_STR_KEYS))
            console.print(" [bold green]OK[/]")
        except subprocess.CalledProcessError as e:
            err_console.print(f"Error converting {path} to {outfile}: {e}")
            carryon: str = console.input(prompt="Continue? [Y/N] ", emoji=False)
            if carryon.lower() != "y":
                raise typer.Abort()


@app.command()
def xlsx(
    infile: List[Path] = typer.Argument(
        ...,
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="Source FIT data file(s)",
    ),
    outpath: Path = typer.Option(
        None,
        "--outpath",
        "-o",
        dir_okay=True,
        file_okay=True,
        writable=True,
        help="Output directory for files. Default is the same directory as the input file.",
    ),
):

    for path in infile:
        if outpath is None:
            outfile = path.with_suffix(".xlsx")
        elif outpath.is_dir():
            outfile = outpath / path.with_suffix(".xlsx").name
        elif outpath.is_file() and len(infile) == 1:
            outfile = outpath
        else:
            raise typer.BadParameter("If output path is a file, only one input file can be specified")

        try:
            console.print(f"Converting [bold blue]{path}[/] to [bold yellow]{outfile}[/] ...")
            messages, errors = decode_file(path)

            if errors:
                err_console.print(f"Errors decoding {path}: {errors}")

            wb = Workbook()
            wb.iso_dates = True
            for message_type, message_data in messages.items():
                ws = wb.create_sheet(message_type)

                headers = [x for x in message_data[0].keys() if not (type(x) is int or x.isdigit())]
                console.print(
                    f"Writing {len(message_data)} rows of {len(headers)} columns to {message_type} sheet"
                )
                console.print(f'Headers: {", ".join(headers)}')
                ws.append(headers)
                for row in message_data:
                    values = []
                    for column in headers:
                        value = row.get(column, "")
                        if type(value) is datetime:
                            value = value.isoformat()
                        values.append(value)

                    ws.append(values)

            wb.save(outfile)
            console.print(" [bold green]OK[/]")
        except subprocess.CalledProcessError as e:
            err_console.print(f"Error converting {path} to {outfile}: {e}")
            carryon: str = console.input(prompt="Continue? [Y/N] ", emoji=False)
            if carryon.lower() != "y":
                raise typer.Abort()
