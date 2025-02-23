import os
import asyncio
from pyrogram import Client, filters
from yt_dlp import YoutubeDL
import re

# Telegram bot sozlamalari
API_ID = "22437042"
API_HASH = "95b6e9f809983d4990af5a4f60c51652"
BOT_TOKEN = "6693824512:AAHdjkrF0mqVdUHgeBmb3_qPLfa7CzjKxYM"
ADMIN_ID = 5510219247

app = Client("video_downloader_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Cookie fayllar
YOUTUBE_COOKIES = "youtube_cookies.txt"
INSTAGRAM_COOKIES = "instagram_cookies.txt"

# Yuklab olish funksiyasi
async def download_media(url, message):
    temp_dir = "downloads"
    os.makedirs(temp_dir, exist_ok=True)

    # URL-ga qarab cookie faylni tanlash
    if "instagram.com" in url:
        cookies_file = INSTAGRAM_COOKIES
    elif "youtube.com" in url or "youtu.be" in url:
        cookies_file = YOUTUBE_COOKIES
    else:
        cookies_file = None

    # Yuklab olish sozlamalari
    ydl_opts = {
        'outtmpl': f'{temp_dir}/%(title)s.%(ext)s',
        'format': 'best',
        'noplaylist': True  # Playlist emas, faqat bitta postni yuklaydi
    }

    if cookies_file and os.path.exists(cookies_file):
        ydl_opts['cookiefile'] = cookies_file

    msg = await message.reply("📥 Yuklab olinmoqda...")

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            files = [ydl.prepare_filename(info)]

        # Agar post ichida bir nechta media bo‘lsa, barchasini olish
        if "entries" in info:
            files = [ydl.prepare_filename(entry) for entry in info["entries"]]

        caption = "✅ Yuklab olindi!\n\n@shoxsan_bot"
        user_info = f"👤 User: {message.from_user.mention} (ID: {message.from_user.id})"

        for file in files:
            if not os.path.exists(file):
                continue  # Fayl topilmasa o'tkazib yuboramiz

            # Rasm yoki video ekanligini tekshiramiz
            if file.endswith((".mp4", ".mov", ".mkv")):
                await message.reply_video(video=file, caption=caption)
                await app.send_video(ADMIN_ID, video=file, caption=user_info)
            elif file.endswith((".jpg", ".jpeg", ".png", ".webp")):
                await message.reply_photo(photo=file, caption=caption)
                await app.send_photo(ADMIN_ID, photo=file, caption=user_info)

            os.remove(file)  # Foydalanuvchiga yuborilgandan keyin faylni o‘chirib tashlaymiz

    except Exception as e:
        error_message = f"❌ Xatolik yuz berdi: {str(e)}"
        await message.reply(error_message)
        await app.send_message(ADMIN_ID, f"⚠️ Xatolik yuz berdi!\n🔗 {url}\n❌ {str(e)}")

    await msg.delete()

# Start komandasi
@app.on_message(filters.private & filters.command("start"))
async def start_command(client, message):
    await message.reply("👋 Salom! Menga video yoki rasm havolasini yuboring, men uni yuklab beraman.")

# Foydalanuvchi havola yuborganida
@app.on_message(filters.private & filters.text & ~filters.user(ADMIN_ID))
async def handle_message(client, message):
    url = message.text.strip()
    user_info = f"👤 User: {message.from_user.mention} (ID: {message.from_user.id})"

    await app.send_message(ADMIN_ID, f"📩 {user_info} botga quyidagi xabarni yubordi:\n{url}")

    if url.startswith("http"):
        await download_media(url, message)
    else:
        await message.reply("❌ Iltimos, to'g'ri havola yuboring!")

app.run()
