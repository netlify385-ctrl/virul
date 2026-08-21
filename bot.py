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
async def handle(request): return web.Response(text="Bot is Active")
async def start_web_server():
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, '0.0.0.0', 8080).start()

@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    kb = [[KeyboardButton(text="🚀 Open Viral App", web_app=WebAppInfo(url=MINI_APP_URL))]]
    await message.answer("ভিডিও আনলক করতে নিচের বাটনে ক্লিক করুন:", reply_markup=ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True))

@dp.message(F.video)
async def get_id(msg: types.Message):
    await msg.reply(f"File ID: `{msg.video.file_id}`", parse_mode="Markdown")

# --- ডিলিট ফাংশন ---
async def delete_after(chat_id, message_id, minutes):
    await asyncio.sleep(minutes * 60)
    try:
        await bot.delete_message(chat_id, message_id)
    except:
        pass

# --- Mini App ডাটা রিসিভার ---
@dp.message(F.web_app_data)
async def handle_webapp_data(message: types.Message):
    try:
        data = json.loads(message.web_app_data.data)
        
        if data.get("action") == "send_video":
            file_id = data.get("file_id")
            video_title = data.get("video_title", "Viral Video")
            success_msg = data.get("custom_message", "✅ ভিডিও আনলক সফল!")
            protect = data.get("protect_content", True)
            del_timer = data.get("delete_timer", 0) # মিনিটে
            
            final_caption = f"🎬 **{video_title}**\n\n{success_msg}"
            if del_timer > 0:
                final_caption += f"\n\n⏰ এই ভিডিওটি {del_timer} মিনিট পর অটো ডিলিট হয়ে যাবে।"

            sent_msg = await bot.send_video(
                chat_id=message.chat.id, 
                video=file_id, 
                caption=final_caption, 
                
                protect_content=protect
            )
            
            # যদি টাইম সেট করা থাকে তবে ডিলিট শিডিউল হবে
            if del_timer > 0:
                asyncio.create_task(delete_after(message.chat.id, sent_msg.message_id, del_timer))
                
            logging.info(f"Video '{video_title}' sent to {message.chat.id}")
            
    except Exception as e:
        logging.error(f"Error: {e}")
        await message.answer(f"⚠️ সমস্যা হয়েছে! ভিডিওর File ID চেক করুন।")

async def main():
    await asyncio.gather(dp.start_polling(bot), start_web_server())

if __name__ == "__main__":
    asyncio.run(main())
