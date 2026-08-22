import json
import logging
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo, InputMediaPhoto
from aiohttp import web
import firebase_admin
from firebase_admin import credentials, firestore

# --- সেটিংস ---
API_TOKEN = '8799274180:AAGP9lLvWNWv4NsuL_B37iOKBDnnWlNOUp4'
MINI_APP_URL = 'https://newbogpostb.blogspot.com/?m=0'
ADMIN_ID = 8835355994  # আপনার নিজের টেলিগ্রাম আইডি দিন (আইডি পেতে @userinfobot এ মেসেজ দিন)
BOT_USER = 'virul_link_bot' # আপনার বটের ইউজারনেম (@ ছাড়া)

# ফায়ারবেস (এটি শুধু আইডিগুলো মনে রাখার জন্য, আপনাকে কিছু করতে হবে না)
if not firebase_admin._apps:
    cred = credentials.ApplicationDefault()
    firebase_admin.initialize_app(cred, {'projectId': 'virul-923ca'})

db = firestore.client()
logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# --- ব্রডকাস্ট সিস্টেম (আপনার স্ক্রিনশটের মতো পোস্ট করার জন্য) ---
# ব্যবহারের নিয়ম: ২-৩টি ছবি সিলেক্ট করুন, ক্যাপশনে লিখুন /post VideoID টাইটেল
@dp.message(Command("post"))
async def cmd_post(message: types.Message):
    if message.from_user.id != ADMIN_ID: return

    # কমান্ড থেকে তথ্য নেওয়া (উদা: /post 9FDW8 ভিডিও টাইটেল)
    args = message.text.replace("/post", "").strip().split(maxsplit=1)
    if len(args) < 2:
        await message.answer("⚠️ নিয়ম: `/post ভিডিও_আইডি পোস্টের_লেখা` লিখে ছবিসহ পাঠান।", parse_mode="Markdown")
        return

    v_id = args[0]
    caption_text = args[1]
    
    # ডাইনামিক লিঙ্ক তৈরি
    app_link = f"https://t.me/{BOT_USER}/?startapp={v_id}"
    
    final_caption = f"{caption_text}\n\n🎬 **ফুল ভিডিও লিঙ্ক** 👇\n{app_link}"

    # সব ইউজার আইডি আনা
    users = db.collection("bot_users").stream()
    count = 0

    for user in users:
        try:
            # একক ছবি বা শুধু টেক্সট হলে
            await bot.send_message(chat_id=user.id, text=final_caption, parse_mode="Markdown")
            count += 1
            await asyncio.sleep(0.05)
        except: continue

    await message.answer(f"✅ সফলভাবে {count} জন ইউজারের কাছে পোস্ট পাঠানো হয়েছে।")

# --- ইউজার আইডি অটো সেভ (যাতে বট জানে কাকে পাঠাতে হবে) ---
@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    db.collection("bot_users").document(str(message.chat.id)).set({"u": True})
    
    # নিচের বাটনটি স্ক্রিনশটের মতো সেট করা
    kb = [[KeyboardButton(text="ভিডিও দেখুন 🥵", web_app=WebAppInfo(url=MINI_APP_URL))]]
    await message.answer(
        "স্বাগতম! ভিডিও দেখতে সরাসরি নিচের বাটন থেকে অ্যাপটি ওপেন করুন।",
        reply_markup=ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    )

# --- বাকি API এবং লজিক (আগের মতো) ---
async def unlock_api_handler(request):
    try:
        data = await request.json()
        u_id, f_id, title, msg, prt, tmr = data.get("user_id"), data.get("file_id"), data.get("title"), data.get("msg"), data.get("protect"), data.get("timer")
        if u_id and f_id:
            ids = f_id.split(",")
            for fid in ids:
                cap = f"🎬 **{title}**\n\n{msg}"
                if tmr > 0: cap += f"\n\n⏰ ডিলিট হবে {tmr} মিনিট পর।"
                s = await bot.send_video(chat_id=u_id, video=fid, caption=cap, protect_content=prt)
                if tmr > 0: asyncio.create_task(delete_after(u_id, s.message_id, tmr))
                await asyncio.sleep(0.5)
            return web.json_response({"status": "ok"}, headers={"Access-Control-Allow-Origin": "*"})
    except: pass
    return web.json_response({"status": "error"}, status=500, headers={"Access-Control-Allow-Origin": "*"})

async def delete_after(c, m, t):
    await asyncio.sleep(t * 60)
    try: await bot.delete_message(c, m)
    except: pass

async def start_web_server():
    app = web.Application()
    app.router.add_post('/api/unlock', unlock_api_handler)
    app.router.add_options('/api/unlock', lambda r: web.Response(headers={"Access-Control-Allow-Origin": "*", "Access-Control-Allow-Methods": "POST, OPTIONS", "Access-Control-Allow-Headers": "Content-Type"}))
    await web.TCPSite(web.AppRunner(app), '0.0.0.0', 8080).start()

@dp.message(F.video)
async def get_id(msg: types.Message):
    await msg.reply(f"ID: `{msg.video.file_id}`", parse_mode="Markdown")

async def main():
    await asyncio.gather(dp.start_polling(bot), start_web_server())

if __name__ == "__main__":
    asyncio.run(main())
