import json
import logging
import asyncio
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.types import ReplyKeyboardRemove, KeyboardButton, ReplyKeyboardMarkup, WebAppInfo
from aiohttp import web
import firebase_admin
from firebase_admin import credentials, firestore

# --- সেটিংস ---
API_TOKEN = '8799274180:AAGP9lLvWNWv4NsuL_B37iOKBDnnWlNOUp4'
MINI_APP_URL = 'https://newbogpostb.blogspot.com/?m=0'
ADMIN_ID = 8835355994 
BOT_USER = 'virul_link_bot'

# ফায়ারবেস ইনিশিয়ালাইজেশন (রেন্ডারের জন্য ফিক্সড)
if not firebase_admin._apps:
    # এখানে শুধুমাত্র প্রোজেক্ট আইডি দিয়ে শুরু করার চেষ্টা করা হচ্ছে
    firebase_admin.initialize_app(options={'projectId': 'virul-923ca'})

db = firestore.client()
logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

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
    await message.answer("✅ সফল!")

@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    db.collection("bot_users").document(str(message.chat.id)).set({"u": True}, merge=True)
    await message.answer("স্বাগতম! ভিডিও দেখতে মেনু বা বাটন ব্যবহার করুন।", reply_markup=ReplyKeyboardRemove())

# --- API সিস্টেম ---
async def unlock_api_handler(request):
    if request.method == "OPTIONS": return web.Response(status=200, headers={"Access-Control-Allow-Origin": "*", "Access-Control-Allow-Methods": "POST, OPTIONS", "Access-Control-Allow-Headers": "Content-Type"})
    try:
        data = await request.json()
        u_id, f_id, title, msg, prt, tmr = data.get("user_id"), data.get("file_id"), data.get("title"), data.get("msg"), data.get("protect"), data.get("timer")
        if u_id and f_id:
            for fid in f_id.split(","):
                cap = f"🎬 **{title}**\n\n{msg}"
                s = await bot.send_video(chat_id=u_id, video=fid, caption=cap, protect_content=prt)
                if tmr > 0: asyncio.create_task(delete_after(u_id, s.message_id, tmr))
            return web.json_response({"status": "ok"}, headers={"Access-Control-Allow-Origin": "*"})
    except: pass
    return web.json_response({"status": "error"}, status=500, headers={"Access-Control-Allow-Origin": "*"})

async def delete_after(c, m, t):
    await asyncio.sleep(t * 60)
    try: await bot.delete_message(c, m)
    except: pass

# --- Render Web Server (Port ফিক্স) ---
async def start_web_server():
    app = web.Application()
    app.router.add_get('/', lambda r: web.Response(text="Running"))
    app.router.add_post('/api/unlock', unlock_api_handler)
    app.router.add_options('/api/unlock', unlock_api_handler)
    runner = web.AppRunner(app)
    await runner.setup()
    # Render-এর দেওয়া PORT ব্যবহার করা হচ্ছে
    port = int(os.environ.get("PORT", 8080))
    await web.TCPSite(runner, '0.0.0.0', port).start()

@dp.message(F.video)
async def get_id(msg: types.Message): await msg.reply(f"ID: `{msg.video.file_id}`", parse_mode="Markdown")

async def main():
    await asyncio.gather(dp.start_polling(bot), start_web_server())

if __name__ == "__main__":
    asyncio.run(main())
