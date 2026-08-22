import json
import logging
import asyncio
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.types import ReplyKeyboardRemove
from aiohttp import web
import firebase_admin
from firebase_admin import credentials, firestore

# --- সেটিংস ---
API_TOKEN = '8799274180:AAGP9lLvWNWv4NsuL_B37iOKBDnnWlNOUp4'
MINI_APP_URL = 'https://newbogpostb.blogspot.com/?m=0'
ADMIN_ID = 8835355994 
BOT_USER = 'virul_link_bot'

# লগিং সেটআপ
logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# --- ফায়ারবেস ফিক্সড কানেকশন ---
try:
    if not firebase_admin._apps:
        # শুধুমাত্র প্রোজেক্ট আইডি দিয়ে রেন্ডারে কানেক্ট করার জন্য এটিই বেস্ট
        firebase_admin.initialize_app(options={'projectId': 'virul-923ca'})
    db = firestore.client()
    logging.info("✅ Firebase Connected Successfully!")
except Exception as e:
    logging.error(f"❌ Firebase Connection Error: {e}")

# --- ব্রডকাস্ট সিস্টেম ---
@dp.message(Command("post"))
async def cmd_broadcast(message: types.Message):
    if message.from_user.id != ADMIN_ID: return
    text_data = message.text or message.caption
    if not text_data: return
    args = text_data.replace("/post", "").strip().split(maxsplit=1)
    if len(args) < 2: return
    video_id, msg_body = args[0], args[1]
    app_link = f"https://t.me/{BOT_USER}/app?startapp={video_id}"
    final_caption = f"{msg_body}\n\n🎬 **ফুল ভিডিও লিঙ্ক** 👇\n{app_link}"
    
    users_ref = db.collection("bot_users").stream()
    for user in users_ref:
        try:
            if message.photo: await bot.send_photo(chat_id=user.id, photo=message.photo[-1].file_id, caption=final_caption, parse_mode="Markdown")
            else: await bot.send_message(chat_id=user.id, text=final_caption, parse_mode="Markdown")
            await asyncio.sleep(0.05)
        except: continue
    await message.answer("✅ ব্রডকাস্ট সফল!")

@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    # ইউজার আইডি সেভ করা
    try:
        db.collection("bot_users").document(str(message.chat.id)).set({"u": True}, merge=True)
    except: pass
    await message.answer("স্বাগতম! ভিডিও দেখতে সরাসরি মেনু বাটন থেকে অ্যাপটি ওপেন করুন।", reply_markup=ReplyKeyboardRemove())

# --- API সিস্টেম ---
async def unlock_api_handler(request):
    try:
        data = await request.json()
        u_id, f_id, title, msg, prt, tmr = data.get("user_id"), data.get("file_id"), data.get("title"), data.get("msg"), data.get("protect"), data.get("timer")
        if u_id and f_id:
            for fid in f_id.split(","):
                cap = f"🎬 **{title}**\n\n{msg}"
                s = await bot.send_video(chat_id=u_id, video=fid, caption=cap, protect_content=prt)
                if tmr and int(tmr) > 0: asyncio.create_task(delete_after(u_id, s.message_id, int(tmr)))
            return web.json_response({"status": "ok"}, headers={"Access-Control-Allow-Origin": "*"})
    except Exception as e:
        logging.error(f"API Error: {e}")
    return web.json_response({"status": "error"}, headers={"Access-Control-Allow-Origin": "*"})

async def delete_after(c, m, t):
    await asyncio.sleep(t * 60)
    try: await bot.delete_message(c, m)
    except: pass

@dp.message(F.video)
async def get_id(msg: types.Message): await msg.reply(f"ID: `{msg.video.file_id}`", parse_mode="Markdown")

# --- Render Web Server (এটির কারণে Port Error আসছিল) ---
async def start_web_server():
    app = web.Application()
    app.router.add_get('/', lambda r: web.Response(text="Bot is Running"))
    app.router.add_post('/api/unlock', unlock_api_handler)
    app.router.add_options('/api/unlock', lambda r: web.Response(headers={"Access-Control-Allow-Origin": "*", "Access-Control-Allow-Methods": "POST, OPTIONS", "Access-Control-Allow-Headers": "Content-Type"}))
    
    runner = web.AppRunner(app)
    await runner.setup()
    # Render-এর জন্য এই পোর্ট বাইন্ডিংটা সবচেয়ে জরুরি
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    logging.info(f"✅ Web Server started on port {port}")

async def main():
    # বট এবং ওয়েব সার্ভার একসাথে চালু করা
    server_task = asyncio.create_task(start_web_server())
    bot_task = asyncio.create_task(dp.start_polling(bot))
    await asyncio.gather(server_task, bot_task)

if __name__ == "__main__":
    asyncio.run(main())
