import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes

import database as db
import price_fetcher as prices
import product_search as search

# ========== توکن ==========
TOKEN = os.getenv('TOKEN')
PORT = int(os.getenv('PORT', 10000))

# ========== وب‌سرور برای Render ==========
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running!")

def run_health_server():
    server = HTTPServer(('0.0.0.0', PORT), HealthHandler)
    server.serve_forever()

# ========== منوی اصلی ==========
def get_main_menu():
    keyboard = [
        [InlineKeyboardButton("💰 ثبت هزینه", callback_data='add_expense')],
        [InlineKeyboardButton("📈 ثبت درآمد", callback_data='add_income')],
        [InlineKeyboardButton("📊 گزارش ماهانه", callback_data='report')],
        [InlineKeyboardButton("💎 قیمت طلا و ارز", callback_data='prices')],
        [InlineKeyboardButton("🛍️ جستجوی محصولات", callback_data='search_product')],
        [InlineKeyboardButton("📋 تاریخچه", callback_data='history')],
    ]
    return InlineKeyboardMarkup(keyboard)

# ========== هندلر استارت ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 سلام! به **دستیار مالی هوشمند** خوش اومدی.\n\n"
        "من می‌تونم این کارها رو برات انجام بدم:\n"
        "✅ ثبت هزینه و درآمد\n"
        "✅ گزارش ماهانه\n"
        "✅ قیمت لحظه‌ای طلا و دلار\n"
        "✅ جستجوی بهترین قیمت محصولات\n\n"
        "یکی از گزینه‌ها رو انتخاب کن:",
        reply_markup=get_main_menu()
    )

# ========== هندلر دکمه‌ها ==========
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    
    if query.data == 'add_expense':
        await query.edit_message_text("💸 مبلغ هزینه رو به تومان وارد کن (مثلاً ۲۵۰۰۰۰):")
        context.user_data['state'] = 'waiting_expense'
    
    elif query.data == 'add_income':
        await query.edit_message_text("💰 مبلغ درآمد رو به تومان وارد کن:")
        context.user_data['state'] = 'waiting_income'
    
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
    
    elif query.data == 'search_product':
        await query.edit_message_text("🔍 نام محصول مورد نظر را وارد کن (مثلاً گوشی، لپ‌تاپ، ساعت):")
        context.user_data['state'] = 'waiting_search'
    
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
    
    elif query.data == 'back_to_menu':
        await query.edit_message_text("👋 به منوی اصلی برگشتی.", reply_markup=get_main_menu())
        context.user_data['state'] = None

# ========== هندلر متن ==========
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id
    state = context.user_data.get('state')
    
    if state == 'waiting_expense':
        try:
            amount = int(text.replace(',', ''))
            db.add_transaction(user_id, amount, "عمومی", "ثبت دستی", "expense")
            await update.message.reply_text(f"✅ هزینه {amount:,} تومانی ثبت شد.", reply_markup=get_main_menu())
            context.user_data['state'] = None
        except ValueError:
            await update.message.reply_text("❌ عدد رو درست وارد کن!")
    
    elif state == 'waiting_income':
        try:
            amount = int(text.replace(',', ''))
            db.add_transaction(user_id, amount, "عمومی", "ثبت دستی", "income")
            await update.message.reply_text(f"✅ درآمد {amount:,} تومانی ثبت شد.", reply_markup=get_main_menu())
            context.user_data['state'] = None
        except ValueError:
            await update.message.reply_text("❌ عدد رو درست وارد کن!")
    
    elif state == 'waiting_search':
        await update.message.reply_text("⏳ در حال جستجو در فروشگاه‌های آنلاین...")
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
    
    else:
        await update.message.reply_text("لطفاً از دکمه‌های منو استفاده کن.", reply_markup=get_main_menu())

# ========== اصلی ==========
def main():
    # وب‌سرور برای Render
    threading.Thread(target=run_health_server, daemon=True).start()
    print(f"🌐 وب‌سرور روی پورت {PORT} روشن شد")
    
    # ربات
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    
    print("🚀 ربات مالی هوشمند روشن شد!")
    app.run_polling()

if __name__ == '__main__':
    main()
