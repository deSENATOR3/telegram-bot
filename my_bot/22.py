import asyncio
import nest_asyncio
nest_asyncio.apply()

import pandas as pd
from datetime import datetime, timedelta
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# 🔹 Bot tokeningizni shu yerga yozing
import os
BOT_TOKEN = os.getenv("8020408213:AAGs4JiNp_fmUfT1qHyklaQfT0Lfv2nTYww")


# 🔹 Excel fayl manzili
EXCEL_PATH = "jadval.xlsx"

# 🔹 Foydalanuvchining holatini saqlash uchun
user_data = {}


# 🔸 /start komandasi
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    user_name = update.message.from_user.first_name or "Foydalanuvchi"
    
    keyboard = [
        [InlineKeyboardButton("🎓 Guruhni tanlang", callback_data="select_group")],
        [InlineKeyboardButton("ℹ️ Ma'lumot", callback_data="info")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"👋 Salom, {user_name}! 🎉\n\n"
        f"Bu bot sizga dars jadvalini ko'rsatadi.\n"
        f"Boshlash uchun guruhni tanlang.",
        reply_markup=reply_markup,
    )


# 🔸 Tugma bosilganda — "Guruhni tanlang"
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "select_group":
        await query.message.reply_text(
            "✍️ Iltimos, guruh nomini kiriting.\n"
            "Masalan: 45-22 E va A"
        )
    elif query.data == "info":
        await query.message.reply_text(
            "ℹ️ **Bot haqida:**\n\n"
            "Bu bot sizning dars jadvalingizni ko'rsatadi.\n"
            "Guruhingizni kiriting va kerakli kunni tanlang.\n\n"
            "📚 Bugungi va ertangi darslarni ko'rishingiz mumkin.",
            parse_mode="Markdown"
        )


# 🔸 Foydalanuvchi guruh nomini yozganda
async def group_entered(update: Update, context: ContextTypes.DEFAULT_TYPE):
    group_name = update.message.text.strip()
    user_id = update.message.from_user.id
    user_data[user_id] = {"group": group_name}

    keyboard = [
        [
            InlineKeyboardButton("📅 Bugun", callback_data="today"),
            InlineKeyboardButton("📆 Ertaga", callback_data="tomorrow"),
        ],
        [InlineKeyboardButton("🔄 Guruhni o'zgartirish", callback_data="select_group")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"✅ Guruh: *{group_name}*\n\nEndi kunni tanlang:",
        parse_mode="Markdown",
        reply_markup=reply_markup,
    )


# 🔸 Jadvalni chiqarish
async def show_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    if user_id not in user_data or "group" not in user_data[user_id]:
        await query.message.reply_text("⚠️ Avval guruhni kiriting!")
        return

    group_name = user_data[user_id]["group"]

    # Sana tanlovini aniqlaymiz
    if query.data == "today":
        date = datetime.now()
        title = "📅 Bugungi jadval"
    else:
        date = datetime.now() + timedelta(days=1)
        title = "📆 Ertangi jadval"

    kun_uz = date.strftime("%A")
    kun_uz = (
        kun_uz.replace("Monday", "Dushanba")
        .replace("Tuesday", "Seshanba")
        .replace("Wednesday", "Chorshanba")
        .replace("Thursday", "Payshanba")
        .replace("Friday", "Juma")
        .replace("Saturday", "Shanba")
        .replace("Sunday", "Yakshanba")
    )

    sana = date.strftime("%d-%B")
    full_title = f"{title}\n\n📅 {kun_uz}, {sana}\n\n"

    try:
        df = pd.read_excel(EXCEL_PATH)

        expected_columns = ["Kun", "Vaqt", "Fan", "Turi", "Guruh", "Joy", "O'qituvchi"]
        if not all(col in df.columns for col in expected_columns):
            await query.message.reply_text("❌ Excel fayl formati noto'g'ri!")
            return

        # Faqat shu kun va shu guruhdagi darslarni olish
        jadval = df[
            (df["Kun"].str.lower() == kun_uz.lower())
            & (df["Guruh"].str.contains(group_name, case=False, na=False))
        ]

        if jadval.empty:
            await query.message.reply_text(f"📭 {kun_uz} kuni uchun jadval topilmadi.")
            return

        text = full_title
        for idx, (_, row) in enumerate(jadval.iterrows(), 1):
            text += (
                f"{idx}. *{row['Vaqt']}*\n"
                f"Fan: {row['Fan']}\n"
                f"Turi: {row['Turi']}\n"
                f"Guruh: {row['Guruh']}\n"
                f"Joy: {row['Joy']}\n"
                f"O'qituvchi: {row['O\'qituvchi']}\n\n"
            )

        await query.message.reply_text(text, parse_mode="Markdown")

    except FileNotFoundError:
        await query.message.reply_text("❌ Excel fayl topilmadi (`D:\\jadval.xlsx`).")
    except Exception as e:
        await query.message.reply_text(f"⚠️ Xatolik: {e}")


# 🔹 Asosiy ishga tushirish
async def main():
    print("🤖 Bot ishga tushdi...")

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler, pattern="select_group|info"))
    app.add_handler(CallbackQueryHandler(show_schedule, pattern="today|tomorrow"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, group_entered))

    await app.run_polling()


if __name__ == "__main__":
    asyncio.run(main())