import os
import requests
from datetime import datetime, timedelta
import re

# ==================== تنظیمات ====================
FMP_API_KEY = os.getenv('FMP_API_KEY')
FMP_BASE_URL = "https://financialmodelingprep.com/stable/economic-calendar"

ALL_CURRENCIES = ['USD', 'EUR', 'GBP', 'JPY', 'XAU', 'CAD', 'AUD', 'NZD', 'CHF', 'CNY']

# ==================== دیکشنری توضیحات فارسی ====================
NEWS_EXPLANATIONS = {
    'Federal Funds Rate': {'desc': 'نرخ بهره کلیدی آمریکا.', 'effect': 'افزایش → دلار قوی، طلا ضعیف.', 'gold': '🔴 نزولی', 'dollar': '🟢 صعودی'},
    'Fed Interest Rate': {'desc': 'نرخ بهره کلیدی آمریکا.', 'effect': 'افزایش → دلار قوی، طلا ضعیف.', 'gold': '🔴 نزولی', 'dollar': '🟢 صعودی'},
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


def _impact_from_string(impact_str):
    """تبدیل impact FMP به High/Medium/Low"""
    if not impact_str:
        return 'Low'
    s = str(impact_str).lower()
    if 'high' in s:
        return 'High'
    if 'medium' in s:
        return 'Medium'
    return 'Low'


def fetch_events(days_ahead=7):
    """دریافت رویدادهای اقتصادی از FMP"""
    if not FMP_API_KEY:
        print("[DEBUG] FMP_API_KEY not set!", flush=True)
        return []
    
    try:
        today = datetime.now().date()
        end_date = today + timedelta(days=days_ahead)
        
        params = {
            'from': today.strftime('%Y-%m-%d'),
            'to': end_date.strftime('%Y-%m-%d'),
            'apikey': FMP_API_KEY,
        }
        
        print(f"[DEBUG] Fetching FMP: {today} to {end_date}", flush=True)
        
        res = requests.get(FMP_BASE_URL, params=params, timeout=20)
        print(f"[DEBUG] FMP status: {res.status_code}", flush=True)
        
        if res.status_code != 200:
            print(f"[DEBUG] FMP error: {res.text[:300]}", flush=True)
            return []
        
        data = res.json()
        print(f"[DEBUG] FMP returned: {len(data) if isinstance(data, list) else 'not a list'}", flush=True)
        
        if not isinstance(data, list) or not data:
            return []
        
        # چاپ نمونه
        print(f"[DEBUG] Sample keys: {list(data[0].keys())}", flush=True)
        print(f"[DEBUG] Sample: {data[0]}", flush=True)
        
        events = []
        for item in data:
            try:
                # استخراج فیلدها
                title = item.get('event') or item.get('name') or ''
                currency = item.get('currency') or ''
                date_str = item.get('date') or ''
                impact = item.get('impact') or ''
                forecast = item.get('forecast') or ''
                previous = item.get('previous') or ''
                actual = item.get('actual') or ''
                
                if not title or not currency:
                    continue
                
                currency = str(currency).strip().upper()
                impact_str = _impact_from_string(impact)
                
                # پارس تاریخ (فرمت FMP: YYYY-MM-DD یا YYYY-MM-DD HH:MM:SS)
                parsed_date = None
                time_str = ''
                if date_str:
                    try:
                        if ' ' in str(date_str):
                            parts = str(date_str).split(' ')
                            parsed_date = datetime.strptime(parts[0], '%Y-%m-%d').date()
                            time_str = parts[1][:5]  # HH:MM
                        else:
                            parsed_date = datetime.strptime(str(date_str)[:10], '%Y-%m-%d').date()
                    except Exception as e:
                        print(f"[DEBUG] Date parse error: {e} for {date_str}", flush=True)
                        continue
                
                if not parsed_date:
                    continue
                
                events.append({
                    'title': str(title).strip(),
                    'currency': currency,
                    'date': str(date_str),
                    'parsed_date': parsed_date,
                    'time': time_str,
                    'impact': impact_str,
                    'forecast': str(forecast),
                    'previous': str(previous),
                    'actual': str(actual),
                })
            except Exception as e:
                continue
        
        print(f"[DEBUG] Total events parsed: {len(events)}", flush=True)
        
        # حذف تکراری‌ها
        seen = set()
        unique_events = []
        for ev in events:
            key = (ev['title'], ev['currency'], str(ev['parsed_date']))
            if key not in seen:
                seen.add(key)
                unique_events.append(ev)
        
        print(f"[DEBUG] Unique events: {len(unique_events)}", flush=True)
        return unique_events
        
    except Exception as e:
        print(f"[DEBUG] FMP error: {e}", flush=True)
        import traceback
        traceback.print_exc()
        return []


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
