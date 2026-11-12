
import telebot
from telebot import types
import html

BOT_TOKEN = "8015441015:AAGqrJHctA9y7-Gxbp68uzY_RdRQWj3k5WQ"
ADMIN_ID = 7789281265

bot = telebot.TeleBot(BOT_TOKEN)


@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(
        message,
        "Салом! 👋\n"
        "Лазиза калайсиз."
    )


@bot.message_handler(
    func=lambda m: m.reply_to_message is not None,
    content_types=['text', 'photo', 'video', 'document',
                   'audio', 'voice', 'sticker', 'animation']
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
        'text', 'photo', 'video', 'document',
        'audio', 'voice', 'video_note',
        'sticker', 'animation', 'location',
        'contact', 'venue'
    ]
)
def receive_message(message):
    if message.from_user.is_bot:
        return

    user = message.from_user

    name = html.escape(user.first_name or "Номаълум")
    username = (
        f"@{html.escape(user.username)}"
        if user.username else "Йўқ"
    )

    info = (
        f"📩 <b>Янги хабар</b>\n\n"
        f"👤 Исм: {name}\n"
        f"🆔 ID: <code>{user.id}</code>\n"
        f"🔗 Username: {username}\n"
        f"🌐 <a href='tg://user?id={user.id}'>Профиль</a>\n"
        f"\nUSER_ID:{user.id}"
    )

    try:
        bot.send_message(
            ADMIN_ID,
            info,
            parse_mode="HTML"
        )

        bot.copy_message(
            ADMIN_ID,
            message.chat.id,
            message.message_id
        )

        bot.reply_to(message, "✅ Хабар юборилди рахмат асалим 😘.")

    except Exception as e:
        print("ERROR:", e)
        bot.reply_to(message, "❌ Хабарни етказишда хатолик.")


print("🤖 Bot ishga tushdi!")
bot.infinity_polling(skip_pending=True)
