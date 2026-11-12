"""Bott Telegram bot — Render-ready webhook entry point.

Run with: python bot.py
Required environment: BOT_TOKEN, ADMIN_ID, WEBHOOK_BASE_URL (or RENDER_EXTERNAL_URL).
Optional: WEBHOOK_SECRET, WEBHOOK_PATH.
"""
import html
import logging
import os

import telebot
from flask import Flask, abort, jsonify, request
from waitress import serve

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("bott")

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "7789281265"))
WEBHOOK_BASE_URL = (
    os.getenv("WEBHOOK_BASE_URL") or os.getenv("RENDER_EXTERNAL_URL")
)
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")
WEBHOOK_PATH = os.getenv("WEBHOOK_PATH", "/webhook").strip()

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN environment variable is not set")
if not WEBHOOK_PATH.startswith("/"):
    WEBHOOK_PATH = "/" + WEBHOOK_PATH

# Synchronous handlers make webhook processing finish before returning HTTP 200.
bot = telebot.TeleBot(BOT_TOKEN, threaded=False)
app = Flask(__name__)


@bot.message_handler(commands=["start"])
def start(message):
    bot.reply_to(message, "Салом! 👋\nЛазиза калайсиз.")


@bot.message_handler(
    func=lambda m: m.reply_to_message is not None,
    content_types=[
        "text", "photo", "video", "document",
        "audio", "voice", "sticker", "animation",
    ],
)
def admin_reply(message):
    if message.chat.id != ADMIN_ID:
        return

    original = message.reply_to_message.text or ""
    if not original.startswith("USER_ID:"):
        return

    try:
        user_id = int(original.splitlines()[0].split(":", 1)[1])
        bot.copy_message(
            chat_id=user_id,
            from_chat_id=message.chat.id,
            message_id=message.message_id,
        )
        bot.reply_to(message, "✅ Хабар юборилди рахмат асалим 😘")
    except Exception:
        logger.exception("Failed to forward admin reply")
        bot.reply_to(message, "❌ Хабарни юборишда хатолик.")


@bot.message_handler(
    content_types=[
        "text", "photo", "video", "document",
        "audio", "voice", "video_note", "sticker",
        "animation", "location", "contact", "venue",
    ],
)
def receive_message(message):
    if message.from_user and message.from_user.is_bot:
        return

    user = message.from_user
    if not user:
        return

    name = html.escape(user.first_name or "Номаълум")
    username = f"@{html.escape(user.username)}" if user.username else "Йўқ"
    info = (
        "📩 <b>Янги хабар</b>\n\n"
        f"👤 Исм: {name}\n"
        f"🆔 ID: <code>{user.id}</code>\n"
        f"🔗 Username: {username}\n"
        f"🌐 <a href='tg://user?id={user.id}'>Профиль</a>\n\n"
        f"USER_ID:{user.id}"
    )

    try:
        bot.send_message(ADMIN_ID, info, parse_mode="HTML")
        bot.copy_message(ADMIN_ID, message.chat.id, message.message_id)
        bot.reply_to(message, "✅ Хабар юборилди рахмат асалим 😘.")
    except Exception:
        logger.exception("Failed to deliver user message to admin")
        try:
            bot.reply_to(message, "❌ Хабарни етказишда хатолик.")
        except Exception:
            logger.exception("Could not send failure notice to user")


@app.get("/")
def home():
    return jsonify({"status": "ok", "service": "bott"}), 200


@app.get("/health")
def health():
    return jsonify({"status": "healthy"}), 200


@app.post(WEBHOOK_PATH)
def telegram_webhook():
    if WEBHOOK_SECRET:
        supplied_secret = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
        if supplied_secret != WEBHOOK_SECRET:
            abort(403)

    try:
        payload = request.get_json(silent=False)
        update = telebot.types.Update.de_json(payload)
        if update is None:
            return jsonify({"ok": False, "error": "Invalid update"}), 400

        bot.process_new_updates([update])
        return jsonify({"ok": True}), 200
    except Exception:
        logger.exception("Webhook update processing failed")
        return jsonify({"ok": False}), 500


def main():
    if not WEBHOOK_BASE_URL:
        raise RuntimeError(
            "Set WEBHOOK_BASE_URL or use Render's RENDER_EXTERNAL_URL"
        )

    webhook_url = f"{WEBHOOK_BASE_URL.rstrip('/')}{WEBHOOK_PATH}"
    logger.info("Configuring Telegram webhook: %s", webhook_url)

    # Fail startup clearly if Telegram rejects the token or webhook URL.
    result = bot.set_webhook(
        url=webhook_url,
        secret_token=WEBHOOK_SECRET or None,
        allowed_updates=["message"],
        drop_pending_updates=False,
    )
    if not result:
        raise RuntimeError("Telegram rejected setWebhook request")

    logger.info("Telegram webhook configured successfully")
    port = int(os.getenv("PORT", "10000"))
    logger.info("Starting web server on 0.0.0.0:%s", port)
    serve(app, host="0.0.0.0", port=port, threads=4)


if __name__ == "__main__":
    main()
