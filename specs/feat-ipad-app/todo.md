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

