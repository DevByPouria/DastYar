import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes
from telegram.request import HTTPXRequest
import httpx

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
def get_main_menu(selected_category=None):
    """منوی اصلی با طراحی شیشه‌ای و دکمه‌های انتخابی"""
    
    # دسته‌بندی‌های اصلی
    categories = [
        ('ثبت هزینه', 'add_expense', '💰'),
        ('ثبت درآمد', 'add_income', '📈'),
        ('گزارش ماهانه', 'report', '📊'),
        ('تاریخچه', 'history', '📋'),
        ('قیمت طلا و ارز', 'prices', '💎'),
        ('جستجوی محصولات', 'search_product', '🛍️'),
    ]
    
    keyboard = []
    row = []
    for i, (name, callback, emoji) in enumerate(categories):
        # دکمه با استایل شیشه‌ای و انتخاب‌شونده
        if callback == selected_category:
            button_text = f"✅ {emoji} {name}"
        else:
            button_text = f"{emoji} {name}"
        
        row.append(InlineKeyboardButton(button_text, callback_data=callback))
        
        # هر ردیف ۲ دکمه (برای نمای شیشه‌ای بهتر)
        if len(row) == 2 or i == len(categories) - 1:
            keyboard.append(row)
            row = []
    
    # دکمه‌های ویژه در پایین
    keyboard.append([
        InlineKeyboardButton("🔍 جستجوی پیشرفته", callback_data='advanced_search'),
        InlineKeyboardButton("📌 راهنما", callback_data='help')
    ])
    
    return InlineKeyboardMarkup(keyboard)

# ========== منوی جستجوی پیشرفته (انتخاب دسته‌بندی) ==========
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

