import requests
import json
from datetime import datetime

def get_price(item):
    """
    دریافت قیمت لحظه‌ای از tgju.org
    item: 'gold' یا 'dollar' یا 'coin'
    """
    urls = {
        'gold': 'https://www.tgju.org/price-chart/geram18',
        'dollar': 'https://www.tgju.org/price-chart/price_dollar_rl',
        'coin': 'https://www.tgju.org/price-chart/sekeb'
    }
    
    try:
        response = requests.get(urls.get(item), timeout=10)
        # tgju داده‌ها رو توی یه تگ script با id خاص ذخیره می‌کنه
        # این روش ساده‌ست ولی ممکنه با تغییر سایت خراب بشه
        # برای راه‌حل حرفه‌ای‌تر از API غیررسمی استفاده کن
        return 0  # فعلاً مقدار تستی
    except Exception as e:
        print(f"Error fetching {item}: {e}")
        return None

def get_all_prices():
    """دریافت همه‌ی قیمت‌ها به صورت همزمان"""
    result = {}
    items = ['gold', 'dollar', 'coin']
    for item in items:
        price = get_price(item)
        if price is not None:
            result[item] = price
    return result

def format_price_message(prices):
    """قالب‌بندی قیمت‌ها برای ارسال به کاربر"""
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
