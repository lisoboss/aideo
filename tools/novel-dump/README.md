# Novel Dump

通过浏览器用户脚本读取起点中文网当前章节，并交给本机保存服务写入文本文件。

本工具只处理当前账号有权在浏览器中阅读的内容。使用时请遵守网站条款、版权要求和当地法律，不要传播导出的受版权保护内容。

## 目录结构

```text
novel-dump/
├── server.py                       # 本地保存服务
├── userscript/qidian-export.user.js # 浏览器用户脚本
├── books/                          # 导出的章节，默认不纳入版本控制
├── data/                           # 本地运行数据，默认不纳入版本控制
└── tests/                          # 基础测试
```

## 使用方法

### 1. 启动本地服务

```bash
cd /Volumes/WorkSpace/IntelligentEngineeringLab/tools/novel-dump
uv sync
uv run python server.py
```

服务只监听 `127.0.0.1:2314`。可访问 `http://127.0.0.1:2314/health` 检查状态。

### 2. 安装用户脚本

在 Tampermonkey、Violentmonkey 等用户脚本管理器中新建脚本，将 `userscript/qidian-export.user.js` 的内容粘贴进去并保存。

打开起点章节页后，页面右侧会显示：

- 导出：通过浏览器直接下载当前章节
- 自动：将当前章节保存到本地服务，并继续下一章
- 停止：停止自动导出
- 上一章／下一章：手动切换章节
- 清除：清除浏览器中的导出进度

章节默认保存为：

```text
books/{书名}/{章节编号} - {章节名}.txt
```

## 配置

本地服务支持以下环境变量：

- `NOVEL_DUMP_HOST`：监听地址，默认 `127.0.0.1`
- `NOVEL_DUMP_PORT`：监听端口，默认 `2314`
- `NOVEL_DUMP_BOOKS_DIR`：保存目录，默认项目下的 `books/`
- `NOVEL_DUMP_MAX_BODY_BYTES`：单章最大字节数，默认 5 MiB

## 验证

```bash
uv run pytest
node --check userscript/qidian-export.user.js
```

涉及网站页面结构、登录状态与连续翻页的部分，需要在真实浏览器中手动验证。