# ========== منوی قیمت‌ها (با انتخاب نوع) ==========
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
    
    # ======== بخش ثبت هزینه ========
    if data == 'add_expense':
        await query.edit_message_text(
            "💸 مبلغ هزینه رو به تومان وارد کن (مثلاً ۲۵۰۰۰۰):\n\n"
            "🔹 می‌تونی عدد رو با کاما هم بنویسی (مثل ۲۵۰,۰۰۰)",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data='back_to_menu')]])
        )
        context.user_data['state'] = 'waiting_expense'
    
    # ======== بخش ثبت درآمد ========
    elif data == 'add_income':
        await query.edit_message_text(
            "💰 مبلغ درآمد رو به تومان وارد کن:\n\n"
            "🔹 می‌تونی عدد رو با کاما هم بنویسی",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data='back_to_menu')]])
        )
        context.user_data['state'] = 'waiting_income'
    
    # ======== بخش گزارش ========
    elif data == 'report':
        total_income, total_expense = db.get_monthly_summary(user_id)
        balance = total_income - total_expense
        await query.edit_message_text(
            f"📊 **گزارش ماهانه**\n\n"
            f"💰 **درآمد:** {total_income:,} تومان\n"
            f"💸 **هزینه:** {total_expense:,} تومان\n"
            f"📌 **مانده:** {balance:,} تومان\n"
            f"💳 **وضعیت:** {'✅ مثبت' if balance >= 0 else '❌ منفی'}\n\n"
            f"🔹 برای مشاهده جزئیات، از گزینه تاریخچه استفاده کن.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data='back_to_menu')]])
        )
    
    # ======== بخش تاریخچه ========
    elif data == 'history':
        transactions = db.get_all_transactions(user_id)
        if not transactions:
            await query.edit_message_text(
                "📋 **تاریخچه تراکنش‌ها**\n\n"
                "❌ هنوز هیچ تراکنشی ثبت نشده!\n\n"
                "💡 برای شروع، یک هزینه یا درآمد ثبت کن.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data='back_to_menu')]])
            )
            return
        
        message = "📋 **۲۰ تراکنش اخیر**\n\n"
        for amount, category, desc, trans_type, date in transactions:
            emoji = "💰" if trans_type == 'income' else "💸"
            message += f"{emoji} {date} - **{category}**: {amount:,} تومان"
            if desc:
                message += f" ({desc})"
            message += "\n"
        
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data='back_to_menu')]])
        )
    
    # ======== بخش قیمت‌ها ========
    elif data == 'prices':
        await query.edit_message_text(
            "💎 **قیمت‌های لحظه‌ای بازار**\n\n"
            "🔹 یکی از گزینه‌های زیر رو انتخاب کن:",
            reply_markup=get_price_menu()
        )
    
    # ======== بخش قیمت طلا ========
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
    
    # ======== بخش قیمت دلار ========
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
    
    # ======== بخش قیمت سکه ========
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
    
    # ======== بخش همه قیمت‌ها ========
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
    
    # ======== بخش جستجوی محصولات ========
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
            f"مثال: {category_name} سامسونگ، {category_name} شیائومی\n\n"
            f"💡 جستجو در فروشگاه‌های دیجیکالا و ترب انجام میشه.",
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
                f"✅ هزینه {amount:,} تومانی ثبت شد.\n\n"
                f"💡 برای ثبت هزینه جدید، دوباره گزینه ثبت هزینه رو انتخاب کن.",
                reply_markup=get_main_menu()
            )
            context.user_data['state'] = None
        except ValueError:
            await update.message.reply_text(
                "❌ عدد رو درست وارد کن!\n\n"
                "🔹 عدد رو بدون کاما یا با کاما بنویس (مثل ۲۵۰۰۰۰ یا ۲۵۰,۰۰۰)",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data='back_to_menu')]])
            )
    
    # ======== ثبت درآمد ========
    elif state == 'waiting_income':
        try:
            amount = int(text.replace(',', '').replace('،', '').replace(' ', ''))
            db.add_transaction(user_id, amount, "عمومی", "ثبت دستی", "income")
            await update.message.reply_text(
                f"✅ درآمد {amount:,} تومانی ثبت شد.\n\n"
                f"💡 برای ثبت درآمد جدید، دوباره گزینه ثبت درآمد رو انتخاب کن.",
                reply_markup=get_main_menu()
            )
            context.user_data['state'] = None
        except ValueError:
            await update.message.reply_text(
                "❌ عدد رو درست وارد کن!\n\n"
                "🔹 عدد رو بدون کاما یا با کاما بنویس (مثل ۲۵۰۰۰۰ یا ۲۵۰,۰۰۰)",
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
        await update.message.reply_text(
            f"⏳ در حال جستجو در دسته‌بندی {category_name}...\n"
            f"🔍 عبارت: {text}"
        )
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
    
    # ======== پیام‌های غیرمجاز ========
    else:
        await update.message.reply_text(
            "🔹 لطفاً از دکمه‌های منو استفاده کن.\n\n"
            "💡 برای شروع، دکمه‌ی /start رو بزن.",
            reply_markup=get_main_menu()
        )

# ========== هندلر عکس ==========
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📸 **اسکن فاکتور**\n\n"
        "❌ این بخش در حال توسعه است.\n\n"
        "💡 لطفاً از دکمه‌های منو برای ثبت هزینه یا درآمد استفاده کن.",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data='back_to_menu')]])
    )

# ========== اصلی ==========
def main():
    # اجرای وب‌سرور برای Render
    threading.Thread(target=run_health_server, daemon=True).start()
    print(f"🌐 وب‌سرور روی پورت {PORT} روشن شد")
    
    # تنظیم timeout برای جلوگیری از TimedOut
    http_client = httpx.AsyncClient(timeout=60.0)
    request = HTTPXRequest(http_client=http_client)
    
    # ساخت اپلیکیشن
    app = Application.builder().token(TOKEN).request(request).build()
    
    # اضافه کردن هندلرها
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    
    print("🚀 ربات مالی هوشمند روشن شد!")
    print("✨ نسخه با دکمه‌های شیشه‌ای و انتخابی")
    
    # اجرای ربات
    app.run_polling(poll_interval=1.0, timeout=60, drop_pending_updates=True)

if __name__ == '__main__':
    main()
