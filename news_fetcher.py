import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import zoneinfo

FF_XML_URL = "https://nfs.faireconomy.media/ff_calendar_thisweek.xml"

RELEVANT_CURRENCIES = ['USD', 'EUR', 'GBP', 'JPY', 'XAU']

HIGH_IMPACT_KEYWORDS = [
    'Non-Farm Employment Change',
    'ADP',
    'CPI',
    'FOMC',
    'Federal Funds Rate',
    'Interest Rate Decision',
    'GDP',
    'Unemployment Rate',
    'Retail Sales',
    'PMI',
    'PPI'
]

# ==================== دیکشنری توضیحات فارسی ====================
NEWS_EXPLANATIONS = {
    'Federal Funds Rate': {
        'desc': 'نرخ بهره کلیدی آمریکا که توسط فدرال رزرو (بانک مرکزی آمریکا) تعیین می‌شود.',
        'effect': 'افزایش نرخ بهره → دلار قوی‌تر می‌شود، طلا ضعیف‌تر (چون طلا سود نمی‌دهد و سرمایه‌ها به سمت اوراق قرضه می‌روند). کاهش نرخ بهره → برعکس.',
        'gold': '🔴 نزولی (با افزایش)',
        'dollar': '🟢 صعودی (با افزایش)'
    },
    'FOMC Statement': {
        'desc': 'بیانیه کمیته بازار آزاد فدرال رزرو درباره سیاست پولی و نرخ بهره.',
        'effect': 'لحن این بیانیه (انقباضی یا انبساطی) جهت بازار را مشخص می‌کند. لحن انقباضی (هوکیش) → دلار قوی، طلا ضعیف. لحن انبساطی (داویش) → برعکس.',
        'gold': '⚠️ بستگی به لحن دارد',
        'dollar': '⚠️ بستگی به لحن دارد'
    },
    'FOMC Economic Projections': {
        'desc': 'پیش‌بینی‌های اقتصادی اعضای فدرال رزرو از رشد، تورم و بیکاری.',
        'effect': 'اگر پیش‌بینی تورم بالاتر از قبل باشد → احتمال افزایش نرخ بهره بیشتر → دلار قوی، طلا ضعیف.',
        'gold': '⚠️ بستگی به داده دارد',
        'dollar': '⚠️ بستگی به داده دارد'
    },
    'FOMC Press Conference': {
        'desc': 'کنفرانس خبری رئیس فدرال رزرو پس از نشست.',
        'effect': 'هر کلمه‌ای که رئیس فدرال رزرو بگوید می‌تواند بازار را تکان دهد. اگر از ادامه افزایش نرخ بگوید → دلار قوی، طلا ضعیف.',
        'gold': '⚠️ بستگی به صحبت‌ها دارد',
        'dollar': '⚠️ بستگی به صحبت‌ها دارد'
    },
    'CPI': {
        'desc': 'شاخص قیمت مصرف‌کننده. مهم‌ترین معیار تورم در آمریکا.',
        'effect': 'CPI بالاتر از انتظار → تورم بیشتر → احتمال افزایش نرخ بهره → دلار قوی، طلا ضعیف (در کوتاه‌مدت). CPI پایین‌تر از انتظار → برعکس.',
        'gold': '🔴 نزولی (با CPI بالا)',
        'dollar': '🟢 صعودی (با CPI بالا)'
    },
    'Core CPI': {
        'desc': 'شاخص قیمت مصرف‌کننده بدون احتساب غذا و انرژی (نوسانات کمتری دارد).',
        'effect': 'مشابه CPI. عدد بالاتر → دلار قوی، طلا ضعیف.',
        'gold': '🔴 نزولی (با Core CPI بالا)',
        'dollar': '🟢 صعودی (با Core CPI بالا)'
    },
    'PPI': {
        'desc': 'شاخص قیمت تولیدکننده. تورم در سطح تولید.',
        'effect': 'PPI بالا → تورم بیشتر در آینده → احتمال افزایش نرخ بهره → دلار قوی، طلا ضعیف.',
        'gold': '🔴 نزولی (با PPI بالا)',
        'dollar': '🟢 صعودی (با PPI بالا)'
    },
    'Non-Farm Employment Change': {
        'desc': 'تغییر تعداد شاغلان غیرکشاورزی آمریکا (NFP). مهم‌ترین گزارش اشتغال.',
        'effect': 'NFP قوی‌تر از انتظار → اقتصاد قوی → احتمال افزایش نرخ بهره → دلار قوی، طلا ضعیف. NFP ضعیف‌تر → برعکس.',
        'gold': '🔴 نزولی (با NFP قوی)',
        'dollar': '🟢 صعودی (با NFP قوی)'
    },
    'ADP': {
        'desc': 'گزارش اشتغال بخش خصوصی (پیش‌درآمد NFP).',
        'effect': 'مشابه NFP. ADP قوی → دلار قوی، طلا ضعیف.',
        'gold': '🔴 نزولی (با ADP قوی)',
        'dollar': '🟢 صعودی (با ADP قوی)'
    },
    'Unemployment Rate': {
        'desc': 'نرخ بیکاری آمریکا.',
        'effect': 'نرخ بیکاری پایین‌تر از انتظار → اقتصاد قوی → دلار قوی، طلا ضعیف. نرخ بیکاری بالاتر → برعکس.',
        'gold': '🔴 نزولی (با بیکاری کم)',
        'dollar': '🟢 صعودی (با بیکاری کم)'
    },
    'GDP': {
        'desc': 'تولید ناخالص داخلی. معیار اصلی رشد اقتصاد آمریکا.',
        'effect': 'GDP قوی → اقتصاد قوی → دلار قوی، طلا ضعیف. GDP ضعیف → برعکس (طلا به عنوان پناهگاه امن).',
        'gold': '🔴 نزولی (با GDP قوی)',
        'dollar': '🟢 صعودی (با GDP قوی)'
    },
    'Retail Sales': {
        'desc': 'فروش خرده‌فروشی. نشان‌دهنده قدرت مصرف‌کننده.',
        'effect': 'خرده‌فروشی قوی → اقتصاد قوی → دلار قوی، طلا ضعیف.',
        'gold': '🔴 نزولی (با خرده‌فروشی قوی)',
        'dollar': '🟢 صعودی (با خرده‌فروشی قوی)'
    },
    'PMI': {
        'desc': 'شاخص مدیران خرید. بالای ۵۰ = رشد، زیر ۵۰ = رکود.',
        'effect': 'PMI قوی (بالای ۵۰) → اقتصاد قوی → دلار قوی، طلا ضعیف. PMI ضعیف (زیر ۵۰) → برعکس.',
        'gold': '🔴 نزولی (با PMI قوی)',
        'dollar': '🟢 صعودی (با PMI قوی)'
    },
    'Interest Rate Decision': {
        'desc': 'تصمیم نرخ بهره بانک مرکزی (فدرال رزرو یا سایر بانک‌ها).',
        'effect': 'افزایش نرخ → دلار قوی، طلا ضعیف. کاهش نرخ → برعکس.',
        'gold': '🔴 نزولی (با افزایش)',
        'dollar': '🟢 صعودی (با افزایش)'
    },
}

