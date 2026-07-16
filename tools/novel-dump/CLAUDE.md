# 项目协作说明

## 项目概述

本项目通过浏览器用户脚本读取起点章节内容，再由本机 FastAPI 服务保存为文本文件。

## 常用命令

```bash
uv sync
uv run python server.py
uv run pytest
node --check userscript/qidian-export.user.js
```

## 约定

- 修改前先更新 `TODO.md` 中的计划。
- 服务默认只监听本机地址，不扩大网络暴露范围。
- `books/` 和 `data/` 是用户本地数据，不提交其中内容。
- 不在日志、测试或提交内容中暴露 Cookie 等登录凭据。
- 网站页面结构相关改动必须注明需要浏览器手动验证。
