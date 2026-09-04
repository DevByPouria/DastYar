import os
import logging
from threading import Thread
from flask import Flask
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from product_search import search_products, format_product_message
from gold_currency import get_gold_and_currency_prices, format_gold_currency_message

# web server کوچک برای جلو گیری از Conflict در Render
app_flask = Flask('')
@app_flask.route('/')
def home():
    return "Bot is active!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app_flask.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_flask)
    t.start()

keep_alive()

# تنظیم سطح لاگ عمومی
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# 🤫 مخفی کردن درخواست‌های httpx که حاوی توکن تلگرام هستند
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("telegram.ext").setLevel(logging.WARNING)

TOKEN = os.getenv("BOT_TOKEN")

KEYBOARD = ReplyKeyboardMarkup(
    [[KeyboardButton("🪙 قیمت طلا و ارز"), KeyboardButton("🛍️ جستجوی کالا")]],
    resize_keyboard=True
)

# دکمه شیشه‌ای زیر پیام قیمت‌ها
REFRESH_BUTTON = InlineKeyboardMarkup([
    [InlineKeyboardButton("🔄 به‌روزرسانی قیمت‌ها", callback_data="refresh_prices")]
])

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "سلام! 👋 به ربات دستیار خوش آمدید.\n"
        "یک گزینه را انتخاب کنید یا نام محصول مورد نظر خود را بفرستید:",
        reply_markup=KEYBOARD
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    
    if text == "🪙 قیمت طلا و ارز":
        wait_msg = await update.message.reply_text("⏳ در حال استعلام آخرین نرخ‌ها...")
        prices = get_gold_and_currency_prices()
        msg = format_gold_currency_message(prices)
        await wait_msg.edit_text(msg, parse_mode='Markdown', reply_markup=REFRESH_BUTTON)
        return

    if text == "🛍️ جستجوی کالا":
        await update.message.reply_text("🔹 لطفاً نام کالای مورد نظر خود را بفرستید (مثال: گوشی سامسونگ A54):")
        return

    wait_msg = await update.message.reply_text("🔍 در حال جستجوی کالا...")
    products = search_products(text)
    response_text = format_product_message(products)
    
    await wait_msg.edit_text(response_text, parse_mode='Markdown', disable_web_page_preview=True)

# هندلر کلیک روی دکمه شیشه‌ای "به‌روزرسانی"
async def handle_refresh_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("⏳ در حال دریافت قیمت‌های جدید...")
    
    prices = get_gold_and_currency_prices()
    msg = format_gold_currency_message(prices)
    
    try:
        await query.edit_message_text(msg, parse_mode='Markdown', reply_markup=REFRESH_BUTTON)
    except Exception as e:
        # اگر قیمت تغییر نکرده باشد تلگرام خطا می‌دهد که نادیده گرفته می‌شود
        pass

def main():
    if not TOKEN:
        print("Error: BOT_TOKEN is missing!")
        return

    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(handle_refresh_callback, pattern="^refresh_prices$"))
    
    print("Bot is running...")
    app.run_polling()

if __name__ == '__main__':
    main()
