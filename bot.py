import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes

import database as db
import price_fetcher as prices
import product_search as search

# ========== توکن و پورت ==========
TOKEN = os.getenv('TOKEN')
PORT = int(os.getenv('PORT', 10000))

# ========== وب‌سرور برای Render ==========
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running!")
    
    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()

def run_health_server():
    server = HTTPServer(('0.0.0.0', PORT), HealthHandler)
    server.serve_forever()

# ========== منوی اصلی با دکمه‌های شیشه‌ای ==========
def get_main_menu():
    """منوی اصلی با طراحی شیشه‌ای و دکمه‌های زیبا"""
    keyboard = [
        [
            InlineKeyboardButton("💰 ثبت هزینه", callback_data='add_expense'),
            InlineKeyboardButton("📈 ثبت درآمد", callback_data='add_income')
        ],
        [
            InlineKeyboardButton("📊 گزارش ماهانه", callback_data='report'),
            InlineKeyboardButton("📋 تاریخچه", callback_data='history')
        ],
        [
            InlineKeyboardButton("💎 قیمت طلا و ارز", callback_data='prices'),
            InlineKeyboardButton("🛍️ جستجوی محصولات", callback_data='search_product')
        ],
        [
            InlineKeyboardButton("🔍 جستجوی پیشرفته", callback_data='advanced_search'),
            InlineKeyboardButton("📌 راهنما", callback_data='help')
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

# ========== منوی جستجوی پیشرفته (دکمه‌های انتخابی) ==========
def get_advanced_search_menu():
    """دکمه‌های انتخاب دسته‌بندی برای جستجوی پیشرفته"""
    keyboard = [
        [
            InlineKeyboardButton("📱 گوشی", callback_data='search_phone'),
            InlineKeyboardButton("💻 لپ‌تاپ", callback_data='search_laptop'),
            InlineKeyboardButton("⌚ ساعت", callback_data='search_watch')
        ],
        [
            InlineKeyboardButton("🎧 هدفون", callback_data='search_headphone'),
            InlineKeyboardButton("📷 دوربین", callback_data='search_camera'),
            InlineKeyboardButton("🔊 اسپیکر", callback_data='search_speaker')
        ],
        [
            InlineKeyboardButton("🛋️ لوازم خانگی", callback_data='search_appliance'),
            InlineKeyboardButton("👗 پوشاک", callback_data='search_clothing'),
            InlineKeyboardButton("📚 کتاب", callback_data='search_book')
        ],
        [
            InlineKeyboardButton("🔙 بازگشت به منو", callback_data='back_to_menu')
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

# ========== منوی قیمت‌ها (دکمه‌های انتخابی) ==========
def get_price_menu():
    """دکمه‌های انتخاب نوع قیمت"""
    keyboard = [
        [
            InlineKeyboardButton("⚜️ طلا", callback_data='price_gold'),
            InlineKeyboardButton("💵 دلار", callback_data='price_dollar'),
            InlineKeyboardButton("🪙 سکه", callback_data='price_coin')
        ],
        [
            InlineKeyboardButton("📊 همه قیمت‌ها", callback_data='price_all'),
            InlineKeyboardButton("🔄 بروزرسانی", callback_data='refresh_prices')
        ],
        [
            InlineKeyboardButton("🔙 بازگشت", callback_data='back_to_menu')
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

# ========== هندلر استارت ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 سلام! به **دستیار مالی هوشمند** خوش اومدی.\n\n"
        "✨ من یک ربات **شیشه‌ای** و **حرفه‌ای** هستم!\n\n"
        "🔹 **ثبت هزینه و درآمد**\n"
        "🔹 **گزارش‌های مالی ماهانه**\n"
        "🔹 **قیمت لحظه‌ای طلا و ارز**\n"
        "🔹 **جستجوی بهترین قیمت محصولات**\n\n"
        "💡 یکی از دکمه‌های زیر رو انتخاب کن:",
        reply_markup=get_main_menu()
    )

# ========== هندلر دکمه‌ها ==========
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    data = query.data
    
    # ======== ثبت هزینه ========
    if data == 'add_expense':
        await query.edit_message_text(
            "💸 مبلغ هزینه رو به تومان وارد کن (مثلاً ۲۵۰۰۰۰):",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data='back_to_menu')]])
        )
        context.user_data['state'] = 'waiting_expense'
    
    # ======== ثبت درآمد ========
    elif data == 'add_income':
        await query.edit_message_text(
            "💰 مبلغ درآمد رو به تومان وارد کن:",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data='back_to_menu')]])
        )
        context.user_data['state'] = 'waiting_income'
    
    # ======== گزارش ========
    elif data == 'report':
        total_income, total_expense = db.get_monthly_summary(user_id)
        balance = total_income - total_expense
        await query.edit_message_text(
            f"📊 **گزارش ماهانه**\n\n"
            f"💰 درآمد: {total_income:,} تومان\n"
            f"💸 هزینه: {total_expense:,} تومان\n"
            f"📌 مانده: {balance:,} تومان\n"
            f"💳 وضعیت: {'✅ مثبت' if balance >= 0 else '❌ منفی'}",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data='back_to_menu')]])
        )
    
    # ======== تاریخچه ========
    elif data == 'history':
        transactions = db.get_all_transactions(user_id)
        if not transactions:
            await query.edit_message_text(
                "📋 **تاریخچه تراکنش‌ها**\n\nهیچ تراکنشی ثبت نشده!",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data='back_to_menu')]])
            )
            return
        
        message = "📋 **۲۰ تراکنش اخیر**\n\n"
        for amount, category, desc, trans_type, date in transactions:
            emoji = "💰" if trans_type == 'income' else "💸"
            message += f"{emoji} {date} - {category}: {amount:,} تومان"
            if desc:
                message += f" ({desc})"
            message += "\n"
        
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data='back_to_menu')]])
        )
    
    # ======== قیمت‌ها ========
    elif data == 'prices':
        await query.edit_message_text(
            "💎 **قیمت‌های لحظه‌ای بازار**\n\n"
            "🔹 یکی از گزینه‌های زیر رو انتخاب کن:",
            reply_markup=get_price_menu()
        )
    
    # ======== قیمت طلا ========
    elif data == 'price_gold':
        price_data = prices.get_all_prices()
        gold_price = price_data.get('gold', 0)
        await query.edit_message_text(
            f"⚜️ **قیمت طلا (گرم ۱۸)**\n\n"
            f"💰 قیمت: {gold_price:,} تومان\n"
            f"🕐 {prices.get_current_time()}\n\n"
            f"🔹 برای بروزرسانی، گزینه زیر رو بزن.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 بروزرسانی", callback_data='price_gold')],
                [InlineKeyboardButton("🔙 بازگشت", callback_data='prices')]
            ])
        )
    
    # ======== قیمت دلار ========
    elif data == 'price_dollar':
        price_data = prices.get_all_prices()
        dollar_price = price_data.get('dollar', 0)
        await query.edit_message_text(
            f"💵 **قیمت دلار**\n\n"
            f"💰 قیمت: {dollar_price:,} تومان\n"
            f"🕐 {prices.get_current_time()}\n\n"
            f"🔹 برای بروزرسانی، گزینه زیر رو بزن.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 بروزرسانی", callback_data='price_dollar')],
                [InlineKeyboardButton("🔙 بازگشت", callback_data='prices')]
            ])
        )
    
    # ======== قیمت سکه ========
    elif data == 'price_coin':
        price_data = prices.get_all_prices()
        coin_price = price_data.get('coin', 0)
        await query.edit_message_text(
            f"🪙 **قیمت سکه امامی**\n\n"
            f"💰 قیمت: {coin_price:,} تومان\n"
            f"🕐 {prices.get_current_time()}\n\n"
            f"🔹 برای بروزرسانی، گزینه زیر رو بزن.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 بروزرسانی", callback_data='price_coin')],
                [InlineKeyboardButton("🔙 بازگشت", callback_data='prices')]
            ])
        )
    
    # ======== همه قیمت‌ها ========
    elif data == 'price_all' or data == 'refresh_prices':
        price_data = prices.get_all_prices()
        message = prices.format_price_message(price_data)
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 بروزرسانی", callback_data='refresh_prices')],
                [InlineKeyboardButton("🔙 بازگشت", callback_data='prices')]
            ])
        )
    
    # ======== جستجوی محصولات ========
    elif data == 'search_product':
        await query.edit_message_text(
            "🛍️ **جستجوی محصولات**\n\n"
            "🔹 نام محصول مورد نظر را وارد کن:\n"
            "مثال: گوشی، لپ‌تاپ، ساعت، هدفون\n\n"
            "💡 برای جستجوی پیشرفته، گزینه زیر رو بزن.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔍 جستجوی پیشرفته", callback_data='advanced_search')],
                [InlineKeyboardButton("🔙 بازگشت", callback_data='back_to_menu')]
            ])
        )
        context.user_data['state'] = 'waiting_search_simple'
    
    # ======== جستجوی پیشرفته ========
    elif data == 'advanced_search':
        await query.edit_message_text(
            "🔍 **جستجوی پیشرفته**\n\n"
            "🔹 دسته‌بندی مورد نظر را انتخاب کن:\n\n"
            "💡 انتخاب دسته‌بندی باعث دقیق‌تر شدن نتایج میشه.",
            reply_markup=get_advanced_search_menu()
        )
    
    # ======== جستجوی پیشرفته با دسته‌بندی ========
    elif data.startswith('search_'):
        category = data.replace('search_', '')
        category_names = {
            'phone': 'گوشی',
            'laptop': 'لپ‌تاپ',
            'watch': 'ساعت',
            'headphone': 'هدفون',
            'camera': 'دوربین',
            'speaker': 'اسپیکر',
            'appliance': 'لوازم خانگی',
            'clothing': 'پوشاک',
            'book': 'کتاب'
        }
        category_name = category_names.get(category, 'محصولات')
        await query.edit_message_text(
            f"🔍 **جستجو در دسته‌بندی {category_name}**\n\n"
            f"🔹 نام محصول مورد نظر را وارد کن:\n"
            f"مثال: {category_name} سامسونگ، {category_name} شیائومی",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data='advanced_search')]])
        )
        context.user_data['state'] = 'waiting_search_advanced'
        context.user_data['search_category'] = category
    
    # ======== راهنما ========
    elif data == 'help':
        await query.edit_message_text(
            "📌 **راهنمای ربات**\n\n"
            "✅ **ثبت هزینه**: هزینه‌های روزانه خود را ثبت کنید.\n"
            "✅ **ثبت درآمد**: درآمدهای خود را ثبت کنید.\n"
            "✅ **گزارش ماهانه**: خلاصه مالی ماه جاری را مشاهده کنید.\n"
            "✅ **تاریخچه**: لیست ۲۰ تراکنش اخیر را ببینید.\n"
            "✅ **قیمت طلا و ارز**: قیمت لحظه‌ای طلا، دلار و سکه.\n"
            "✅ **جستجوی محصولات**: بهترین قیمت محصولات از دیجیکالا و ترب.\n\n"
            "💡 برای بازگشت به منو، از دکمه‌ی بازگشت استفاده کن.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data='back_to_menu')]])
        )
    
    # ======== بازگشت به منو ========
    elif data == 'back_to_menu':
        await query.edit_message_text(
            "👋 به منوی اصلی برگشتی.\n\n"
            "✨ یکی از گزینه‌های زیر رو انتخاب کن:",
            reply_markup=get_main_menu()
        )
        context.user_data['state'] = None

