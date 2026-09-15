import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import re
import json
import os

# ==================== تنظیمات ====================
FF_XML_THIS_WEEK = "https://nfs.faireconomy.media/ff_calendar_thisweek.xml"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
}

CACHE_FILE = '/tmp/news_cache.json'
CACHE_DURATION_HOURS = 6

ALL_CURRENCIES = ['USD', 'EUR', 'GBP', 'JPY', 'XAU', 'CAD', 'AUD', 'NZD', 'CHF', 'CNY']

# ==================== دیکشنری توضیحات فارسی ====================
NEWS_EXPLANATIONS = {
    'Federal Funds Rate': {'desc': 'نرخ بهره کلیدی آمریکا.', 'effect': 'افزایش → دلار قوی، طلا ضعیف.', 'gold': '🔴 نزولی', 'dollar': '🟢 صعودی'},
    'FOMC Statement': {'desc': 'بیانیه فدرال رزرو.', 'effect': 'لحن انقباضی → دلار قوی.', 'gold': '⚠️ بستگی دارد', 'dollar': '⚠️ بستگی دارد'},
    'FOMC Economic Projections': {'desc': 'پیش‌بینی‌های فدرال رزرو.', 'effect': 'تورم بالاتر → دلار قوی.', 'gold': '⚠️ بستگی دارد', 'dollar': '⚠️ بستگی دارد'},
    'FOMC Press Conference': {'desc': 'کنفرانس رئیس فدرال رزرو.', 'effect': 'هر کلمه بازار رو تکان می‌ده.', 'gold': '⚠️ بستگی دارد', 'dollar': '⚠️ بستگی دارد'},
    'FOMC Member': {'desc': 'سخنرانی عضو فدرال رزرو.', 'effect': 'تغییر انتظارات نرخ بهره.', 'gold': '⚠️ بستگی دارد', 'dollar': '⚠️ بستگی دارد'},
    'CPI': {'desc': 'شاخص قیمت مصرف‌کننده.', 'effect': 'CPI بالا → دلار قوی، طلا ضعیف.', 'gold': '🔴 نزولی', 'dollar': '🟢 صعودی'},
    'Core CPI': {'desc': 'CPI بدون غذا و انرژی.', 'effect': 'مشابه CPI.', 'gold': '🔴 نزولی', 'dollar': '🟢 صعودی'},
    'PPI': {'desc': 'شاخص قیمت تولیدکننده.', 'effect': 'PPI بالا → دلار قوی.', 'gold': '🔴 نزولی', 'dollar': '🟢 صعودی'},
    'Non-Farm': {'desc': 'تغییر شاغلان غیرکشاورزی (NFP).', 'effect': 'NFP قوی → دلار قوی.', 'gold': '🔴 نزولی', 'dollar': '🟢 صعودی'},
    'ADP': {'desc': 'اشتغال بخش خصوصی.', 'effect': 'ADP قوی → دلار قوی.', 'gold': '🔴 نزولی', 'dollar': '🟢 صعودی'},
    'Unemployment': {'desc': 'نرخ بیکاری.', 'effect': 'بیکاری کم → دلار قوی.', 'gold': '🔴 نزولی', 'dollar': '🟢 صعودی'},
    'Jobless Claims': {'desc': 'مدعیان بیمه بیکاری.', 'effect': 'عدد کمتر → دلار قوی.', 'gold': '🔴 نزولی', 'dollar': '🟢 صعودی'},
    'Unemployment Claims': {'desc': 'مدعیان بیمه بیکاری.', 'effect': 'عدد کمتر → دلار قوی.', 'gold': '🔴 نزولی', 'dollar': '🟢 صعودی'},
    'GDP': {'desc': 'تولید ناخالص داخلی.', 'effect': 'GDP قوی → دلار قوی.', 'gold': '🔴 نزولی', 'dollar': '🟢 صعودی'},
    'Retail Sales': {'desc': 'فروش خرده‌فروشی.', 'effect': 'قوی → دلار قوی.', 'gold': '🔴 نزولی', 'dollar': '🟢 صعودی'},
    'PMI': {'desc': 'شاخص مدیران خرید.', 'effect': 'بالای ۵۰ → ارز قوی.', 'gold': '🔴 نزولی', 'dollar': '🟢 صعودی'},
    'Interest Rate': {'desc': 'نرخ بهره بانک مرکزی.', 'effect': 'افزایش → دلار قوی.', 'gold': '🔴 نزولی', 'dollar': '🟢 صعودی'},
    'Official Bank Rate': {'desc': 'نرخ بهره بانک انگلستان.', 'effect': 'افزایش → پوند قوی.', 'gold': '🔴 نزولی', 'dollar': '⚠️ غیرمستقیم'},
    'BOJ Policy Rate': {'desc': 'نرخ بهره بانک ژاپن.', 'effect': 'افزایش → ین قوی.', 'gold': '⚠️ غیرمستقیم', 'dollar': '⚠️ غیرمستقیم'},
    'Employment Change': {'desc': 'تغییر اشتغال.', 'effect': 'قوی → ارز قوی.', 'gold': '🔴 نزولی', 'dollar': '🟢 صعودی'},
    'Trade Balance': {'desc': 'تراز تجاری.', 'effect': 'مثبت → ارز قوی.', 'gold': '⚠️ غیرمستقیم', 'dollar': '⚠️ غیرمستقیم'},
    'Current Account': {'desc': 'حساب جاری.', 'effect': 'مثبت → ارز قوی.', 'gold': '⚠️ غیرمستقیم', 'dollar': '⚠️ غیرمستقیم'},
    'ZEW': {'desc': 'احساسات اقتصادی ZEW آلمان.', 'effect': 'بالا → یورو قوی.', 'gold': '⚠️ غیرمستقیم', 'dollar': '⚠️ غیرمستقیم'},
    'Consumer Confidence': {'desc': 'اعتماد مصرف‌کننده.', 'effect': 'بالا → ارز قوی.', 'gold': '⚠️ غیرمستقیم', 'dollar': '⚠️ غیرمستقیم'},
    'Business Climate': {'desc': 'فضای کسب و کار.', 'effect': 'بالا → ارز قوی.', 'gold': '⚠️ غیرمستقیم', 'dollar': '⚠️ غیرمستقیم'},
    'Manufacturing': {'desc': 'شاخص تولید صنعتی.', 'effect': 'بالا → ارز قوی.', 'gold': '⚠️ غیرمستقیم', 'dollar': '⚠️ غیرمستقیم'},
    'Services': {'desc': 'شاخص بخش خدمات.', 'effect': 'بالا → ارز قوی.', 'gold': '⚠️ غیرمستقیم', 'dollar': '⚠️ غیرمستقیم'},
    'Housing': {'desc': 'شاخص مسکن.', 'effect': 'بالا → ارز قوی.', 'gold': '⚠️ غیرمستقیم', 'dollar': '⚠️ غیرمستقیم'},
    'Building Permits': {'desc': 'مجوزهای ساخت.', 'effect': 'بالا → دلار قوی.', 'gold': '⚠️ غیرمستقیم', 'dollar': '🟢 صعودی'},
    'Bond Auction': {'desc': 'حراج اوراق قرضه.', 'effect': 'تقاضای بالا → ارز قوی.', 'gold': '⚠️ غیرمستقیم', 'dollar': '⚠️ غیرمستقیم'},
    'Lagarde': {'desc': 'سخنرانی رئیس ECB.', 'effect': 'روی یورو تأثیر داره.', 'gold': '⚠️ غیرمستقیم', 'dollar': '⚠️ غیرمستقیم'},
    'Powell': {'desc': 'سخنرانی رئیس فدرال رزرو.', 'effect': 'مهم‌ترین سخنران.', 'gold': '⚠️ بستگی دارد', 'dollar': '⚠️ بستگی دارد'},
    'ECB': {'desc': 'بانک مرکزی اروپا.', 'effect': 'روی یورو تأثیر داره.', 'gold': '⚠️ غیرمستقیم', 'dollar': '⚠️ غیرمستقیم'},
}

