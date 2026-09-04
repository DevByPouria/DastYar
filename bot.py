import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

import database as db
import product_search as search
import price_fetcher  # استفاده از فایل قیمت‌های شما

# تنظیمات لاگ
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

def get_main_menu():
    keyboard = [
        [InlineKeyboardButton("🛍️ جستجوی محصول", callback_data='search_product'),
         InlineKeyboardButton("🪙 قیمت طلا و ارز", callback_data='gold_price')],
        
        [InlineKeyboardButton("📋 لیست خرید من", callback_data='wishlist_menu')],
        [InlineKeyboardButton("❓ راهنما و پشتیبانی", callback_data='help_support')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_wishlist_menu():
    keyboard = [
        [InlineKeyboardButton("📜 مشاهده لیست و محاسبه قیمت کل", callback_data='view_wishlist')],
        [InlineKeyboardButton("🗑️ پاک‌سازی لیست", callback_data='clear_wishlist')],
        [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data='back_to_menu')]
    ]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['state'] = None
    welcome_text = (
        "سلام! 👋 به **دستیار هوشمند خرید** خوش آمدید.\n\n"
        "من به شما کمک می‌کنم قیمت محصولات را مقایسه کنید، "
        "از قیمت لحظه‌ای طلا و ارز باخبر شوید و لیست خرید خود را مدیریت کنید."
    )
    await update.message.reply_text(welcome_text, reply_markup=get_main_menu(), parse_mode='Markdown')

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = query.from_user.id

    if data == 'back_to_menu':
        context.user_data['state'] = None
        await query.edit_message_text("🏠 **منوی اصلی:**", reply_markup=get_main_menu(), parse_mode='Markdown')

    elif data == 'search_product':
        context.user_data['state'] = 'waiting_search'
        await query.edit_message_text(
            "🛍️ **جستجوی محصولات**\n\n🔹 لطفاً نام محصول مورد نظرتان را بفرستید:",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data='back_to_menu')]]),
            parse_mode='Markdown'
        )

    # 🪙 دریافت و نمایش سریع متنی قیمت‌های درخواستی
    elif data == 'gold_price':
        try:
            # دریافت دیکشنری کامل قیمت‌ها از فایل price_fetcher شما
            raw_prices = price_fetcher.get_all_prices()
            current_time = price_fetcher.get_current_time()

            # نقشه تطبیق کلیدهای قیمت‌ها با نام‌های درخواستی شما
            items_mapping = [
                ('🌐 Ounce Gold', 'اونس طلا'),
                ('🔱 Mesghal 17', 'مثقال ۱۷'),
                ('⚜️ Gold 18k', 'گرم ۱۸'),
                ('🪙 Sekke Emami', 'سکه امامی'),
                ('🪙 Sekke Nim', 'سکه نیم'),
                ('🪙 Sekke Rob', 'سکه ربع'),
                ('🥈 Ounce Silver', 'نقره (اونس)'),
                ('🧱 Shmesh', 'شمش گرمی'),
                ('₿ Bitcoin', 'بیت کوین'),
                ('📊 Sekke Value', 'ارزش سکه'),
                ('🛢️ Oil', 'نفت'),
                ('💵 USD / Tether', 'تتر'),
                ('🥇 Parsian', 'سکه پارسیان'),
                ('🪙 Sekke Ghadim', 'سکه قدیم'),
                ('🛒 Gold Buy', 'گرم خرید'),
                ('🇹🇷 Lir', 'لیر ترکیه'),
                ('🇴🇲 OMR', 'ریال عمان'),
                ('💎 Ethereum', 'اتریوم')
            ]

            msg = f"⚡ **قیمت‌های زنده بازار** ({current_time})\n"
            msg += "───────────────────\n"

            for key, label in items_mapping:
                val = raw_prices.get(key, 'نامشخص')
                msg += f"▫️ **{label}:** `{val}`\n"

            msg += "───────────────────\n"
            msg += "🔄 *قیمت‌ها به صورت خودکار بروزرسانی می‌شوند.*"

            await query.edit_message_text(
                msg,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔄 به‌روزرسانی", callback_data='gold_price')],
                    [InlineKeyboardButton("🔙 بازگشت به منو", callback_data='back_to_menu')]
                ]),
                parse_mode='Markdown'
            )
        except Exception as e:
            print(f"Error fetching prices: {e}")
            await query.edit_message_text(
                "❌ خطایی در دریافت قیمت‌ها رخ داد. لطفاً چند لحظه بعد تلاش کنید.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data='back_to_menu')]])
            )

    elif data == 'wishlist_menu':
        await query.edit_message_text(
            "📋 **لیست خرید هوشمند (Wishlist)**",
            reply_markup=get_wishlist_menu(),
            parse_mode='Markdown'
        )

    elif data == 'view_wishlist':
        items = db.get_user_wishlist(user_id)
        if not items:
            await query.edit_message_text(
                "🛒 لیست خرید شما خالی است!",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data='wishlist_menu')]])
            )
        else:
            msg = "📜 **لیست خرید شما:**\n\n"
            total_price = 0
            for idx, item in enumerate(items, 1):
                title, price, link = item
                total_price += price
                msg += f"{idx}. [{title}]({link})\n💰 قیمت: `{price:,} تومان`\n───────────────\n"
            
            msg += f"\n💵 **مجموع کل:** `{total_price:,} تومان`"
            await query.edit_message_text(
                msg,
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data='wishlist_menu')]]),
                parse_mode='Markdown',
                disable_web_page_preview=True
            )

    elif data == 'clear_wishlist':
        db.clear_user_wishlist(user_id)
        await query.answer("🗑️ لیست خرید شما پاک شد.", show_alert=True)
        await query.edit_message_text("🛒 لیست خرید شما خالی شد.", reply_markup=get_wishlist_menu())

    elif data == 'help_support':
        await query.edit_message_text(
            "❓ **راهنما:**\n\nنام محصول را ارسال کنید تا قیمت‌ها مقایسه شوند.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data='back_to_menu')]]),
            parse_mode='Markdown'
        )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    state = context.user_data.get('state')
    text = update.message.text.strip()

    if state == 'waiting_search':
        status_msg = await update.message.reply_text("⏳ در حال جستجو...")
        products = search.search_all_shops(text)
        
        await status_msg.edit_text(
            search.format_product_message(products),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 جستجوی مجدد", callback_data='search_product')],
                [InlineKeyboardButton("🔙 بازگشت به منو", callback_data='back_to_menu')]
            ]),
            parse_mode='Markdown',
            disable_web_page_preview=True
        )
        context.user_data['state'] = None
    else:
        await update.message.reply_text(
            "لطفاً از منوی زیر استفاده کنید:",
            reply_markup=get_main_menu()
        )

def main():
    db.init_db()
    TOKEN = os.getenv("BOT_TOKEN")
    
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(handle_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot is running...")
    application.run_polling()

if __name__ == '__main__':
    main()
