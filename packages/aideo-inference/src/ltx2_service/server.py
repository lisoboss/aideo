"""LTX-2 inference service — FastAPI server."""

from uuid import UUID

import uvicorn
from fastapi import FastAPI, HTTPException
from ltx2_service.model import LTX2Model
from ltx2_service.progress import send_progress
from pydantic import BaseModel


class GenerateRequest(BaseModel):
    """Payload from aideo-serv to start generation."""

    task_id: UUID
    prompt: str
    params: dict | None = None
    callback_url: str = ""


app = FastAPI(title="ltx2-service", version="0.1.0")
model = LTX2Model()


@app.on_event("startup")
async def startup():
    """Pre-load the model on startup."""
    await model.load()


@app.post("/generate", status_code=202)
async def generate(req: GenerateRequest):
    """Start a video generation task.

    Reports progress to the callback_url during generation,
    then posts a completed or error event.
    """
    try:
        async for progress in model.generate(req.prompt, req.params):
            await send_progress(
                req.callback_url,
                req.task_id,
                "progress",
                {"progress": progress},
            )

        await send_progress(
            req.callback_url,
            req.task_id,
            "completed",
            {"result_path": "stub"},
        )
        return {"status": "completed", "task_id": str(req.task_id)}

    except Exception as e:
        await send_progress(
            req.callback_url,
            req.task_id,
            "error",
            {"message": str(e)},
        )
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health():
    """Health check."""
    return {"status": "ok"}


def main():
    """Entry point: ltx2-server."""
    uvicorn.run(
        "ltx2_service.server:app",
        host="0.0.0.0",
        port=9090,
        reload=False,
    )


if __name__ == "__main__":
    main()
