import requests
from datetime import datetime
import pytz

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept': 'application/json'
}

def get_current_time():
    """محاسبه ساعت دقیق تهران"""
    tehran_tz = pytz.timezone('Asia/Tehran')
    now = datetime.now(tehran_tz)
    return now.strftime('%H:%M:%S')

def get_all_prices():
    """دریافت قیمت‌های واقعی طلا، دلار و سکه از APIهای پایدار"""
    prices = {'gold': 0, 'dollar': 0, 'coin': 0}
    
    # API اول: BRS API (سازگار با سرورهای خارجی)
    try:
        url = "https://brsapi.ir/FreeTomanExchangeApi/Short.json"
        response = requests.get(url, headers=HEADERS, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            # استخراج قیمت طلا ۱۸ عیار
            for item in data.get('gold', []):
                if '18' in item.get('name', ''):
                    prices['gold'] = int(item.get('price', 0))
                    break
            
            # استخراج قیمت دلار
            for item in data.get('currency', []):
                if 'دلار' in item.get('name', ''):
                    prices['dollar'] = int(item.get('price', 0))
                    break
                    
            # استخراج قیمت سکه امامی
            for item in data.get('coin', []):
                if 'امامی' in item.get('name', ''):
                    prices['coin'] = int(item.get('price', 0))
                    break
    except Exception as e:
        print(f"Error fetching from Primary BRS API: {e}")

    # API دوم (پشتیبان): Navasan API در صورت عدم پاسخگویی API اول
    if prices['gold'] == 0 or prices['dollar'] == 0:
        try:
            url_backup = "https://api.navasan.tech/latest/?api_key=free"
            res = requests.get(url_backup, headers=HEADERS, timeout=10)
            if res.status_code == 200:
                b_data = res.json()
                if 'geram18' in b_data and 'value' in b_data['geram18']:
                    prices['gold'] = int(b_data['geram18']['value'])
                if 'usd_sell' in b_data and 'value' in b_data['usd_sell']:
                    prices['dollar'] = int(b_data['usd_sell']['value'])
                if 'sekke' in b_data and 'value' in b_data['sekke']:
                    prices['coin'] = int(b_data['sekke']['value'])
        except Exception as e:
            print(f"Error fetching backup API: {e}")

    return prices

def format_price_message(prices):
    if not prices or all(v == 0 for v in prices.values()):
        return "❌ امکان دریافت قیمت‌ها در این لحظه وجود ندارد. لطفاً دقایقی دیگر دوباره تلاش کنید."
    
    message = "💎 **قیمت‌های لحظه‌ای و واقعی بازار**\n"
    message += f"🕐 زمان استعلام (به وقت تهران): {get_current_time()}\n\n"
    
    if prices.get('gold'):
        message += f"⚜️ طلا (گرم ۱۸): {prices['gold']:,} تومان\n"
    if prices.get('dollar'):
        message += f"💵 دلار: {prices['dollar']:,} تومان\n"
    if prices.get('coin'):
        message += f"🪙 سکه امامی: {prices['coin']:,} تومان\n"
        
    return message
