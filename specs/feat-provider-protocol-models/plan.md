# Technical Plan: feat-provider-protocol-models

## 目录结构

```text
packages/aideo-runtime/
├── src/aideo_runtime/protocol/
│   ├── base.py                         # [修改] 明确 Adapter 的同步/流式协议边界
│   ├── openai.py                       # [修改] Responses API 模型与 Adapter
│   ├── comfyui.py                      # [修改] 本地 Workflow API 模型与 Adapter
│   └── ltx.py                          # [修改] LTX v2 async job 模型与 Adapter
└── tests/
    ├── test_openai_protocol.py         # [新增] OpenAI 编码、响应与 SSE 映射
    ├── test_comfyui_protocol.py        # [新增] Workflow、queue/history 与进度映射
    └── test_ltx_protocol.py            # [新增] video job 编码、状态与结果映射

specs/feat-provider-protocol-models/
├── spec.md                             # ✅ 已确认
├── plan.md                             # ✅ 当前文件
└── tasks.md                            # [下一阶段]
```

## 核心数据模型

### OpenAI Responses

```python
@dataclass(frozen=True, slots=True)
class OpenAIResponseRequest:
    model: str
    input: list[OpenAIInputMessage]
    stream: bool
    max_output_tokens: int | None
    temperature: float | None

@dataclass(frozen=True, slots=True)
class OpenAIStreamEvent:
    type: str
    delta: str | None = None
    response: OpenAIResponse | None = None
    error: OpenAIError | None = None
```

`OpenAIProtocol` 仅接受 `chat` 与 `vision`；将统一 messages 转为 Responses `input` 项，并映射 `response.output_text.delta`、`response.completed`、`response.failed`。

### ComfyUI Local API

```python
@dataclass(frozen=True, slots=True)
class ComfyWorkflowRequest:
    prompt: dict[str, ComfyNode]
    client_id: str | None = None

@dataclass(frozen=True, slots=True)
class ComfyQueueResponse:
    prompt_id: str
    number: int

@dataclass(frozen=True, slots=True)
class ComfyWebSocketEvent:
    type: Literal["status", "execution_start", "executing", "progress", "executed", "execution_error"]
    data: dict[str, Any]
```

`ComfyUIProtocol` 要求统一 image input 提供 API-format `workflow`；编码为 `/prompt` 请求。Adapter 解码 queue/history JSON；WebSocket 消息通过一个显式 `decode_ws_event()` 方法映射事件。HTTP SSE 的 `decode_stream()` 保持为兼容入口，但 ComfyUI 实时路径由 WebSocket Transport 后续接入。

### LTX Async v2

```python
@dataclass(frozen=True, slots=True)
class LTXTextToVideoRequest:
    model: str
    prompt: str
    duration: float | None
    resolution: str | None

@dataclass(frozen=True, slots=True)
class LTXJob:
    id: str
    status: Literal["queued", "processing", "completed", "failed"]
    progress: float | None
    result: LTXResult | None
    error: LTXError | None
```

`LTXProtocol` 仅接受 `video`；编码为 `/v2/text-to-video`。由于上游使用状态轮询，新增 `decode_job()`：queued/processing 映射 `ProgressEvent`，completed 映射 `DoneEvent`（metadata 中携带 `VideoOutput` 表示），failed 映射 `ErrorEvent`。

## 接口定义

```python
class ComfyUIProtocol:
    def encode(self, request: BackendRequest, endpoint: str) -> HttpRequest: ...
    def decode(self, response: HttpResponse) -> BackendResponse: ...
    def decode_ws_event(self, payload: dict[str, Any]) -> BackendEvent | None: ...

class LTXProtocol:
    def encode(self, request: BackendRequest, endpoint: str) -> HttpRequest: ...
    def decode(self, response: HttpResponse) -> BackendResponse: ...
    def decode_job(self, response: HttpResponse) -> BackendEvent: ...
```

`decode_stream()` 仍由所有 Adapter 满足 `ProtocolAdapter`；OpenAI 真实实现 SSE，ComfyUI/LTX 对不适用的 SSE 输入产生清晰错误，防止误用。

## 实施阶段

### Phase 1 — OpenAI Responses

- 目标：完成当前最成熟的 HTTP + SSE Adapter 参考实现。
- 产出：`openai.py`、`test_openai_protocol.py`。

### Phase 2 — ComfyUI Workflow

- 目标：完成 workflow 提交、queue/history 解码和 WebSocket JSON 进度转换。
- 产出：`comfyui.py`、`test_comfyui_protocol.py`。

### Phase 3 — LTX Async Jobs

- 目标：完成 video job 提交、状态轮询解码与错误/结果映射。
- 产出：`ltx.py`、`test_ltx_protocol.py`、变更日志。
