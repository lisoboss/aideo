# demo/sse.py
# uv add fastapi uvicorn sse-starlette


import asyncio

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.event_stream import EventSourceResponse

app = FastAPI()

# 允许跨域（前端测试必备）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 异步生成器：模拟流式生成数据
async def event_generator():
    text = "这是使用 FastAPI 和 SSE 实现的流式输出内容，正在逐字发送..."

    for char in text:
        # 每次向客户端推送一个字
        yield {
            "event": "message",  # 事件类型，默认为 message
            "data": char,  # 传送的数据内容
        }
        # 模拟生成延迟（打字机效果）
        await asyncio.sleep(0.1)


@app.get("/stream")
async def stream_endpoint(request: Request):
    # 使用 EventSourceResponse 将生成器包装为 SSE 流
    return EventSourceResponse(event_generator())


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
