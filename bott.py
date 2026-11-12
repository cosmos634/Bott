import os
import html
import telebot
from flask import Flask, request, jsonify

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "7789281265"))

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN environment variable is not set")

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)


@bot.message_handler(commands=["start"])
def start(message):
    bot.reply_to(
        message,
        "Салом! 👋\n"
        "Лазиза калайсиз."
    )


@bot.message_handler(
    func=lambda m: m.reply_to_message is not None,
    content_types=[
        "text", "photo", "video", "document",
        "audio", "voice", "sticker", "animation"
    ]
)
def admin_reply(message):
    if message.chat.id != ADMIN_ID:
        return

    original = message.reply_to_message.text or ""
    if not original.startswith("USER_ID:"):
        return

    try:
        user_id = int(original.splitlines()[0].split(":")[1])
        bot.copy_message(
            chat_id=user_id,
            from_chat_id=message.chat.id,
            message_id=message.message_id
        )
        bot.reply_to(message, "✅ Хабар юборилди рахмат асалим 😘")
    except Exception as e:
        bot.reply_to(message, f"❌ Хатолик: {e}")


@bot.message_handler(
    content_types=[
        "text", "photo", "video", "document",
        "audio", "voice", "video_note",
        "sticker", "animation", "location",
        "contact", "venue"
    ]
)
def receive_message(message):
    if message.from_user.is_bot:
        return

    user = message.from_user
    name = html.escape(user.first_name or "Номаълум")
    username = f"@{html.escape(user.username)}" if user.username else "Йўқ"

    info = (
        f"📩 <b>Янги хабар</b>\n\n"
        f"👤 Исм: {name}\n"
        f"🆔 ID: <code>{user.id}</code>\n"
        f"🔗 Username: {username}\n"
        f"🌐 <a href='tg://user?id={user.id}'>Профиль</a>\n"
        f"\nUSER_ID:{user.id}"
    )

    try:
        bot.send_message(ADMIN_ID, info, parse_mode="HTML")
        bot.copy_message(
            ADMIN_ID,
            message.chat.id,
            message.message_id
        )
        bot.reply_to(message, "✅ Хабар юборилди рахмат асалим 😘.")
    except Exception as e:
        print("ERROR:", e)
        bot.reply_to(message, "❌ Хабарни етказишда хатолик.")


@app.get("/")
def home():
    return jsonify({"status": "ok", "service": "telegram-bot"}), 200


@app.get("/health")
def health():
    return jsonify({"status": "healthy"}), 200


@app.post("/webhook")
def telegram_webhook():
    try:
        update = telebot.types.Update.de_json(
            request.get_data(as_text=True)
        )
        if update:
            bot.process_new_updates([update])
        return jsonify({"ok": True}), 200
    except Exception as e:
        print("WEBHOOK ERROR:", e)
        return jsonify({"ok": False}), 500


def configure_webhook():
    base_url = (
        os.getenv("WEBHOOK_URL")
        or os.getenv("RENDER_EXTERNAL_URL")
    )
    if not base_url:
        print("WEBHOOK_URL / RENDER_EXTERNAL_URL not set; webhook not configured")
        return

    webhook_url = f"{base_url.rstrip('/')}/webhook"
    result = bot.set_webhook(url=webhook_url)
    print(f"Webhook configured: {webhook_url} ({result})")


configure_webhook()


if __name__ == "__main__":
    port = int(os.getenv("PORT", "10000"))
    app.run(host="0.0.0.0", port=port)
