# feat-startup-script-hardening

## 背景与目标

优化 `interface.sh` 与 `http-server.sh` 两个独立启动脚本，以 Linux GPU 部署为主要
场景，让部署者能够更早发现配置错误，并以一致、可读的方式启动 Runtime 和服务端。

## 用户故事

- 作为本地部署者，我希望启动 Runtime 前立即看到缺失的 `uv`、路径或 Provider
  配置，而不是在首次推理时才失败。
- 作为服务端部署者，我希望启动 aideo-serv 前确认 Runtime 可访问，避免服务上线后
  才发现推理地址错误。
- 作为开发者，我希望两个脚本的日志、目录创建和 debug 配置行为一致。

## 功能列表

### MVP（必须有）

- [ ] 保持 `interface.sh` 与 `http-server.sh` 独立启动，不新增编排脚本。
- [ ] 两个脚本均检查 `uv` 是否存在，并在缺失时输出可操作错误。
- [ ] 两个脚本创建其拥有的本地数据目录；不创建或修改模型 checkpoint 内容。
- [ ] `interface.sh` 输出并转发 `AIDEO_RUNTIME_DEBUG`，并对已启用的本地 Provider
  给出必要配置的预检提示。
- [ ] `http-server.sh` 在启动前检查 `AIDEO_INFERENCE_URL/health`；Runtime 不可用时
  以明确错误退出，可用时显示已连接状态。
- [ ] 两个脚本使用一致的日志格式，敏感 AI API Key 始终脱敏。
- [ ] 覆盖脚本静态语法、缺失依赖、目录准备、环境转发与 Runtime 健康检查。

### 后续迭代（可以有）

- [ ] 添加 `--check` 仅预检模式。
- [ ] 添加 Windows PowerShell 原生启动脚本。
- [ ] 在服务端失联时提供可选重试策略。

## 技术方案概述

- 平台/运行环境：Linux 为主；Windows Git Bash/WSL 与 macOS 尽力兼容。
- 核心技术栈：Bash、`curl` 健康检查、`uv` workspace 命令。
- 关键约束：不改变既有环境变量名称、默认端口或独立启动拓扑；API Key 不写入日志。

## 非功能需求

- 可诊断性：失败信息必须说明哪个变量或外部依赖导致失败。
- 安全性：不输出 `AIDEO_AI_API_KEY` 原文；debug 仅显示开关状态。
- 兼容性：脚本通过 `bash -n`；可使用 Linux 常见工具，但不依赖特定发行版服务管理器。

## 待定问题

- 无。健康检查使用 Runtime 已有的 `/health` 端点，默认超时为短时预检。
