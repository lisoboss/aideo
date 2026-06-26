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
