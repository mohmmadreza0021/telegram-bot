import sqlite3
import asyncio
import uuid
import os
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage

# دریافت مقادیر از متغیرهای محیطی
TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")

# اتصال به دیتابیس
conn = sqlite3.connect("texts.db")
cursor = conn.cursor()
cursor.execute("""
    CREATE TABLE IF NOT EXISTS texts (
        id TEXT PRIMARY KEY,
        content TEXT
    )
""")
conn.commit()

# تنظیمات ربات
bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# بررسی عضویت در کانال
async def is_subscribed(user_id):
    try:
        chat_member = await bot.get_chat_member(CHANNEL_ID, user_id)
        return chat_member.status in ['member', 'administrator', 'creator']
    except Exception:
        return False

# دستور `/start`
@dp.message(Command("start"))
async def start_command(message: types.Message):
    user_id = message.from_user.id
    args = message.text.split(" ")[1:] if len(message.text.split(" ")) > 1 else []

    if args:
        return await send_text(message, args[0])

    if not await is_subscribed(user_id):
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ عضویت در کانال", url=f"https://t.me/{CHANNEL_ID[1:]}")]
        ])
        return await message.answer("📢 لطفاً ابتدا در کانال عضو شوید.", reply_markup=keyboard)

    await message.answer("✅ خوش آمدید! از ربات استفاده کنید.")

# ارسال متن ذخیره شده
async def send_text(message: types.Message, text_id):
    user_id = message.from_user.id

    if not await is_subscribed(user_id):
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ عضویت در کانال", url=f"https://t.me/{CHANNEL_ID[1:]}")]
        ])
        return await message.answer("📢 لطفاً ابتدا در کانال عضو شوید.", reply_markup=keyboard)

    cursor.execute("SELECT content FROM texts WHERE id = ?", (text_id,))
    row = cursor.fetchone()
    if row:
        text_content = row[0]
        sent_message = await message.answer(text_content)

        await asyncio.sleep(30)
        await bot.delete_message(chat_id=message.chat.id, message_id=sent_message.message_id)
        await message.answer("⏳ متن حذف شد! لطفاً قبل از حذف، آن را ذخیره کنید.")
    else:
        await message.answer("⛔ متن یافت نشد یا حذف شده است.")

# افزودن متن توسط ادمین
@dp.message(Command("add"))
async def add_text(message: types.Message):
    if message.from_user.id != 5226795399:  # آیدی تلگرام خودت رو اینجا بذار
        return await message.answer("⛔ شما اجازه افزودن متن را ندارید.")

    text_content = message.text.replace("/add", "").strip()
    if not text_content:
        return await message.answer("📌 لطفاً متن را بعد از دستور ارسال کنید.")

    text_id = str(uuid.uuid4())[:8]
    cursor.execute("INSERT INTO texts (id, content) VALUES (?, ?)", (text_id, text_content))
    conn.commit()

    link = f"https://t.me/YourBot?start={text_id}"
    await message.answer(f"✅ متن ذخیره شد!\n\n🔗 لینک: {link}")

# اجرای ربات با asyncio
async def main():
    print("✅ Bot is running...")

    # حذف Webhook برای جلوگیری از Conflict
    await bot.delete_webhook(drop_pending_updates=True)

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
