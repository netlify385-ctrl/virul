import json
import logging
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.types import ReplyKeyboardRemove
from aiohttp import web

# --- সেটিংস ---
API_TOKEN = '8799274180:AAGP9lLvWNWv4NsuL_B37iOKBDnnWlNOUp4'

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# গ্লোবাল ডিকশনারি গ্রুপ ভিডিও প্রসেসিং এর জন্য
album_cache = {}

# --- ভিডিও আইডি কালেক্টর লজিক ---
@dp.message(F.video)
async def handle_video_input(message: types.Message):
    # যদি ভিডিওটি অ্যালবামের (Group) অংশ হয়
    if message.media_group_id:
        gid = message.media_group_id
        if gid not in album_cache:
            album_cache[gid] = []
            asyncio.create_task(process_group_ids(message.chat.id, gid))
        
        album_cache[gid].append(message.video.file_id)
        return

    # যদি সিঙ্গেল ভিডিও হয়
    await message.reply(f"✅ **Single Video ID:**\n\n`{message.video.file_id}`", parse_mode="Markdown")

# গ্রুপ ভিডিওকে একটি মাস্টার আইডিতে রূপান্তর করার ফাংশন
async def process_group_ids(chat_id, gid):
    await asyncio.sleep(2) # সব ভিডিও রিসিভ করার জন্য সময়
    if gid in album_cache:
        ids = album_cache[gid]
        # সব আইডিকে কমা (,) দিয়ে জোড়া লাগিয়ে একটি মাস্টার আইডি তৈরি
        master_id = ",".join(ids)
        
        response = f"📦 **Group Video Pack Created!**\n\nনিচে এই গ্রুপের জন্য একটি **Master ID** দেওয়া হলো। এটি কপি করে অ্যাডমিন প্যানেলে 'File ID' বক্সে বসান। ইউজার আনলক করলে এই গ্রুপের {len(ids)}টি ভিডিওই পেয়ে যাবে।\n\n`{master_id}`"
        
        await bot.send_message(chat_id, response, parse_mode="Markdown")
        del album_cache[gid]

# --- API সিস্টেম (মাল্টি-ভিডিও সাপোর্ট সহ) ---
async def unlock_api_handler(request):
    if request.method == "OPTIONS":
        return web.Response(status=200, headers={"Access-Control-Allow-Origin": "*", "Access-Control-Allow-Methods": "POST, OPTIONS", "Access-Control-Allow-Headers": "Content-Type"})
    
    try:
        data = await request.json()
        user_id = data.get("user_id")
        master_file_id = data.get("file_id") # এটি সিঙ্গেল আইডি বা কমা দেওয়া মাস্টার আইডি হতে পারে
        title = data.get("title", "Premium Video")
        msg = data.get("msg", "✅ ভিডিও আনলক সফল!")
        protect = data.get("protect", True)
        timer = data.get("timer", 0)

        if user_id and master_file_id:
            # চেক করা হচ্ছে এটি কি মাস্টার আইডি (গ্রুপ)?
            file_ids = master_file_id.split(",")
            
            # ইউজারকে ভিডিও পাঠানো (লুপের মাধ্যমে)
            for i, fid in enumerate(file_ids):
                # প্রথম ভিডিওর সাথে টাইটেল এবং মেসেজ যাবে
                caption = f"🎬 **{title}** (Part {i+1})\n\n{msg}" if len(file_ids) > 1 else f"🎬 **{title}**\n\n{msg}"
                
                sent = await bot.send_video(
                    chat_id=user_id, 
                    video=fid, 
                    caption=caption, 
                    
                    protect_content=protect
                )
                
                # অটো ডিলিট সেট করা থাকলে
                if timer > 0:
                    asyncio.create_task(delete_after(user_id, sent.message_id, timer))
                
                # এক ভিডিও থেকে অন্য ভিডিও পাঠানোর মাঝে ছোট বিরতি (টেলিগ্রাম লিমিট এড়াতে)
                await asyncio.sleep(0.5)

            return web.json_response({"status": "ok"}, headers={"Access-Control-Allow-Origin": "*"})
    except Exception as e:
        return web.json_response({"status": "error", "error": str(e)}, status=500, headers={"Access-Control-Allow-Origin": "*"})

async def delete_after(chat, msg_id, mins):
    await asyncio.sleep(mins * 60)
    try: await bot.delete_message(chat, msg_id)
    except: pass

async def handle_alive(request): return web.Response(text="Bot is Active")

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', handle_alive)
    app.router.add_post('/api/unlock', unlock_api_handler)
    app.router.add_options('/api/unlock', unlock_api_handler)
    await web.TCPSite(web.AppRunner(app), '0.0.0.0', 8080).start()

@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    await message.answer("স্বাগতম! ভিডিও দেখতে মেনু বাটন থেকে অ্যাপ ওপেন করুন।", reply_markup=ReplyKeyboardRemove())

async def main():
    await asyncio.gather(dp.start_polling(bot), start_web_server())

if __name__ == "__main__":
    asyncio.run(main())
