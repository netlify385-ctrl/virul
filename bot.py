import json
import logging
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
from aiohttp import web

# --- সেটিংস ---
API_TOKEN = '8799274180:AAGP9lLvWNWv4NsuL_B37iOKBDnnWlNOUp4'  # BotFather থেকে পাওয়া টোকেন
MINI_APP_URL = 'https://newbogpostb.blogspot.com/?m=0' # আপনার Mini App লিঙ্ক

# লগিং সেটআপ (Render-এর Logs-এ সব দেখতে পাবেন)
logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Render-এর জন্য Web Server (জাগিয়ে রাখার জন্য)
async def handle(request):
    return web.Response(text="Bot is Alive!")

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8080)
    await site.start()

# /start কমান্ড
@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    kb = [[KeyboardButton(text="🚀 Open Viral App", web_app=WebAppInfo(url=MINI_APP_URL))]]
    keyboard = ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    await message.answer(
        f"স্বাগতম {message.from_user.first_name}!\nভিডিও আনলক করতে নিচের বাটনে ক্লিক করুন:",
        reply_markup=keyboard
    )

# Mini App থেকে আসা ডাটা প্রসেস করার উন্নত লজিক
@dp.message(F.web_app_data)
async def handle_webapp_data(message: types.Message):
    logging.info(f"Received Data from App: {message.web_app_data.data}")
    
    try:
        # JSON ডাটা রিসিভ করা
        raw_data = message.web_app_data.data
        data = json.loads(raw_data)
        
        if data.get("action") == "send_video":
            file_id = data.get("file_id")
            
            if file_id:
                logging.info(f"Attempting to send video with File ID: {file_id}")
                # ইউজারকে ভিডিও সেন্ড করা
                await bot.send_video(
                    chat_id=message.chat.id,
                    video=file_id,
                    caption="✅ **আপনার ভিডিওটি আনলক হয়েছে!**"
                )
            else:
                await message.answer("❌ ভিডিওর File ID পাওয়া যায়নি।")
                
    except Exception as e:
        logging.error(f"Error sending video: {e}")
        await message.answer(f"⚠️ ভিডিও পাঠাতে সমস্যা হয়েছে। ভুল: {e}")

async def main():
    logging.info("Starting bot...")
    # বট এবং সার্ভার একসাথে রান করা
    await asyncio.gather(dp.start_polling(bot), start_web_server())

if __name__ == "__main__":
    asyncio.run(main())
