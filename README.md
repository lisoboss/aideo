# Aideo — AI Video Generator Studio

## Linux 启动

先启动本地推理 Runtime，再启动 API 服务：

```bash
./interface.sh
./http-server.sh
```

两个脚本会在启动前检查 `uv`、创建本地数据目录。`http-server.sh` 还会检查
`$AIDEO_INFERENCE_URL/health`；Runtime 未就绪时会明确退出，而不会启动一个无法推理的
服务端。

使用 LTX2 时，`interface.sh` 会验证 `LTX2_DISTILLED_CHECKPOINT`、
`LTX2_GEMMA_ROOT` 和 `LTX2_SPATIAL_UPSAMPLER` 都存在于
`AIDEO_RUNTIME_MODELS_DIR` 下。仅运行 demo 或 Whisper 时，可以通过
`AIDEO_RUNTIME_PROVIDERS=demo` 或 `AIDEO_RUNTIME_PROVIDERS=faster_whisper2`
跳过 LTX2 资源预检。

本地排障可设置 `AIDEO_RUNTIME_DEBUG=true`。该模式会返回 Python traceback，只应在受信任的开发网络启用。
