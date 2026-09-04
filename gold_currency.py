import requests

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
}

def get_gold_and_currency_prices():
    """استعلام مستقیم و پایدار نرخ طلا، سکه و ارز از API سایت tala.ir"""
    prices = {}
    
    # آدرس API مستقیم tala.ir
    api_url = "https://www.tala.ir/ajax/prices"

    try:
        res = requests.get(api_url, headers=HEADERS, timeout=8)
        if res.status_code == 200:
            data = res.json()
            
            # در صورتی که API به صورت دیکشنری یا لیست دیتا بازگرداند
            items_data = data.get('data', {}) if isinstance(data, dict) else data

            # نگاشت شناسه‌های API سایت tala.ir به عناوین فارسی
            mapping = {
                'geram18': '🪙 طلای ۱۸ عیار',
                'geram24': '🪙 طلای ۲۴ عیار',
                'sekeb': '🟡 سکه امامی',
                'bahar': '🟡 سکه بهار آزادی',
                'nim': '🟡 نیم سکه',
                'rob': '🟡 ربع سکه',
                'dollar': '💵 دلار آمریکا',
                'eur': '💶 یورو'
            }

            if isinstance(items_data, dict):
                for key, label in mapping.items():
                    if key in items_data:
                        item_info = items_data[key]
                        price_val = item_info.get('price') if isinstance(item_info, dict) else item_info
                        if price_val:
                            prices[label] = f"{int(price_val):,}"

    except Exception as e:
        print(f"Primary tala.ir API error: {e}")

    # مکانیزم رزرو (Fallback) از بخش عمومی tala.ir در صورت عدم پاسخگویی ای‌پي‌آی
    if not prices:
        try:
            url = "https://www.tala.ir/"
            res = requests.get(url, headers=HEADERS, timeout=8)
            if res.status_code == 200:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(res.text, 'html.parser')
                
                rows = soup.find_all('tr')
                for row in rows:
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
            print(f"Fallback tala.ir HTML error: {e}")

    return prices


def format_gold_currency_message(prices):
    if not prices:
        return "❌ در حال حاضر امکان دریافت نرخ از tala.ir وجود ندارد. لطفا لحظاتی بعد مجدداً تلاش کنید."
        
    msg = "💰 **نرخ لحظه‌ای طلا، سکه و ارز (تومان):**\n\n"
    for label, price in prices.items():
        msg += f"▫️ **{label}:** `{price} تومان`\n"
        
    msg += "\n⏱ *منبع: سایت طلا (tala.ir)*"
    return msg
