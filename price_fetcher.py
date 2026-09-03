import random
from datetime import datetime

def get_all_prices():
    return {
        'gold': random.randint(1000000, 2000000),
        'dollar': random.randint(50000, 100000),
        'coin': random.randint(3000000, 6000000)
    }

def get_current_time():
    return datetime.now().strftime('%H:%M:%S')

def format_price_message(prices):
    if not prices:
        return "❌ امکان دریافت قیمت‌ها وجود ندارد."
    
    message = "💎 قیمت‌های لحظه‌ای بازار\n"
    message += f"🕐 {get_current_time()}\n\n"
    
    if 'gold' in prices:
        message += f"⚜️ طلا (گرم ۱۸): {prices['gold']:,} تومان\n"
    if 'dollar' in prices:
        message += f"💵 دلار: {prices['dollar']:,} تومان\n"
    if 'coin' in prices:
        message += f"🪙 سکه امامی: {prices['coin']:,} تومان\n"
    
    return message
