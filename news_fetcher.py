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
# برای هر خبر، توضیح ساده + تأثیر روی طلا و دلار
NEWS_EXPLANATIONS = {
    # ===== نرخ بهره فدرال رزرو =====
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

    # ===== تورم =====
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

    # ===== اشتغال =====
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

    # ===== رشد اقتصادی =====
    'GDP': {
        'desc': 'تولید ناخالص داخلی. معیار اصلی رشد اقتصاد آمریکا.',
        'effect': 'GDP قوی → اقتصاد قوی → دلار قوی، طلا ضعیف. GDP ضعیف → برعکس (طلا به عنوان پناهگاه امن).',
        'gold': '🔴 نزولی (با GDP قوی)',
        'dollar': '🟢 صعودی (با GDP قوی)'
    },

    # ===== خرده‌فروشی =====
    'Retail Sales': {
        'desc': 'فروش خرده‌فروشی. نشان‌دهنده قدرت مصرف‌کننده.',
        'effect': 'خرده‌فروشی قوی → اقتصاد قوی → دلار قوی، طلا ضعیف.',
        'gold': '🔴 نزولی (با خرده‌فروشی قوی)',
        'dollar': '🟢 صعودی (با خرده‌فروشی قوی)'
    },

    # ===== PMI =====
    'PMI': {
        'desc': 'شاخص مدیران خرید. بالای ۵۰ = رشد، زیر ۵۰ = رکود.',
        'effect': 'PMI قوی (بالای ۵۰) → اقتصاد قوی → دلار قوی، طلا ضعیف. PMI ضعیف (زیر ۵۰) → برعکس.',
        'gold': '🔴 نزولی (با PMI قوی)',
        'dollar': '🟢 صعودی (با PMI قوی)'
    },

    # ===== سایر =====
    'Interest Rate Decision': {
        'desc': 'تصمیم نرخ بهره بانک مرکزی (فدرال رزرو یا سایر بانک‌ها).',
        'effect': 'افزایش نرخ → دلار قوی، طلا ضعیف. کاهش نرخ → برعکس.',
        'gold': '🔴 نزولی (با افزایش)',
        'dollar': '🟢 صعودی (با افزایش)'
    },
}

# ==================== توضیحات برای ارزهای غیر دلاری ====================
CURRENCY_NAMES = {
    'USD': '🇺🇸 دلار آمریکا',
    'EUR': '🇪🇺 یورو',
    'GBP': '🇬🇧 پوند انگلستان',
    'JPY': '🇯🇵 ین ژاپن',
    'XAU': '🥇 طلا',
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

def filter_today_events(events):
    """فیلتر اخبار مهم"""
    if not events:
        return []
    filtered = []
    for ev in events:
        if ev['impact'] != 'High':
            continue
        if ev['currency'] not in RELEVANT_CURRENCIES:
            continue
        if not any(k.lower() in ev['title'].lower() for k in HIGH_IMPACT_KEYWORDS):
            continue
        filtered.append(ev)
    return filtered

def get_news_explanation(title):
    """
    دریافت توضیح فارسی برای یک خبر
    برمی‌گرداند دیکشنری با توضیح، تأثیر، اثر روی طلا و دلار
    """
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
            'summary': "📰 امروز خبر مهم اقتصادی مؤثری در تقویم نیست."
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
        
        # CPI بالا → صعودی برای طلا (در بلندمدت)
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
    msg += "📊 **اخبار مهم امروز:**\n\n"
    
    for ev in events[:6]:
        impact_emoji = '🔴' if ev['impact'] == 'High' else '🟡'
        currency_name = CURRENCY_NAMES.get(ev['currency'], ev['currency'])
        
        msg += f"{impact_emoji} **{currency_name}** — {ev['title']}\n"
        
        # اضافه کردن توضیح فارسی
        explanation = get_news_explanation(ev['title'])
        if explanation:
            msg += f"   📖 **توضیح:** {explanation['desc']}\n"
            msg += f"   💡 **تأثیر:** {explanation['effect']}\n"
            msg += f"   🥇 **طلا:** {explanation['gold']}  |  💵 **دلار:** {explanation['dollar']}\n"
        
        # نمایش پیش‌بینی و مقدار قبلی
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
