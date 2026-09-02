import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes

# ========== توکن ==========
TOKEN = os.getenv('TOKEN')

# ========== وب‌سرور برای رفع مشکل پورت در Render ==========
PORT = int(os.getenv('PORT', 10000))

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
        [InlineKeyboardButton("📸 اسکن فاکتور", callback_data='scan_bill')],
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
        "✅ خواندن فاکتور با دوربین\n"
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
    
    if query.data == 'add_expense':
        await query.edit_message_text("💸 مبلغ هزینه رو به تومان وارد کن:")
        context.user_data['state'] = 'waiting_expense'
    
    elif query.data == 'add_income':
        await query.edit_message_text("💰 مبلغ درآمد رو به تومان وارد کن:")
        context.user_data['state'] = 'waiting_income'
    
    elif query.data == 'report':
        await query.edit_message_text("📊 گزارش ماهانه:\n\nدرآمد: ۰ تومان\nهزینه: ۰ تومان\nمانده: ۰ تومان")
    
    elif query.data == 'scan_bill':
        await query.edit_message_text("📸 از فاکتور یا قبض خود عکس بفرست:")
        context.user_data['state'] = 'waiting_photo'
    
    elif query.data == 'prices':
        await query.edit_message_text("💰 قیمت لحظه‌ای:\n\nطلا: در حال دریافت...")
    
    elif query.data == 'search_product':
        await query.edit_message_text("🔍 نام محصول مورد نظر را وارد کن:")
        context.user_data['state'] = 'waiting_search'
    
    elif query.data == 'history':
        await query.edit_message_text("📋 تاریخچه تراکنش‌ها:\n\nهیچ تراکنشی ثبت نشده.")
    
    elif query.data == 'back_to_menu':
        await query.edit_message_text("👋 به منوی اصلی برگشتی.", reply_markup=get_main_menu())
        context.user_data['state'] = None

# ========== هندلر متن ==========
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    state = context.user_data.get('state')
    
    if state == 'waiting_expense':
        await update.message.reply_text(f"✅ هزینه {update.message.text} تومانی ثبت شد.")
        context.user_data['state'] = None
    
    elif state == 'waiting_income':
        await update.message.reply_text(f"✅ درآمد {update.message.text} تومانی ثبت شد.")
        context.user_data['state'] = None
    
    elif state == 'waiting_search':
        await update.message.reply_text(f"🔍 در حال جستجوی «{update.message.text}»...\n(این بخش در حال توسعه است)")
        context.user_data['state'] = None
    
    else:
        await update.message.reply_text("لطفاً از دکمه‌های منو استفاده کن.", reply_markup=get_main_menu())

# ========== هندلر عکس ==========
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('state') == 'waiting_photo':
        await update.message.reply_text("📸 عکس دریافت شد. در حال پردازش...\n(این بخش در حال توسعه است)")
        context.user_data['state'] = None

# ========== اصلی ==========
def main():
    # اجرای وب‌سرور برای Render
    threading.Thread(target=run_health_server, daemon=True).start()
    
    # ساخت اپلیکیشن
    app = Application.builder().token(TOKEN).build()
    
    # اضافه کردن هندلرها
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    
    print("🚀 ربات مالی هوشمند روشن شد!")
    app.run_polling()

if __name__ == '__main__':
    main()