# ========== هندلر متن ==========
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id
    state = context.user_data.get('state')
    
    # ======== ثبت هزینه ========
    if state == 'waiting_expense':
        try:
            amount = int(text.replace(',', '').replace('،', '').replace(' ', ''))
            db.add_transaction(user_id, amount, "عمومی", "ثبت دستی", "expense")
            await update.message.reply_text(
                f"✅ هزینه {amount:,} تومانی ثبت شد.",
                reply_markup=get_main_menu()
            )
            context.user_data['state'] = None
        except ValueError:
            await update.message.reply_text(
                "❌ عدد رو درست وارد کن!",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data='back_to_menu')]])
            )
    
    # ======== ثبت درآمد ========
    elif state == 'waiting_income':
        try:
            amount = int(text.replace(',', '').replace('،', '').replace(' ', ''))
            db.add_transaction(user_id, amount, "عمومی", "ثبت دستی", "income")
            await update.message.reply_text(
                f"✅ درآمد {amount:,} تومانی ثبت شد.",
                reply_markup=get_main_menu()
            )
            context.user_data['state'] = None
        except ValueError:
            await update.message.reply_text(
                "❌ عدد رو درست وارد کن!",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data='back_to_menu')]])
            )
    
    # ======== جستجوی ساده ========
    elif state == 'waiting_search_simple':
        await update.message.reply_text("⏳ در حال جستجو در فروشگاه‌های آنلاین...")
        products = search.search_all_shops(text)
        message = search.format_product_message(products)
        await update.message.reply_text(
            message,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 جستجوی مجدد", callback_data='search_product')],
                [InlineKeyboardButton("🔍 جستجوی پیشرفته", callback_data='advanced_search')],
                [InlineKeyboardButton("🔙 بازگشت", callback_data='back_to_menu')]
            ]),
            disable_web_page_preview=True
        )
        context.user_data['state'] = None
    
    # ======== جستجوی پیشرفته ========
    elif state == 'waiting_search_advanced':
        category = context.user_data.get('search_category', '')
        category_names = {
            'phone': 'گوشی',
            'laptop': 'لپ‌تاپ',
            'watch': 'ساعت',
            'headphone': 'هدفون',
            'camera': 'دوربین',
            'speaker': 'اسپیکر',
            'appliance': 'لوازم خانگی',
            'clothing': 'پوشاک',
            'book': 'کتاب'
        }
        category_name = category_names.get(category, 'محصولات')
        await update.message.reply_text(f"⏳ در حال جستجو در دسته‌بندی {category_name}...")
        products = search.search_all_shops(f"{text} {category_name}")
        message = search.format_product_message(products)
        await update.message.reply_text(
            message,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 جستجوی مجدد", callback_data='advanced_search')],
                [InlineKeyboardButton("🔙 بازگشت", callback_data='back_to_menu')]
            ]),
            disable_web_page_preview=True
        )
        context.user_data['state'] = None
        context.user_data['search_category'] = None
    
    # ======== پیام‌های دیگر ========
    else:
        await update.message.reply_text(
            "🔹 لطفاً از دکمه‌های منو استفاده کن.",
            reply_markup=get_main_menu()
        )

# ========== اصلی ==========
def main():
    # اجرای وب‌سرور برای Render
    threading.Thread(target=run_health_server, daemon=True).start()
    print(f"🌐 وب‌سرور روی پورت {PORT} روشن شد")
    
    # ساخت اپلیکیشن (بدون پارامتر اضافی)
    app = Application.builder().token(TOKEN).build()
    
    # اضافه کردن هندلرها
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    
    print("🚀 ربات مالی هوشمند روشن شد!")
    print("✨ نسخه با دکمه‌های شیشه‌ای و انتخابی")
    
    # اجرای ربات
    app.run_polling(poll_interval=1.0, drop_pending_updates=True)

if __name__ == '__main__':
    main()