CURRENCY_NAMES = {
    'USD': '🇺🇸 دلار آمریکا', 'EUR': '🇪🇺 یورو', 'GBP': '🇬🇧 پوند انگلستان',
    'JPY': '🇯🇵 ین ژاپن', 'XAU': '🥇 طلا', 'CAD': '🇨🇦 دلار کانادا',
    'AUD': '🇦🇺 دلار استرالیا', 'NZD': '🇳🇿 دلار نیوزیلند',
    'CHF': '🇨🇭 فرانک سوئیس', 'CNY': '🇨🇳 یوان چین',
}
# ================================================================


def _parse_value(v):
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
    """
    پارسر مقاوم تاریخ - همه فرمت‌های ممکن رو می‌شناسه
    """
    if not date_str:
        return None
    
    original = str(date_str).strip()
    print(f"[DEBUG] _parse_date input: '{original}'", flush=True)
    
    # ماه‌ها
    months = {
        'jan': 1, 'january': 1, 'feb': 2, 'february': 2,
        'mar': 3, 'march': 3, 'apr': 4, 'april': 4,
        'may': 5, 'jun': 6, 'june': 6, 'jul': 7, 'july': 7,
        'aug': 8, 'august': 8, 'sep': 9, 'sept': 9, 'september': 9,
        'oct': 10, 'october': 10, 'nov': 11, 'november': 11,
        'dec': 12, 'december': 12,
    }
    
    today = datetime.now().date()
    
    # فرمت 1: ISO (2026-09-16 یا 2026-09-16T10:30:00)
    if re.match(r'^\d{4}-\d{2}-\d{2}', original):
        try:
            return datetime.fromisoformat(original.replace('Z', '').split('T')[0]).date()
        except:
            pass
    
    # فرمت 2: MM/DD/YYYY یا DD/MM/YYYY یا MM-DD-YYYY
    m = re.match(r'^(\d{1,2})[/\-\.](\d{1,2})(?:[/\-\.](\d{2,4}))?$', original)
    if m:
        a, b, y = int(m.group(1)), int(m.group(2)), m.group(3)
        year = int(y) if y else today.year
        if year < 100:
            year += 2000
        # اگه a > 12، پس روزه
        if a > 12:
            return datetime(year, b, a).date()
        # اگه b > 12، پس a ماهه
        elif b > 12:
            return datetime(year, a, b).date()
        else:
            # پیش‌فرض: MM/DD (آمریکایی)
            return datetime(year, a, b).date()
    
    # فرمت 3: متنی (Sep 16, 16 Sep, Tue Sep 16)
    clean = original.lower().replace(',', '').replace('.', ' ')
    parts = clean.split()
    
    month = None
    day = None
    year = None
    
    for part in parts:
        part = part.strip()
        if part in months:
            month = months[part]
        elif part.isdigit():
            n = int(part)
            if n > 31:
                year = n
            elif day is None:
                day = n
    
    if month and day:
        if year is None:
            year = today.year
        try:
            result = datetime(year, month, day).date()
            print(f"[DEBUG] Parsed: {result}", flush=True)
            return result
        except Exception as e:
            print(f"[DEBUG] Date construct error: {e}", flush=True)
    
    print(f"[DEBUG] Could not parse date: '{original}'", flush=True)
    return None


