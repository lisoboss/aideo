# 2026-07-11 — 图片编辑/超分 全链路（serv 端点 + runtime provider 基础）

补齐 `aideo-serv` 的图片编辑与超分端点，并在 `aideo-runtime` 落地 `image` provider 品类基础，
闭合 iPad 早已声明、后端缺失的协议（iPad `editImage()` / `upscaleImage()` 之前调用会 404）。
契约与 `docs/API.md`、iPad `EditImageRequest`/`UpscaleRequest` 完全对齐。具体模型实现待补。

## 端点实现

### 新增文件

| 文件 | 说明 |
|------|------|
| `models/edit.py` | `ImageEditMode`(4 模式)、`MaskRegion`(相对坐标 0–1)、`EditImageRequest`、`EditImageResponse`、`UpscaleRequest`(scale=`Literal[2,4]`)、`UpscaleResponse` |
| `api/canvas_image.py` | `image_router`(prefix `/canvas`)：`POST /canvas/edit-image`、`POST /canvas/upscale` |
| `tests/test_canvas_image.py` | 12 用例：201 成功、asset/project 404、mode/scale/mask 422 |

### 修改文件

| 文件 | 变更 |
|------|------|
| `api/router.py` | `include_router(image_router)` |
| `services/inference_client.py` | `TASK_TO_PROVIDER` +`image_edit`/`image_upscale` → `("image","stub")` |
| `api/tasks.py` | `_SERVICE_FOR_TASK_TYPE` +`image_edit`/`image_upscale` |

### 变更要点

- **流程复用 `/generate`**：校验 project + asset（`base_image`/`reference_images` 按 `asset_id` 解析为磁盘路径）→ `serialize_prompt(prompt_blocks)` → `task_svc.create(task_type=…)` → `asyncio.create_task(_submit_to_inference(…))` fire-and-forget → 返回 `{task_id, task}`(201)。客户端经项目级 WS 跟踪进度。
- **`input_files` 带 `role`**：edit-image 下 `base`/`reference`，upscale 下 `source`，供 runtime 区分底图与参考图。
- **校验**：`mode` 非法 → 422；`mask_regions` 坐标越界(>1.0) → 422；`scale` ∉ {2,4} → 422；asset/project 不存在 → 404（`RESOURCE_NOT_FOUND`）。
- **runtime provider 待补**：serv 侧已完整；`image` 品类的 runtime provider 尚未实现，故任务派发后会以明确错误优雅失败（`resolve_provider` 已识别 task_type，POST `/api/v1/image/stub` 返回 404 → `on_error` → task failed）。待 aideo-runtime 增加 `image` 品类后自动生效。
- **文档**：`docs/API.md` 早已记录该协议（`### 图片编辑（NEW）`），本次为实现补齐，无需改文档。

## Runtime image provider 基础（aideo-runtime）

新增 `image` provider 品类，闭合 serv 端派发目标 `("image", "stub")`。遵循 speech 品类的
正确范式（yield `ProgressStatus`，非 dict；`register_provider` 自注册），非 chat/vision 旧 stub 的 dict 写法。

### 新增文件

| 文件 | 说明 |
|------|------|
| `image/provider.py` | `ImageProvider` ABC + `PROVIDERS` 注册表；`run()` 接收 serv `_submit_to_inference` 载荷（prompt/params/input_files/task_id/output_root/input_root） |
| `image/stub.py` | `StubImageProvider`（`provider_name="stub@image.provider"`）：按 `params` 区分 edit/upscale，yield `ProgressStatus`，完成时 `result_data.status="not_implemented"` |
| `image/__init__.py` | 导出 + `import image.stub` 触发自注册 |
| `tests/test_image_provider.py` | 11 用例：接口/继承、prefix 发现、edit/upscale run、取消、SSE 序列化 |

### 修改文件

| 文件 | 变更 |
|------|------|
| `server.py` | `CATEGORIES` +`image`；startup 预导入 `aideo_runtime.image` |
| `README.md` | 品类列表 + 目录树 +`image/` |

### 变更要点

- **正确范式**：yield `ProgressStatus`（`.model_dump_json()` 供 server SSE），非旧 stub 的 dict（README 编码规则第 4/77 行明确要求）。
- **发现**：serv `("image","stub")` → server `_discover_provider_cls` 先精确匹配 `stub` 未命中 → 前缀匹配 `"stub@image.provider".startswith("stub")` 命中。测试 `test_discoverable_by_prefix` 覆盖。
- **stub 语义**：完成并回 `result_data.status="not_implemented"`（清晰占位，全链路可跑通）。换真模型时保持 `run()` 契约即可。
- **模型待补**：diffusion inpainting（edit）/ Real-ESRGAN（upscale）等真实实现后续补充。

## 测试

- serv：`uv run --package aideo-serv pytest packages/aideo-serv/tests` → **173 passed**（161 + 新增 12）。
- runtime：`PYTHONPATH=packages/aideo-runtime/src uv run --no-sync pytest packages/aideo-runtime/tests/test_image_provider.py` → **11 passed**（image 模块仅依赖 pydantic，无 torch）。
- 全量 runtime 测试需 Linux/CUDA 环境（本机 macOS 无法 sync `nvidia-cublas`，与本变更无关）；将在具备 GPU 的机器上验证。
- 所有新增/修改 runtime 文件 `python -m py_compile` 通过。

## 涉及文件总览

```
aideo/
├── .claude/rules/architecture-runtime.md                  # 修改：+image 品类 + HTTP+SSE 现状
├── docs/
│   ├── changes.md                                         # +本条索引
│   └── changes/
│       └── changed-2026-07-11-backend-edit-image-upscale.md  # 本文件
└── packages/
    ├── aideo-serv/
    │   ├── src/aideo_serv/
    │   │   ├── models/edit.py                             # 新增
    │   │   ├── api/canvas_image.py                        # 新增
    │   │   ├── api/router.py                              # 修改：include image_router
    │   │   ├── api/tasks.py                               # 修改：_SERVICE_FOR_TASK_TYPE
    │   │   └── services/inference_client.py               # 修改：TASK_TO_PROVIDER
    │   └── tests/test_canvas_image.py                     # 新增
    └── aideo-runtime/
        ├── src/aideo_runtime/
        │   ├── image/__init__.py                          # 新增
        │   ├── image/provider.py                          # 新增
        │   ├── image/stub.py                              # 新增
        │   └── server.py                                  # 修改：CATEGORIES + startup import
        ├── README.md                                      # 修改：品类 + 目录树
        └── tests/test_image_provider.py                  # 新增
```
