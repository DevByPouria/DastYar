import os
import random
import logging
from threading import Thread
from flask import Flask
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from product_search import search_products, format_product_message
from gold_currency import get_gold_and_currency_prices, format_gold_currency_message

# ---------------------------------------------------------
# ۱. تنظیمات مخفی‌سازی توکن و کاهش سطح لاگ‌ها
# ---------------------------------------------------------
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("telegram.ext").setLevel(logging.WARNING)

# ---------------------------------------------------------
# ۲. تنظیمات شخص خاص
# ---------------------------------------------------------
SPECIAL_USERNAME = "Ayydddda_2007" 
SPECIAL_USER_ID = 6876769630 

SPECIAL_WELCOME_MESSAGES = [
    "به ربات خیلی خوش اومدی زندگی پوریا ❤️\n\n(از طرف پوریا)",
    "پوریا خیلی خوش‌شانسه که تو رو توی زندگیش داره ✨\n\n(از طرف پوریا)",
    "سلام به قشنگ‌ترین اتفاق زندگی پوریا 🥰 خوش اومدی!\n\n(از طرف پوریا)",
    "امروز دنیا خیلی قشنگ‌تره چون تو اینجایی 🌸\n\n(از طرف پوریا)",
    "ورودت به ربات مبارک تمام دارایی پوریا 💖\n\n(از طرف پوریا)",
    "امیدوارم لحظه‌هات مثل لبخندت قشنگ باشه جانِ پوریا 💫\n\n(از طرف پوریا)",
    "خوش اومدی همه‌کس پوریا 💖 بودنِ تو یعنی حالِ خوب!\n\n(از طرف پوریا)"
]

# ---------------------------------------------------------
# ۳. وب‌سرور Flask جهت آنلاین نگه‌داشتن ربات در Render
# ---------------------------------------------------------
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

# ---------------------------------------------------------
# ۴. کیبوردها و تنظیمات ربات
# ---------------------------------------------------------
TOKEN = os.getenv("BOT_TOKEN")

KEYBOARD = ReplyKeyboardMarkup(
    [[KeyboardButton("🪙 قیمت طلا و ارز"), KeyboardButton("🛍️ جستجوی کالا")]],
    resize_keyboard=True
)

REFRESH_BUTTON = InlineKeyboardMarkup([
    [InlineKeyboardButton("🔄 به‌روزرسانی قیمت‌ها", callback_data="refresh_prices")]
])

# ---------------------------------------------------------
# ۵. هندلرها (دستورات و پیام‌ها)
# ---------------------------------------------------------
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    is_special = False
    if user.username and SPECIAL_USERNAME and user.username.lower() == SPECIAL_USERNAME.lower():
        is_special = True
    elif SPECIAL_USER_ID and user.id == SPECIAL_USER_ID:
        is_special = True
        
    if is_special:
        welcome_text = random.choice(SPECIAL_WELCOME_MESSAGES)
        await update.message.reply_text(welcome_text, reply_markup=KEYBOARD)
    else:
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

    wait_msg = await update.message.reply_text("🔍 در حال جستجوی کالا در ترب، دیجی‌کالا و باسلام...")
    products = search_products(text)
    response_text = format_product_message(products)
    
    await wait_msg.edit_text(response_text, parse_mode='Markdown', disable_web_page_preview=True)

async def handle_refresh_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("⏳ در حال دریافت قیمت‌های جدید...")
    
    prices = get_gold_and_currency_prices()
    msg = format_gold_currency_message(prices)
    
    try:
        await query.edit_message_text(msg, parse_mode='Markdown', reply_markup=REFRESH_BUTTON)
    except Exception:
        pass

# ---------------------------------------------------------
# ۶. اجرای اصلی برنامه
# ---------------------------------------------------------
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
