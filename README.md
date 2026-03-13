# Telegram AI Bot（含首次密码验证 + 图片识别 + 文件支持）

这个项目实现了一个 Telegram Bot，具备以下功能：

- 接入第三方 AI API（OpenAI 兼容接口）
- 新用户首次对话必须输入密码验证
- 支持图片识别（视觉模型）
- 图片分析附带“上一句 + 下一句（或 caption）”上下文（自动截断）
- 支持接收文件并回传确认
- 支持 `/new` 开新对话、`/refresh` 刷新上下文

## 1. 安装依赖

```bash
pip install -r requirements.txt
```

## 2. 配置环境变量（支持直接读取 `.env`）

```bash
cp .env.example .env
```

程序启动时会自动 `load_dotenv()`，无需手动 `export`。

`.env` 示例：

```env
TELEGRAM_BOT_TOKEN=<你的telegram token>
BOT_PASSWORD=<首次聊天密码>
AI_API_KEY=<第三方AI token>
AI_API_BASE=http://192.168.1.99:9870/v1
AI_MODEL=gpt-4o-mini
AI_TIMEOUT=120
AI_TEMPERATURE=0.3
AI_MAX_CONTEXT_CHARS=120
AI_MAX_IMAGE_BYTES=350000
AI_RETRY_502=2
AI_BYPASS_PROXY_FOR_LOCAL=true
TELEGRAM_PROXY_URL=http://127.0.0.1:7890
DB_PATH=users.db
```

## 3. 启动

```bash
python bot.py
```

## 4. 使用方式

- `/start`：首次使用会提示输入密码。
- `/new`：开启新对话（清空缓存上下文）。
- `/refresh`：刷新聊天（清空缓存上下文）。
- 认证后发送文本：Bot 调用 AI 返回回复。
- 认证后发送图片：
  - 若带 caption：直接识图并结合上下文回复。
  - 若不带 caption：Bot 会提示你再发一句；随后将“上一句 + 这句 + 图片”一起发给视觉模型。
- 认证后发送文件：Bot 接收后回传文件，并给出 AI 确认文案。

## 5. 502 与代理说明

- Bot 支持对 `502/503/504` 自动重试（`AI_RETRY_502`）。
- 若你看到 502 但 AI 后台无请求记录，常见原因是上游网关/代理链路失败，不一定到达模型服务。
- 现在支持“Telegram 走代理、AI 本地接口直连”：
  - `TELEGRAM_PROXY_URL=http://127.0.0.1:7890` 仅用于 Telegram API。
  - `AI_BYPASS_PROXY_FOR_LOCAL=true` 时，本地网段 AI 地址（如 `192.168.x.x`）不会走代理。
