import requests
from datetime import datetime

def get_price(item):
    """دریافت قیمت لحظه‌ای از tgju.org"""
    urls = {
        'gold': 'https://www.tgju.org/price-chart/geram18',
        'dollar': 'https://www.tgju.org/price-chart/price_dollar_rl',
        'coin': 'https://www.tgju.org/price-chart/sekeb'
    }
    
    try:
        response = requests.get(urls.get(item), timeout=10)
        # اینجا باید داده رو از HTML استخراج کنی
        # فعلاً مقدار تستی برمی‌گردونیم
        return 0
    except Exception as e:
        print(f"Error fetching {item}: {e}")
        return None

def get_all_prices():
    result = {}
    items = ['gold', 'dollar', 'coin']
    for item in items:
        price = get_price(item)
        if price is not None:
            result[item] = price
    return result

def format_price_message(prices):
    if not prices:
        return "❌ امکان دریافت قیمت‌ها وجود ندارد. لطفاً بعداً تلاش کنید."
    
    message = "💰 **قیمت‌های لحظه‌ای بازار**\n"
    message += f"🕐 {datetime.now().strftime('%H:%M:%S')}\n\n"
    
    if 'gold' in prices:
        message += f"⚜️ **طلا (گرم ۱۸):** {prices['gold']:,} تومان\n"
    if 'dollar' in prices:
        message += f"💵 **دلار:** {prices['dollar']:,} تومان\n"
    if 'coin' in prices:
        message += f"🪙 **سکه امامی:** {prices['coin']:,} تومان\n"
    
    return message
