import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes

import database as db
import price_fetcher as prices
import product_search as search

# ========== تنظیمات اولیه ==========
TOKEN = os.getenv('TOKEN')
PORT = int(os.getenv('PORT', 10000))
ADMIN_ID = 7012983895  # ⚠️ شماره کاربری خودت رو اینجا بذار!

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

# ========== منوها ==========
def get_main_menu():
    keyboard = [
        [InlineKeyboardButton("💰 ثبت هزینه", callback_data='add_expense'),
         InlineKeyboardButton("📈 ثبت درآمد", callback_data='add_income')],
        [InlineKeyboardButton("📊 گزارش ماهانه", callback_data='report'),
         InlineKeyboardButton("📋 تاریخچه", callback_data='history')],
        [InlineKeyboardButton("💎 قیمت طلا و ارز", callback_data='prices'),
         InlineKeyboardButton("🛍️ جستجوی محصولات", callback_data='search_product')],
        [InlineKeyboardButton("🔍 جستجوی پیشرفته", callback_data='advanced_search'),
         InlineKeyboardButton("📌 راهنما", callback_data='help')],
        [InlineKeyboardButton("📱 ثبت شماره تلفن", callback_data='share_phone')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_advanced_search_menu():
    keyboard = [
        [InlineKeyboardButton("📱 گوشی", callback_data='search_phone'),
         InlineKeyboardButton("💻 لپ‌تاپ", callback_data='search_laptop'),
         InlineKeyboardButton("⌚ ساعت", callback_data='search_watch')],
        [InlineKeyboardButton("🎧 هدفون", callback_data='search_headphone'),
         InlineKeyboardButton("📷 دوربین", callback_data='search_camera'),
         InlineKeyboardButton("🔊 اسپیکر", callback_data='search_speaker')],
        [InlineKeyboardButton("🛋️ لوازم خانگی", callback_data='search_appliance'),
         InlineKeyboardButton("👗 پوشاک", callback_data='search_clothing'),
         InlineKeyboardButton("📚 کتاب", callback_data='search_book')],
        [InlineKeyboardButton("🔙 بازگشت", callback_data='back_to_menu')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_price_menu():
    keyboard = [
        [InlineKeyboardButton("⚜️ طلا", callback_data='price_gold'),
         InlineKeyboardButton("💵 دلار", callback_data='price_dollar'),
         InlineKeyboardButton("🪙 سکه", callback_data='price_coin')],
        [InlineKeyboardButton("📊 همه قیمت‌ها", callback_data='price_all'),
         InlineKeyboardButton("🔄 بروزرسانی", callback_data='refresh_prices')],
        [InlineKeyboardButton("🔙 بازگشت", callback_data='back_to_menu')]
    ]
    return InlineKeyboardMarkup(keyboard)

# ========== استارت ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db.save_user(user)
    
    first_name = user.first_name or 'کاربر عزیز'
    user_id = user.id
    username = f"@{user.username}" if user.username else 'ندارد'
    full_name = f"{user.first_name or ''} {user.last_name or ''}".strip() or 'ندارد'
    language = user.language_code or 'نامشخص'
    
    message = (
        f"👋 سلام {first_name}! به دستیار مالی هوشمند خوش اومدی.\n\n"
        f"📌 اطلاعات شما ثبت شد:\n"
        f"🆔 شناسه: {user_id}\n"
        f"👤 نام: {full_name}\n"
        f"📛 یوزرنیم: {username}\n"
        f"🌐 زبان: {language}\n\n"
        "💡 از منوی زیر یکی از گزینه‌ها رو انتخاب کن:"
    )
    
    await update.message.reply_text(message, reply_markup=get_main_menu())

# ========== دستور ادمین ==========
async def admin_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ شما دسترسی به این بخش ندارید.")
        return
    
    users = db.get_all_users()
    count = db.get_user_count()
    
    if not users:
        await update.message.reply_text("📊 هیچ کاربری ثبت نشده.")
        return
    
    message = f"📊 لیست کاربران ({count} نفر)\n\n"
    for user in users[:10]:
        user_id, username, first_name, last_name, phone, lang, is_bot, first_seen, last_seen, interactions, active, data = user
        name = f"{first_name or ''} {last_name or ''}".strip() or "بدون نام"
        uname = f"@{username}" if username else "❌"
        phone_str = phone or "❌"
        message += f"🆔 {user_id} - {name}\n"
        message += f"📛 {uname} - 📱 {phone_str}\n"
        message += f"📅 اولین بازدید: {first_seen}\n\n"
    
    if count > 10:
        message += f"... و {count - 10} نفر دیگر"
    
    await update.message.reply_text(message)

# ========== دکمه‌ها ==========
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    data = query.data
    
    # ===== اشتراک شماره =====
    if data == 'share_phone':
        keyboard = [[InlineKeyboardButton("📱 ارسال شماره تلفن", request_contact=True)]]
        await query.edit_message_text(
            "📱 لطفاً دکمه زیر رو بزن تا شماره‌ات رو برام بفرستی:\n\n"
            "🔹 این شماره فقط برای ارتباط با شما ذخیره میشه.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    # ===== ثبت هزینه =====
    elif data == 'add_expense':
        await query.edit_message_text(
            "💸 مبلغ هزینه رو به تومان وارد کن (مثلاً ۲۵۰۰۰۰):",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data='back_to_menu')]])
        )
        context.user_data['state'] = 'waiting_expense'
    
    # ===== ثبت درآمد =====
    elif data == 'add_income':
        await query.edit_message_text(
            "💰 مبلغ درآمد رو به تومان وارد کن:",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data='back_to_menu')]])
        )
        context.user_data['state'] = 'waiting_income'
    
    # ===== گزارش =====
    elif data == 'report':
        total_income, total_expense = db.get_monthly_summary(user_id)
        balance = total_income - total_expense
        status = '✅ مثبت' if balance >= 0 else '❌ منفی'
        await query.edit_message_text(
            f"📊 گزارش ماهانه\n\n"
            f"💰 درآمد: {total_income:,} تومان\n"
            f"💸 هزینه: {total_expense:,} تومان\n"
            f"📌 مانده: {balance:,} تومان\n"
            f"💳 وضعیت: {status}",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data='back_to_menu')]])
        )
    
    # ===== تاریخچه =====
    elif data == 'history':
        transactions = db.get_all_transactions(user_id)
        if not transactions:
            await query.edit_message_text(
                "📋 تاریخچه تراکنش‌ها\n\nهیچ تراکنشی ثبت نشده!",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data='back_to_menu')]])
            )
            return
        message = "📋 ۲۰ تراکنش اخیر\n\n"
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
    
   # ===== بخش نمایش تصویر قیمت‌ها =====
    elif data == 'prices':
        await query.edit_message_text("💎 قیمت‌های لحظه‌ای بازار", reply_markup=get_price_menu())

    elif data in ['price_gold', 'price_dollar', 'price_coin', 'price_all', 'refresh_prices']:
        # حذف پیام متنی قبلی برای ارسال عکس جدید
        await query.message.delete()
        
        status_msg = await context.bot.send_message(
            chat_id=query.message.chat_id, 
            text="⏳ در حال تولید تصویر قیمت‌ها..."
        )
        
        # تولید عکس جدول قیمت‌ها
        photo_bytes = prices.generate_price_image()
        
        # حذف پیام در حال بارگذاری
        await status_msg.delete()
        
        # ارسال عکس
        await context.bot.send_photo(
            chat_id=query.message.chat_id,
            photo=photo_bytes,
            caption="💎 **تابلو قیمت‌های زنده بازار**",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 بروزرسانی", callback_data='refresh_prices')],
                [InlineKeyboardButton("🔙 بازگشت", callback_data='back_to_menu')]
            ])
        )
    
    # ===== جستجو =====
    elif data == 'search_product':
        await query.edit_message_text(
            "🛍️ جستجوی محصولات\n\n🔹 نام محصول رو وارد کن (مثل گوشی، لپ‌تاپ):",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔍 جستجوی پیشرفته", callback_data='advanced_search')],
                [InlineKeyboardButton("🔙 بازگشت", callback_data='back_to_menu')]
            ])
        )
        context.user_data['state'] = 'waiting_search'
    
    elif data == 'advanced_search':
        await query.edit_message_text("🔍 جستجوی پیشرفته\n\nدسته‌بندی مورد نظر رو انتخاب کن:", reply_markup=get_advanced_search_menu())
    
    elif data.startswith('search_'):
        category = data.replace('search_', '')
        names = {'phone': 'گوشی', 'laptop': 'لپ‌تاپ', 'watch': 'ساعت', 'headphone': 'هدفون',
                 'camera': 'دوربین', 'speaker': 'اسپیکر', 'appliance': 'لوازم خانگی',
                 'clothing': 'پوشاک', 'book': 'کتاب'}
        category_name = names.get(category, 'محصولات')
        await query.edit_message_text(
            f"🔍 جستجو در {category_name}\n\nنام محصول رو وارد کن:",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data='advanced_search')]])
        )
        context.user_data['state'] = 'waiting_search_advanced'
        context.user_data['search_category'] = category
    
    # ===== راهنما =====
    elif data == 'help':
        await query.edit_message_text(
            "📌 راهنمای ربات\n\n"
            "✅ ثبت هزینه و درآمد\n"
            "✅ گزارش ماهانه\n"
            "✅ تاریخچه تراکنش‌ها\n"
            "✅ قیمت طلا و ارز\n"
            "✅ جستجوی محصولات\n\n"
            "💡 با دکمه‌های منو کار کن.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data='back_to_menu')]])
        )
    
    # ===== بازگشت =====
    elif data == 'back_to_menu':
        await query.message.delete()
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text="👋 به منوی اصلی برگشتی.",
            reply_markup=get_main_menu()
        )
        context.user_data['state'] = None

