# feat-provider-protocol-models

## 背景与目标

> 为 Runtime 提供 OpenAI、ComfyUI 与 LTX 的完整协议数据模型、请求/响应转换与流式事件映射，让 Agent 保持 Provider 无感知。

## 用户故事

- 作为 Agent，我希望使用统一 `BackendRequest` 发起 chat、image 和 video 请求，而不理解 Provider JSON。
- 作为 Runtime 开发者，我希望每个 Adapter 明确表达其协议请求、响应、任务状态和流式事件，以便安全维护不同服务的差异。
- 作为运维人员，我希望 Provider 错误、任务 ID、进度和结果 URI 都被映射到统一响应与事件模型。

## 功能列表

### MVP（必须有）

- [ ] OpenAI Responses API 协议模型：请求、输入项、文本/图片/文件内容、响应输出、usage 与 SSE 事件。
- [ ] `OpenAIProtocol`：编码 chat/vision 请求，解码完成响应，并将 `response.output_text.delta`、完成及失败事件映射为 Runtime 事件。
- [ ] ComfyUI 本地 API 协议模型：API-format workflow、`POST /prompt`、队列响应、WebSocket JSON 事件、history 输出和图像 URI。
- [ ] `ComfyUIProtocol`：将 image 请求包装为 workflow 提交请求；解码队列/历史响应，并将执行进度和完成/错误映射为 Runtime 事件。
- [ ] LTX v2 异步协议模型：文本到视频请求、job 提交、任务状态、结果视频 URI 和 API 错误。
- [ ] `LTXProtocol`：编码 video 请求，解码 job/status 响应，并将轮询状态映射为 Runtime 进度、完成或错误事件。
- [ ] HTTP 测试：使用 `httpx.MockTransport` 覆盖三种 Adapter 的请求编码、完成响应和典型流式/状态事件。

### 不在本次范围

- [ ] Provider 鉴权、密钥环境变量和 Provider 模块注册。
- [ ] ComfyUI 二进制 WebSocket 预览图帧与文件上传。
- [ ] LTX 视频上传、image-to-video、audio-to-video、retake 与 extend。
- [ ] OpenAI 工具调用执行循环、background 模式与会话持久化。

## 协议边界

| Provider | Runtime capability | 上游协议 | 完成语义 |
| --- | --- | --- | --- |
| OpenAI | `chat`、`vision` | `POST /v1/responses` + SSE | `response.completed` |
| ComfyUI | `image` | `POST /prompt` + WebSocket + `GET /history/{prompt_id}` | `executing` node 为 `null` 或 history output |
| LTX | `video` | `POST /v2/text-to-video` + job 状态轮询 | job `completed` + `result.video_url` |

## 统一映射

- OpenAI 文本增量 → `DeltaEvent`；完成 → `DoneEvent`；错误 → `ErrorEvent`。
- ComfyUI `progress` → `ProgressEvent`；`execution_error` → `ErrorEvent`；history 输出图像 → `ImageOutput` 与 `DoneEvent`。
- LTX queued/processing → `ProgressEvent`；completed 视频 URI → `VideoOutput` 与 `DoneEvent`；failed → `ErrorEvent`。

## 技术约束

- Python 3.12+，dataclass、typing.Protocol、现有 HTTP/SSE Transport。
- Provider JSON 模型不得泄漏到 `models/` 的统一核心契约。
- Adapter 只转换协议；HTTP Backend 仍负责传输、超时和连接池。
- 协议模型以当前官方文档为准；Provider 文档变更时仅修改相应 `protocol/<provider>.py` 与测试。

## 非功能需求

- 可测试性：所有协议转换都可离线以 fixture/MockTransport 测试。
- 可扩展性：新增 Provider 不修改统一 Request、Response、Event 或 Backend 接口。
- 错误可观测性：Provider 的原始错误 code/message 保留在 `ErrorEvent` 或响应 metadata 中。
