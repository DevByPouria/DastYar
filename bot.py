import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes

import config
import database as db
import ocr_handler as ocr
import price_fetcher as prices
import product_search as search

# ========== وب‌سرور برای رفع مشکل پورت در Render ==========
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Smart Wallet Bot is running!")

def run_health_server():
    server = HTTPServer(('0.0.0.0', config.PORT), HealthHandler)
    server.serve_forever()
# ===========================================================

# ========== منوی اصلی ==========
def get_main_menu():
    keyboard = [
        [InlineKeyboardButton("💰 ثبت هزینه", callback_data='add_expense')],
        [InlineKeyboardButton("📈 ثبت درآمد", callback_data='add_income')],
        [InlineKeyboardButton("📊 گزارش ماهانه", callback_data='report')],
        [InlineKeyboardButton("📸 اسکن فاکتور", callback_data='scan_bill')],
        [InlineKeyboardButton("💎 قیمت طلا و ارز", callback_data='prices')],
        [InlineKeyboardButton("🛍️ جستجوی محصولات", callback_data='search_product')],
        [InlineKeyboardButton("📋 تاریخچه تراکنش‌ها", callback_data='history')],
    ]
    return InlineKeyboardMarkup(keyboard)

# ========== هندلرها ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 سلام! به **دستیار مالی هوشمند** خوش اومدی.\n\n"
        "من می‌تونم این کارها رو برات انجام بدم:\n"
        "✅ ثبت هزینه و درآمد\n"
        "✅ خواندن فاکتور با دوربین\n"
        "✅ گزارش ماهانه و نمودار\n"
        "✅ قیمت لحظه‌ای طلا و دلار\n"
        "✅ جستجوی بهترین قیمت محصولات\n\n"
        "یکی از گزینه‌ها رو انتخاب کن:",
        reply_markup=get_main_menu()
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    
    # ---- ثبت هزینه ----
    if query.data == 'add_expense':
        await query.edit_message_text(
            "💸 مبلغ هزینه رو به تومان وارد کن (مثلاً ۲۵۰۰۰۰):",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data='back_to_menu')]])
        )
        context.user_data['state'] = 'waiting_expense_amount'
    
    # ---- ثبت درآمد ----
    elif query.data == 'add_income':
        await query.edit_message_text(
            "💰 مبلغ درآمد رو به تومان وارد کن:",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data='back_to_menu')]])
        )
        context.user_data['state'] = 'waiting_income_amount'
    
    # ---- گزارش ماهانه ----
    elif query.data == 'report':
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
        context.user_data['state'] = None
    
    # ---- اسکن فاکتور ----
    elif query.data == 'scan_bill':
        await query.edit_message_text(
            "📸 از فاکتور یا قبض خود عکس بفرست تا مبلغ رو تشخیص بدم:",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data='back_to_menu')]])
        )
        context.user_data['state'] = 'waiting_photo'
    
    # ---- قیمت طلا و ارز ----
    elif query.data == 'prices':
        await query.edit_message_text("⏳ در حال دریافت قیمت‌های لحظه‌ای...")
        price_data = prices.get_all_prices()
        message = prices.format_price_message(price_data)
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 بروزرسانی", callback_data='prices')],
                [InlineKeyboardButton("🔙 بازگشت", callback_data='back_to_menu')]
            ])
        )
    
    # ---- جستجوی محصولات ----
    elif query.data == 'search_product':
        await query.edit_message_text(
            "🔍 نام محصول مورد نظر را وارد کن (مثلاً گوشی، لپ‌تاپ، ساعت، ...):",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data='back_to_menu')]])
        )
        context.user_data['state'] = 'waiting_search_query'
    
    # ---- تاریخچه ----
    elif query.data == 'history':
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
    
    # ---- بازگشت به منو ----
    elif query.data == 'back_to_menu':
        await query.edit_message_text(
            "👋 به منوی اصلی برگشتی. یکی از گزینه‌ها رو انتخاب کن:",
            reply_markup=get_main_menu()
        )
        context.user_data['state'] = None

