import requests
from bs4 import BeautifulSoup

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
}

def get_gold_and_currency_prices():
    """استعلام قیمت طلا، سکه و ارز از منبع tgju.org"""
    url = "https://www.tgju.org/"
    prices = {}
    
    try:
        res = requests.get(url, headers=HEADERS, timeout=8)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, 'html.parser')
            
            # کلیدواژه‌های مورد نیاز
            items = {
                'price_dollar_rl': '💵 دلار آمریکا',
                'price_eur': '💶 یورو',
                'geram18': '🪙 طلای ۱۸ عیار',
                'sekeb': '🟡 سکه امامی',
                'nim': '🟡 نیم سکه',
                'rob': '🟡 ربع سکه'
            }
            
            for item_id, label in items.items():
                target = soup.find('tr', {'data-market-row': item_id})
                if target:
                    price_td = target.find('td', class_='market-price')
                    if price_td:
                        price_val = price_td.text.strip()
                        prices[label] = price_val

    except Exception as e:
        print(f"Error fetching gold/currency prices: {e}")
        
    return prices


def format_gold_currency_message(prices):
    if not prices:
        return "❌ در حال حاضر دریافت نرخ طلا و ارز با خطا مواجه شد."
        
    msg = "💰 **نرخ لحظه‌ای طلا، سکه و ارز:**\n\n"
    for label, price in prices.items():
        msg += f"▫️ **{label}:** `{price} ریال`\n"
        
    msg += "\n⏱ *منبع: شبکه اطلاع‌رسانی طلا و ارز*"
    return msg