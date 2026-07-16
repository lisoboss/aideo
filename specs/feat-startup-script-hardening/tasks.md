# Tasks: feat-startup-script-hardening

> 生成时间：2026-07-16
> 基于：spec.md + plan.md

## 进度

- [x] 5 / 5 任务完成

---

### Task 1: 创建 Runtime 启动脚本测试 ✅

- **文件**：`tests/test_interface_script.sh`
- **类型**：测试
- **依赖**：无
- **描述**：以 fake `uv`/临时目录覆盖 `uv` 缺失、目录创建、debug 变量转发与 LTX 条件预检。
- **验收**：当前脚本不满足新增断言，测试为红。

### Task 2: 优化 Runtime 启动脚本 ✅

- **文件**：`interface.sh`
- **类型**：实现
- **依赖**：Task 1
- **描述**：实现一致日志、`uv` 检查、Runtime 根目录创建、debug 转发与 LTX 资源条件校验。
- **验收**：Task 1 通过，且 `bash -n interface.sh` 成功。

### Task 3: 创建服务端启动脚本测试 ✅

- **文件**：`tests/test_http_server_script.sh`
- **类型**：测试
- **依赖**：无
- **描述**：以 fake `uv`/`curl` 覆盖目录创建、Runtime 健康 URL、不可达失败和 API Key 脱敏。
- **验收**：当前脚本不满足新增断言，测试为红。

### Task 4: 优化服务端启动脚本 ✅

- **文件**：`http-server.sh`
- **类型**：实现
- **依赖**：Task 3
- **描述**：实现一致日志、`uv`/`curl` 检查、服务目录创建和 Runtime 健康预检。
- **验收**：Task 3 通过，且 `bash -n http-server.sh` 成功。

### Task 5: 更新启动说明、变更记录与验证 ✅

- **文件**：`docs/changes/changed-2026-07-16-startup-script-hardening.md`
- **类型**：集成/文档
- **依赖**：Task 2、Task 4
- **描述**：更新 Linux 启动说明、变更索引与详情；运行 shell 测试、`bash -n` 和 pre-commit。
- **验收**：两个脚本独立可预检启动，验证结果记录完整。
