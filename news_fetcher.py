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
    """فیلتر اخبار مهم امروز"""
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
    bias_map = {'bullish': '🟢 صعودی', 'bearish': '🔴 نزولی', 'neutral': '⚪ خنثی'}
    msg = f"📰 **تحلیل فاندامنتال:** {bias_map.get(bias, '⚪ خنثی')}\n\n"
    msg += "📊 **اخبار مهم امروز:**\n"
    for ev in events[:6]:
        impact_emoji = '🔴' if ev['impact'] == 'High' else '🟡'
        msg += f"  {impact_emoji} **{ev['currency']}** — {ev['title']}\n"
        if ev['forecast']:
            msg += f"     پیش‌بینی: `{ev['forecast']}`"
            if ev['previous']:
                msg += f" | قبلی: `{ev['previous']}`"
            msg += "\n"
    msg += f"\n📈 امتیاز صعودی: **{bull}**\n"
    msg += f"📉 امتیاز نزولی: **{bear}**"
    return msg
