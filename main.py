import os
from threading import Thread
from flask import Flask

# ساخت یک وب‌سرور ساده برای راضی نگه داشتن Render
app = Flask('')

@app.route('/')
def home():
    return "Bot is alive!"

def run():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()

# اجرا کردن سرور قبل از شروع ربات
keep_alive()

import os
import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from product_search import search_products, format_product_message
from gold_currency import get_gold_and_currency_prices, format_gold_currency_message

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

TOKEN = os.getenv("BOT_TOKEN")

KEYBOARD = ReplyKeyboardMarkup(
    [[KeyboardButton("🪙 قیمت طلا و ارز"), KeyboardButton("🛍️ جستجوی کالا")]],
    resize_keyboard=True
)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "سلام! 👋 به ربات دستیار خوش آمدید.\n"
        "یک گزینه را انتخاب کنید یا نام محصول مورد نظر خود را بفرستید:",
        reply_markup=KEYBOARD
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    
    if text == "🪙 قیمت طلا و ارز":
        wait_msg = await update.message.reply_text("⏳ در حال استعلام نرخ طلا و ارز...")
        prices = get_gold_and_currency_prices()
        msg = format_gold_currency_message(prices)
        await wait_msg.edit_text(msg, parse_mode='Markdown')
        return

    if text == "🛍️ جستجوی کالا":
        await update.message.reply_text("🔹 لطفاً نام کالای مورد نظر خود را بفرستید (مثال: قاب آیفون 13):")
        return

    # در غیر این صورت هر متنی بفرستد به‌عنوان جستجوی کالا فرض می‌شود
    wait_msg = await update.message.reply_text("🔍 در حال جستجوی کالا...")
    products = search_products(text)
    response_text = format_product_message(products)
    
    await wait_msg.edit_text(response_text, parse_mode='Markdown', disable_web_page_preview=True)

def main():
    if not TOKEN:
        print("Error: BOT_TOKEN variable is missing!")
        return

    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("Bot is running...")
    app.run_polling()

if __name__ == '__main__':
    main()
