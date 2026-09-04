import requests
from datetime import datetime
import zoneinfo

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36'
}

def get_gold_and_currency_prices():
    """دریافت تمامی ۱۸ آیتم تصویر به همراه زمان دقیق به وقت تهران"""
    prices = {}
    
    # ۱. استعلام از API جامع بازار (TGJU / Nobitex)
    try:
        res = requests.get("https://call1.tgju.org/ajax.json", headers=HEADERS, timeout=10)
        if res.status_code == 200:
            data = res.json().get('current', {})
            
            mapping = {
                'ons': '👑 اونس طلا',
                'mesghal': '📀 مثقال ۱۷',
                'geram18': '🪙 گرم ۱۸',
                'sekeb': '🟡 سکه امامی',
                'nim': '🟡 سکه نیم',
                'rob': '🟡 سکه ربع',
                'silver_ons': '⚪ نقره (اونس)',
                'gold_bar': '🧈 شمش گرمی',
                'crypto_btc': '₿ بیت کوین',
                'sekeb_real': '💎 ارزش سکه',
                'oil': '🛢️ نفت',
                'usdt': '💵 تتر',
                'parsian': '🪙 سکه پارسیان',
                'sekeg': '🟡 سکه قدیم',
                'geram_buy': '🛒 گرم خرید',
                'try': '🇹🇷 لیر ترکیه',
                'omr': '🇴🇲 ریال عمان',
                'crypto_eth': 'Ξ اتریوم'
            }
            
            for key, label in mapping.items():
                if key in data and 'p' in data[key]:
                    val = data[key]['p'].replace(',', '')
                    prices[label] = val
    except Exception as e:
        print(f"Error fetching main market data: {e}")

    # پشتیبان نوبیتکس برای تتر و کریپتو در صورت لزوم
    if '💵 تتر' not in prices:
        try:
            res_nobit = requests.get("https://api.nobitex.ir/v2/orderbook/USDTIRT", headers=HEADERS, timeout=5)
            if res_nobit.status_code == 200:
                last_p = res_nobit.json().get('lastTradePrice')
                if last_p:
                    prices['💵 تتر'] = f"{int(last_p)//10:,}"
        except Exception:
            pass

    return prices


def format_gold_currency_message(prices):
    # زمان زنده به وقت تهران
    try:
        tehran_tz = zoneinfo.ZoneInfo("Asia/Tehran")
        now_str = datetime.now(tehran_tz).strftime("%Y/%m/%d - %H:%M:%S")
    except Exception:
        now_str = datetime.now().strftime("%H:%M:%S")

    if not prices:
        return f"❌ در حال حاضر استعلام قیمت‌ها با خطا مواجه شد.\n\n⏱ **آخرین تلاش:** `{now_str}`"
        
    msg = "📊 **جدول نرخ لحظه‌ای طلا، سکه، ارز و رمزارز:**\n"
    msg += "───────────────────\n"
    
    for label, price in prices.items():
        # تشخیص واحد (دلار/تومان)
        if any(x in label for x in ['اونس', 'بیت کوین', 'اتریوم', 'نفت']):
            unit = "$"
        else:
            unit = "تومان"
            try:
                # تبدیل قیمت‌های ریالی به تومان
                val_int = int(price.replace(',', ''))
                if val_int > 10000:
                    price = f"{val_int // 10:,}"
            except ValueError:
                pass

        msg += f"▫️ **{label}:** `{price}` {unit}\n"
        
    msg += "───────────────────\n"
    msg += f"⏱ **زمان بروزرسانی:** `{now_str}`"
    return msg
