import requests
from bs4 import BeautifulSoup
from datetime import datetime

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
}

def clean_price(price_str):
    """تبدیل رشته قیمت حاوی کاما یا حروف به عدد صحیح (به تومان)"""
    try:
        # حذف کاما، فضاها و کاراکترهای غیرعددی
        digits = ''.join(c for c in price_str if c.isdigit())
        if not digits:
            return 0
        val = int(digits)
        # اگر قیمت به ریال بود (مثلاً بیش از ۸ رقم برای طلا)، تبدیل به تومان
        return val
    except:
        return 0

def get_prices_from_tala_ir():
    """استخراج مستقیم قیمت‌ها از سایت tala.ir"""
    prices = {}
    try:
        url = "https://www.tala.ir/"
        response = requests.get(url, headers=HEADERS, timeout=8)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # استخراج قیمت طلا 18 عیار
            # در tala.ir قیمت‌ها در آیتم‌های مشخصی قرار دارند
            gold_item = soup.find('div', {'data-id': '1'}) or soup.find('tr', {'data-id': '1'})
            if not gold_item:
                # جستجو بر اساس متن در صورت تغییر ID
                for row in soup.find_all('tr'):
                    if 'طلا ۱۸' in row.text or 'طلا 18' in row.text:
                        gold_item = row
                        break
            
            if gold_item:
                price_text = gold_item.find_all('td')[-1].text if gold_item.find_all('td') else gold_item.text
                prices['gold'] = clean_price(price_text)

            # استخراج دلار
            usd_item = soup.find('div', {'data-id': '8'}) or soup.find('tr', {'data-id': '8'})
            if not usd_item:
                for row in soup.find_all('tr'):
                    if 'دلار' in row.text:
                        usd_item = row
                        break
            if usd_item:
                price_text = usd_item.find_all('td')[-1].text if usd_item.find_all('td') else usd_item.text
                prices['dollar'] = clean_price(price_text)

            # استخراج سکه طرح جدید (امامی)
            coin_item = soup.find('div', {'data-id': '3'}) or soup.find('tr', {'data-id': '3'})
            if not coin_item:
                for row in soup.find_all('tr'):
                    if 'سکه امامی' in row.text or 'سکه طرح جدید' in row.text:
                        coin_item = row
                        break
            if coin_item:
                price_text = coin_item.find_all('td')[-1].text if coin_item.find_all('td') else coin_item.text
                prices['coin'] = clean_price(price_text)

    except Exception as e:
        print(f"Error scraping tala.ir: {e}")
        
    return prices

def get_all_prices():
    """دریافت قیمت‌ها با اولویت tala.ir و پشتیبان هوشمند"""
    # گام ۱: تلاش برای دریافت از tala.ir
    prices = get_prices_from_tala_ir()
    
    # گام ۲: اگر tala.ir پاسخ نداد یا قیمتی صفر بود، از API پشتیبان استفاده کن
    if not prices.get('gold') or prices.get('gold') == 0:
        try:
            backup_url = "https://brsapi.ir/FreeTomanExchangeApi/Short.json"
            res = requests.get(backup_url, headers=HEADERS, timeout=6)
            if res.status_code == 200:
                b_data = res.json()
                
                for item in b_data.get('gold', []):
                    if '18' in item.get('name', ''):
                        prices['gold'] = int(item.get('price', 0))
                
                for item in b_data.get('currency', []):
                    if 'دلار' in item.get('name', ''):
                        prices['dollar'] = int(item.get('price', 0))
                        
                for item in b_data.get('coin', []):
                    if 'امامی' in item.get('name', ''):
                        prices['coin'] = int(item.get('price', 0))
        except Exception as e:
            print(f"Error fetching backup prices: {e}")

    return prices

def get_current_time():
    return datetime.now().strftime('%H:%M:%S')

def format_price_message(prices):
    if not prices or all(v == 0 for v in prices.values()):
        return "❌ امکان دریافت قیمت‌ها در این لحظه وجود ندارد. لطفاً دقایقی دیگر دوباره تلاش کنید."
    
    message = "💎 **قیمت‌های لحظه‌ای بازار (منبع: Tala.ir)**\n"
    message += f"🕐 زمان استعلام: {get_current_time()}\n\n"
    
    if prices.get('gold'):
        message += f"⚜️ طلا (گرم ۱۸): {prices['gold']:,} تومان\n"
    if prices.get('dollar'):
        message += f"💵 دلار: {prices['dollar']:,} تومان\n"
    if prices.get('coin'):
        message += f"🪙 سکه امامی: {prices['coin']:,} تومان\n"
        
    return message
