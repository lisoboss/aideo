"""CLI subcommands for aideo."""

import asyncio
import json

import typer


def _run(coro):
    """Run an async coroutine synchronously."""
    return asyncio.run(coro)


def _print_output(data, fmt: str):
    """Print data as JSON or rich table format."""
    if fmt == "json":
        if isinstance(data, dict) and "tasks" in data:
            # List response
            typer.echo(json.dumps(data, indent=2))
        else:
            typer.echo(json.dumps(data, indent=2))
    else:
        if isinstance(data, list):
            from rich.console import Console
            from rich.table import Table

            console = Console()
            table = Table(title="Tasks")
            table.add_column("ID", style="dim")
            table.add_column("Status")
            table.add_column("Prompt")
            table.add_column("Progress")
            for t in data:
                table.add_row(
                    t.get("id", "")[:8],
                    t.get("status", ""),
                    t.get("prompt", "")[:40],
                    f"{t.get('progress', 0):.0f}%",
                )
            console.print(table)
        elif isinstance(data, dict) and "tasks" in data:
            _print_output(data["tasks"], "table")
        else:
            typer.echo(json.dumps(data, indent=2))


def submit(
    prompt: str = typer.Argument(..., help="Video generation prompt"),
    param: list[str] = typer.Option(
        None, "--param", "-p", help="Extra params: key=value"
    ),
    fmt: str = typer.Option(
        "table", "--format", "-f", help="Output format: table|json"
    ),
    server: str = typer.Option("http://localhost:8000", "--server", "-s"),
):
    """Submit a new video generation task."""
    from aideo_cli.client import AideoClient

    client = AideoClient(server=server)
    params = None
    if param:
        params = {}
        for p in param:
            k, v_raw = p.split("=", 1)
            v: str | int | float = v_raw
            try:
                v = int(v_raw)
            except ValueError:
                try:
                    v = float(v_raw)
                except ValueError:
                    pass
            params[k] = v

    task = _run(client.submit(prompt, params=params))
    _print_output(task, fmt)


def list_tasks(
    status: str = typer.Option(None, "--status", help="Filter by status"),
    limit: int = typer.Option(20, "--limit", "-n"),
    fmt: str = typer.Option("table", "--format", "-f"),
    server: str = typer.Option("http://localhost:8000", "--server", "-s"),
):
    """List tasks."""
    from aideo_cli.client import AideoClient

    client = AideoClient(server=server)
    result = _run(client.list_tasks(status=status, limit=limit))
    _print_output(result, fmt)


def status(
    task_id: str = typer.Argument(..., help="Task UUID"),
    fmt: str = typer.Option("table", "--format", "-f"),
    server: str = typer.Option("http://localhost:8000", "--server", "-s"),
):
    """Get task details and progress."""
    from aideo_cli.client import AideoClient

    client = AideoClient(server=server)
    task = _run(client.get_task(task_id))
    _print_output(task, fmt)


def cancel(
    task_id: str = typer.Argument(..., help="Task UUID"),
    server: str = typer.Option("http://localhost:8000", "--server", "-s"),
):
    """Cancel a running or queued task."""
    from aideo_cli.client import AideoClient

    client = AideoClient(server=server)
    task = _run(client.cancel_task(task_id))
    typer.echo(f"Cancelled: {task['id']}")


def download(
    task_id: str = typer.Argument(..., help="Task UUID"),
    output: str = typer.Option(..., "--output", "-o", help="Output file path"),
    server: str = typer.Option("http://localhost:8000", "--server", "-s"),
):
    """Download a generated video."""
    from aideo_cli.client import AideoClient

    client = AideoClient(server=server)
    path = _run(client.download_result(task_id, output))
    typer.echo(f"Downloaded: {path}")


def transcribe(
    audio_file: str = typer.Argument(..., help="Audio file path to transcribe"),
    language: str = typer.Option(None, "--language", "-l", help="Language code (auto-detect if not set)"),
    beam_size: int = typer.Option(5, "--beam-size", help="Beam search width"),
    word_timestamps: bool = typer.Option(True, "--word-timestamps/--no-word-timestamps"),
    vad_filter: bool = typer.Option(False, "--vad/--no-vad", help="Voice activity detection filter"),
    fmt: str = typer.Option("json", "--format", "-f", help="Output format: table|json"),
    server: str = typer.Option("http://localhost:8000", "--server", "-s"),
):
    """Submit a speech-to-text transcription task."""
    from pathlib import Path

    from aideo_cli.client import AideoClient

    audio_path = Path(audio_file).resolve()
    if not audio_path.exists():
        typer.echo(f"Error: file not found: {audio_path}", err=True)
        raise typer.Exit(code=1)

    client = AideoClient(server=server)
    params = {
        "beam_size": beam_size,
        "word_timestamps": word_timestamps,
        "vad_filter": vad_filter,
    }
    task = _run(client.transcribe(
        audio_path=str(audio_path),
        language=language,
        params=params,
    ))
    _print_output(task, fmt)


def ws(
    task_id: str = typer.Argument(..., help="Task UUID"),
    server: str = typer.Option("http://localhost:8000", "--server", "-s"),
):
    """Watch real-time task progress via WebSocket."""
    from aideo_cli.client import AideoClient

    async def _watch():
        client = AideoClient(server=server)
        async for event in client.connect_ws(task_id):
            typer.echo(json.dumps(event))

    asyncio.run(_watch())


def transcribe_stream(
    audio_file: str = typer.Argument(..., help="Audio file path (.wav, .mp3, …)"),
    language: str = typer.Option(
        None, "--language", "-l", help="Language code (auto-detect if not set)"
    ),
    chunk_seconds: float = typer.Option(
        0.0, "--chunk-seconds", "-c", help="Split audio into N-second chunks (0 = send whole file)"
    ),
    server: str = typer.Option("http://localhost:8000", "--server", "-s"),
):
    """Streaming speech-to-text — send audio chunks over WebSocket and receive
    transcription in real time.

    Each audio chunk is sent as a binary WebSocket frame; the server replies
    with JSON progress/result events.  The connection stays open across chunks.
    """
    from pathlib import Path

    from aideo_cli.client import AideoClient

    audio_path = Path(audio_file).resolve()
    if not audio_path.exists():
        typer.echo(f"Error: file not found: {audio_path}", err=True)
        raise typer.Exit(code=1)

    # Read the entire file; detect WAV parameters if applicable
    audio_bytes = audio_path.read_bytes()
    chunks: list[bytes]

    if chunk_seconds > 0:
        # Try to parse WAV header for split points
        try:
            import wave

            with wave.open(str(audio_path), "rb") as wf:
                sample_rate = wf.getframerate()
                sample_width = wf.getsampwidth()
                n_channels = wf.getnchannels()
                bytes_per_second = sample_rate * sample_width * n_channels
                chunk_size = int(bytes_per_second * chunk_seconds)

            if chunk_size <= 0:
                chunk_size = len(audio_bytes)

            chunks = [
                audio_bytes[i : i + chunk_size]
                for i in range(0, len(audio_bytes), chunk_size)
            ]
        except Exception:
            # Not a WAV file — send whole file as one chunk
            chunks = [audio_bytes]
    else:
        chunks = [audio_bytes]

    async def _stream():
        client = AideoClient(server=server)
        async for event in client.stream_transcribe(chunks):
            typer.echo(json.dumps(event))

    asyncio.run(_stream())
