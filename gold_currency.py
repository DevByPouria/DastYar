import requests
from bs4 import BeautifulSoup

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36',
    'Accept-Language': 'fa-IR,fa;q=0.9,en-US;q=0.8,en;q=0.7'
}

def get_gold_and_currency_prices():
    """استعلام آنلاین و پایدار نرخ طلا، سکه و ارز بر اساس اتحادیه (تومان)"""
    prices = {}
    
    # منبع اصلی: TGJU (هم‌قیمت با tala.ir و اتحادیه)
    url = "https://www.tgju.org/"
    
    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, 'html.parser')
            
            # نگاشت شناسه‌ها
            targets = [
                ('price_dollar_rl', '💵 دلار آمریکا'),
                ('price_eur', '💶 یورو'),
                ('geram18', '🪙 طلای ۱۸ عیار'),
                ('sekeb', '🟡 سکه امامی'),
                ('nim', '🟡 نیم سکه'),
                ('rob', '🟡 ربع سکه')
            ]
            
            for tag_id, label in targets:
                row = soup.find('tr', {'data-market-row': tag_id})
                if row:
                    price_td = row.find('td', class_='market-price')
                    if price_td:
                        raw_price = price_td.text.strip().replace(',', '')
                        if raw_price.isdigit():
                            # تبدیل ریال به تومان
                            toman_price = int(raw_price) // 10
                            prices[label] = f"{toman_price:,}"

    except Exception as e:
        print(f"Error in fetching market prices: {e}")

    return prices


def format_gold_currency_message(prices):
    if not prices:
        return "❌ در حال حاضر دریافت نرخ‌ها با خطا مواجه شد. لطفا بعداً تلاش کنید."
        
    msg = "💰 **نرخ لحظه‌ای طلا، سکه و ارز (تومان):**\n\n"
    for label, price in prices.items():
        msg += f"▫️ **{label}:** `{price} تومان`\n"
        
    msg += "\n⏱ *منبع: نرخ‌های رسمی اتحادیه طلا و ارز*"
    return msg
