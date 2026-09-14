import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import zoneinfo
import re

# ==================== تنظیمات ====================
FF_URL = "https://www.forexfactory.com/calendar"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
}

RELEVANT_CURRENCIES = ['USD', 'EUR', 'GBP', 'JPY', 'XAU', 'CAD', 'AUD', 'NZD', 'CHF', 'CNY']

# ==================== دیکشنری توضیحات فارسی ====================
NEWS_EXPLANATIONS = {
    'Federal Funds Rate': {
        'desc': 'نرخ بهره کلیدی آمریکا که توسط فدرال رزرو تعیین می‌شود.',
        'effect': 'افزایش نرخ → دلار قوی، طلا ضعیف. کاهش نرخ → برعکس.',
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
    'Trade Balance': {
        'desc': 'تراز تجاری (صادرات منهای واردات).',
        'effect': 'تراز مثبت → ارز قوی‌تر.',
        'gold': '⚠️ بستگی به ارز دارد',
        'dollar': '⚠️ بستگی به ارز دارد'
    },
    'ZEW': {
        'desc': 'شاخص احساسات اقتصادی ZEW آلمان.',
        'effect': 'ZEW بالا → یورو قوی.',
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
    v = v.strip().replace(',', '').replace('%', '')
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
    """
    پارس تاریخ از فرمت‌های مختلف
    'Tue Sep 15' | 'Sep 15' | 'Tue Sep 15, 2026'
    """
    if not date_str:
        return None
    
    months = {
        'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
        'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12,
        'january': 1, 'february': 2, 'march': 3, 'april': 4,
        'june': 6, 'july': 7, 'august': 8, 'september': 9,
        'october': 10, 'november': 11, 'december': 12,
    }
    
    clean = date_str.strip().lower().replace(',', '')
    parts = clean.split()
    
    month = None
    day = None
    year = None
    
    for part in parts:
        part = part.strip('.')
        if part in months:
            month = months[part]
        elif part.isdigit():
            n = int(part)
            if n > 31:
                year = n
            elif day is None:
                day = n
    
    if month is None or day is None:
        return None
    
    if year is None:
        year = datetime.now().year
    
    try:
        return datetime(year, month, day).date()
    except:
        return None


def fetch_events(days_ahead=7):
    """
    دریافت رویدادها از ForexFactory با curl_cffi (دور زدن Cloudflare)
    """
    events = []
    
    try:
        # استفاده از curl_cffi برای شبیه‌سازی مرورگر واقعی
        from curl_cffi import requests as cf_requests
        
        url = "https://www.forexfactory.com/calendar"
        
        res = cf_requests.get(
            url,
            impersonate="chrome124",
            timeout=30,
            headers={
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            }
        )
        
        print(f"[DEBUG] Status Code: {res.status_code}")
        print(f"[DEBUG] Content Length: {len(res.text)}")
        
        if res.status_code != 200:
            print(f"[DEBUG] Bad status: {res.status_code}")
            return []
        
        soup = BeautifulSoup(res.text, 'lxml')
        
        # پیدا کردن جدول تقویم
        calendar_table = soup.find('table', class_=re.compile('calendar__table'))
        if not calendar_table:
            print("[DEBUG] Calendar table not found!")
            # شاید کلاس متفاوت باشه
            all_tables = soup.find_all('table')
            print(f"[DEBUG] Found {len(all_tables)} tables total")
            for t in all_tables:
                cls = ' '.join(t.get('class', []))
                print(f"[DEBUG] Table class: {cls}")
            return []
        
        print("[DEBUG] Calendar table found!")
        
        # پیدا کردن همه سطرهای تقویم
        rows = calendar_table.find_all('tr', class_=re.compile('calendar__row'))
        print(f"[DEBUG] Found {len(rows)} rows")
        
        if not rows:
            # شاید ساختار متفاوته
            rows = calendar_table.find_all('tr')
            print(f"[DEBUG] Fallback: {len(rows)} total rows")
        
        from datetime import datetime as _dt
        today = _dt.now().date()
        current_date = today
        
        for row in rows:
            try:
                # آیا این سطر تاریخ داره؟
                date_cell = row.find('td', class_=re.compile('calendar__date'))
                if date_cell and date_cell.get_text(strip=True):
                    date_text = date_cell.get_text(strip=True)
                    parsed = _parse_date(date_text)
                    if parsed:
                        current_date = parsed
                
                # استخراج اطلاعات خبر
                currency_cell = row.find('td', class_=re.compile('calendar__currency'))
                event_cell = row.find('td', class_=re.compile('calendar__event'))
                impact_cell = row.find('td', class_=re.compile('calendar__impact'))
                time_cell = row.find('td', class_=re.compile('calendar__time'))
                forecast_cell = row.find('td', class_=re.compile('calendar__forecast'))
                previous_cell = row.find('td', class_=re.compile('calendar__previous'))
                
                if not currency_cell or not event_cell:
                    continue
                
                currency = currency_cell.get_text(strip=True)
                title = event_cell.get_text(strip=True)
                
                if not currency or not title:
                    continue
                
                # تشخیص سطح اهمیت
                impact = 'Low'
                if impact_cell:
                    impact_span = impact_cell.find('span')
                    if impact_span:
                        classes = ' '.join(impact_span.get('class', []))
                        if 'high' in classes.lower():
                            impact = 'High'
                        elif 'medium' in classes.lower():
                            impact = 'Medium'
                        elif 'low' in classes.lower():
                            impact = 'Low'
                
                events.append({
                    'title': title,
                    'currency': currency,
                    'date': current_date.strftime('%b %d'),
                    'parsed_date': current_date,
                    'time': time_cell.get_text(strip=True) if time_cell else '',
                    'impact': impact,
                    'forecast': forecast_cell.get_text(strip=True) if forecast_cell else '',
                    'previous': previous_cell.get_text(strip=True) if previous_cell else '',
                })
            except Exception as e:
                continue
        
        print(f"[DEBUG] Fetched {len(events)} events")
        return events
        
    except Exception as e:
        print(f"Scrape error: {e}")
        import traceback
        traceback.print_exc()
        return []


def filter_today_events(events, days_ahead=0, min_impact='Medium'):
    """
    فیلتر اخبار بر اساس بازه زمانی و اهمیت
    """
    if not events:
        return []
    
    today = datetime.now().date()
    max_date = today + timedelta(days=days_ahead)
    filtered = []
    
    allowed_impacts = {
        'High': ['High'],
        'Medium': ['High', 'Medium'],
        'Low': ['High', 'Medium', 'Low'],
    }
    allowed = allowed_impacts.get(min_impact, ['High', 'Medium'])
    
    for ev in events:
        # فیلتر اهمیت
        if ev['impact'] not in allowed:
            continue
        
        # فیلتر ارز
        if ev['currency'] not in RELEVANT_CURRENCIES:
            continue
        
        # فیلتر تاریخ
        ev_date = ev.get('parsed_date')
        if ev_date is None:
            continue
        
        if not (today <= ev_date <= max_date):
            continue
        
        filtered.append(ev)
    
    # مرتب‌سازی
    impact_order = {'High': 0, 'Medium': 1, 'Low': 2}
    filtered.sort(key=lambda x: (
        x.get('parsed_date') or today,
        impact_order.get(x['impact'], 3)
    ))
    
    return filtered


def get_news_explanation(title):
    """دریافت توضیح فارسی برای یک خبر"""
    title_lower = title.lower()
    for key, explanation in NEWS_EXPLANATIONS.items():
        if key.lower() in title_lower:
            return explanation
    return None


def analyze_sentiment(events):
    """تحلیل احساسات اخبار"""
    if not events:
        return {
            'bias': 'neutral',
            'score': 0,
            'bullish': 0,
            'bearish': 0,
            'events': [],
            'summary': _format_summary([], 'neutral', 0, 0)
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
        'bias': bias,
        'score': net,
        'bullish': bull,
        'bearish': bear,
        'events': events,
        'summary': _format_summary(events, bias, bull, bear)
    }


def _format_summary(events, bias, bull, bear):
    """ساخت خلاصه فارسی"""
    bias_map = {
        'bullish': '🟢 صعودی',
        'bearish': '🔴 نزولی',
        'neutral': '⚪ خنثی'
    }
    
    msg = "📰 **تحلیل فاندامنتال**\n"
    msg += "━━━━━━━━━━━━━━━━━━━━\n"
    msg += f"**بایاس کلی:** {bias_map.get(bias, '⚪ خنثی')}\n\n"
    
    if not events:
        msg += "⚠️ **خبری در این بازه پیدا نشد.**\n\n"
        msg += "⚠️ _این تحلیل صرفاً آماری است و توصیه مالی نیست._"
        return msg
    
    today = datetime.now().date()
    msg += f"📊 **{len(events)} خبر مهم پیش رو:**\n\n"
    
    for ev in events[:10]:
        impact_emoji = {'High': '🔴', 'Medium': '🟡', 'Low': '🟢'}.get(ev['impact'], '⚪')
        currency_name = CURRENCY_NAMES.get(ev['currency'], ev['currency'])
        
        # برچسب تاریخ
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
            if ev.get('time'):
                msg += f" | ⏰ `{ev['time']}`"
            msg += "\n"
        
        # توضیح فارسی
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
    
    msg += f"\n📈 امتیاز صعودی: `{bull}`\n"
    msg += f"📉 امتیاز نزولی: `{bear}`\n"
    msg += "\n⚠️ _این تحلیل صرفاً آماری است و توصیه مالی نیست._"
    
    return msg
