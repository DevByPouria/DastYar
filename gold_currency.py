import requests
from bs4 import BeautifulSoup

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
}

def get_gold_and_currency_prices():
    """استعلام قیمت طلا، سکه و ارز مستقیم از سایت tala.ir"""
    prices = {}
    url = "https://www.tala.ir/"
    
    # لیست آیتم‌هایی که می‌خواهیم از سایت tala.ir استخراج کنیم
    target_items = {
        'dollar': '💵 دلار آمریکا',
        'eur': '💶 یورو',
        'geram18': '🪙 طلای ۱۸ عیار',
        'sekeb': '🟡 سکه امامی',
        'nim': '🟡 نیم سکه',
        'rob': '🟡 ربع سکه'
    }

    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, 'html.parser')
            
            # tala.ir اطلاعات را در سطرها یا کادرهای قیمت مشخص نگهداری می‌کند
            for key, label in target_items.items():
                # جستجو بر اساس کلاس‌ها و شناسه المان‌های سایت tala.ir
                element = soup.find('tr', {'data-id': key}) or soup.find(id=key) or soup.find('div', class_=f'price_{key}')
                
                if not element:
                    # روش جایگزین: جستجوی متنی در جدول قیمت‌های tala.ir
                    for row in soup.find_all('tr'):
                        text = row.text.strip()
                        if label.replace('💵 ', '').replace('💶 ', '').replace('🪙 ', '').replace('🟡 ', '') in text:
                            cols = row.find_all('td')
                            if len(cols) >= 2:
                                price_val = cols[1].text.strip()
                                if price_val:
                                    prices[label] = price_val
                            break
                else:
                    price_td = element.find('td', class_='price') or element.find('span', class_='value')
                    if price_td:
                        prices[label] = price_td.text.strip()

    except Exception as e:
        print(f"Error fetching prices from tala.ir: {e}")

    # در صورت پاسخ ندادن یا عدم استخراج کامل، از ساختار کلی صفحات قیمت tala.ir استخراج انجام می‌شود
    if not prices:
        try:
            res = requests.get(url, headers=HEADERS, timeout=10)
            soup = BeautifulSoup(res.text, 'html.parser')
            # استخراج بر اساس جدول‌های اصلی صفحه اول tala.ir
            tables = soup.find_all('table')
            for table in tables:
                for row in table.find_all('tr'):
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
            print(f"Fallback tala.ir error: {e}")

    return prices


def format_gold_currency_message(prices):
    if not prices:
        return "❌ در حال حاضر دریافت نرخ طلا و ارز از سایت tala.ir با خطا مواجه شد."
        
    msg = "💰 **نرخ لحظه‌ای طلا، سکه و ارز (تومان):**\n\n"
    for label, price in prices.items():
        msg += f"▫️ **{label}:** `{price} تومان`\n"
        
    msg += "\n⏱ *منبع: سایت طلا (tala.ir)*"
    return msg
