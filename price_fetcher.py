import requests
from bs4 import BeautifulSoup
from datetime import datetime

# هدرها برای جلوگیری از مسدود شدن توسط وب‌سایت‌ها
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

def get_all_prices():
    """دریافت قیمت‌های واقعی از منابع معتبر"""
    prices = {}
    
    # دریافت قیمت دلار و طلا
    try:
        url = "https://www.bonbast.com/"
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # استخراج قیمت دلار (کلاس یا ID مربوطه)
            usd_element = soup.find('td', {'id': 'usd1'})
            if usd_element:
                prices['dollar'] = int(usd_element.text.strip().replace(',', ''))
                
            # استخراج قیمت طلای ۱۸ عیار
            gold_element = soup.find('td', {'id': 'gold_18k'})
            if gold_element:
                prices['gold'] = int(gold_element.text.strip().replace(',', ''))
    except Exception as e:
        print(f"Error fetching dollar/gold: {e}")

    # پشتیبان: دریافت قیمت‌ها از API رایگان Navasan در صورت عدم پاسخگویی source اولیه
    if not prices:
        try:
            res = requests.get("https://api.navasan.tech/latest/?api_key=free", timeout=10)
            if res.status_code == 200:
                data = res.json()
                if 'usd_sell' in data:
                    prices['dollar'] = int(data['usd_sell']['value'])
                if 'geram18' in data:
                    prices['gold'] = int(data['geram18']['value'])
                if 'sekke' in data:
                    prices['coin'] = int(data['sekke']['value'])
        except Exception as e:
            print(f"Error fetching from Navasan API: {e}")

    return prices

def get_current_time():
    return datetime.now().strftime('%H:%M:%S')

def format_price_message(prices):
    if not prices:
        return "❌ امکان دریافت قیمت‌های لحظه‌ای در این مشخصات وجود ندارد. لطفاً بعداً دوباره تلاش کنید."
    
    message = "💎 **قیمت‌های لحظه‌ای بازار (واقعی)**\n"
    message += f"🕐 زمان استعلام: {get_current_time()}\n\n"
    
    if 'gold' in prices:
        message += f"⚜️ طلا (گرم ۱۸): {prices['gold']:,} تومان\n"
    if 'dollar' in prices:
        message += f"💵 دلار: {prices['dollar']:,} تومان\n"
    if 'coin' in prices:
        message += f"🪙 سکه طرح جدید: {prices['coin']:,} تومان\n"
        
    return message
