import os
import requests
from datetime import datetime, timedelta
import re

# ==================== تنظیمات ====================
RAPIDAPI_KEY = os.getenv('RAPIDAPI_KEY')
RAPIDAPI_HOST = "economic-calendar-api3.p.rapidapi.com"

# همه ارزهای اصلی
ALL_CURRENCIES = ['USD', 'EUR', 'GBP', 'JPY', 'XAU', 'CAD', 'AUD', 'NZD', 'CHF', 'CNY']

# ==================== دیکشنری توضیحات فارسی ====================
NEWS_EXPLANATIONS = {
    'Federal Funds Rate': {
        'desc': 'نرخ بهره کلیدی آمریکا که توسط فدرال رزرو تعیین می‌شود.',
        'effect': 'افزایش نرخ → دلار قوی، طلا ضعیف. کاهش نرخ → برعکس.',
        'gold': '🔴 نزولی (با افزایش)',
        'dollar': '🟢 صعودی (با افزایش)'
    },
    'Fed Interest Rate': {
        'desc': 'نرخ بهره کلیدی آمریکا (فدرال رزرو).',
        'effect': 'افزایش → دلار قوی، طلا ضعیف. کاهش → برعکس.',
        'gold': '🔴 نزولی (با افزایش)',
        'dollar': '🟢 صعودی (با افزایش)'
    },
    'FOMC Statement': {
        'desc': 'بیانیه کمیته فدرال رزرو درباره سیاست پولی.',
        'effect': 'لحن انقباضی → دلار قوی. لحن انبساطی → طلا قوی.',
        'gold': '⚠️ بستگی به لحن دارد',
        'dollar': '⚠️ بستگی به لحن دارد'
    },
    'FOMC Economic Projections': {
        'desc': 'پیش‌بینی‌های اقتصادی اعضای فدرال رزرو.',
        'effect': 'پیش‌بینی تورم بالاتر → دلار قوی، طلا ضعیف.',
        'gold': '⚠️ بستگی به داده دارد',
        'dollar': '⚠️ بستگی به داده دارد'
    },
    'FOMC Press Conference': {
        'desc': 'کنفرانس خبری رئیس فدرال رزرو.',
        'effect': 'هر کلمه می‌تونه بازار رو تکان بده.',
        'gold': '⚠️ بستگی به صحبت‌ها دارد',
        'dollar': '⚠️ بستگی به صحبت‌ها دارد'
    },
    'FOMC Member': {
        'desc': 'سخنرانی یکی از اعضای فدرال رزرو.',
        'effect': 'می‌تونه انتظارات نرخ بهره رو تغییر بده.',
        'gold': '⚠️ بستگی به صحبت‌ها دارد',
        'dollar': '⚠️ بستگی به صحبت‌ها دارد'
    },
    'CPI': {
        'desc': 'شاخص قیمت مصرف‌کننده. مهم‌ترین معیار تورم.',
        'effect': 'CPI بالا → احتمال افزایش نرخ بهره → دلار قوی، طلا ضعیف.',
        'gold': '🔴 نزولی (با CPI بالا)',
        'dollar': '🟢 صعودی (با CPI بالا)'
    },
    'Core CPI': {
        'desc': 'شاخص قیمت مصرف‌کننده بدون غذا و انرژی.',
        'effect': 'مشابه CPI.',
        'gold': '🔴 نزولی (با CPI بالا)',
        'dollar': '🟢 صعودی (با CPI بالا)'
    },
    'PPI': {
        'desc': 'شاخص قیمت تولیدکننده.',
        'effect': 'PPI بالا → تورم بیشتر → دلار قوی، طلا ضعیف.',
        'gold': '🔴 نزولی (با PPI بالا)',
        'dollar': '🟢 صعودی (با PPI بالا)'
    },
    'Non-Farm': {
        'desc': 'تغییر شاغلان غیرکشاورزی (NFP). مهم‌ترین گزارش اشتغال.',
        'effect': 'NFP قوی → دلار قوی، طلا ضعیف.',
        'gold': '🔴 نزولی (با NFP قوی)',
        'dollar': '🟢 صعودی (با NFP قوی)'
    },
    'ADP': {
        'desc': 'گزارش اشتغال بخش خصوصی.',
        'effect': 'ADP قوی → دلار قوی، طلا ضعیف.',
        'gold': '🔴 نزولی (با ADP قوی)',
        'dollar': '🟢 صعودی (با ADP قوی)'
    },
    'Unemployment': {
        'desc': 'نرخ بیکاری.',
        'effect': 'بیکاری کم → دلار قوی، طلا ضعیف.',
        'gold': '🔴 نزولی (با بیکاری کم)',
        'dollar': '🟢 صعودی (با بیکاری کم)'
    },
    'Jobless Claims': {
        'desc': 'تعداد مدعیان بیمه بیکاری.',
        'effect': 'عدد کمتر → اشتغال قوی → دلار قوی.',
        'gold': '🔴 نزولی',
        'dollar': '🟢 صعودی'
    },
    'Unemployment Claims': {
        'desc': 'تعداد مدعیان بیمه بیکاری.',
        'effect': 'عدد کمتر → اشتغال قوی → دلار قوی.',
        'gold': '🔴 نزولی',
        'dollar': '🟢 صعودی'
    },
    'GDP': {
        'desc': 'تولید ناخالص داخلی.',
        'effect': 'GDP قوی → دلار قوی، طلا ضعیف.',
        'gold': '🔴 نزولی (با GDP قوی)',
        'dollar': '🟢 صعودی (با GDP قوی)'
    },
    'Retail Sales': {
        'desc': 'فروش خرده‌فروشی.',
        'effect': 'خرده‌فروشی قوی → دلار قوی، طلا ضعیف.',
        'gold': '🔴 نزولی (با خرده‌فروشی قوی)',
        'dollar': '🟢 صعودی (با خرده‌فروشی قوی)'
    },
    'PMI': {
        'desc': 'شاخص مدیران خرید. بالای ۵۰ = رشد، زیر ۵۰ = رکود.',
        'effect': 'PMI قوی → دلار قوی، طلا ضعیف.',
        'gold': '🔴 نزولی (با PMI قوی)',
        'dollar': '🟢 صعودی (با PMI قوی)'
    },
    'Interest Rate': {
        'desc': 'تصمیم نرخ بهره بانک مرکزی.',
        'effect': 'افزایش نرخ → دلار قوی، طلا ضعیف.',
        'gold': '🔴 نزولی (با افزایش)',
        'dollar': '🟢 صعودی (با افزایش)'
    },
    'BoE Interest Rate': {
        'desc': 'نرخ بهره بانک مرکزی انگلستان.',
        'effect': 'افزایش → پوند قوی، طلا ضعیف (به دلار).',
        'gold': '🔴 نزولی',
        'dollar': '🟢 صعودی (غیرمستقیم)'
    },
    'BoJ Interest Rate': {
        'desc': 'نرخ بهره بانک مرکزی ژاپن.',
        'effect': 'افزایش → ین قوی.',
        'gold': '⚠️ غیرمستقیم',
        'dollar': '⚠️ غیرمستقیم'
    },
    'Employment Change': {
        'desc': 'تغییر اشتغال.',
        'effect': 'اشتغال قوی → ارز قوی، طلا ضعیف.',
        'gold': '🔴 نزولی',
        'dollar': '🟢 صعودی'
    },
    'Trade Balance': {
        'desc': 'تراز تجاری (صادرات منهای واردات).',
        'effect': 'تراز مثبت → ارز قوی‌تر.',
        'gold': '⚠️ بستگی به ارز دارد',
        'dollar': '⚠️ بستگی به ارز دارد'
    },
    'Current Account': {
        'desc': 'حساب جاری. نشان‌دهنده جریان تجارت و سرمایه.',
        'effect': 'حساب جاری مثبت → ارز قوی‌تر.',
        'gold': '⚠️ غیرمستقیم',
        'dollar': '⚠️ غیرمستقیم'
    },
    'ZEW': {
        'desc': 'شاخص احساسات اقتصادی ZEW آلمان.',
        'effect': 'ZEW بالا → یورو قوی.',
        'gold': '⚠️ غیرمستقیم',
        'dollar': '⚠️ غیرمستقیم'
    },
    'Consumer Confidence': {
        'desc': 'اعتماد مصرف‌کننده.',
        'effect': 'اعتماد بالا → اقتصاد قوی → ارز قوی.',
        'gold': '⚠️ غیرمستقیم',
        'dollar': '⚠️ غیرمستقیم'
    },
    'Business Climate': {
        'desc': 'فضای کسب و کار.',
        'effect': 'بالا → اقتصاد قوی → ارز قوی.',
        'gold': '⚠️ غیرمستقیم',
        'dollar': '⚠️ غیرمستقیم'
    },
    'Manufacturing': {
        'desc': 'شاخص تولید صنعتی.',
        'effect': 'بالا → اقتصاد قوی → ارز قوی.',
        'gold': '⚠️ غیرمستقیم',
        'dollar': '⚠️ غیرمستقیم'
    },
    'Services': {
        'desc': 'شاخص بخش خدمات.',
        'effect': 'بالا → اقتصاد قوی → ارز قوی.',
        'gold': '⚠️ غیرمستقیم',
        'dollar': '⚠️ غیرمستقیم'
    },
    'Housing': {
        'desc': 'شاخص بازار مسکن.',
        'effect': 'بالا → اقتصاد قوی → ارز قوی.',
        'gold': '⚠️ غیرمستقیم',
        'dollar': '⚠️ غیرمستقیم'
    },
    'Building Permits': {
        'desc': 'مجوزهای ساخت و ساز.',
        'effect': 'بالا → اقتصاد قوی → دلار قوی.',
        'gold': '⚠️ غیرمستقیم',
        'dollar': '🟢 صعودی'
    },
    'Bond Auction': {
        'desc': 'حراج اوراق قرضه دولتی.',
        'effect': 'تقاضای بالا → ارز قوی‌تر.',
        'gold': '⚠️ غیرمستقیم',
        'dollar': '⚠️ غیرمستقیم'
    },
    'Lagarde': {
        'desc': 'سخنرانی رئیس بانک مرکزی اروپا (ECB).',
        'effect': 'هر کلمه‌ای می‌تونه یورو رو تکان بده.',
        'gold': '⚠️ غیرمستقیم',
        'dollar': '⚠️ غیرمستقیم'
    },
    'Powell': {
        'desc': 'سخنرانی رئیس فدرال رزرو.',
        'effect': 'مهم‌ترین سخنران بازار.',
        'gold': '⚠️ بستگی به صحبت‌ها دارد',
        'dollar': '⚠️ بستگی به صحبت‌ها دارد'
    },
    'ECB': {
        'desc': 'سخنرانی یا تصمیم بانک مرکزی اروپا.',
        'effect': 'روی یورو تأثیر مستقیم داره.',
        'gold': '⚠️ غیرمستقیم',
        'dollar': '⚠️ غیرمستقیم'
    },
}

