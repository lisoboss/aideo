# 变更日志

## 2026-07-11 — 图片编辑/超分 全链路（serv 端点 + runtime provider 基础）

[changed-2026-07-11-backend-edit-image-upscale.md](changes/changed-2026-07-11-backend-edit-image-upscale.md)

补齐 `aideo-serv` 的 `POST /canvas/edit-image`、`POST /canvas/upscale`，并在 `aideo-runtime` 落地 `image` provider 品类基础，闭合 iPad 早已声明、后端缺失的图片编辑/超分协议。具体模型实现待补。

**涉及**：`packages/aideo-serv/` (models/edit.py, api/canvas_image.py 新增；router.py, tasks.py, inference_client.py 修改；test_canvas_image.py 新增)、`packages/aideo-runtime/` (image/ 品类新增；server.py, README.md 修改；test_image_provider.py 新增)、`.claude/rules/architecture-runtime.md`

**关键指标**：
- 2 REST 端点（edit-image 4 模式 + upscale 2x/4x）+ runtime `image` 品类
- serv +12 tests (173 passed)、runtime +11 tests (image 模块 passed)
- runtime `image` 真实模型待补（stub 占位，全链路可跑通）

## 2026-07-10 — Aideo v2.0 Full-Stack

[changed-2026-07-10-aideo-v2.md](changes/changed-2026-07-10-aideo-v2.md)

API v2.0 协议设计 + iPad 端全量实现 + aideo-runtime HTTP+SSE 重构 + aideo-serv WS→HTTP+SSE 重构 + iPad 契约对齐修复。

**涉及**：`docs/API.md`, `packages/aideo-serv/` (16 files), `packages/aideo-runtime/` (10 files), `packages/aideo-ipad/` (22 files), `specs/feat-ipad-app/`

**关键指标**：
- 17 REST + 2 WS 端点
- iPad 端 5 新建 / 2 删除 / 18 修改
- aideo-serv 161 tests passed
- aideo-runtime 2.0 HTTP+SSE
- iPad 契约修复：日期 ISO8601 解码 + WS payload 字段容忍（xcodebuild 通过）
