# Telegram AI Bot（含首次密码验证 + 图片识别 + 文件支持）

这个项目实现了一个 Telegram Bot，具备以下功能：

- 接入第三方 AI API（OpenAI 兼容接口）
- 新用户首次对话必须输入密码验证
- 支持图片识别（视觉模型）
- 图片分析会附带用户“上一句 + 下一句（或 caption）”上下文
- 支持接收文件并回传确认

## 1. 安装依赖

```bash
pip install -r requirements.txt
```

## 2. 配置环境变量（支持直接读取 `.env`）

复制并填写配置：

```bash
cp .env.example .env
```

> 程序启动时会自动 `load_dotenv()`，无需手动 `export`。

`.env` 示例：

```env
TELEGRAM_BOT_TOKEN=<你的telegram token>
BOT_PASSWORD=<首次聊天密码>
AI_API_KEY=<第三方AI token>
AI_API_BASE=https://api.openai.com/v1
AI_MODEL=gpt-4o-mini
AI_TIMEOUT=120
AI_TEMPERATURE=0.3
DB_PATH=users.db
```

## 3. 启动

```bash
python bot.py
```

## 4. 使用方式

- `/start`：首次使用会提示输入密码。
- 新用户输入正确密码后会被记录为已认证用户（默认本地 `users.db`）。
- 认证后发送文本：Bot 调用 AI 返回回复。
- 认证后发送图片：
  - 若带 caption：直接识图并结合上下文回复。
  - 若不带 caption：Bot 会提示你再发一句；随后将“上一句 + 这句 + 图片”一起发给视觉模型。
- 认证后发送文件：Bot 接收后回传文件，并给出 AI 确认文案。

## 5. 说明

- AI 接口使用 OpenAI-compatible `POST /chat/completions`。
- 若你使用 OpenRouter、OneAPI、Azure 兼容网关等，只要兼容该协议，修改 `AI_API_BASE` / `AI_MODEL` 即可。
- 若接口偶发 `502`，建议增大 `AI_TIMEOUT`、检查反向代理与上游模型服务稳定性。
