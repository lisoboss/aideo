"""Entry point for running aideo-serv via uvicorn."""

import uvicorn
from aideo_serv.app import create_app
from aideo_serv.config import Settings

app = create_app()


def main() -> None:
    """Start the aideo-serv API server."""
    settings = Settings()
    uvicorn.run(
        "aideo_serv.main:app",
        host=settings.server_host,
        port=settings.server_port,
        reload=True,
    )


if __name__ == "__main__":
    main()
