import asyncio
import base64
import logging
import mimetypes
import os
import sqlite3
import tempfile
from pathlib import Path
from typing import Any, Optional

import requests
from dotenv import load_dotenv
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)


load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
BOT_PASSWORD = os.getenv("BOT_PASSWORD", "")
AI_API_KEY = os.getenv("AI_API_KEY", "")
AI_API_BASE = os.getenv("AI_API_BASE", "https://api.openai.com/v1").rstrip("/")
AI_MODEL = os.getenv("AI_MODEL", "gpt-4o-mini")
AI_TIMEOUT = int(os.getenv("AI_TIMEOUT", "120"))
AI_TEMPERATURE = float(os.getenv("AI_TEMPERATURE", "0.3"))
DB_PATH = os.getenv("DB_PATH", "users.db")


class AuthStore:
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    authorized INTEGER NOT NULL DEFAULT 0
                )
                """
            )
            conn.commit()

    def is_authorized(self, user_id: int) -> bool:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT authorized FROM users WHERE user_id = ?", (user_id,)
            ).fetchone()
        return bool(row and row[0] == 1)

    def ensure_user(self, user_id: int) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO users (user_id, authorized) VALUES (?, 0)",
                (user_id,),
            )
            conn.commit()

    def authorize(self, user_id: int) -> None:
        with self._connect() as conn:
            conn.execute(
                "UPDATE users SET authorized = 1 WHERE user_id = ?", (user_id,)
            )
            conn.commit()


store = AuthStore(DB_PATH)


def _extract_content(data: dict[str, Any]) -> str:
    choices = data.get("choices", [])
    if not choices:
        return "⚠️ AI 返回为空。"

    content = choices[0].get("message", {}).get("content", "")
    if isinstance(content, str):
        return content.strip()

    if isinstance(content, list):
        chunks = []
        for part in content:
            if isinstance(part, dict) and part.get("type") == "text":
                text = part.get("text", "")
                if text:
                    chunks.append(text)
        return "\n".join(chunks).strip() or "⚠️ AI 未返回文本内容。"

    return str(content).strip() or "⚠️ AI 未返回有效内容。"


def _call_chat_completions(messages: list[dict[str, Any]]) -> str:
    if not AI_API_KEY:
        return "⚠️ 未配置 AI_API_KEY，暂时无法调用 AI。"

    url = f"{AI_API_BASE}/chat/completions"
    headers = {
        "Authorization": f"Bearer {AI_API_KEY}",
        "Content-Type": "application/json",
    }
    payload: dict[str, Any] = {
        "model": AI_MODEL,
        "messages": messages,
        "temperature": AI_TEMPERATURE,
    }

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=AI_TIMEOUT)
        resp.raise_for_status()
        return _extract_content(resp.json())
    except requests.HTTPError as exc:
        detail = ""
        if exc.response is not None:
            detail = exc.response.text[:300]
        logger.exception("AI API HTTP error: %s", exc)
        return f"⚠️ 调用 AI 失败：HTTP {exc.response.status_code if exc.response else 'unknown'} {detail}"
    except requests.RequestException as exc:
        logger.exception("AI API request failed: %s", exc)
        return f"⚠️ 调用 AI 失败：{exc}"


def ask_ai_text(user_input: str) -> str:
    messages: list[dict[str, Any]] = [
        {
            "role": "system",
            "content": "你是一个有帮助的 Telegram 助手，请使用简体中文回答。",
        },
        {"role": "user", "content": user_input},
    ]
    return _call_chat_completions(messages)


def ask_ai_vision(
    image_bytes: bytes,
    mime_type: str,
    prev_text: str,
    next_text: str,
    caption: str,
) -> str:
    image_b64 = base64.b64encode(image_bytes).decode("utf-8")
    image_data_url = f"data:{mime_type};base64,{image_b64}"

    instruction = (
        "你将收到一张用户图片，请识别图片内容并结合上下文回答。\n"
        f"用户上一句：{prev_text or '（无）'}\n"
        f"用户下一句：{next_text or '（无）'}\n"
        f"图片备注（caption）：{caption or '（无）'}\n"
        "请输出：1) 图片内容概述 2) 结合上下文给出简短回复。"
    )

    messages: list[dict[str, Any]] = [
        {
            "role": "system",
            "content": "你是支持图像理解的中文 AI 助手，请准确识图并简明回答。",
        },
        {
            "role": "user",
            "content": [
                {"type": "text", "text": instruction},
                {"type": "image_url", "image_url": {"url": image_data_url}},
            ],
        },
    ]
    return _call_chat_completions(messages)


def is_authorized(user_id: Optional[int]) -> bool:
    if user_id is None:
        return False
    store.ensure_user(user_id)
    return store.is_authorized(user_id)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id if update.effective_user else None
    if user_id is None or update.message is None:
        return

    store.ensure_user(user_id)
    if store.is_authorized(user_id):
        await update.message.reply_text(
            "欢迎回来！你已经通过验证。\n发送文字、图片或文件，我都会处理。"
        )
    else:
        await update.message.reply_text("欢迎！首次使用请先输入访问密码。")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None:
        return
    await update.message.reply_text(
        "使用说明：\n"
        "1) 首次聊天需要输入密码认证。\n"
        "2) 认证后可发送文字，调用第三方 AI 回复。\n"
        "3) 发送图片时，我会用可识图模型识别图片，并附带你上下句文本一起分析。\n"
        "4) 发送文件时，我会接收并回传确认。"
    )


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None:
        return

    user_id = update.effective_user.id if update.effective_user else None
    text = (update.message.text or "").strip()

    if user_id is None:
        return

    store.ensure_user(user_id)

    if not store.is_authorized(user_id):
        if not BOT_PASSWORD:
            await update.message.reply_text("⚠️ 服务端未设置 BOT_PASSWORD，无法完成认证。")
            return

        if text == BOT_PASSWORD:
            store.authorize(user_id)
            await update.message.reply_text("✅ 密码正确，认证成功！现在可以开始聊天了。")
        else:
            await update.message.reply_text("❌ 密码错误，请重新输入。")
        return

    pending_photo = context.user_data.get("pending_photo")
    if pending_photo:
        context.user_data["pending_photo"] = None
        await context.bot.send_chat_action(
            chat_id=update.effective_chat.id, action=ChatAction.TYPING
        )
        ai_reply = await asyncio.to_thread(
            ask_ai_vision,
            pending_photo["image_bytes"],
            pending_photo["mime_type"],
            pending_photo.get("prev_text", ""),
            text,
            pending_photo.get("caption", ""),
        )
        await update.message.reply_text(f"已收到你的图片。\nAI：{ai_reply}")
        context.user_data["last_text"] = text
        return

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
    ai_reply = await asyncio.to_thread(ask_ai_text, text)
    await update.message.reply_text(ai_reply)
    context.user_data["last_text"] = text


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None:
        return

    user_id = update.effective_user.id if update.effective_user else None
    if not is_authorized(user_id):
        await update.message.reply_text("请先输入密码完成认证，再发送图片。")
        return

    photo = update.message.photo[-1]
    tg_file = await photo.get_file()
    image_bytes = bytes(await tg_file.download_as_bytearray())
    caption = (update.message.caption or "").strip()
    prev_text = (context.user_data.get("last_text") or "").strip()

    mime_type = "image/jpeg"
    if tg_file.file_path:
        guessed_mime, _ = mimetypes.guess_type(tg_file.file_path)
        if guessed_mime:
            mime_type = guessed_mime

    if caption:
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
        ai_reply = await asyncio.to_thread(
            ask_ai_vision, image_bytes, mime_type, prev_text, caption, caption
        )
        await update.message.reply_text(f"已收到你的图片。\nAI：{ai_reply}")
    else:
        context.user_data["pending_photo"] = {
            "image_bytes": image_bytes,
            "mime_type": mime_type,
            "prev_text": prev_text,
            "caption": caption,
        }
        await update.message.reply_text(
            "已收到你的图片。请再发送一句补充描述，我会结合你上一句和这句一起识图分析。"
        )


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None:
        return

    user_id = update.effective_user.id if update.effective_user else None
    if not is_authorized(user_id):
        await update.message.reply_text("请先输入密码完成认证，再发送文件。")
        return

    document = update.message.document
    if document is None:
        return

    tg_file = await document.get_file()

    with tempfile.TemporaryDirectory() as tmp_dir:
        filename = document.file_name or f"doc_{document.file_unique_id}"
        local_path = Path(tmp_dir) / filename
        await tg_file.download_to_drive(custom_path=str(local_path))

        prompt = (
            f"用户上传了文件：{filename}，大小约 {document.file_size or 0} 字节。"
            "请生成一句简短确认消息。"
        )
        ai_reply = await asyncio.to_thread(ask_ai_text, prompt)

        with local_path.open("rb") as f:
            await update.message.reply_document(
                document=f,
                caption=f"已收到并回传文件：{filename}\nAI：{ai_reply}",
            )


def validate_env() -> None:
    if not TELEGRAM_BOT_TOKEN:
        raise RuntimeError("缺少 TELEGRAM_BOT_TOKEN 环境变量")


def main() -> None:
    validate_env()

    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))

    logger.info("Bot started.")
    app.run_polling(close_loop=False)


if __name__ == "__main__":
    main()
