import json
import logging
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
from aiohttp import web

# --- সেটিংস ---
API_TOKEN = '8799274180:AAGP9lLvWNWv4NsuL_B37iOKBDnnWlNOUp4' 
MINI_APP_URL = 'https://newbogpostb.blogspot.com/?m=0'

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Render Web Server
async def handle(request): return web.Response(text="Bot Alive")
async def start_web_server():
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, '0.0.0.0', 8080).start()

# /start কমান্ড
@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    kb = [[KeyboardButton(text="🚀 Open Viral App", web_app=WebAppInfo(url=MINI_APP_URL))]]
    await message.answer("ভিডিও আনলক করতে নিচের বাটনে ক্লিক করুন:", reply_markup=ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True))

# --- নতুন ফিচার: ভিডিও পাঠালে File ID দিবে ---
@dp.message(F.video)
async def get_video_file_id(message: types.Message):
    file_id = message.video.file_id
    await message.reply(f"✅ এই ভিডিওর সঠিক File ID নিচে দেওয়া হলো। এটি কপি করে অ্যাডমিন প্যানেলে বসান:\n\n`{file_id}`", parse_mode="Markdown")

# Mini App ডাটা হ্যান্ডলার
@dp.message(F.web_app_data)
async def handle_webapp_data(message: types.Message):
    try:
        data = json.loads(message.web_app_data.data)
        if data.get("action") == "send_video":
            file_id = data.get("file_id")
            # ভিডিও সেন্ড করার চেষ্টা
            await bot.send_video(chat_id=message.chat.id, video=file_id, caption="✅ ভিডিও আনলক সফল!")
    except Exception as e:
        await message.answer(f"⚠️ ভুল File ID ব্যবহার করা হয়েছে!\nসার্ভার মেসেজ: {e}")

async def main():
    await asyncio.gather(dp.start_polling(bot), start_web_server())

if __name__ == "__main__":
    asyncio.run(main())
