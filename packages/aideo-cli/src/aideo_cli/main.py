"""aideo CLI entry point."""

import typer
from aideo_cli.commands import (
    cancel,
    download,
    list_tasks,
    status,
    submit,
    transcribe,
    transcribe_stream,
    ws,
)

app = typer.Typer(
    name="aideo",
    help="AI Video Generator Studio — CLI client",
)


app.command(name="submit")(submit)
app.command(name="transcribe")(transcribe)
app.command(name="transcribe-stream")(transcribe_stream)
app.command(name="list")(list_tasks)
app.command(name="status")(status)
app.command(name="cancel")(cancel)
app.command(name="download")(download)
app.command(name="ws")(ws)
