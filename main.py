import os
from datetime import datetime
import random
import logging
from pdf_generator import generate_news_pdf
from threading import Thread
from flask import Flask
from telegram import (
    Update, ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, filters, ContextTypes
)

from product_search import search_products, format_product_messages
from gold_currency import get_gold_and_currency_prices, format_gold_currency_message

import historical_data as hist
import pandas as pd
from technical_analyzer import TechnicalAnalyzer
from news_fetcher import (
    fetch_events, filter_today_events, analyze_sentiment
)
from signal_engine import SignalEngine

# ================== تنظیمات ==================
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("telegram.ext").setLevel(logging.WARNING)

SPECIAL_USERNAME = "Ayydddda_2007"
SPECIAL_USER_ID = 6876769630

SPECIAL_WELCOME_MESSAGES = [
    "به ربات خیلی خوش اومدی زندگی پوریا ❤️\n\n(از طرف پوریا)",
    "پوریا خیلی خوش‌شانسه که تو رو توی زندگیش داره ✨\n\n(از طرف پوریا)",
    "سلام به قشنگ‌ترین اتفاق زندگی پوریا 🥰 خوش اومدی!\n\n(از طرف پوریا)",
    "امروز دنیا خیلی قشنگ‌تره چون تو اینجایی 🌸\n\n(از طرف پوریا)",
    "ورودت به ربات مبارک تمام دارایی پوریا 💖\n\n(از طرف پوریا)",
]

# ================== وب‌سرور ==================
flask_app = Flask('')

@flask_app.route('/')
def home():
    return "Bot is active!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    flask_app.run(host='0.0.0.0', port=port)

Thread(target=run_flask, daemon=True).start()

# ================== کیبوردها ==================
TOKEN = os.getenv("BOT_TOKEN")

KEYBOARD = ReplyKeyboardMarkup(
    [
        [KeyboardButton("🪙 قیمت طلا و ارز"), KeyboardButton("🛍️ جستجوی کالا")],
        [KeyboardButton("📈 سیگنال معاملاتی"), KeyboardButton("📰 اخبار بازار")],
    ],
    resize_keyboard=True
)

REFRESH_BUTTON = InlineKeyboardMarkup([
    [InlineKeyboardButton("🔄 به‌روزرسانی قیمت‌ها", callback_data="refresh_prices")]
])

SIGNAL_MENU = InlineKeyboardMarkup([
    [InlineKeyboardButton("🥇 طلا", callback_data="sig_gold"),
     InlineKeyboardButton("💵 دلار", callback_data="sig_dollar")],
    [InlineKeyboardButton("🪙 سکه", callback_data="sig_coin")],
])

# ================== منوی اخبار ==================
def get_news_menu():
    """منوی اخبار با 3 گزینه"""
    keyboard = [
        [InlineKeyboardButton("📅 اخبار امروز", callback_data="news_today")],
        [InlineKeyboardButton("📅 اخبار هفته", callback_data="news_week")],
        [InlineKeyboardButton("🔥 اخبار مهم هفته", callback_data="news_important")],
    ]
    return InlineKeyboardMarkup(keyboard)

# ================== راه‌اندازی دیتابیس ==================
hist.init_db()