# ========== هندلر شماره تلفن ==========
async def handle_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    contact = update.message.contact
    if contact.user_id == update.effective_user.id:
        db.update_user_phone(contact.user_id, contact.phone_number)
        await update.message.reply_text(
            f"✅ شماره تلفن شما ({contact.phone_number}) ثبت شد.",
            reply_markup=get_main_menu()
        )
    else:
        await update.message.reply_text("❌ لطفاً شماره خودت رو ارسال کن.")

# ========== هندلر متن (نسخه بروزرسانی شده برای لینک‌های واقعی) ==========
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id
    state = context.user_data.get('state')
    
    # ۱. ثبت هزینه
    if state == 'waiting_expense':
        try:
            amount = int(text.replace(',', ''))
            db.add_transaction(user_id, amount, "عمومی", "دستی", "expense")
            await update.message.reply_text(f"✅ هزینه {amount:,} تومانی ثبت شد.", reply_markup=get_main_menu())
            context.user_data['state'] = None
        except:
            await update.message.reply_text("❌ لطفاً مبلغ را به صورت عدد وارد کنید!")
    
    # ۲. ثبت درآمد
    elif state == 'waiting_income':
        try:
            amount = int(text.replace(',', ''))
            db.add_transaction(user_id, amount, "عمومی", "دستی", "income")
            await update.message.reply_text(f"✅ درآمد {amount:,} تومانی ثبت شد.", reply_markup=get_main_menu())
            context.user_data['state'] = None
        except:
            await update.message.reply_text("❌ لطفاً مبلغ را به صورت عدد وارد کنید!")
    
    # ۳. جستجوی عمومی محصولات (با داده واقعی و لینک Markdown)
    elif state == 'waiting_search':
        await update.message.reply_text("⏳ در حال دریافت اطلاعات واقعی از دیجیکالا...")
        products = search.search_all_shops(text)
        await update.message.reply_text(
            search.format_product_message(products),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 دوباره", callback_data='search_product')],
                [InlineKeyboardButton("🔙 بازگشت", callback_data='back_to_menu')]
            ]),
            parse_mode='Markdown',
            disable_web_page_preview=True
        )
        context.user_data['state'] = None
    
    # ۴. جستجوی پیشرفته محصولات (با داده واقعی و لینک Markdown)
    elif state == 'waiting_search_advanced':
        category = context.user_data.get('search_category', '')
        names = {
            'phone': 'گوشی', 'laptop': 'لپ‌تاپ', 'watch': 'ساعت', 'headphone': 'هدفون',
            'camera': 'دوربین', 'speaker': 'اسپیکر', 'appliance': 'لوازم خانگی',
            'clothing': 'پوشاک', 'book': 'کتاب'
        }
        category_name = names.get(category, 'محصولات')
        await update.message.reply_text(f"⏳ در حال جستجوی واقعی در دسته‌بندی {category_name}...")
        
        products = search.search_all_shops(f"{text} {category_name}")
        await update.message.reply_text(
            search.format_product_message(products),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 دوباره", callback_data='advanced_search')],
                [InlineKeyboardButton("🔙 بازگشت", callback_data='back_to_menu')]
            ]),
            parse_mode='Markdown',
            disable_web_page_preview=True
        )
        context.user_data['state'] = None
        context.user_data['search_category'] = None
    
    else:
        await update.message.reply_text("🔹 لطفاً از دکمه‌های منو استفاده کنید.", reply_markup=get_main_menu())
    
    # ===== ثبت هزینه =====
    if state == 'waiting_expense':
        try:
            amount = int(text.replace(',', ''))
            db.add_transaction(user_id, amount, "عمومی", "دستی", "expense")
            await update.message.reply_text(f"✅ هزینه {amount:,} تومانی ثبت شد.", reply_markup=get_main_menu())
            context.user_data['state'] = None
        except:
            await update.message.reply_text("❌ عدد رو درست وارد کن!")
    
    # ===== ثبت درآمد =====
    elif state == 'waiting_income':
        try:
            amount = int(text.replace(',', ''))
            db.add_transaction(user_id, amount, "عمومی", "دستی", "income")
            await update.message.reply_text(f"✅ درآمد {amount:,} تومانی ثبت شد.", reply_markup=get_main_menu())
            context.user_data['state'] = None
        except:
            await update.message.reply_text("❌ عدد رو درست وارد کن!")
    
    # ===== جستجوی ساده =====
    elif state == 'waiting_search':
        await update.message.reply_text("⏳ در حال جستجو...")
        products = search.search_all_shops(text)
        await update.message.reply_text(
            search.format_product_message(products),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 دوباره", callback_data='search_product')],
                [InlineKeyboardButton("🔙 بازگشت", callback_data='back_to_menu')]
            ]),
            disable_web_page_preview=True
        )
        context.user_data['state'] = None
    
    # ===== جستجوی پیشرفته =====
    elif state == 'waiting_search_advanced':
        category = context.user_data.get('search_category', '')
        names = {'phone': 'گوشی', 'laptop': 'لپ‌تاپ', 'watch': 'ساعت', 'headphone': 'هدفون',
                 'camera': 'دوربین', 'speaker': 'اسپیکر', 'appliance': 'لوازم خانگی',
                 'clothing': 'پوشاک', 'book': 'کتاب'}
        category_name = names.get(category, 'محصولات')
        await update.message.reply_text(f"⏳ در حال جستجو در {category_name}...")
        products = search.search_all_shops(f"{text} {category_name}")
        await update.message.reply_text(
            search.format_product_message(products),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 دوباره", callback_data='advanced_search')],
                [InlineKeyboardButton("🔙 بازگشت", callback_data='back_to_menu')]
            ]),
            disable_web_page_preview=True
        )
        context.user_data['state'] = None
        context.user_data['search_category'] = None
    
    else:
        await update.message.reply_text("🔹 لطفاً از دکمه‌های منو استفاده کن.", reply_markup=get_main_menu())

# ========== اجرای اصلی ==========
def main():
    threading.Thread(target=run_health_server, daemon=True).start()
    print(f"🌐 وب‌سرور روی پورت {PORT} روشن شد")
    
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin_users", admin_users))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.CONTACT, handle_contact))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    
    print("🚀 ربات مالی هوشمند روشن شد!")
    app.run_polling(poll_interval=1.0, drop_pending_updates=True)

if __name__ == '__main__':
    main()
