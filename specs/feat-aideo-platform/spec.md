# feat-aideo-platform

## 背景与目标

> 一句话：为 AI 视频创作者提供从 prompt 到成品视频的完整管线——iPad 上遥控，云端 GPU 生成，CLI 自动化。

Aideo 是一个 AI 视频生成工作室。用户通过 iPad（SwiftUI 原生客户端）或 CLI 提交视频生成任务，后端 API 网关接收请求并调度独立推理服务（LTX-2），通过 WebSocket 实时推送进度，最终交付可下载的视频文件。MVP 先筑地基——把管线跑通，AI 能力逐步接入。

## 用户故事

- 作为 **内容创作者**，我希望在 iPad 上输入一段 prompt，AI 帮我生成视频，以便快速产出社交媒体内容
- 作为 **专业制作人员**，我希望通过 CLI 批量提交任务、监控进度、下载结果，以便集成到自动化后期流程
- 作为 **普通消费者**，我希望有一个简洁的 iPad 界面来管理我的视频生成任务，不需要理解底层技术

## 功能列表

### MVP（必须有）

- [ ] **任务生命周期 API** — REST API：创建视频生成任务（POST /tasks）、查询状态（GET /tasks/{id}）、取消任务（DELETE /tasks/{id}）、列出历史任务（GET /tasks）
- [ ] **推理服务调度** — aideo-serv 将任务转发到独立 LTX-2 推理服务，管理请求队列和 GPU 资源
- [ ] **WebSocket 实时进度推送** — 任务状态变更（queued → running → generating → completed/failed）、生成进度百分比实时通知客户端
- [ ] **生成进度中间结果** — 生成过程中产出关键帧/缩略图，通过 WebSocket 推送到客户端预览
- [ ] **结果管理与下载** — 视频本地文件存储（预留迁移到 S3 的目录结构），HTTP 下载端点（GET /results/{id}/download），流式播放支持
- [ ] **CLI 完整功能** — `aideo-cli` 命令行工具：提交 prompt（`aideo submit`）、查看队列（`aideo list`）、查看任务详情（`aideo status <id>`）、下载结果（`aideo download <id>`）、支持 JSON/表格格式化输出
- [ ] **iPad 最小可用原型** — SwiftUI 基础界面：输入 prompt 提交任务、任务列表（状态+进度）、点击查看视频预览/下载

### 后续迭代（可以有）

- [ ] 文生视频（T2V）— 接入 LTX-2 text-to-video 能力
- [ ] 图生视频（I2V）— iPad 端选择照片/拍照上传，LTX-2 处理
- [ ] 视频风格迁移 / 编辑增强
- [ ] 全流程视频工作室（剧本→分镜→生成→剪辑）
- [ ] 任务队列优先级管理 — 支持优先级排序、并发限制、GPU 资源分配策略
- [ ] 健康监控 & 可观测性 — 推理服务健康检查、Prometheus metrics、结构化日志
- [ ] JWT 用户认证 — 用户注册/登录、token 管理、权限控制
- [ ] 对象存储集成 — 从本地存储迁移到 S3 兼容对象存储，CDN 分发
- [ ] Android / Web 客户端

## 技术方案概述

- **平台/运行环境**：
  - API 服务：Linux（生产）/ Windows（开发），Python 3.12+
  - 推理服务：Linux + NVIDIA CUDA GPU
  - iPad 客户端：iPadOS（SwiftUI 原生）
  - CLI：跨平台（macOS / Linux / Windows）
- **核心技术栈**：
  - API 网关：**FastAPI**（异步原生 + WebSocket + 自动 OpenAPI 文档）
  - 通信协议：**REST**（任务生命周期） + **WebSocket**（实时进度推送）
  - 推理服务：独立部署，LTX-2（Lightricks，开源）
  - CLI：Python（aideo-cli 包），调用 aideo-serv API
  - iPad：SwiftUI + Swift Concurrency（async/await）
- **关键约束**：
  - 视频参数由 LTX-2 模型能力决定，API 使用开放式参数设计（预留 resolution、duration、fps、seed 等字段，不做硬性上限）
  - 存储先本地后迁移：目录结构提前设计（按 task_id 分桶），为未来 S3/MinIO 迁移留接口
  - 认证预留 JWT Bearer Token 中间件，MVP 不强制验证
  - 推理服务与 API 网关解耦：aideo-serv 不直接加载模型，通过内部协议转发请求

## 架构概览

```
┌─────────────────────────────────────────────────────────┐
│  iPad (SwiftUI)          CLI (Python)                   │
│  · prompt 输入            · aideo submit               │
│  · 任务列表               · aideo list/status/download  │
│  · 视频预览               · JSON/表格输出               │
└──────────┬──────────────────┬───────────────────────────┘
           │ REST + WebSocket │
           ▼                  ▼
┌─────────────────────────────────────────────────────────┐
│  aideo-serv (FastAPI)                                   │
│  · /tasks          — 任务生命周期                        │
│  · /ws/tasks/{id}  — WebSocket 进度推送                 │
│  · /results/{id}   — 视频下载                           │
│  · 任务编排 + 推理调度                                   │
│  · JWT 中间件（预留）                                    │
└──────────────────────┬──────────────────────────────────┘
                       │ 内部协议 (HTTP/gRPC)
                       ▼
┌─────────────────────────────────────────────────────────┐
│  LTX-2 推理服务 (独立进程，CUDA GPU)                     │
│  · 模型加载 & 推理                                       │
│  · 进度回调 → aideo-serv                                 │
│  · 视频输出 → 本地存储                                   │
└─────────────────────────────────────────────────────────┘
```

## 非功能需求

- **性能**：API 响应 < 200ms（非生成类请求）；WebSocket 进度推送延迟 < 1s
- **安全**：JWT 中间件预留但 MVP 不强制；推理服务仅内网可达；视频文件访问通过签名 URL
- **兼容性**：iPad 最低支持 iPadOS 18+；Python 3.12+；CUDA 12.x+

## 待定问题

- LTX-2 推理服务的部署方式（裸进程 vs Docker vs Triton Server），待接入时根据模型实际依赖确定
- iPad 客户端的 UI 设计细节（布局、交互、播放器选型），待独立进行 UI/UX 设计时细化
- CLI 与 aideo-serv 之间是否需要 mTLS 或其他安全层，待后续安全评审确定
