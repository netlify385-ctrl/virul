import json
import logging
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
from aiohttp import web

# --- সেটিংস ---
API_TOKEN = '8799274180:AAGP9lLvWNWv4NsuL_B37iOKBDnnWlNOUp4'
MINI_APP_URL = 'https://newbogpostb.blogspot.com'

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# --- Render-এর জন্য Dummy Web Server ---
async def handle(request):
    return web.Response(text="Bot is Running!")

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8080)
    await site.start()

# --- বট লজিক ---
@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    kb = [[KeyboardButton(text="🚀 Open Viral App", web_app=WebAppInfo(url=MINI_APP_URL))]]
    keyboard = ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    await message.answer("ভিডিও আনলক করতে নিচের বাটনে ক্লিক করুন:", reply_markup=keyboard)

@dp.message(F.web_app_data)
async def handle_webapp_data(message: types.Message):
    try:
        data = json.loads(message.web_app_data.data)
        if data.get("action") == "send_video":
            file_id = data.get("file_id")
            await bot.send_video(chat_id=message.chat.id, video=file_id, caption="✅ আনলক সফল হয়েছে!")
    except Exception as e:
        logging.error(f"Error: {e}")

async def main():
    # বট এবং ওয়েব সার্ভার একসাথে চালানো
    await asyncio.gather(dp.start_polling(bot), start_web_server())

if __name__ == "__main__":
    asyncio.run(main())