# ================== هندلرها ==================
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    is_special = False
    if user.username and user.username.lower() == SPECIAL_USERNAME.lower():
        is_special = True
    elif SPECIAL_USER_ID and user.id == SPECIAL_USER_ID:
        is_special = True

    if is_special:
        await update.message.reply_text(
            random.choice(SPECIAL_WELCOME_MESSAGES),
            reply_markup=KEYBOARD
        )
    else:
        await update.message.reply_text(
            "سلام! 👋 به **ربات تحلیلگر بازار** خوش آمدید.\n\n"
            "🔹 قیمت لحظه‌ای طلا، ارز و رمزارز\n"
            "🔹 جستجوی کالا در فروشگاه‌ها\n"
            "🔹 سیگنال معاملاتی (تکنیکال + فاندامنتال)\n"
            "🔹 اخبار مهم اقتصادی\n\n"
            "یک گزینه را انتخاب کنید یا نام محصول مورد نظر را بفرستید:",
            reply_markup=KEYBOARD
        )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    # ============ قیمت طلا و ارز ============
    if text == "🪙 قیمت طلا و ارز":
        wait = await update.message.reply_text("⏳ در حال استعلام آخرین نرخ‌ها...")
        prices = get_gold_and_currency_prices()
        for label, price in prices.items():
            try:
                hist.save_snapshot(label, int(price.replace(',', '')))
            except:
                pass
        msg = format_gold_currency_message(prices)
        await wait.edit_text(msg, parse_mode='Markdown', reply_markup=REFRESH_BUTTON)
        return

    # ============ جستجوی کالا ============
    if text == "🛍️ جستجوی کالا":
        await update.message.reply_text(
            "🔹 لطفاً نام کالای مورد نظر خود را بفرستید (مثال: گوشی سامسونگ A54):"
        )
        return

    # ============ سیگنال معاملاتی ============
    if text == "📈 سیگنال معاملاتی":
        await update.message.reply_text(
            "📈 **سیگنال معاملاتی**\n\n"
            "کدام دارایی را تحلیل کنم؟",
            reply_markup=SIGNAL_MENU,
            parse_mode='Markdown'
        )
        return

    # ============ اخبار بازار ============
    if text == "📰 اخبار بازار":
        await update.message.reply_text(
            "📰 **اخبار بازار**\n\n"
            "🔹 کدوم بازه زمانی رو می‌خوای ببینی؟",
            reply_markup=get_news_menu(),
            parse_mode='Markdown'
        )
        return

    # ============ جستجوی پیش‌فرض محصول ============
    wait = await update.message.reply_text("🔍 در حال جستجوی کالا...")
    results = search_products(text)
    messages = format_product_messages(results)
    await wait.edit_text(messages[0], parse_mode='Markdown', disable_web_page_preview=True)
    for m in messages[1:]:
        await update.message.reply_text(m, parse_mode='Markdown', disable_web_page_preview=True)


async def refresh_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("⏳ در حال دریافت...")
    prices = get_gold_and_currency_prices()
    for label, price in prices.items():
        try:
            hist.save_snapshot(label, int(price.replace(',', '')))
        except:
            pass
    msg = format_gold_currency_message(prices)
    try:
        await query.edit_message_text(msg, parse_mode='Markdown', reply_markup=REFRESH_BUTTON)
    except:
        pass


async def signal_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """هندلر دکمه‌های سیگنال"""
    query = update.callback_query
    await query.answer("⏳ در حال تحلیل...")

    data = query.data
    asset_map = {
        'sig_gold': ('gold_gram18', 'طلا (اونس جهانی)'),
        'sig_dollar': ('dollar', 'دلار'),
        'sig_coin': ('gold_gram18', 'سکه'),
    }
    asset_key, asset_name = asset_map.get(data, ('gold_gram18', 'طلا'))

    # ===== دریافت تاریخچه =====
    rows = hist.get_history(asset_key, limit=200)

    if len(rows) < 20:
        await query.edit_message_text(
            f"⚠️ **داده کافی برای تحلیل {asset_name} موجود نیست.**\n\n"
            f"📊 تعداد رکورد: `{len(rows)}`",
            parse_mode='Markdown'
        )
        return

    # ===== تحلیل تکنیکال =====
    df = pd.DataFrame(rows, columns=['price', 'timestamp'])
    df['price'] = df['price'].astype(float)

    analyzer = TechnicalAnalyzer(df)
    tech_result = analyzer.run_all()

    # تعیین جهت سیگنال بر اساس امتیاز
    tech_net = tech_result.get('net_score', 0)
    if tech_net >= 2:
        direction = 'BUY'
    elif tech_net <= -2:
        direction = 'SELL'
    else:
        direction = 'BUY'  # خنثی: پیش‌فرض

    sl, tp, rr = analyzer.get_risk_levels(direction=direction)
    tech_result['stop_loss'] = sl
    tech_result['take_profit'] = tp
    tech_result['risk_reward'] = rr

    # ===== تحلیل فاندامنتال =====
    events = fetch_events(days_ahead=7)
    filtered = filter_today_events(events, days_ahead=7, min_impact='High')
    fund_result = analyze_sentiment(filtered)

    # ===== سیگنال نهایی =====
    engine = SignalEngine()
    msg = engine.generate(tech_result, fund_result, asset_name)

    await query.edit_message_text(
        msg,
        parse_mode='Markdown',
        disable_web_page_preview=True,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 تحلیل مجدد", callback_data=data)],
            [InlineKeyboardButton("📰 اخبار بازار", callback_data="news_today")],
            [InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main")],
        ])
    )