# ==================== توضیحات برای ارزها ====================
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


def _parse_event_date(date_str):
    """
    تبدیل تاریخ ForexFactory به شیء date پایتون
    فرمت‌های ممکن: 'Tue Sep 15' | 'Tuesday September 15' | 'Sep 15' | '09-15-2026'
    """
    if not date_str:
        return None
    
    months_short = {
        'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
        'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12,
    }
    months_long = {
        'january': 1, 'february': 2, 'march': 3, 'april': 4, 'may': 5, 'june': 6,
        'july': 7, 'august': 8, 'september': 9, 'october': 10,
        'november': 11, 'december': 12,
    }
    
    clean = date_str.strip().lower()
    parts = clean.replace(',', ' ').replace('.', ' ').split()
    
    month = None
    day = None
    year = None
    
    for part in parts:
        part = part.strip()
        if part in months_short:
            month = months_short[part]
        elif part in months_long:
            month = months_long[part]
        elif part.isdigit():
            num = int(part)
            if num > 31:  # این ساله
                year = num
            elif num <= 31 and day is None:
                day = num
    
    if month is None or day is None:
        return None
    
    if year is None:
        year = datetime.now().year
    
    try:
        return datetime(year, month, day).date()
    except:
        return None


def fetch_events():
    """دریافت رویدادها از ForexFactory"""
    try:
        res = requests.get(FF_XML_URL, timeout=15,
                           headers={'User-Agent': 'Mozilla/5.0'})
        res.raise_for_status()
        root = ET.fromstring(res.content)
        events = []
        for ev in root.findall('.//event'):
            events.append({
                'title': (ev.findtext('title') or '').strip(),
                'currency': (ev.findtext('country') or '').strip(),
                'date': (ev.findtext('date') or '').strip(),
                'time': (ev.findtext('time') or '').strip(),
                'impact': (ev.findtext('impact') or 'Low').strip(),
                'forecast': (ev.findtext('forecast') or '').strip(),
                'previous': (ev.findtext('previous') or '').strip(),
            })
        return events
    except Exception as e:
        print(f"News fetch error: {e}")
        return []


