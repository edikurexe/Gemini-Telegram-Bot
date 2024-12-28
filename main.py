import argparse
import traceback
import asyncio
import google.generativeai as genai
import re
import telebot
from telebot.async_telebot import AsyncTeleBot
from telebot.types import Message

gemini_player_dict = {}
gemini_pro_player_dict = {}
default_model_dict = {}
warn_dict = {}  # Menyimpan user_id dan jumlah peringatannya

error_info = "⚠️⚠️⚠️\nSomething went wrong!\nplease try to change your prompt or contact the admin!"
before_generate_info = "🤖 Bot sedang menulis jawaban 🤖"
download_pic_notify = "🤖 Bot sedang membuat gambar 🤖"

n = 30  # Number of historical records to keep

generation_config = {
    "temperature": 1,
    "top_p": 1,
    "top_k": 1,
    "max_output_tokens": 2048,
}

safety_settings = [
    {
        "category": "HARM_CATEGORY_HARASSMENT",
        "threshold": "BLOCK_NONE",
    },
    {
        "category": "HARM_CATEGORY_HATE_SPEECH",
        "threshold": "BLOCK_NONE",
    },
    {
        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
        "threshold": "BLOCK_NONE",
    },
    {
        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
        "threshold": "BLOCK_NONE",
    },
]


async def main():
    # Init args
    parser = argparse.ArgumentParser()
    parser.add_argument("TELEGRAM_BOT_API_KEY", help="telegram token")
    parser.add_argument("GOOGLE_GEMINI_KEY", help="Google Gemini API key")
    parser.add_argument("auth_id", help="Authorized user ID", type=int)
    parser.add_argument("auth_group_id", help="Authorized group ID", type=int)
    options = parser.parse_args()
    print("Arg parse done.")

    genai.configure(api_key=options.GOOGLE_GEMINI_KEY)

    # Init bot
    bot = AsyncTeleBot(options.tg_token)
    await bot.delete_my_commands(scope=None, language_code=None)
    await bot.set_my_commands(
        commands=[
            telebot.types.BotCommand("start", "Start"),
            telebot.types.BotCommand("gemini", "using gemini-1.5-flash"),
            telebot.types.BotCommand("gemini_pro", "using gemini-1.5-pro"),
            telebot.types.BotCommand("clear", "Clear all history"),
            telebot.types.BotCommand("switch", "switch default model"),
        ],
    )
    print("Bot init done.")

    @bot.message_handler(func=lambda message: True, content_types=["new_chat_members", "text"])
    async def warn_and_kick_handler(message: Message):
        # Abaikan jika bukan grup
        if message.chat.type not in ["group", "supergroup"]:
            return

        # Periksa jika pengirim adalah admin, lewati mereka
        admins = [admin.user.id for admin in await bot.get_chat_administrators(message.chat.id)]
        if message.from_user.id in admins:
            return

        user = message.from_user

        # Jika ada anggota baru, beri peringatan jika tidak memiliki username
        if hasattr(message, "new_chat_members"):
            for new_member in message.new_chat_members:
                if not new_member.username:
                    await bot.reply_to(
                        message,
                        f"Halo {new_member.first_name}, silakan tambahkan username Anda agar tetap berada di grup ini.",
                    )
                    warn_dict[new_member.id] = 1
            return

        # Jika ada pesan, periksa apakah pengguna sudah memiliki username
        if not user.username:
            # Periksa apakah pengguna sudah diperingatkan sebelumnya
            if user.id in warn_dict:
                warn_dict[user.id] += 1
                # Jika peringatan sudah 2 kali, keluarkan pengguna
                if warn_dict[user.id] >= 2:
                    await bot.kick_chat_member(message.chat.id, user.id)
                    await bot.reply_to(
                        message,
                        f"Pengguna {user.first_name} telah dikeluarkan karena tidak menambahkan username.",
                    )
                    del warn_dict[user.id]
                else:
                    await bot.reply_to(
                        message,
                        f"Halo {user.first_name}, ini peringatan kedua. Tambahkan username Anda segera!",
                    )
            else:
                # Peringatan pertama
                warn_dict[user.id] = 1
                await bot.reply_to(message, f"Halo {user.first_name}, silakan tambahkan username Anda.")

    print("Starting Gemini_Telegram_Bot.")
    await bot.polling(none_stop=True)


if __name__ == "__main__":
    asyncio.run(main())
