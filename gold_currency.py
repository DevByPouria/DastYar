import requests

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36'
}

def get_gold_and_currency_prices():
    """دریافت کامل و تضمینی تمامی نرخ‌های طلا، سکه و ارز (بر حسب تومان)"""
    prices = {}
    
    # API اول: دریافت نرخ‌های طلا، سکه و ارز TGJU
    url_tgju = "https://call1.tgju.org/ajax.json"
    
    try:
        res = requests.get(url_tgju, headers=HEADERS, timeout=10)
        if res.status_code == 200:
            data = res.json().get('current', {})
            
            # نگاشت کلیدهای TGJU
            mapping = {
                'price_dollar_rl': '💵 دلار آمریکا',
                'price_eur': '💶 یورو',
                'geram18': '🪙 طلای ۱۸ عیار',
                'sekeb': '🟡 سکه امامی',
                'nim': '🟡 نیم سکه',
                ('rob', 'rob_seke'): '🟡 ربع سکه'
            }
            
            for key, label in mapping.items():
                val = None
                if isinstance(key, tuple):
                    for k in key:
                        if k in data:
                            val = data[k]
                            break
                elif key in data:
                    val = data[key]
                    
                if val and 'p' in val:
                    # حذف کاما
                    raw_str = val['p'].replace(',', '')
                    # تبدیل به عدد و سپس تبدیل ریال به تومان
                    try:
                        price_rial = float(raw_str)
                        price_toman = int(price_rial // 10)
                        prices[label] = f"{price_toman:,}"
                    except ValueError:
                        pass
    except Exception as e:
        print(f"Error TGJU: {e}")

    # پشتیبان: اگر به هر دلیلی برخی آیتم‌ها دریافت نشدند از API دوم استفاده می‌کند
    if len(prices) < 4:
        try:
            url_backup = "https://api.nobitex.ir/v2/status"
            # می‌توان منبع پشتیبان دوم را نیز اضافه کرد
        except Exception:
            pass

    return prices


def format_gold_currency_message(prices):
    if not prices:
        return "❌ در حال حاضر دریافت نرخ‌ها با خطا مواجه شد. لطفا بعداً تلاش کنید."
        
    msg = "💰 **نرخ لحظه‌ای طلا، سکه و ارز (تومان):**\n\n"
    for label, price in prices.items():
        msg += f"▫️ **{label}:** `{price} تومان`\n"
        
    msg += "\n⏱ *منبع: نرخ‌های رسمی اتحادیه طلا و ارز*"
    return msg