# ========== هندلرهای متنی ==========
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id
    state = context.user_data.get('state')
    
    # ---- ثبت هزینه ----
    if state == 'waiting_expense_amount':
        try:
            amount = int(text.replace(',', ''))
            await update.message.reply_text("📂 دسته‌بندی رو انتخاب کن (یا «سایر» رو بفرست):")
            context.user_data['temp_amount'] = amount
            context.user_data['state'] = 'waiting_expense_category'
        except ValueError:
            await update.message.reply_text("❌ عدد رو درست وارد کن!")
    
    elif state == 'waiting_expense_category':
        category = text.strip()
        amount = context.user_data.get('temp_amount', 0)
        db.add_transaction(user_id, amount, category, "ثبت دستی", "expense")
        await update.message.reply_text(
            f"✅ هزینه {amount:,} تومانی در دسته‌ی «{category}» ثبت شد.",
            reply_markup=get_main_menu()
        )
        context.user_data['state'] = None
        context.user_data['temp_amount'] = None
    
    # ---- ثبت درآمد ----
    elif state == 'waiting_income_amount':
        try:
            amount = int(text.replace(',', ''))
            await update.message.reply_text("📂 منبع درآمد رو وارد کن:")
            context.user_data['temp_amount'] = amount
            context.user_data['state'] = 'waiting_income_source'
        except ValueError:
            await update.message.reply_text("❌ عدد رو درست وارد کن!")
    
    elif state == 'waiting_income_source':
        source = text.strip()
        amount = context.user_data.get('temp_amount', 0)
        db.add_transaction(user_id, amount, source, "ثبت دستی", "income")
        await update.message.reply_text(
            f"✅ درآمد {amount:,} تومانی از «{source}» ثبت شد.",
            reply_markup=get_main_menu()
        )
        context.user_data['state'] = None
        context.user_data['temp_amount'] = None
    
    # ---- جستجوی محصولات ----
    elif state == 'waiting_search_query':
        await update.message.reply_text("⏳ در حال جستجو در فروشگاه‌های آنلاین... لطفاً صبر کن.")
        products = search.search_all_shops(text)
        message = search.format_product_message(products)
        await update.message.reply_text(
            message,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 جستجوی مجدد", callback_data='search_product')],
                [InlineKeyboardButton("🔙 بازگشت", callback_data='back_to_menu')]
            ])
        )
        context.user_data['state'] = None

# ========== هندلر عکس (اسکن فاکتور) ==========
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('state') == 'waiting_photo':
        photo_file = await update.message.photo[-1].get_file()
        file_bytes = await photo_file.download_as_bytearray()
        
        await update.message.reply_text("⏳ در حال خواندن فاکتور...")
        amount = ocr.extract_amount_from_image(file_bytes)
        
        if amount:
            db.add_transaction(update.effective_user.id, amount, "فاکتور", "تشخیص خودکار", "expense")
            await update.message.reply_text(
                f"✅ مبلغ {amount:,} تومان از روی فاکتور خونده شد و ثبت شد.",
                reply_markup=get_main_menu()
            )
        else:
            await update.message.reply_text(
                "❌ نتونستم مبلغ رو تشخیص بدم. لطفاً دستی وارد کن.",
                reply_markup=get_main_menu()
            )
        context.user_data['state'] = None

# ========== اصلی ==========
def main():
    # رفع مشکل پورت در Render
    threading.Thread(target=run_health_server, daemon=True).start()
    
    # ساخت اپلیکیشن
    app = Application.builder().token(config.TOKEN).build()
    
    # اضافه کردن هندلرها
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    
    print("🚀 ربات مالی هوشمند روشن شد!")
    app.run_polling()

if __name__ == '__main__':
    main()
