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

## 🔴 进行中

### 文生图（MVP）
- [ ] GenerationParams 扩展 aspect_ratio, image_quality
- [ ] POST /generate 支持 output_content_type: "image"
- [ ] MediaOutputNode(contentType: .image) 生成流程验证
- [ ] API.md 更新

### 图片编辑
- [ ] EditImageRequest/Response + MaskRegion 模型
- [ ] POST /canvas/edit-image（composite | replace_character | inpainting | style_transfer）
- [ ] APIClient.editImage() / upscaleImage()
- [ ] POST /canvas/upscale
- [ ] 选区 UI（手势画矩形选区）
- [ ] API.md 更新

## 🟢 低优先级

### 新建项目保存
- 空画布 onDisappear 会保存，新项目首次切换无数据丢失
- 实际风险：无

## 📋 不做（后续迭代）

- [ ] 项目导出/导入（JSON/文件）
- [ ] iCloud 同步
- [ ] 分享扩展

