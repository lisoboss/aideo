# feat-local-ltx-asr-providers

## 背景与目标

> 将 main 分支已验证的本地 LTX-2 视频生成和 Faster-Whisper2 语音转写能力迁移到新 Runtime 的动态 Provider 架构。

## 用户故事

- 作为 Agent，我希望以 `video` capability 调用本地 LTX-2 模型并得到统一的视频 URI 和进度事件。
- 作为 Agent，我希望以 `asr` capability 调用本地 Faster-Whisper2 模型并得到转写文本、语言和分段元数据。
- 作为运维人员，我希望通过 `AIDEO_RUNTIME_PROVIDERS=ltx2,faster_whisper2` 选择本地模型，并使用全局模型、输入和输出根目录管理所有 Provider 文件。
- 作为 GPU 主机管理员，我希望模型首次调用时才载入，并可通过 Backend 生命周期关闭释放内存。

## 功能列表

### MVP（必须有）

- [ ] 添加 `backend/providers/ltx2.py`：实现 `RuntimeProvider` 契约和 LTX-2.3 distilled text-to-video Backend。
- [ ] 添加 `backend/providers/faster_whisper2.py`：实现 `RuntimeProvider` 契约和 Faster-Whisper2 ASR Backend。
- [ ] LTX 使用旧版 DistilledPipeline 参数：checkpoint、Gemma、spatial upsampler、LoRA、device、offload、quantization，并将结果写入全局输出目录。
- [ ] Faster-Whisper2 支持模型名/相对模型路径、device、compute type、language、beam size、word timestamps、VAD filter。
- [ ] 提供全局路径配置：模型根目录、输入根目录、输出根目录；Provider 不得定义独立根目录。
- [ ] 所有请求文件路径必须相对输入根目录解析；所有生成文件必须写入输出根目录；路径越界必须拒绝。
- [ ] 两种 Backend 均延迟导入 GPU 库与模型实现、支持 `health()`、`models()`、`invoke()`、`stream()`、`aclose()`。
- [ ] LTX stream 提供准备、阶段一、阶段二、编码和完成进度；完成事件包含输出视频 URI。
- [ ] ASR stream 提供加载/转写/完成进度；完成事件包含文本、语言、时长和分段元数据。
- [ ] 通过 mock 的 pipeline/WhisperModel 单元测试覆盖 Provider 加载、请求映射、结果映射、GPU 不可用回退和缺失输入。
- [ ] 恢复 main 分支的 CUDA 13、LTX 与 Faster-Whisper2 pyproject 依赖及 uv sources，保留现有 HTTP Runtime 依赖。

### 不在本次范围

- [ ] LTX image-to-video、audio-to-video、retake、extend 或分布式推理。
- [ ] ASR 实时麦克风、说话人分离和翻译。
- [ ] 自动下载 LTX 权重、密钥管理和远程模型 Provider。

## Provider 配置

```env
AIDEO_RUNTIME_PROVIDERS=ltx2,faster_whisper2

# ComfyUI-style shared roots
AIDEO_RUNTIME_MODELS_DIR=./models
AIDEO_RUNTIME_INPUT_DIR=./data/input
AIDEO_RUNTIME_OUTPUT_DIR=./data/output

# Paths below are relative to AIDEO_RUNTIME_MODELS_DIR
LTX2_DISTILLED_CHECKPOINT=ltx2/ltx-2.3-distilled.safetensors
LTX2_GEMMA_ROOT=gemma-3
LTX2_SPATIAL_UPSAMPLER=ltx2/ltx-upscaler.safetensors
LTX2_DEVICE=cuda
LTX2_OFFLOAD_MODE=none
LTX2_QUANTIZATION=fp8-cast

# A model name downloads under AIDEO_RUNTIME_MODELS_DIR; a relative path is resolved below it.
WHISPER_MODEL=large-v3
WHISPER_DEVICE=cuda
WHISPER_COMPUTE_TYPE=float16
```

## 统一请求与结果

| Provider | Capability | `input` | `parameters` | 统一完成结果 |
| --- | --- | --- | --- |
| ltx2 | `video` | `prompt` | seed、height、width、num_frames、frame_rate、enhance_prompt | `VideoOutput(runtime://output/{filename})` |
| faster_whisper2 | `asr` | 相对 `audio_path`、language | beam_size、word_timestamps、vad_filter | `TextOutput(text)` + segments metadata |

## 技术约束

- Python 3.12+；GPU 重型模块必须在 Backend `load()` 内导入。
- 运行时核心不能在 import 时导入 torch、ltx-pipelines 或 faster-whisper。
- 配置中的 Provider 名必须是合法 Python 模块名：`ltx2`、`faster_whisper2`。
- 路径解析必须使用 `Path.resolve()` 并验证结果仍位于对应根目录内，拒绝 `..` 越界路径。
- 使用用户提供的 pyproject 依赖与 uv CUDA index/source 定义；新增依赖必须经 `uv add` 管理。
