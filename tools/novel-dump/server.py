"""起点章节本地保存服务。"""

from __future__ import annotations

import os
import re
import unicodedata
from pathlib import Path
from urllib.parse import unquote
from uuid import uuid4

import uvicorn
from fastapi import FastAPI, HTTPException, Query, Request, status
from fastapi.middleware.cors import CORSMiddleware

PROJECT_DIR = Path(__file__).resolve().parent
BOOKS_DIR = (
    Path(os.getenv("NOVEL_DUMP_BOOKS_DIR", str(PROJECT_DIR / "books")))
    .expanduser()
    .resolve()
)
MAX_BODY_BYTES = int(os.getenv("NOVEL_DUMP_MAX_BODY_BYTES", 5 * 1024 * 1024))

INVALID_FILENAME_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
MULTIPLE_SPACES = re.compile(r"\s+")

app = FastAPI(title="Novel Dump", version="0.2.0")
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https://([a-z0-9-]+\.)?qidian\.com",
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["content-type"],
)


def safe_path_component(value: str, *, max_length: int = 120) -> str:
    """把外部文本转换为安全、可读的单个路径名称。"""

    decoded = unicodedata.normalize("NFKC", unquote(value))
    cleaned = INVALID_FILENAME_CHARS.sub("_", decoded)
    cleaned = MULTIPLE_SPACES.sub(" ", cleaned).strip(" ._")
    if not cleaned or cleaned in {".", ".."}:
        raise ValueError("名称为空或不合法")
    return cleaned[:max_length].rstrip(" ._")


def chapter_filename(chapter_name: str, chapter_id: str | None) -> str:
    """生成稳定且不会因同名章节轻易覆盖的文件名。"""

    safe_name = safe_path_component(chapter_name, max_length=160)
    if chapter_id:
        safe_id = safe_path_component(chapter_id, max_length=40)
        return f"{safe_id} - {safe_name}.txt"
    return f"{safe_name}.txt"


@app.post("/save/{book_name}/{chapter_name}", status_code=status.HTTP_201_CREATED)
async def save_chapter(
    book_name: str,
    chapter_name: str,
    request: Request,
    chapter_id: str | None = Query(default=None),
) -> dict[str, str | int]:
    """接收纯文本章节内容并原子写入本地目录。"""

    try:
        safe_book = safe_path_component(book_name)
        filename = chapter_filename(chapter_name, chapter_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    body = await request.body()
    if not body.strip():
        raise HTTPException(status_code=400, detail="章节内容为空")
    if len(body) > MAX_BODY_BYTES:
        raise HTTPException(status_code=413, detail="章节内容超过大小限制")

    book_path = (BOOKS_DIR / safe_book).resolve()
    if book_path.parent != BOOKS_DIR:
        raise HTTPException(status_code=400, detail="书名路径不合法")
    book_path.mkdir(parents=True, exist_ok=True)

    file_path = book_path / filename
    temporary_path = book_path / f".{filename}.{uuid4().hex}.part"
    try:
        temporary_path.write_bytes(body)
        temporary_path.replace(file_path)
    except OSError as exc:
        temporary_path.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail="章节保存失败") from exc

    return {
        "status": "ok",
        "path": str(file_path.relative_to(PROJECT_DIR)),
        "bytes": len(body),
    }


@app.get("/health")
async def health() -> dict[str, str]:
    """健康检查。"""

    return {"status": "ok"}


def main() -> None:
    host = os.getenv("NOVEL_DUMP_HOST", "127.0.0.1")
    port = int(os.getenv("NOVEL_DUMP_PORT", "2314"))
    print(f"服务地址：http://{host}:{port}")
    print(f"保存目录：{BOOKS_DIR}")
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
