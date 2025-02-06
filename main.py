import os
import time
import asyncio
import subprocess
from pyrogram import Client, filters
from yt_dlp import YoutubeDL
import re

# Telegram bot sozlamalari
API_ID = "22437042"
API_HASH = "95b6e9f809983d4990af5a4f60c51652"
BOT_TOKEN = "6693824512:AAHdjkrF0mqVdUHgeBmb3_qPLfa7CzjKxYM"
ADMIN_ID = 5510219247

app = Client("video_downloader_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# FFmpeg yordamida metadata yangilash funksiyasi
def fix_video_metadata(video_path):
    fixed_video_path = f"fixed_{os.path.basename(video_path)}"
    command = [
        "ffmpeg",
        "-i", video_path,
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "28",
        "-c:a", "aac",
        "-movflags", "+faststart",
        fixed_video_path
    ]
    subprocess.run(command, check=True)
    return fixed_video_path

# Yuklab olish uchun funksiyalar
async def download_video(url, message):
    temp_dir = "downloads"
    os.makedirs(temp_dir, exist_ok=True)
    
    ydl_opts = {
        'outtmpl': f'{temp_dir}/%(title)s.%(ext)s',
        'format': 'best',
        'cookiefile': 'cookies.txt'  # <-- COOKIES YO‘LNI KO‘SHING
    }
    
    msg = await message.reply("\ud83d\udce5 Yuklab olinmoqda...")
    status_msg_id = msg.id
    
    def progress_hook(d):
        if d['status'] == 'downloading':
            percent = d.get('percentage', 0)
            asyncio.create_task(message.edit(f"\u23f3 Yuklanmoqda: {percent:.2f}%"))

    ydl_opts['progress_hooks'] = [progress_hook]
    
    video_path = None  # Fayl yo‘lini aniqlash uchun
    
    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            video_path = ydl.prepare_filename(info)
        
        if not os.path.exists(video_path):
            raise Exception("\u274c Yuklab olishda xatolik yuz berdi, fayl topilmadi!")
        
        # FFmpeg yordamida metadata'ni to'g'rilash
        fixed_video_path = fix_video_metadata(video_path)
        
        caption = "\u2705 Shunchaki foydalaning\n\n@shoxsan_bot"
        user_info = f"\ud83d\udc64 User: {message.from_user.mention} (ID: {message.from_user.id})"
        
        # Foydalanuvchiga video yuborish
        await message.reply_video(video=fixed_video_path, caption=caption)
        
        # Admin uchun video yuborish
        admin_msg = await app.send_message(ADMIN_ID, f"\ud83d\udce9 Yangi video yuklandi!\n{user_info}\n\ud83d\udd17 {url}")
        await app.send_video(ADMIN_ID, video=fixed_video_path, caption=user_info, reply_to_message_id=admin_msg.id)
    
    except Exception as e:
        error_message = f"\u274c Xatolik yuz berdi: {str(e)}"
        await message.reply(error_message)
        await app.send_message(ADMIN_ID, f"\u26a0\ufe0f Xatolik yuz berdi!\n\ud83d\udd17 {url}\n\u274c {str(e)}")

    finally:
        # Fayl mavjud bo‘lsa, uni o‘chirish
        if video_path and os.path.exists(video_path):
            os.remove(video_path)
        if fixed_video_path and os.path.exists(fixed_video_path):
            os.remove(fixed_video_path)
    
    await message.delete()  # Eski xabarlarni tozalash
    await app.delete_messages(message.chat.id, status_msg_id)


@app.on_message(filters.private & filters.command("start"))
async def start_command(client, message):
    await message.reply("\ud83d\udc4b Salom! Menga video havolasini yuboring, men uni yuklab beraman.")

@app.on_message(filters.private & filters.text & ~filters.user(ADMIN_ID))
async def handle_message(client, message):
    url = message.text.strip()
    user_info = f"\ud83d\udc64 User: {message.from_user.mention} (ID: {message.from_user.id})"
    
    # Adminga foydalanuvchi xabarini yuborish
    admin_msg = await app.send_message(ADMIN_ID, f"\ud83d\udce9 {user_info} botga quyidagi xabarni yubordi:\n{url}")
    
    if url.startswith("http"):
        await message.delete()
        await download_video(url, message)
    else:
        error_message = "\u274c Iltimos, to'g'ri havola yuboring!"
        await message.reply(error_message)
        await app.send_message(ADMIN_ID, f"\u26a0\ufe0f Xatolik! {user_info} noto‘g‘ri havola yubordi: {url}")

@app.on_message(filters.private & filters.reply & filters.user(ADMIN_ID))
async def reply_to_user(client, message):
    if message.reply_to_message:
        user_id_match = re.search(r'ID: (\d+)', message.reply_to_message.text)
        if user_id_match:
            user_id = int(user_id_match.group(1))
            await app.send_message(user_id, f"\ud83d\udce9 Admin javobi:\n{message.text}")
            await message.reply("\u2705 Xabar foydalanuvchiga yuborildi.")
        else:
            await message.reply("\u26a0\ufe0f Ushbu xabarda foydalanuvchi ID topilmadi.")
    else:
        await message.reply("\u26a0\ufe0f Ushbu xabar orqali foydalanuvchini aniqlab bo‘lmadi.")

app.run()
