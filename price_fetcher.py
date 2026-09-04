import requests
from datetime import datetime

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept': 'application/json'
}

def get_all_prices():
    """دریافت واقعی و زنده قیمت طلا، دلار و سکه از API معتبر"""
    prices = {}
    
    # منبع ۱: API زنده سرویس TGJU / Navasan
    try:
        url = "https://api.navasan.tech/latest/?api_key=free"
        response = requests.get(url, headers=HEADERS, timeout=8)
        
        if response.status_code == 200:
            data = response.json()
            
            # قیمت طلای ۱۸ عیار
            if 'geram18' in data and 'value' in data['geram18']:
                prices['gold'] = int(data['geram18']['value'])
                
            # قیمت دلار
            if 'usd_sell' in data and 'value' in data['usd_sell']:
                prices['dollar'] = int(data['usd_sell']['value'])
                
            # قیمت سکه امامی
            if 'sekke' in data and 'value' in data['sekke']:
                prices['coin'] = int(data['sekke']['value'])
                
    except Exception as e:
        print(f"Error fetching prices from Primary API: {e}")

    # منبع پشتیبان (Backup) در صورت ناموفق بودن منبع اول
    if not prices or 'gold' not in prices:
        try:
            backup_url = "https://brsapi.ir/FreeTomanExchangeApi/Short.json"
            res = requests.get(backup_url, headers=HEADERS, timeout=8)
            if res.status_code == 200:
                b_data = res.json()
                
                # استخراج طلا و دلار از پشتیبان
                for item in b_data.get('gold', []):
                    if item.get('name') == 'طلا 18 عیار':
                        prices['gold'] = int(item.get('price', 0))
                
                for item in b_data.get('currency', []):
                    if item.get('name') == 'دلار':
                        prices['dollar'] = int(item.get('price', 0))
                        
                for item in b_data.get('coin', []):
                    if 'امامی' in item.get('name', ''):
                        prices['coin'] = int(item.get('price', 0))
        except Exception as e:
            print(f"Error fetching from Backup API: {e}")

    return prices

def get_current_time():
    return datetime.now().strftime('%H:%M:%S')

def format_price_message(prices):
    if not prices or all(v == 0 for v in prices.values()):
        return "❌ امکان دریافت قیمت‌ها در این لحظه وجود ندارد. لطفاً دقایقی دیگر دوباره تلاش کنید."
    
    message = "💎 **قیمت‌های لحظه‌ای و واقعی بازار**\n"
    message += f"🕐 زمان استعلام: {get_current_time()}\n\n"
    
    if prices.get('gold'):
        message += f"⚜️ طلا (گرم ۱۸): {prices['gold']:,} تومان\n"
    if prices.get('dollar'):
        message += f"💵 دلار: {prices['dollar']:,} تومان\n"
    if prices.get('coin'):
        message += f"🪙 سکه امامی: {prices['coin']:,} تومان\n"
        
    return message