def _load_cache():
    if not os.path.exists(CACHE_FILE):
        return None
    try:
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        cached_at = datetime.fromisoformat(data.get('cached_at', '2000-01-01'))
        if datetime.now() - cached_at < timedelta(hours=CACHE_DURATION_HOURS):
            print(f"[DEBUG] Using CACHE ({len(data.get('events', []))} events)", flush=True)
            events = []
            for ev in data.get('events', []):
                if ev.get('parsed_date'):
                    ev['parsed_date'] = datetime.fromisoformat(ev['parsed_date']).date()
                events.append(ev)
            return events
        else:
            print("[DEBUG] Cache expired", flush=True)
            return None
    except Exception as e:
        print(f"[DEBUG] Cache load error: {e}", flush=True)
        return None


def _save_cache(events):
    try:
        serializable = []
        for ev in events:
            ev_copy = ev.copy()
            if ev_copy.get('parsed_date'):
                ev_copy['parsed_date'] = ev_copy['parsed_date'].isoformat()
            serializable.append(ev_copy)
        data = {'cached_at': datetime.now().isoformat(), 'events': serializable}
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False)
        print(f"[DEBUG] Cache SAVED ({len(events)} events)", flush=True)
    except Exception as e:
        print(f"[DEBUG] Cache save error: {e}", flush=True)