CURRENCY_NAMES = {
    'USD': '🇺🇸 دلار آمریکا',
    'EUR': '🇪🇺 یورو',
    'GBP': '🇬🇧 پوند انگلستان',
    'JPY': '🇯🇵 ین ژاپن',
    'XAU': '🥇 طلا',
    'CAD': '🇨🇦 دلار کانادا',
    'AUD': '🇦🇺 دلار استرالیا',
    'NZD': '🇳🇿 دلار نیوزیلند',
    'CHF': '🇨🇭 فرانک سوئیس',
    'CNY': '🇨🇳 یوان چین',
}
# ================================================================


def _parse_value(v):
    """تبدیل مقدار مثل 120K یا 2.1% به عدد"""
    if not v:
        return None
    v = str(v).strip().replace(',', '').replace('%', '')
    try:
        if v.endswith('K'):
            return float(v[:-1]) * 1000
        if v.endswith('M'):
            return float(v[:-1]) * 1_000_000
        if v.endswith('B'):
            return float(v[:-1]) * 1_000_000_000
        return float(v)
    except:
        return None


def _parse_date(date_str):
    """پارس تاریخ از فرمت‌های مختلف"""
    if not date_str:
        return None
    
    date_str = str(date_str).strip()
    
    # فرمت ISO: 2026-09-16 یا 2026-09-16T10:30:00
    if re.match(r'\d{4}-\d{2}-\d{2}', date_str):
        try:
            return datetime.fromisoformat(date_str.replace('Z', '')).date()
        except:
            try:
                return datetime.strptime(date_str[:10], '%Y-%m-%d').date()
            except:
                pass
    
    return None


