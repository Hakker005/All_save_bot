import os
import time
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

# Cookies faylini tekshirish
COOKIES_FILE = "cookies.txt"
if not os.path.exists(COOKIES_FILE):
    print("⚠️ Ogohlantirish: cookies.txt topilmadi. Instagram yuklab olish ishlamasligi mumkin!")

# Yuklab olish uchun funksiyalar
async def download_video(url, message):
    temp_dir = "downloads"
    os.makedirs(temp_dir, exist_ok=True)
    
    ydl_opts = {
        'outtmpl': f'{temp_dir}/%(title)s.%(ext)s',
        'format': 'best',
    }
    
    if os.path.exists(COOKIES_FILE):
        ydl_opts['cookiefile'] = COOKIES_FILE
    
    msg = await message.reply("📥 Yuklab olinmoqda...")
    
    video_path = None  # Fayl yo‘lini aniqlash uchun
    
    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            video_path = ydl.prepare_filename(info)
        
        if not os.path.exists(video_path):
            raise Exception("❌ Yuklab olishda xatolik yuz berdi, fayl topilmadi!")
        
        caption = "✅ Shunchaki foydalaning\n\n@shoxsan_bot"
        user_info = f"👤 User: {message.from_user.mention} (ID: {message.from_user.id})"
        
        # Foydalanuvchiga video yuborish
        await message.reply_video(video=video_path, caption=caption)
        
        # Admin uchun video yuborish
        admin_msg = await app.send_message(ADMIN_ID, f"📩 Yangi video yuklandi!\n{user_info}\n🔗 {url}")
        await app.send_video(ADMIN_ID, video=video_path, caption=user_info, reply_to_message_id=admin_msg.id)
    
    except Exception as e:
        error_message = f"❌ Xatolik yuz berdi: {str(e)}"
        await message.reply(error_message)
        await app.send_message(ADMIN_ID, f"⚠️ Xatolik yuz berdi!\n🔗 {url}\n❌ {str(e)}")

    finally:
        # Fayl mavjud bo‘lsa, uni o‘chirish
        if video_path and os.path.exists(video_path):
            os.remove(video_path)
    
    await message.delete()


@app.on_message(filters.private & filters.command("start"))
async def start_command(client, message):
    await message.reply("👋 Salom! Menga video havolasini yuboring, men uni yuklab beraman.")

@app.on_message(filters.private & filters.text & ~filters.user(ADMIN_ID))
async def handle_message(client, message):
    url = message.text.strip()
    user_info = f"👤 User: {message.from_user.mention} (ID: {message.from_user.id})"
    
    await app.send_message(ADMIN_ID, f"📩 {user_info} botga quyidagi xabarni yubordi:\n{url}")
    
    if url.startswith("http"):
        await download_video(url, message)
    else:
        await message.reply("❌ Iltimos, to'g'ri havola yuboring!")

@app.on_message(filters.private & filters.reply & filters.user(ADMIN_ID))
async def reply_to_user(client, message):
    if message.reply_to_message:
        user_id_match = re.search(r'ID: (\d+)', message.reply_to_message.text)
        if user_id_match:
            user_id = int(user_id_match.group(1))
            await app.send_message(user_id, f"📩 Admin javobi:\n{message.text}")
            await message.reply("✅ Xabar foydalanuvchiga yuborildi.")
        else:
            await message.reply("⚠️ Ushbu xabarda foydalanuvchi ID topilmadi.")
    else:
        await message.reply("⚠️ Ushbu xabar orqali foydalanuvchini aniqlab bo‘lmadi.")

app.run()