def _fetch_from_xml():
    events = []
    
    try:
        res = requests.get(FF_XML_THIS_WEEK, headers=HEADERS, timeout=20)
        print(f"[DEBUG] XML status={res.status_code}, size={len(res.content)}", flush=True)
        
        if res.status_code == 429:
            print("[DEBUG] Rate limited!", flush=True)
            return []
        
        if res.status_code != 200:
            return []
        
        # ⬇️ چاپ 1500 کاراکتر اول XML برای دیباگ
        print("=" * 60, flush=True)
        print("[DEBUG] XML PREVIEW (first 1500 chars):", flush=True)
        print(res.text[:1500], flush=True)
        print("=" * 60, flush=True)
        
        root = ET.fromstring(res.content)
        print(f"[DEBUG] Root tag: {root.tag}", flush=True)
        
        # پیدا کردن همه eventها
        all_events = root.findall('.//event')
        print(f"[DEBUG] Found {len(all_events)} <event> elements", flush=True)
        
        # اگه هیچی پیدا نشد، ساختار رو چاپ کن
        if not all_events:
            print("[DEBUG] No <event> tags found. Structure:", flush=True)
            for child in root:
                print(f"[DEBUG]   <{child.tag}> with {len(list(child))} children", flush=True)
            return []
        
        # چاپ 3 نمونه اول
        for i, ev in enumerate(all_events[:3]):
            print(f"[DEBUG] Event {i} children: {[c.tag for c in ev]}", flush=True)
            print(f"[DEBUG] Event {i} title='{ev.findtext('title')}' date='{ev.findtext('date')}' country='{ev.findtext('country')}'", flush=True)
        
        count = 0
        skip_no_title = 0
        skip_no_date = 0
        skip_date_parse = 0
        
        for ev in all_events:
            title = (ev.findtext('title') or '').strip()
            currency = (ev.findtext('country') or '').strip()
            date_str = (ev.findtext('date') or '').strip()
            time_str = (ev.findtext('time') or '').strip()
            impact = (ev.findtext('impact') or 'Low').strip()
            forecast = (ev.findtext('forecast') or '').strip()
            previous = (ev.findtext('previous') or '').strip()
            
            if not title:
                skip_no_title += 1
                continue
            if not date_str:
                skip_no_date += 1
                continue
            
            parsed_date = _parse_date(date_str)
            if not parsed_date:
                skip_date_parse += 1
                continue
            if not currency:
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
            count += 1
        
        print(f"[DEBUG] Parsed OK: {count}", flush=True)
        print(f"[DEBUG] Skipped - no title: {skip_no_title}, no date: {skip_no_date}, date parse fail: {skip_date_parse}", flush=True)
        
    except Exception as e:
        print(f"[DEBUG] XML error: {e}", flush=True)
        import traceback
        traceback.print_exc()
    
    return events


def fetch_events(days_ahead=7):
    print("[DEBUG] fetch_events STARTED", flush=True)
    
    cached = _load_cache()
    if cached and len(cached) > 0:
        return cached
    
    events = _fetch_from_xml()
    
    if events:
        _save_cache(events)
    
    # حذف تکراری‌ها
    seen = set()
    unique_events = []
    for ev in events:
        key = (ev['title'], ev['currency'], str(ev['parsed_date']))
        if key not in seen:
            seen.add(key)
            unique_events.append(ev)
    
    print(f"[DEBUG] Total unique events: {len(unique_events)}", flush=True)
    return unique_events


def filter_today_events(events, days_ahead=7, min_impact='All'):
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
    
    impact_order = {'High': 0, 'Medium': 1, 'Low': 2, '': 3}
    filtered.sort(key=lambda x: (x.get('parsed_date') or today, impact_order.get(x['impact'], 3)))
    
    print(f"[DEBUG] Filtered: {len(filtered)} events", flush=True)
    return filtered


def get_news_explanation(title):
    title_lower = title.lower()
    for key, explanation in NEWS_EXPLANATIONS.items():
        if key.lower() in title_lower:
            return explanation
    return None


def analyze_sentiment(events):
    if not events:
        return {'bias': 'neutral', 'score': 0, 'bullish': 0, 'bearish': 0,
                'events': [], 'summary': _format_summary([], 'neutral', 0, 0)}
    
    bull = 0; bear = 0
    for ev in events:
        t = ev['title'].lower()
        forecast = _parse_value(ev['forecast'])
        previous = _parse_value(ev['previous'])
        
        if 'non-farm' in t or 'adp' in t:
            if forecast is not None and previous is not None:
                if forecast < previous: bull += 3
                else: bear += 2
        elif 'cpi' in t:
            if forecast is not None and previous is not None:
                if forecast > previous: bull += 2
                else: bear += 2
        elif 'gdp' in t:
            if forecast is not None and previous is not None:
                if forecast < previous: bull += 2
                else: bear += 1
        elif 'interest rate' in t or 'fomc' in t or 'federal funds' in t:
            bear += 1
    
    net = bull - bear
    if net >= 3: bias = 'bullish'
    elif net <= -3: bias = 'bearish'
    else: bias = 'neutral'
    
    return {'bias': bias, 'score': net, 'bullish': bull, 'bearish': bear,
            'events': events, 'summary': _format_summary(events, bias, bull, bear)}


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
        impact_emoji = {'High': '🔴', 'Medium': '🟡', 'Low': '🟢', '': '⚪'}.get(ev['impact'], '⚪')
        currency_name = CURRENCY_NAMES.get(ev['currency'], ev['currency'])
        
        date_label = ''
        if ev.get('parsed_date'):
            ev_date = ev['parsed_date']
            if ev_date == today: date_label = '📅 امروز'
            elif ev_date == today + timedelta(days=1): date_label = '📅 فردا'
            else: date_label = f"📅 {ev_date.strftime('%m/%d')}"
        
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
