import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

import database as db
import product_search as search
import price_fetcher  # 👈 اتصال فایل دریافت قیمت طلا و سکه

# پیکربندی لاگ‌ها
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# کیبوردهای اصلی
def get_main_menu():
    keyboard = [
        [InlineKeyboardButton("🛍️ جستجوی محصول", callback_data='search_product'),
         InlineKeyboardButton("🪙 قیمت طلا و سکه", callback_data='gold_price')],  # 👈 دکمه طلا و سکه
        
        [InlineKeyboardButton("📋 لیست خرید من (Wishlist)", callback_data='wishlist_menu')],
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

# دستور /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['state'] = None
    welcome_text = (
        "سلام! 👋 به **دستیار هوشمند خرید** خوش آمدید.\n\n"
        "من به شما کمک می‌کنم ارزان‌ترین قیمت محصولات را پیدا کنید، "
        "از قیمت لحظه‌ای طلا و سکه باخبر شوید و لیست خرید خود را مدیریت کنید."
    )
    await update.message.reply_text(welcome_text, reply_markup=get_main_menu(), parse_mode='Markdown')

# مدیریت کلیک روی دکمه‌ها (CallbackQuery)
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
            "🛍️ **جستجوی محصولات**\n\n🔹 لطفاً نام محصول مورد نظرتان را بفرستید (مثال: گوشی آیفون 13، لپ تاپ ایسوس):",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data='back_to_menu')]]),
            parse_mode='Markdown'
        )

    # 🪙 دریافت و نمایش قیمت طلا و سکه
    elif data == 'gold_price':
        # ابتدا یک پیام در حال بارگذاری نشان داده می‌شود
        await query.edit_message_text("⏳ در حال دریافت قیمت‌های به‌روز طلا و سکه...")
        
        # فراخوانی مستقیم تابع دریافت قیمت
        gold_msg = price_fetcher.get_gold_prices()

        # نمایش نتیجه به کاربر
        await query.edit_message_text(
            gold_msg,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 به‌روزرسانی", callback_data='gold_price')],
                [InlineKeyboardButton("🔙 بازگشت به منو", callback_data='back_to_menu')]
            ]),
            parse_mode='Markdown'
        )

    elif data == 'wishlist_menu':
        await query.edit_message_text(
            "📋 **لیست خرید هوشمند (Wishlist)**\n\nدر این بخش می‌توانید لیست خریدهای آینده خود را مشاهده و مجموع قیمت آن‌ها را محاسبه کنید.",
            reply_markup=get_wishlist_menu(),
            parse_mode='Markdown'
        )

    elif data == 'view_wishlist':
        items = db.get_user_wishlist(user_id)
        if not items:
            await query.edit_message_text(
                "🛒 لیست خرید شما در حال حاضر خالی است!",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data='wishlist_menu')]])
            )
        else:
            msg = "📜 **لیست خرید شما:**\n\n"
            total_price = 0
            for idx, item in enumerate(items, 1):
                title, price, link = item
                total_price += price
                msg += f"{idx}. [{title}]({link})\n💰 قیمت: `{price:,} تومان`\n───────────────\n"
            
            msg += f"\n💵 **مجموع کل فاکتور:** `{total_price:,} تومان`"
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
            "❓ **راهنما:**\n\n کافیست نام هر کالایی را بفرستید تا قیمت آن در چند فروشگاه مقایسه شود.\n\n 📞 **پشتیبانی:** @your_admin_username",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data='back_to_menu')]]),
            parse_mode='Markdown'
        )

# مدیریت متن‌های ورودی کاربر
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    state = context.user_data.get('state')
    text = update.message.text.strip()

    if state == 'waiting_search':
        status_msg = await update.message.reply_text("⏳ در حال جستجو در فروشگاه‌ها...")
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
            "لطفاً از دکمه‌های منو استفاده کنید یا روی '🛍️ جستجوی محصول' بزنید:",
            reply_markup=get_main_menu()
        )

def main():
    db.init_db()
    TOKEN = os.getenv("BOT_TOKEN", "123456789:YOUR_ACTUAL_BOT_TOKEN")
    
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(handle_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot is running...")
    application.run_polling()

if __name__ == '__main__':
    main()
