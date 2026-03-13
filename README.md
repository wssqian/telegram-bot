# Telegram AI Bot（含首次密码验证 + 图片/文件支持）

这个项目实现了一个 Telegram Bot，具备以下功能：

- 接入第三方 AI API（OpenAI 兼容接口）
- 新用户首次对话必须输入密码验证
- 支持接收图片和文件，并进行回传确认

## 1. 安装依赖

```bash
pip install -r requirements.txt
```

## 2. 配置环境变量

复制并填写配置：

```bash
cp .env.example .env
```

然后在 shell 里导出变量（示例）：

```bash
export TELEGRAM_BOT_TOKEN="<你的telegram token>"
export BOT_PASSWORD="<首次聊天密码>"
export AI_API_KEY="<第三方AI token>"
export AI_API_BASE="https://api.openai.com/v1"
export AI_MODEL="gpt-4o-mini"
```

## 3. 启动

```bash
python bot.py
```

## 4. 使用方式

- `/start`：首次使用时会提示输入密码。
- 新用户输入正确密码后会被记录为已认证用户（本地 `users.db`）。
- 认证后发送文本消息，Bot 会调用 AI API 回复。
- 认证后发送图片或文件，Bot 会接收并回传文件/图片，同时附上一句 AI 回复。

## 5. 说明

- AI 接口使用 OpenAI-compatible `POST /chat/completions`。
- 若你使用的是其他第三方平台（如 OpenRouter、OneAPI、Azure 网关等），只要兼容该协议，修改 `AI_API_BASE` / `AI_MODEL` 即可。
