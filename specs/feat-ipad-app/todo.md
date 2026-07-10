# TODO: feat-ipad-app

> 最后更新：2026-07-10

## ✅ 已完成

- [x] 生成参数接入 CardEditorView + submitGeneration
- [x] 参考素材 base64 编码传入生成
- [x] TaskDetailView 接入输出节点「详情」按钮
- [x] 侧边栏设置入口（服务器地址/下载管理/关于）
- [x] CanvasProject.decode 回退值修复
- [x] Apple Pencil 手写输入（PencilKit 覆盖层）
- [x] 节点模板库（18 预设 + 6 分类）
- [x] 故事板时间轴（自动分镜 + 场景卡片）
- [x] API v2.0 协议设计 + iPad 端全量实现
- [x] 语音转文本输入（SpeechRecognizer + WS /ws/transcribe）
- [x] 转录后 AI 智能纠错（POST /canvas/correct）
- [x] 文生图 + 图片编辑 API 协议（/canvas/edit-image, /canvas/upscale）
- [x] aideo-runtime HTTP+SSE 重构（/api/v1/{category}/{name} + 自动加载/释放）

## ✅ 文生图 + 图片编辑（协议）
- [x] GenerationParams 扩展 aspect_ratio, image_quality
- [x] EditImageRequest/Response + MaskRegion + UpscaleRequest 模型
- [x] APIClient.editImage() / upscaleImage()
- [x] API.md 新增 /canvas/edit-image + /canvas/upscale

## ✅ aideo-runtime HTTP+SSE 重构
- [x] provider.py — 简化为 load/unload/run + ProgressStatus
- [x] speech/faster_whisper.py — 实现 load/unload/run，yield ProgressStatus
- [x] 各 category __init__.py — PROVIDERS 注册表
- [x] server.py — HTTP POST + SSE EventSourceResponse + ProviderManager
- [x] 自动加载（首次请求）+ 空闲释放（5min idle timeout）
- [x] pyproject.toml — +sse-starlette

## 📝 变更日志 (2026-07-10)

### aideo-runtime HTTP+SSE 重构
- provider.py — 简化 BaseProvider（load/unload/run + ProgressStatus + cancel）
- server.py — HTTP+SSE 路由 + ProviderManager（自动加载/5min空闲释放/内存抢占）
- faster_whisper.py — 实现新接口（load/unload/run，yield ProgressStatus，check is_cancelled）
- 路由：POST /api/v1/{category}/{name} → SSE EventSourceResponse
- 内存抢占：X-Memory-Preempt header → 释放所有 model 后独占运行
- 客户端断开 → CancelledError → provider.cancel() 停止推理
- README.md — 设计理念 + 编码规则

### aideo-serv WS → HTTP+SSE 重构
- 删除 services/inference_manager.py（WS-based）
- 新增 services/inference_client.py（HTTP+SSE client → aideo-runtime）
- 删除 /ws/internal/inference 端点（runtime 不再连 WS）
- _submit_to_inference 改为 HTTP POST + SSE 消费
- config.py: inference_url → runtime_url
- models/events.py: 删除 InferenceMessage/InferenceRegistration/ServiceType/MessageType
- api/ws.py transcribe 改用 InferenceClient.run()
- 公共 WS 端点保留（/ws/tasks/{id}, /ws/projects/{id}, /ws/transcribe）
- 161 tests passed

### 文生图 + 图片编辑协议
- GenerationParams: +aspect_ratio, image_quality
- APIv2Models: +MaskRegion, EditImageRequest/Response, UpscaleRequest
- API.md: POST /canvas/edit-image（4 种模式）+ /canvas/upscale

### 语音转文本
- SpeechRecognizer.swift — 录音积攒PCM + 停止时发完整WAV + WS transcribe
- TranscriptPostProcessor.swift — AI 纠错 /canvas/correct（繁简转换）
- CardEditorView + AIEnhanceNodeView — 🎤 按钮三态反馈

### 其他
- 画布级共享 WS（CanvasViewModel.connectProjectWS）
- HealthSheetView（点击连接状态弹出服务详情）
- 语言偏好设置（zh/en/ja/ko/auto）透传到 AI 端点
1. 新增 SpeechRecognizer.swift（录音+WAV+WS transcribe）
2. 新增 TranscriptPostProcessor（AI 纠错 /canvas/correct）
3. 新增 HealthSheetView（服务端状态详情）
4. 画布级共享 WS 连接（CanvasViewModel.connectProjectWS）
5. API v2.0 扩展：文生图 + 图片编辑 + 语音转写 + AI 纠错
6. aideo-runtime 重构：WS → HTTP+SSE，ProviderManager 自动化生命周期
7. 语言偏好设置（zh/en/ja/ko/auto）

## 🟢 低优先级

### 新建项目保存
- 空画布 onDisappear 会保存，新项目首次切换无数据丢失
- 实际风险：无

## 📋 不做（后续迭代）

- [ ] 项目导出/导入（JSON/文件）
- [ ] iCloud 同步
- [ ] 分享扩展

