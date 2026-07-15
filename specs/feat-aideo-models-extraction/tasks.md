# Tasks: feat-aideo-models-extraction

> 生成时间：2026-07-16
> 基于：spec.md + plan.md（执行时补充 workspace bootstrap 前置任务）

## 进度

- [x] 17 / 17 任务完成

---

### Task 1: 创建本地模型接口测试 ✅

- **文件**：`packages/aideo-models/tests/test_local_model_contracts.py`
- **类型**：测试
- **依赖**：无
- **描述**：定义纯 Python 视频生成、转写请求/结果的数据契约与公共导入预期；测试不得导入 Runtime。
- **验收**：实现前红灯已确认。

### Task 2: 创建 `aideo-models` 最小包配置 ✅

- **文件**：`packages/aideo-models/pyproject.toml`、`packages/aideo-models/README.md`、`packages/aideo-models/src/aideo_models/__init__.py`
- **类型**：实现/配置
- **依赖**：Task 1
- **描述**：创建 Python 3.12+、src layout、uv workspace 兼容的最小 package，使测试可被收集。`README.md` 和空的 `__init__.py` 是 build bootstrap，本任务是唯一的多文件结构例外。
- **验收**：Task 1 从 workspace 配置错误变为缺少数据模型的红灯。

### Task 3: 实现本地模型数据契约 ✅

- **文件**：`packages/aideo-models/src/aideo_models/models.py`
- **类型**：实现
- **依赖**：Task 1、Task 2
- **描述**：实现 `VideoGenerationRequest`、`TranscriptionRequest` 与 `TranscriptionResult` dataclass。
- **验收**：Task 1 通过。

### Task 4: 创建 LTX2 模型库测试 ✅

- **文件**：`packages/aideo-models/tests/test_ltx2.py`
- **类型**：测试
- **依赖**：Task 3
- **描述**：以 fake pipeline/encoder 覆盖惰性加载、已验证 output Path、请求参数与不导入 GPU 依赖的行为。
- **验收**：实现前测试为红。

### Task 5: 实现 LTX2 本地模型 ✅

- **文件**：`packages/aideo-models/src/aideo_models/ltx2.py`
- **类型**：实现
- **依赖**：Task 3、Task 4
- **描述**：迁移 LTX 模型加载和生成实现；构造函数仅接收 models_dir，生成请求只接收已验证 output_path。
- **验收**：Task 4 通过。

### Task 6: 创建 Faster-Whisper2 模型库测试 ✅

- **文件**：`packages/aideo-models/tests/test_whisper.py`
- **类型**：测试
- **依赖**：Task 3
- **描述**：以 fake WhisperModel 覆盖惰性加载、CUDA 不可用时 cpu/int8 回退、已验证 audio Path 和转写元数据。
- **验收**：实现前测试为红。

### Task 7: 实现 Faster-Whisper2 本地模型 ✅

- **文件**：`packages/aideo-models/src/aideo_models/whisper.py`
- **类型**：实现
- **依赖**：Task 3、Task 6
- **描述**：迁移 Whisper 模型加载和转写实现；构造函数仅接收 models_dir，转写请求只接收已验证 audio_path。
- **验收**：Task 6 通过。

### Task 8: 创建 `aideo-models` 公共 API 测试 ✅

- **文件**：`packages/aideo-models/tests/test_public_api.py`
- **类型**：测试
- **依赖**：Task 5、Task 7
- **描述**：确认 macOS 无 GPU 包时公共模块可导入，并只导出稳定本地模型 API。
- **验收**：实现前测试为红。

### Task 9: 实现 `aideo-models` 公共 API ✅

- **文件**：`packages/aideo-models/src/aideo_models/__init__.py`
- **类型**：实现
- **依赖**：Task 5、Task 7、Task 8
- **描述**：导出本地请求/结果和 LTX2/Whisper 模型类；不触发 GPU 模块导入。
- **验收**：Task 8 通过。

### Task 10: 创建 Runtime LTX2 适配回归测试 ✅

- **文件**：`packages/aideo-runtime/tests/test_ltx2_provider.py`
- **类型**：测试
- **依赖**：Task 5
- **描述**：mock `aideo_models.LTX2Model`，覆盖 Runtime 保留路径解析、进度事件和 output URI。
- **验收**：薄适配实现前测试为红。

### Task 11: 重构 Runtime LTX2 Provider ✅

- **文件**：`packages/aideo-runtime/src/aideo_runtime/backend/providers/ltx2.py`
- **类型**：实现
- **依赖**：Task 5、Task 10
- **描述**：仅处理 BackendRequest、PathSettings、Runtime 事件/响应，与 `aideo_models.LTX2Model` 协作。
- **验收**：Task 10 通过且不再直接导入 LTX/torch。

### Task 12: 创建 Runtime Whisper 适配回归测试 ✅

- **文件**：`packages/aideo-runtime/tests/test_faster_whisper2_provider.py`
- **类型**：测试
- **依赖**：Task 7
- **描述**：mock `aideo_models.FasterWhisper2Model`，覆盖 Runtime 输入根目录校验及统一转写输出。
- **验收**：薄适配实现前测试为红。

### Task 13: 重构 Runtime Whisper Provider ✅

- **文件**：`packages/aideo-runtime/src/aideo_runtime/backend/providers/faster_whisper2.py`
- **类型**：实现
- **依赖**：Task 7、Task 12
- **描述**：仅处理 BackendRequest、PathSettings、Runtime 事件/响应，与 `aideo_models.FasterWhisper2Model` 协作。
- **验收**：Task 12 通过且不再直接导入 Whisper/torch。

### Task 14: 添加 aideo-models GPU 依赖 ✅

- **文件**：`packages/aideo-models/pyproject.toml`
- **类型**：配置
- **依赖**：Task 5、Task 7、Task 9
- **描述**：用 `uv add` 声明 Linux-only CUDA、LTX、Whisper、Git/PyTorch sources。
- **验收**：`uv sync --all-packages` 可解析 macOS 与 Linux 依赖分支。

### Task 15: 更新 Runtime 包配置与 SSE 版本 ✅

- **文件**：`packages/aideo-runtime/pyproject.toml`
- **类型**：配置
- **依赖**：Task 11、Task 13、Task 14
- **描述**：移除模型/GPU 依赖，添加 workspace `aideo-models`，并用 `uv add` 升级 `sse-starlette`。
- **验收**：Runtime 不再直接声明 torch/LTX/Whisper/NVIDIA 包，SSE 回归测试通过。

### Task 16: 更新本地模型库 README ✅

- **文件**：`packages/aideo-models/README.md`
- **类型**：文档
- **依赖**：Task 14、Task 15
- **描述**：说明库职责、Linux CUDA 安装边界、与 Runtime 的 Path 所有权关系和直接 API。
- **验收**：不将路径配置归属为 aideo-models。

### Task 17: 更新 Runtime 文档、变更记录、锁文件与验证 ✅

- **文件**：`docs/changes/changed-2026-07-16-aideo-models-extraction.md`
- **类型**：集成/文档
- **依赖**：Task 15、Task 16
- **描述**：更新 Runtime README/.env、变更索引与 lockfile；运行 sync、Runtime/Models 测试、ruff、mypy 和 pre-commit。
- **验收**：所有质量检查通过；真实 GPU 推理明确标记为 Linux CUDA 条件验证。
