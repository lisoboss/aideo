# Tasks: feat-local-ltx-asr-providers

> 生成时间：2026-07-15
> 基于：spec.md + plan.md

## 进度

- [x] 12 / 12 任务完成

---

### Task 1: 创建 `tests/test_paths.py` ✅

- **文件**：`packages/aideo-runtime/tests/test_paths.py`
- **类型**：测试
- **依赖**：无
- **描述**：覆盖 models/input/output 根目录创建、相对路径解析、绝对路径与 `..` 越界拒绝、输出 `runtime://output/` URI。
- **验收**：路径模块不存在时测试为红。

### Task 2: 实现 `paths.py` ✅

- **文件**：`packages/aideo-runtime/src/aideo_runtime/paths.py`
- **类型**：实现
- **依赖**：Task 1
- **描述**：实现 `PathSettings` 和安全路径解析；只接受相对路径并验证 resolve 后仍位于根目录。
- **验收**：Task 1 通过。

### Task 3: 更新 `tests/test_runtime_config.py` ✅

- **文件**：`packages/aideo-runtime/tests/test_runtime_config.py`
- **类型**：测试
- **依赖**：Task 2
- **描述**：覆盖三个全局根目录的环境变量解析和默认值。
- **验收**：新增断言在配置实现前为红。

### Task 4: 实现 `config.py` 全局路径配置 ✅

- **文件**：`packages/aideo-runtime/src/aideo_runtime/config.py`
- **类型**：实现
- **依赖**：Task 2、Task 3
- **描述**：将 `PathSettings` 纳入 `RuntimeSettings`，创建/验证全局目录，不保留 Provider 私有根目录。
- **验收**：Task 3 通过。

### Task 5: 创建 `tests/test_faster_whisper2_provider.py` ✅

- **文件**：`packages/aideo-runtime/tests/test_faster_whisper2_provider.py`
- **类型**：测试
- **依赖**：Task 2、Task 4
- **描述**：用 mock WhisperModel/torch 覆盖 Provider 模型目录、懒加载、CPU int8 回退、输入路径解析、转写结果与分段元数据。
- **验收**：Provider 不存在时测试为红。

### Task 6: 实现 `backend/providers/faster_whisper2.py` ✅

- **文件**：`packages/aideo-runtime/src/aideo_runtime/backend/providers/faster_whisper2.py`
- **类型**：实现
- **依赖**：Task 5
- **描述**：迁移 main 分支 FasterWhisperProvider 到 Runtime Backend；在 load 内导入依赖、统一输入/输出路径、实现 invoke/stream/health/models/aclose。
- **验收**：Task 5 通过。

### Task 7: 创建 `tests/test_ltx2_provider.py` ✅

- **文件**：`packages/aideo-runtime/tests/test_ltx2_provider.py`
- **类型**：测试
- **依赖**：Task 2、Task 4
- **描述**：用 mock LTX pipeline/torch 覆盖 Provider 模型目录、懒加载、请求参数、阶段进度、输出文件与 runtime URI。
- **验收**：Provider 不存在时测试为红。

### Task 8: 实现 `backend/providers/ltx2.py` ✅

- **文件**：`packages/aideo-runtime/src/aideo_runtime/backend/providers/ltx2.py`
- **类型**：实现
- **依赖**：Task 7
- **描述**：迁移 main 分支 DistilledPipeline 初始化和生成流程；延迟导入 GPU 依赖，复用全局路径，提供统一 invoke/stream/health/models/aclose。
- **验收**：Task 7 通过。

### Task 9: 更新 `backend/providers/__init__.py` ✅

- **文件**：`packages/aideo-runtime/src/aideo_runtime/backend/providers/__init__.py`
- **类型**：实现
- **依赖**：Task 6、Task 8
- **描述**：补充 Provider 工厂约定文档，说明重型依赖的延迟加载与 PathSettings 注入。
- **验收**：`ltx2` 与 `faster_whisper2` 均可通过 Loader 加载。

### Task 10: 更新 `pyproject.toml` 与 `uv.lock` ✅

- **文件**：`packages/aideo-runtime/pyproject.toml`、`uv.lock`
- **类型**：配置
- **依赖**：Task 6、Task 8
- **描述**：通过 `uv add` 添加用户给出的 CUDA/LTX/Whisper 依赖，再加入 PyTorch index 与 git sources；同步 lockfile。
- **验收**：`uv sync --all-packages` 解析成功。

### Task 11: 更新 `.env.example` 与 README ✅

- **文件**：`packages/aideo-runtime/.env.example`、`packages/aideo-runtime/README.md`
- **类型**：文档
- **依赖**：Task 4、Task 6、Task 8
- **描述**：说明全局根目录、Provider 选择、LTX/Whisper 相对路径和统一输出 URI。
- **验收**：示例不包含 Provider 私有 root/output 目录。

### Task 12: 更新变更记录并验证 ✅

- **文件**：`docs/changes/changed-2026-07-15-unified-inference-runtime.md`
- **类型**：文档
- **依赖**：Task 9、Task 10、Task 11
- **描述**：记录迁移、全局路径、依赖和验证结果；运行 Runtime 测试、pre-commit 和按硬件可用条件执行的集成测试。
- **验收**：静态和 mock 测试通过；GPU/模型依赖缺失时清晰标记为条件性验证。
