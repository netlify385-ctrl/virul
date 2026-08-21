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

# --- ভিডিও অটো ডিলিট ফাংশন ---
async def delete_after(chat_id, message_id, minutes):
    await asyncio.sleep(minutes * 60)
    try:
        await bot.delete_message(chat_id, message_id)
        logging.info(f"Message {message_id} deleted in {chat_id}")
    except:
        pass

# --- মেনু বাটন সাপোর্ট করার জন্য API সিস্টেম ---
async def unlock_api_handler(request):
    try:
        data = await request.json()
        user_id = data.get("user_id")
        file_id = data.get("file_id")
        title = data.get("title", "Viral Video")
        msg = data.get("msg", "✅ আনলক সফল!")
        protect = data.get("protect", True)
        timer = data.get("timer", 0)

        if user_id and file_id:
            caption = f"🎬 **{title}**\n\n{msg}"
            if timer > 0:
                caption += f"\n\n⏰ এই ভিডিওটি {timer} মিনিট পর অটো ডিলিট হয়ে যাবে।"

            sent = await bot.send_video(
                chat_id=user_id, 
                video=file_id, 
                caption=caption, 
                
                protect_content=protect
            )
            
            if timer > 0:
                asyncio.create_task(delete_after(user_id, sent.message_id, timer))
                
            return web.json_response({"status": "ok"})
        return web.json_response({"status": "error", "message": "Missing Data"})
    except Exception as e:
        return web.json_response({"status": "error", "error": str(e)})

async def handle_alive(request): return web.Response(text="Bot is Running")

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', handle_alive)
    app.router.add_post('/api/unlock', unlock_api_handler)
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, '0.0.0.0', 8080).start()

@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    await message.answer("স্বাগতম! ভিডিও দেখতে মেনু বাটন বা নিচের বাটন থেকে অ্যাপ ওপেন করুন।", 
    reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="Watch 📺", web_app=WebAppInfo(url=MINI_APP_URL))]], resize_keyboard=True))

@dp.message(F.video)
async def get_id(msg: types.Message):
    await msg.reply(f"✅ Correct File ID:\n\n`{msg.video.file_id}`", parse_mode="Markdown")

async def main():
    await asyncio.gather(dp.start_polling(bot), start_web_server())

if __name__ == "__main__":
    asyncio.run(main())