async def news_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """هندلر دکمه‌های اخبار - 3 گزینه + PDF"""
    query = update.callback_query
    await query.answer("⏳ در حال دریافت اخبار...")

    data = query.data
    pdf_title = ""

    if data == "news_today":
        events = fetch_events(days_ahead=1)
        filtered = filter_today_events(events, days_ahead=0, min_impact='All')
        analysis = analyze_sentiment(filtered)
        pdf_title = "اخبار امروز"
        if not filtered:
            analysis['summary'] = (
                "📰 **اخبار امروز**\n"
                "━━━━━━━━━━━━━━━━━━━━\n\n"
                "⚠️ **امروز هیچ خبری در تقویم نیست.**\n\n"
                "⚠️ این تحلیل صرفاً آماری است و توصیه مالی نیست."
            )

    elif data == "news_week":
        events = fetch_events(days_ahead=7)
        filtered = filter_today_events(events, days_ahead=7, min_impact='All')
        analysis = analyze_sentiment(filtered)
        pdf_title = "اخبار این هفته"
        if not filtered:
            analysis['summary'] = (
                "📰 **اخبار این هفته**\n\n"
                "⚠️ هیچ خبری در این هفته پیدا نشد."
            )

    elif data == "news_important":
        events = fetch_events(days_ahead=7)
        filtered = filter_today_events(events, days_ahead=7, min_impact='High')
        analysis = analyze_sentiment(filtered)
        pdf_title = "اخبار مهم هفته"
        if not filtered:
            analysis['summary'] = (
                "🔥 **اخبار مهم هفته**\n\n"
                "✅ **این هفته خبر خیلی مهمی در راه نیست.**"
            )
    else:
        return

    back_keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📅 اخبار امروز", callback_data="news_today"),
         InlineKeyboardButton("📅 اخبار هفته", callback_data="news_week")],
        [InlineKeyboardButton("🔥 اخبار مهم هفته", callback_data="news_important")],
    ])

    # ===== ارسال خلاصه (متن) =====
    try:
        await query.edit_message_text(
            analysis['summary'],
            parse_mode='Markdown',
            disable_web_page_preview=True,
            reply_markup=back_keyboard
        )
    except Exception as e:
        if "not modified" not in str(e).lower():
            print(f"[DEBUG] Edit error: {e}", flush=True)

    # ===== ساخت و ارسال PDF =====
    if filtered:
        try:
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text="📄 در حال ساخت فایل PDF با تمام اخبار...",
            )
            
            pdf_path = generate_news_pdf(
                events=filtered,
                bias=analysis['bias'],
                bull=analysis['bullish'],
                bear=analysis['bearish'],
                title=pdf_title
            )
            
            if pdf_path and os.path.exists(pdf_path):
                with open(pdf_path, 'rb') as pdf_file:
                    await context.bot.send_document(
                        chat_id=query.message.chat_id,
                        document=pdf_file,
                        filename=f"DastYar_News_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                        caption=f"📄 **{pdf_title}** — {len(filtered)} خبر\n\n⚠️ این تحلیل صرفاً آماری است.",
                        parse_mode='Markdown'
                    )
                # حذف فایل بعد از ارسال
                try:
                    os.remove(pdf_path)
                except:
                    pass
            else:
                await context.bot.send_message(
                    chat_id=query.message.chat_id,
                    text="❌ متأسفانه ساخت PDF ناموفق بود.",
                )
        except Exception as e:
            print(f"[DEBUG] PDF error: {e}", flush=True)
            import traceback
            traceback.print_exc()
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text=f"❌ خطا در ساخت PDF: {str(e)[:100]}",
            )
# ================== اجرا ==================
def main():
    if not TOKEN:
        print("Error: BOT_TOKEN is missing!")
        return

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(refresh_callback, pattern="^refresh_prices$"))
    app.add_handler(CallbackQueryHandler(signal_callback, pattern="^sig_"))
    app.add_handler(CallbackQueryHandler(news_callback, pattern="^news_"))

    print("🚀 Bot is running...")
    app.run_polling()


if __name__ == '__main__':
    main()
