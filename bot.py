import json
import logging
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.types import ReplyKeyboardRemove
from aiohttp import web

# --- সেটিংস ---
API_TOKEN = '8799274180:AAHf2hgnuNr0PkpA-mErZnp0jiEYIm8Nsjc'

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# --- ভিডিও অটো ডিলিট লজিক ---
async def delete_after(chat_id, message_id, minutes):
    await asyncio.sleep(minutes * 60)
    try:
        await bot.delete_message(chat_id, message_id)
    except:
        pass

# --- API সিস্টেম (CORS ফিক্সড) ---
async def unlock_api_handler(request):
    # CORS প্রি-ফ্লাইট রিকোয়েস্ট হ্যান্ডেল করা
    if request.method == "OPTIONS":
        return web.Response(status=200, headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type",
        })

    try:
        data = await request.json()
        user_id = data.get("user_id")
        file_id = data.get("file_id")
        title = data.get("title", "Viral Video")
        msg = data.get("msg", "✅ ভিডিও আনলক সফল!")
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
                
            return web.json_response({"status": "ok"}, headers={"Access-Control-Allow-Origin": "*"})
        
        return web.json_response({"status": "error", "message": "Data Missing"}, status=400, headers={"Access-Control-Allow-Origin": "*"})
    except Exception as e:
        logging.error(f"API Error: {e}")
        return web.json_response({"status": "error", "error": str(e)}, status=500, headers={"Access-Control-Allow-Origin": "*"})

async def handle_alive(request):
    return web.Response(text="Bot is Running")

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', handle_alive)
    app.router.add_post('/api/unlock', unlock_api_handler)
    app.router.add_options('/api/unlock', unlock_api_handler) # OPTIONS রিকোয়েস্টের জন্য
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, '0.0.0.0', 8080).start()

# /start কমান্ড (বাটন রিমুভ করা হয়েছে)
@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    # ReplyKeyboardRemove() দিয়ে আগের বাটনগুলো মুছে ফেলা হয়েছে
    await message.answer(
        "স্বাগতম! ভিডিও দেখতে সরাসরি মেনু বাটন থেকে অ্যাপটি ওপেন করুন।",
        reply_markup=ReplyKeyboardRemove()
    )

# File ID সংগ্রহকারী
@dp.message(F.video)
async def get_id(msg: types.Message):
    await msg.reply(f"✅ Video File ID:\n\n`{msg.video.file_id}`", parse_mode="Markdown")

async def main():
    await asyncio.gather(dp.start_polling(bot), start_web_server())

if __name__ == "__main__":
    asyncio.run(main())
