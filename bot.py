import json
import logging
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.types import ReplyKeyboardRemove, KeyboardButton, ReplyKeyboardMarkup, WebAppInfo
from aiohttp import web
import firebase_admin
from firebase_admin import credentials, firestore

# --- সেটিংস ---
API_TOKEN = '8799274180:AAGP9lLvWNWv4NsuL_B37iOKBDnnWlNOUp4'
MINI_APP_URL = 'https://newbogpostb.blogspot.com/?m=0'
ADMIN_ID = 8835355994  # আপনার টেলিগ্রাম আইডি
BOT_USER = 'virul_link_bot' # আপনার বটের ইউজারনেম

# ফায়ারবেস সেটআপ
if not firebase_admin._apps:
    cred = credentials.ApplicationDefault()
    firebase_admin.initialize_app(cred, {'projectId': 'virul-923ca'})

db = firestore.client()
logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# --- ব্রডকাস্ট সিস্টেম (/post কমান্ড) ---
# নিয়ম: /post ভিডিও_আইডি আপনার মেসেজ
# ছবির সাথে পাঠাতে চাইলে ছবি সিলেক্ট করে ক্যাপশনে উপরের মতো লিখুন
@dp.message(Command("post"))
async def cmd_broadcast(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return

    text_data = message.text or message.caption
    if not text_data:
        await message.answer("⚠️ নিয়ম: `/post ভিডিও_আইডি পোস্টের_টেক্সট` লিখে পাঠান।", parse_mode="Markdown")
        return

    args = text_data.replace("/post", "").strip().split(maxsplit=1)
    if len(args) < 2:
        await message.answer("⚠️ সঠিক ফরম্যাট: `/post 9FDW8UY মেসেজ বডি`", parse_mode="Markdown")
        return

    video_id = args[0]
    msg_body = args[1]
    
    # অ্যাপের ডাইরেক্ট লিঙ্ক তৈরি
    app_link = f"https://t.me/{BOT_USER}/app?startapp={video_id}"
    final_caption = f"{msg_body}\n\n🎬 **ফুল ভিডিও লিঙ্ক** 👇\n{app_link}"

    status_msg = await message.answer("⏳ ব্রডকাস্ট শুরু হচ্ছে...")
    users_ref = db.collection("bot_users").stream()
    count = 0

    for user in users_ref:
        try:
            if message.photo: # যদি ছবির সাথে পোস্ট করেন
                await bot.send_photo(chat_id=user.id, photo=message.photo[-1].file_id, caption=final_caption, parse_mode="Markdown")
            else: # শুধু টেক্সট পোস্ট হলে
                await bot.send_message(chat_id=user.id, text=final_caption, parse_mode="Markdown")
            count += 1
            await asyncio.sleep(0.05) # লিমিট এড়াতে
        except:
            continue

    await status_msg.edit_text(f"✅ সফল! {count} জন ইউজারের কাছে পোস্ট পাঠানো হয়েছে।")

# --- ইউজার আইডি সেভ করা (/start দিলে) ---
@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    user_id = str(message.chat.id)
    # ডাটাবেসে আইডি সেভ হচ্ছে যাতে পরে পোস্ট পাঠানো যায়
    db.collection("bot_users").document(user_id).set({
        "u": True,
        "name": message.from_user.full_name
    }, merge=True)
    
    await message.answer(
        "স্বাগতম! ভিডিও দেখতে সরাসরি মেনু বাটন থেকে অ্যাপটি ওপেন করুন।",
        reply_markup=ReplyKeyboardRemove()
    )

# --- API সিস্টেম (Mini App এর ভিডিও ডেলিভারি) ---
async def unlock_api_handler(request):
    if request.method == "OPTIONS":
        return web.Response(status=200, headers={"Access-Control-Allow-Origin": "*", "Access-Control-Allow-Methods": "POST, OPTIONS", "Access-Control-Allow-Headers": "Content-Type"})
    try:
        data = await request.json()
        user_id = data.get("user_id")
        master_file_id = data.get("file_id")
        title = data.get("title", "Video")
        msg = data.get("msg", "✅ আনলক সফল!")
        protect = data.get("protect", True)
        timer = data.get("timer", 0)

        if user_id and master_file_id:
            file_ids = master_file_id.split(",")
            for fid in file_ids:
                caption = f"🎬 **{title}**\n\n{msg}"
                sent = await bot.send_video(chat_id=user_id, video=fid, caption=caption, protect_content=protect)
                if timer > 0:
                    asyncio.create_task(delete_after(user_id, sent.message_id, timer))
                await asyncio.sleep(0.5)
            return web.json_response({"status": "ok"}, headers={"Access-Control-Allow-Origin": "*"})
    except Exception as e:
        return web.json_response({"status": "error", "error": str(e)}, status=500, headers={"Access-Control-Allow-Origin": "*"})

async def delete_after(chat, msg_id, mins):
    await asyncio.sleep(mins * 60)
    try: await bot.delete_message(chat, msg_id)
    except: pass

async def handle_alive(request): return web.Response(text="Bot Alive")

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', handle_alive)
    app.router.add_post('/api/unlock', unlock_api_handler)
    app.router.add_options('/api/unlock', unlock_api_handler)
    await web.TCPSite(web.AppRunner(app), '0.0.0.0', 8080).start()

@dp.message(F.video)
async def get_id(msg: types.Message):
    await msg.reply(f"ID: `{msg.video.file_id}`", parse_mode="Markdown")

async def main():
    await asyncio.gather(dp.start_polling(bot), start_web_server())

if __name__ == "__main__":
    asyncio.run(main())