def fetch_events(days_ahead=7):
    """
    دریافت رویدادهای اقتصادی از RapidAPI
    """
    if not RAPIDAPI_KEY:
        print("[DEBUG] RAPIDAPI_KEY is not set!")
        return []
    
    events = []
    
    try:
        # پارامترها
        hours = max(days_ahead * 24, 48)  # حداقل 48 ساعت
        
        url = f"https://{RAPIDAPI_HOST}/v1/calendar/upcoming"
        params = {
            'impact': '{}',
            'hours': str(hours),
            'currency': '{}'
        }
        headers = {
            'Content-Type': 'application/json',
            'x-rapidapi-host': RAPIDAPI_HOST,
            'x-rapidapi-key': RAPIDAPI_KEY,
        }
        
        print(f"[DEBUG] Fetching from RapidAPI: hours={hours}")
        
        response = requests.get(url, headers=headers, params=params, timeout=20)
        print(f"[DEBUG] Status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"[DEBUG] Error response: {response.text[:500]}")
            return []
        
        data = response.json()
        print(f"[DEBUG] Response type: {type(data)}")
        
        # استخراج لیست رویدادها
        raw_events = None
        if isinstance(data, list):
            raw_events = data
        elif isinstance(data, dict):
            # ممکنه توی کلیدهای مختلفی باشه
            for key in ['data', 'events', 'result', 'results', 'calendar']:
                if key in data and isinstance(data[key], list):
                    raw_events = data[key]
                    break
        
        if not raw_events:
            print(f"[DEBUG] No events found in response. Keys: {list(data.keys()) if isinstance(data, dict) else 'list'}")
            return []
        
        print(f"[DEBUG] Raw events: {len(raw_events)}")
        
        # چاپ نمونه
        if raw_events:
            print(f"[DEBUG] Sample event: {raw_events[0]}")
        
        today = datetime.now().date()
        
        for item in raw_events:
            try:
                if not isinstance(item, dict):
                    continue
                
                # استخراج فیلدها با انعطاف
                title = (
                    item.get('event') or item.get('name') or 
                    item.get('title') or item.get('Event') or ''
                )
                currency = (
                    item.get('currency') or item.get('country') or 
                    item.get('symbol') or item.get('Currency') or ''
                )
                date_str = (
                    item.get('date') or item.get('datetime') or 
                    item.get('time') or item.get('Date') or ''
                )
                time_str = (
                    item.get('time') or item.get('hour') or 
                    item.get('Time') or ''
                )
                impact = (
                    item.get('impact') or item.get('importance') or 
                    item.get('Impact') or 'High'
                )
                forecast = str(
                    item.get('forecast') or item.get('forecast_value') or 
                    item.get('Forecast') or ''
                )
                previous = str(
                    item.get('previous') or item.get('previous_value') or 
                    item.get('Previous') or ''
                )
                
                if not title or not currency:
                    continue
                
                # نرمال‌سازی currency
                currency = str(currency).strip().upper()
                
                # نرمال‌سازی impact
                impact_str = str(impact).capitalize()
                if impact_str not in ['High', 'Medium', 'Low']:
                    impact_str = 'High'
                
                # پارس تاریخ
                parsed_date = _parse_date(str(date_str)) if date_str else today
                
                events.append({
                    'title': str(title).strip(),
                    'currency': currency,
                    'date': str(date_str),
                    'parsed_date': parsed_date or today,
                    'time': str(time_str),
                    'impact': impact_str,
                    'forecast': forecast,
                    'previous': previous,
                })
            except Exception as e:
                print(f"[DEBUG] Error parsing item: {e}")
                continue
        
        print(f"[DEBUG] Total events parsed: {len(events)}")
        
        # حذف تکراری‌ها
        seen = set()
        unique_events = []
        for ev in events:
            key = (ev['title'], ev['currency'], str(ev['parsed_date']))
            if key not in seen:
                seen.add(key)
                unique_events.append(ev)
        
        print(f"[DEBUG] Unique events: {len(unique_events)}")
        return unique_events
        
    except Exception as e:
        print(f"[DEBUG] RapidAPI error: {e}")
        import traceback
        traceback.print_exc()
        return []


def filter_today_events(events, days_ahead=7, min_impact='All'):
    """فیلتر اخبار بر اساس بازه و اهمیت"""
    if not events:
        return []
    
    today = datetime.now().date()
    max_date = today + timedelta(days=days_ahead)
    
    allowed_impacts = {
        'High': ['High'],
        'Medium': ['High', 'Medium'],
        'Low': ['High', 'Medium', 'Low'],
        'All': ['High', 'Medium', 'Low', ''],
    }
    allowed = allowed_impacts.get(min_impact, ['High', 'Medium', 'Low', ''])
    
    filtered = []
    for ev in events:
        if ev['impact'] not in allowed:
            continue
        if ev['currency'] not in ALL_CURRENCIES:
            continue
        
        ev_date = ev.get('parsed_date')
        if ev_date is None:
            continue
        
        if not (today <= ev_date <= max_date):
            continue
        
        filtered.append(ev)
    
    # مرتب‌سازی: اول تاریخ، بعد اهمیت
    impact_order = {'High': 0, 'Medium': 1, 'Low': 2, '': 3}
    filtered.sort(key=lambda x: (
        x.get('parsed_date') or today,
        impact_order.get(x['impact'], 3)
    ))
    
    print(f"[DEBUG] Filtered: {len(filtered)} events (min_impact={min_impact})")
    return filtered


def get_news_explanation(title):
    title_lower = title.lower()
    for key, explanation in NEWS_EXPLANATIONS.items():
        if key.lower() in title_lower:
            return explanation
    return None


def analyze_sentiment(events):
    if not events:
        return {
            'bias': 'neutral', 'score': 0, 'bullish': 0, 'bearish': 0,
            'events': [], 'summary': _format_summary([], 'neutral', 0, 0)
        }
    
    bull = 0
    bear = 0
    for ev in events:
        t = ev['title'].lower()
        forecast = _parse_value(ev['forecast'])
        previous = _parse_value(ev['previous'])
        
        if 'non-farm' in t or 'adp' in t:
            if forecast is not None and previous is not None:
                if forecast < previous:
                    bull += 3
                else:
                    bear += 2
        elif 'cpi' in t:
            if forecast is not None and previous is not None:
                if forecast > previous:
                    bull += 2
                else:
                    bear += 2
        elif 'gdp' in t:
            if forecast is not None and previous is not None:
                if forecast < previous:
                    bull += 2
                else:
                    bear += 1
        elif 'interest rate' in t or 'fomc' in t or 'federal funds' in t:
            bear += 1
    
    net = bull - bear
    if net >= 3:
        bias = 'bullish'
    elif net <= -3:
        bias = 'bearish'
    else:
        bias = 'neutral'
    
    return {
        'bias': bias, 'score': net, 'bullish': bull, 'bearish': bear,
        'events': events, 'summary': _format_summary(events, bias, bull, bear)
    }


def _format_summary(events, bias, bull, bear):
    bias_map = {'bullish': '🟢 صعودی', 'bearish': '🔴 نزولی', 'neutral': '⚪ خنثی'}
    
    msg = "📰 **تحلیل فاندامنتال**\n"
    msg += "━━━━━━━━━━━━━━━━━━━━\n"
    msg += f"**بایاس کلی:** {bias_map.get(bias, '⚪ خنثی')}\n\n"
    
    if not events:
        msg += "⚠️ **خبری در این بازه پیدا نشد.**\n\n"
        msg += "⚠️ _این تحلیل صرفاً آماری است و توصیه مالی نیست._"
        return msg
    
    today = datetime.now().date()
    msg += f"📊 **{len(events)} خبر در این بازه:**\n\n"
    
    for ev in events[:20]:
        impact_emoji = {
            'High': '🔴', 'Medium': '🟡', 'Low': '🟢', '': '⚪'
        }.get(ev['impact'], '⚪')
        
        currency_name = CURRENCY_NAMES.get(ev['currency'], ev['currency'])
        
        date_label = ''
        if ev.get('parsed_date'):
            ev_date = ev['parsed_date']
            if ev_date == today:
                date_label = '📅 امروز'
            elif ev_date == today + timedelta(days=1):
                date_label = '📅 فردا'
            else:
                date_label = f"📅 {ev_date.strftime('%m/%d')}"
        
        msg += f"{impact_emoji} **{currency_name}** — `{ev['title']}`\n"
        
        if date_label:
            msg += f"   {date_label}"
            if ev.get('time') and ev['time']:
                msg += f" | ⏰ `{ev['time']}`"
            msg += "\n"
        
        explanation = get_news_explanation(ev['title'])
        if explanation:
            msg += f"   📖 {explanation['desc']}\n"
            msg += f"   💡 {explanation['effect']}\n"
            msg += f"   🥇 طلا: {explanation['gold']} | 💵 دلار: {explanation['dollar']}\n"
        
        if ev['forecast']:
            msg += f"   📊 پیش‌بینی: `{ev['forecast']}`"
            if ev['previous']:
                msg += f" | قبلی: `{ev['previous']}`"
            msg += "\n"
        
        msg += "   ───────────────────\n"
    
    if len(events) > 20:
        msg += f"\n... و {len(events) - 20} خبر دیگر"
    
    msg += f"\n\n📈 امتیاز صعودی: `{bull}`\n"
    msg += f"📉 امتیاز نزولی: `{bear}`\n"
    msg += "\n⚠️ _این تحلیل صرفاً آماری است و توصیه مالی نیست._"
    
    return msg
