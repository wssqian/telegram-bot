# Telegram AI Bot（支持 Skill 安装/使用 + 工具调用）

功能：

- 首次聊天密码验证
- 多轮上下文对话（`/new`、`/refresh`）
- AI 请求队列 + 限速防封 + 流式回复
- 图片视觉理解
- **Skill 安装与启用**
- **工具调用（联网搜索 / 读取 xlsx / 读取文本 / 运行 Python）**

## 1. 安装

```bash
pip install -r requirements.txt
```

## 2. 配置

```bash
cp .env.example .env
```

关键参数：

- `AI_ENABLE_TOOLS=true`：开启工具调用。
- `AI_TOOL_MAX_STEPS=6`：单次对话最多工具调用轮数。
- `SKILLS_DIR=skills`：Skill 存放目录（`.txt`）。
- `FILES_DIR=files`：可读取文件目录（xlsx/txt等）。

## 3. 启动

```bash
python bot.py
```

## 4. Skill 命令

- `/skill_list`：查看已安装技能与当前技能。
- `/skill_install coder|research|xlsx-analyst`：安装内置技能。
- `/skill_use <name>`：启用技能。
- `/skill_off`：关闭技能。

## 5. 可用工具（由 AI 自动选择调用）

- `web_search(query, max_results)`：联网搜索。
- `list_files(subdir, max_items)`：列目录。
- `read_text(path, max_chars)`：读文本。
- `read_xlsx(path, sheet_name, max_rows)`：读 xlsx。
- `run_python(code, timeout_s)`：执行短 Python 代码。

> 建议把要分析的文档放到 `FILES_DIR`（默认 `files/`）里，例如 `files/report.xlsx`。
