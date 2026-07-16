# 变更日志

本文件是所有变更的简要索引。每次有意义的代码变更都应在下方新增一条一行式记录；变更详情、涉及文件和验证结果写入 `docs/changes/` 中同名的 `changed-YYYY-MM-DD-title.md` 文件。

- 格式：`- [changed-YYYY-MM-DD-title.md](changes/changed-YYYY-MM-DD-title.md) — 简述`
- 同一天的相关变更合并到同一个详情文件与索引记录中。

## CHANGES

- [changed-2026-07-16-aideo-models-extraction.md](changes/changed-2026-07-16-aideo-models-extraction.md) — 提取跨平台本地模型库、修复 Faster-Whisper2 导入与本地路径、服务端推理日志及 CUDA 动态库启动，恢复本地模型显存抢占并补齐 ASR HTTP 测试。
- [changed-2026-07-15-unified-inference-runtime.md](changes/changed-2026-07-15-unified-inference-runtime.md) — 新增统一、Provider 无关的 AI 推理运行时与 HTTP/SSE 测试。
- [changed-2026-07-11-backend-edit-image-upscale.md](changes/changed-2026-07-11-backend-edit-image-upscale.md) — 补齐图片编辑和超分的服务端端点与运行时 provider 基础。
- [changed-2026-07-10-aideo-v2.md](changes/changed-2026-07-10-aideo-v2.md) — 完成 Aideo v2.0 API、iPad、运行时与服务端协议重构。