def filter_today_events(events, days_ahead=0, hours_back=0):
    """
    فیلتر اخبار مهم بر اساس بازه زمانی
    
    Args:
        events: لیست رویدادها
        days_ahead: 0 = فقط امروز | 1 = امروز و فردا | 7 = این هفته
    """
    if not events:
        return []
    
    today = datetime.now().date()
    max_date = today + timedelta(days=days_ahead)
    filtered = []
    
    for ev in events:
        # فقط اخبار مهم
        if ev['impact'] != 'High':
            continue
        # فقط ارزهای مرتبط
        if ev['currency'] not in RELEVANT_CURRENCIES:
            continue
        # فقط اخبار با کلمات کلیدی
        if not any(k.lower() in ev['title'].lower() for k in HIGH_IMPACT_KEYWORDS):
            continue
        
        # فیلتر تاریخ
        event_date = _parse_event_date(ev['date'])
        if event_date is None:
            continue
        
        if not (today <= event_date <= max_date):
            continue
        
        ev['parsed_date'] = event_date
        filtered.append(ev)
    
    # مرتب‌سازی بر اساس تاریخ
    filtered.sort(key=lambda x: x['parsed_date'])
    
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
        
        # NFP ضعیف → صعودی برای طلا
        if 'non-farm' in t or 'adp' in t:
            if forecast is not None and previous is not None:
                if forecast < previous:
                    bull += 3
                else:
                    bear += 2
        
        # CPI بالا → صعودی برای طلا
        elif 'cpi' in t:
            if forecast is not None and previous is not None:
                if forecast > previous:
                    bull += 2
                else:
                    bear += 2
        
        # GDP ضعیف → صعودی برای طلا
        elif 'gdp' in t:
            if forecast is not None and previous is not None:
                if forecast < previous:
                    bull += 2
                else:
                    bear += 1
        
        # افزایش نرخ بهره → نزولی برای طلا
        elif 'interest rate' in t or 'fomc' in t or 'federal funds' in t:
            bull += 0
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
    """ساخت خلاصه فارسی برای اخبار"""
    bias_map = {
        'bullish': '🟢 صعودی',
        'bearish': '🔴 نزولی',
        'neutral': '⚪ خنثی'
    }
    
    msg = "📰 **تحلیل فاندامنتال (فارسی)**\n"
    msg += "━━━━━━━━━━━━━━━━━━━━\n"
    msg += f"**بایاس کلی:** {bias_map.get(bias, '⚪ خنثی')}\n\n"
    
    if not events:
        msg += "📊 **امروز و فردا هیچ خبر مهمی در تقویم نیست.**\n\n"
        msg += "✅ بازار احتمالاً آرومه."
        msg += "\n\n⚠️ _این تحلیل صرفاً آماری است و توصیه مالی نیست._"
        return msg
    
    msg += "📊 **اخبار مهم پیش رو:**\n\n"
    
    today = datetime.now().date()
    
    for ev in events[:8]:
        impact_emoji = '🔴' if ev['impact'] == 'High' else '🟡'
        currency_name = CURRENCY_NAMES.get(ev['currency'], ev['currency'])
        
        # برچسب تاریخ
        date_label = ''
        if 'parsed_date' in ev:
            ev_date = ev['parsed_date']
            if ev_date == today:
                date_label = '📅 امروز'
            elif ev_date == today + timedelta(days=1):
                date_label = '📅 فردا'
            else:
                date_label = f"📅 {ev_date.strftime('%Y/%m/%d')}"
        
        # اسم خبر به انگلیسی
        msg += f"{impact_emoji} **{currency_name}** — `{ev['title']}`\n"
        
        if date_label:
            msg += f"   {date_label}"
            if ev.get('time'):
                msg += f" | ⏰ `{ev['time']}`"
            msg += "\n"
        
        # توضیح فارسی
        explanation = get_news_explanation(ev['title'])
        if explanation:
            msg += f"   📖 **توضیح:** {explanation['desc']}\n"
            msg += f"   💡 **تأثیر:** {explanation['effect']}\n"
            msg += f"   🥇 **طلا:** {explanation['gold']}  |  💵 **دلار:** {explanation['dollar']}\n"
        
        # پیش‌بینی و قبلی
        if ev['forecast']:
            msg += f"   📊 پیش‌بینی: `{ev['forecast']}`"
            if ev['previous']:
                msg += f"  |  قبلی: `{ev['previous']}`"
            msg += "\n"
        
        msg += "   ───────────────────\n"
    
    msg += f"\n📈 **امتیاز صعودی:** `{bull}`\n"
    msg += f"📉 **امتیاز نزولی:** `{bear}`\n"
    msg += "\n⚠️ _این تحلیل صرفاً آماری است و توصیه مالی نیست._"
    
    return msg
