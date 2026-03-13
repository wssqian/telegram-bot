# Telegram AI Bot（多轮上下文 + 流式回复 + 队列 + OCR视觉）

功能：

- 第一次聊天密码验证
- 多轮上下文对话（可 `/new`、`/refresh` 清空）
- AI 流式回复（兼容失败自动回退普通请求）
- AI 请求队列（多 worker）
- 自动限速防封（每用户窗口限流）
- 图片 OCR + 视觉分析（可结合上下文）
- Telegram 连接池调大 + Telegram 走代理、AI 本地直连

## 1. 安装

```bash
pip install -r requirements.txt
```

## 2. 配置

```bash
cp .env.example .env
```

程序会自动读取 `.env`。

关键参数：

- `AI_STREAM=true`：启用流式。
- `AI_QUEUE_WORKERS=2`：AI 请求队列 worker 数。
- `AI_MAX_HISTORY_TURNS=8`：多轮上下文轮数。
- `RATE_LIMIT_WINDOW_SECONDS` + `RATE_LIMIT_MAX_REQUESTS`：自动限速。
- `TELEGRAM_POOL_SIZE=32`：Telegram HTTP 连接池。
- `TELEGRAM_PROXY_URL=http://127.0.0.1:7890`：仅 Telegram 走代理。
- `AI_BYPASS_PROXY_FOR_LOCAL=true`：本地 AI 地址不走代理。

## 3. 启动

```bash
python bot.py
```

## 4. 命令

- `/start`：开始
- `/help`：帮助
- `/new`：开启新对话（清空上下文）
- `/refresh`：刷新聊天（清空上下文）

## 5. 说明

- 图片消息将进行 OCR + 视觉联合理解。
- 如果图片无 caption，机器人会要求再发一句文本，随后合并分析。
- 队列可避免高并发下直接压垮后端模型。
