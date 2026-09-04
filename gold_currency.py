import requests
from bs4 import BeautifulSoup

def get_gold_and_currency_prices():
    """استخراج مستقیم از tala.ir با شبیه‌سازی کامل مرورگر واقعی"""
    prices = {}
    
    # ساخت یک Session برای حفظ کوکی‌ها و هدرها
    session = requests.Session()
    
    # هدرهای کامل مرورگر واقعی برای دور زدن سیستم‌های ضداسکرپ tala.ir
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'fa-IR,fa;q=0.9,en-US;q=0.8,en;q=0.7',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache',
        'Referer': 'https://www.google.com/',
        'Sec-Ch-Ua': '"Chromium";v="128", "Not;A=Brand";v="24", "Google Chrome";v="128"',
        'Sec-Ch-Ua-Mobile': '?0',
        'Sec-Ch-Ua-Platform': '"Windows"',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'cross-site',
        'Sec-Fetch-User': '?1',
        'Upgrade-Insecure-Requests': '1'
    }

    # ۱. تلاش اول: فراخوانی مستقیم API داخلی tala.ir با هدرهای شبیه‌سازی شده
    try:
        api_headers = headers.copy()
        api_headers['X-Requested-With'] = 'XMLHttpRequest'
        api_headers['Referer'] = 'https://www.tala.ir/'
        
        res_api = session.get("https://www.tala.ir/ajax/prices", headers=api_headers, timeout=10)
        
        if res_api.status_code == 200:
            data = res_api.json()
            items = data.get('data', {}) if isinstance(data, dict) else {}
            
            mapping = {
                'geram18': '🪙 طلای ۱۸ عیار',
                'sekeb': '🟡 سکه امامی',
                'nim': '🟡 نیم سکه',
                'rob': '🟡 ربع سکه',
                'dollar': '💵 دلار آمریکا',
                'eur': '💶 یورو'
            }
            
            for key, label in mapping.items():
                if key in items:
                    info = items[key]
                    price_val = info.get('price') if isinstance(info, dict) else info
                    if price_val:
                        prices[label] = f"{int(price_val):,}"
                        
            if prices:
                return prices
    except Exception as e:
        print(f"tala.ir API bypass error: {e}")

    # ۲. تلاش دوم: اسکرپ مستقیم صفحه اصلی tala.ir در صورت مسدود بودن API
    try:
        res_page = session.get("https://www.tala.ir/", headers=headers, timeout=10)
        if res_page.status_code == 200:
            soup = BeautifulSoup(res_page.text, 'html.parser')
            
            # جستجوی سطر به سطر در جداول tala.ir
            rows = soup.find_all('tr')
            for row in rows:
                text = row.text.strip()
                cols = row.find_all('td')
                if len(cols) >= 2:
                    title = cols[0].text.strip()
                    price = cols[1].text.strip()
                    
                    if '۱۸ عیار' in title and '🪙 طلای ۱۸ عیار' not in prices:
                        prices['🪙 طلای ۱۸ عیار'] = price
                    elif 'امامی' in title and '🟡 سکه امامی' not in prices:
                        prices['🟡 سکه امامی'] = price
                    elif 'نیم' in title and '🟡 نیم سکه' not in prices:
                        prices['🟡 نیم سکه'] = price
                    elif 'ربع' in title and '🟡 ربع سکه' not in prices:
                        prices['🟡 ربع سکه'] = price
                    elif 'دلار' in title and '💵 دلار آمریکا' not in prices:
                        prices['💵 دلار آمریکا'] = price
                    elif 'یورو' in title and '💶 یورو' not in prices:
                        prices['💶 یورو'] = price
    except Exception as e:
        print(f"tala.ir HTML bypass error: {e}")

    return prices


def format_gold_currency_message(prices):
    if not prices:
        return "❌ اتصال به tala.ir امکان‌پذیر نشد. لطفا بعداً تلاش کنید."
        
    msg = "💰 **نرخ لحظه‌ای طلا، سکه و ارز (تومان):**\n\n"
    for label, price in prices.items():
        msg += f"▫️ **{label}:** `{price} تومان`\n"
        
    msg += "\n⏱ *منبع: سایت طلا (tala.ir)*"
    return msg
