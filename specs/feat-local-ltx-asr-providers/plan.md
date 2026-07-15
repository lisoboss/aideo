# Technical Plan: feat-local-ltx-asr-providers

## 目录结构

```text
packages/aideo-runtime/
├── pyproject.toml                              # [修改] CUDA 13、LTX 与 Faster-Whisper2 依赖/sources
├── .env.example                                # [修改] 全局路径与本地 Provider 示例
├── src/aideo_runtime/
│   ├── config.py                               # [修改] 全局 PathSettings
│   ├── paths.py                                # [新增] 安全相对路径解析与 runtime URI
│   ├── backend/providers/
│   │   ├── ltx2.py                             # [新增] 延迟加载的 LTX-2.3 Backend
│   │   └── faster_whisper2.py                  # [新增] 延迟加载的 Faster-Whisper2 Backend
│   └── models/
│       └── response.py                         # [修改] 输出 URI 元数据约定
└── tests/
    ├── test_paths.py                           # [新增] 根目录、越界和 URI 测试
    ├── test_ltx2_provider.py                   # [新增] mock Pipeline 生命周期和请求/进度测试
    └── test_faster_whisper2_provider.py        # [新增] mock Whisper 生命周期、CPU 回退和转写测试

specs/feat-local-ltx-asr-providers/
├── spec.md                                     # ✅ 已确认
├── plan.md                                     # ✅ 当前文件
└── tasks.md                                    # [下一阶段]
```

## 全局路径模型

```python
@dataclass(frozen=True, slots=True)
class PathSettings:
    models_dir: Path
    input_dir: Path
    output_dir: Path

    def model_path(self, relative: str) -> Path: ...
    def input_path(self, relative: str) -> Path: ...
    def output_path(self, relative: str) -> Path: ...
    def output_uri(self, path: Path) -> str: ...
```

所有根目录在 Runtime 启动时创建或验证。`resolve_under(root, relative)` 必须拒绝绝对路径和解析后离开 root 的相对路径。输出结果统一编码为 `runtime://output/{relative-path}`；后续 aideo-serv 可将该 scheme 映射到共享卷或资产服务。

## Provider 模型与接口

### LTX2 Provider

```python
class LTX2Backend:
    async def invoke(self, request: BackendRequest) -> BackendResponse: ...
    async def stream(self, request: BackendRequest) -> AsyncIterator[BackendEvent]: ...
    async def health(self) -> HealthStatus: ...
    async def models(self) -> list[ModelInfo]: ...
    async def aclose(self) -> None: ...
```

- `load()` 在 worker executor 中导入 torch/LTX 并构造 `DistilledPipeline`。
- LTX 相对 checkpoint、Gemma、upscaler 和 LoRA 路径均经 `PathSettings.model_path()` 解析。
- `stream()` 接收 `video` 请求，使用旧实现的 stage-1 / stage-2 / encode 时间估算发射 `ProgressEvent`，最后发射 `DoneEvent`，metadata 包含 `VideoOutput(runtime://output/...)`。
- `invoke()` 消耗 stream 并返回 `BackendResponse(outputs=[VideoOutput(...)])`。

### Faster-Whisper2 Provider

- `load()` 在 executor 中延迟导入 `faster_whisper.WhisperModel` 和 torch。
- `WHISPER_MODEL` 为路径时通过 `PathSettings.model_path()` 解析；为模型名称时设定 `download_root=PathSettings.models_dir / "whisper"`。
- CUDA 不可用时降级为 `cpu/int8`；显式 CPU 同样使用 `int8`。
- `stream()` 要求 `input.audio_path` 是输入根目录下的相对路径。输出 `ProgressEvent`，终态 `DoneEvent` metadata 含文本、语言、时长、分段和 `TextOutput`。
- `invoke()` 返回带 `TextOutput` 的 `BackendResponse`，元数据包含语言、概率、时长和分段。

## 配置与依赖

`RuntimeSettings` 拆为监听/Provider 配置和 `PathSettings`。启动 `create_app()` 创建目录，但不会导入 GPU 依赖或加载模型。

保留现有 FastAPI/httpx 依赖并添加用户给出的：`websockets`、`sse-starlette`、`faster-whisper2`、`ltx-core[xformers]`、`ltx-pipelines`、torch 生态及 NVIDIA CUDA 13 依赖。使用用户提供的 PyTorch CUDA index 和 git sources。

## 实施阶段

### Phase 1 — 基础路径与配置

- 目标：全局根目录、路径安全和 Provider 可见配置。
- 产出：`paths.py`、`config.py`、`test_paths.py`、`.env.example`。

### Phase 2 — Faster-Whisper2 ASR

- 目标：迁移旧转写逻辑到新 Backend/Provider，确保 CPU 回退和统一结果。
- 产出：`faster_whisper2.py`、`test_faster_whisper2_provider.py`。

### Phase 3 — LTX-2.3 Video

- 目标：迁移旧 DistilledPipeline 和阶段进度到新 Backend/Provider。
- 产出：`ltx2.py`、`test_ltx2_provider.py`。

### Phase 4 — 依赖、文档与验证

- 目标：同步 uv 配置、示例配置、变更日志、测试和静态检查。
- 产出：`pyproject.toml`、`uv.lock`、README、变更日志。
