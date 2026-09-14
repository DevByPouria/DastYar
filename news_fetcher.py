import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import re

# ==================== URLها ====================
FF_XML_THIS_WEEK = "https://nfs.faireconomy.media/ff_calendar_thisweek.xml"
FF_XML_NEXT_WEEK = "https://nfs.faireconomy.media/ff_calendar_nextweek.xml"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
}

# همه ارزها (نه فقط ارزهای اصلی)
ALL_CURRENCIES = ['USD', 'EUR', 'GBP', 'JPY', 'XAU', 'CAD', 'AUD', 'NZD', 'CHF', 'CNY']

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
    'Bond Auction': {
        'desc': 'حراج اوراق قرضه دولتی.',
        'effect': 'تقاضای بالا → ارز قوی‌تر.',
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
    """پارس تاریخ"""
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
    """دریافت رویدادها از XML فید ForexFactory"""
    events = []
    
    for url in [FF_XML_THIS_WEEK, FF_XML_NEXT_WEEK]:
        try:
            res = requests.get(url, headers=HEADERS, timeout=20)
            print(f"[DEBUG] XML {url.split('/')[-1]}: status={res.status_code}, size={len(res.content)}")
            
            if res.status_code != 200:
                continue
            
            root = ET.fromstring(res.content)
            week_events = 0
            
            for ev in root.findall('.//event'):
                title = (ev.findtext('title') or '').strip()
                currency = (ev.findtext('country') or '').strip()
                date_str = (ev.findtext('date') or '').strip()
                time_str = (ev.findtext('time') or '').strip()
                impact = (ev.findtext('impact') or 'Low').strip()
                forecast = (ev.findtext('forecast') or '').strip()
                previous = (ev.findtext('previous') or '').strip()
                
                parsed_date = _parse_date(date_str)
                
                if not title or not currency or not parsed_date:
                    continue
                
                events.append({
                    'title': title,
                    'currency': currency,
                    'date': date_str,
                    'parsed_date': parsed_date,
                    'time': time_str,
                    'impact': impact,
                    'forecast': forecast,
                    'previous': previous,
                })
                week_events += 1
            
            print(f"[DEBUG] {url.split('/')[-1]}: {week_events} events")
            
        except Exception as e:
            print(f"[DEBUG] Error for {url}: {e}")
            continue
    
    # حذف تکراری‌ها
    seen = set()
    unique_events = []
    for ev in events:
        key = (ev['title'], ev['currency'], str(ev['parsed_date']))
        if key not in seen:
            seen.add(key)
            unique_events.append(ev)
    
    print(f"[DEBUG] Total unique events: {len(unique_events)}")
    return unique_events


def filter_today_events(events, days_ahead=7, min_impact='All'):
    """
    فیلتر اخبار
    
    Args:
        days_ahead: 0 = امروز | 7 = این هفته
        min_impact: 'High' | 'Medium' | 'Low' | 'All'
            - High: فقط High
            - Medium: High + Medium
            - Low: High + Medium + Low
            - All: همه اخبار (حتی بدون impact)
    """
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
    
    # مرتب‌سازی: اول High، بعد Medium، بعد Low (داخل هر گروه بر اساس تاریخ)
    impact_order = {'High': 0, 'Medium': 1, 'Low': 2, '': 3}
    filtered.sort(key=lambda x: (
        x.get('parsed_date') or today,
        impact_order.get(x['impact'], 3)
    ))
    
    print(f"[DEBUG] Filtered: {len(filtered)} events (min_impact={min_impact}, days_ahead={days_ahead})")
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
    
    # نمایش 20 خبر اول (چون حالا ممکنه خیلی زیاد باشن)
    for ev in events[:20]:
        impact_emoji = {
            'High': '🔴',
            'Medium': '🟡',
            'Low': '🟢',
            '': '⚪'
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
            if ev.get('time'):
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
