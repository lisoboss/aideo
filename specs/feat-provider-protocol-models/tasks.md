# Tasks: feat-provider-protocol-models

> 生成时间：2026-07-15
> 基于：spec.md + plan.md

## 进度

- [x] 8 / 8 任务完成

---

### Task 1: 创建 `tests/test_openai_protocol.py`

- **文件**：`packages/aideo-runtime/tests/test_openai_protocol.py`
- **类型**：测试
- **依赖**：无
- **描述**：覆盖 chat/vision 请求编码、非流式输出与 usage 解码、OpenAI SSE 文本 delta/完成/失败映射，以及不支持 capability 的拒绝。
- **验收**：当前空 OpenAI Adapter 使测试为红。

### Task 2: 实现 `protocol/openai.py`

- **文件**：`packages/aideo-runtime/src/aideo_runtime/protocol/openai.py`
- **类型**：实现
- **依赖**：Task 1
- **描述**：实现 Responses API 协议 dataclass、`POST /v1/responses` 编码、响应与 SSE 解码；将请求参数映射到上游兼容字段。
- **验收**：Task 1 通过。

### Task 3: 创建 `tests/test_comfyui_protocol.py`

- **文件**：`packages/aideo-runtime/tests/test_comfyui_protocol.py`
- **类型**：测试
- **依赖**：无
- **描述**：覆盖 API-format workflow 的 `/prompt` 编码、queue/history 输出、WebSocket `progress`/`executed`/`execution_error` 映射及无 workflow 请求拒绝。
- **验收**：当前空 ComfyUI Adapter 使测试为红。

### Task 4: 实现 `protocol/comfyui.py`

- **文件**：`packages/aideo-runtime/src/aideo_runtime/protocol/comfyui.py`
- **类型**：实现
- **依赖**：Task 3
- **描述**：实现 Comfy workflow、queue/history、WebSocket 协议模型与 Adapter 转换；保留 HTTP SSE 误用的明确错误。
- **验收**：Task 3 通过。

### Task 5: 创建 `tests/test_ltx_protocol.py`

- **文件**：`packages/aideo-runtime/tests/test_ltx_protocol.py`
- **类型**：测试
- **依赖**：无
- **描述**：覆盖 text-to-video 请求、job 状态响应、queued/processing/completed/failed 映射，以及非 video 请求拒绝。
- **验收**：当前空 LTX Adapter 使测试为红。

### Task 6: 实现 `protocol/ltx.py`

- **文件**：`packages/aideo-runtime/src/aideo_runtime/protocol/ltx.py`
- **类型**：实现
- **依赖**：Task 5
- **描述**：实现 LTX v2 请求、job/result/error 模型与 Adapter 编码/解码；新增 job 状态转换方法。
- **验收**：Task 5 通过。

### Task 7: 更新 `protocol/base.py`

- **文件**：`packages/aideo-runtime/src/aideo_runtime/protocol/base.py`
- **类型**：实现
- **依赖**：Task 2、Task 4、Task 6
- **描述**：补充 ProtocolAdapter 文档，明确 HTTP SSE、WebSocket 和轮询状态适配入口的责任边界。
- **验收**：所有 Adapter 仍符合核心 `encode`/`decode`/`decode_stream` 合约。

### Task 8: 更新文档与验证

- **文件**：`packages/aideo-runtime/README.md`、`docs/changes/changed-2026-07-15-unified-inference-runtime.md`
- **类型**：文档
- **依赖**：Task 2、Task 4、Task 6、Task 7
- **描述**：记录三套 Provider 协议边界、未覆盖范围及验证结果；运行 Runtime 测试与 pre-commit。
- **验收**：文档与实现一致，完整验证通过。
