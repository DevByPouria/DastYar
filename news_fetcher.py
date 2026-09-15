import json
from datetime import datetime, timedelta
import requests
import re

# ==================== تنظیمات ====================
GITHUB_RAW_URL = "https://raw.githubusercontent.com/DevByPouria/DastYar/main/calendar.json"

ALL_CURRENCIES = ['USD', 'EUR', 'GBP', 'JPY', 'XAU', 'CAD', 'AUD', 'NZD', 'CHF', 'CNY']

# ارزهایی که بیشترین تأثیر رو روی طلا دارن
PRIMARY_CURRENCIES = ['USD', 'EUR']

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
        if v.endswith('K'): return float(v[:-1]) * 1000
        if v.endswith('M'): return float(v[:-1]) * 1_000_000
        if v.endswith('B'): return float(v[:-1]) * 1_000_000_000
        return float(v)
    except:
        return None


def fetch_events(days_ahead=7):
    """دریافت رویدادها از calendar.json توی گیت‌هاب"""
    try:
        print(f"[DEBUG] Fetching from GitHub: {GITHUB_RAW_URL}", flush=True)
        res = requests.get(GITHUB_RAW_URL, timeout=15)
        
        if res.status_code != 200:
            print(f"[DEBUG] GitHub returned {res.status_code}", flush=True)
            return []
        
        data = res.json()
        raw_events = data.get('events', [])
        
        print(f"[DEBUG] Got {len(raw_events)} events from GitHub", flush=True)
        
        events = []
        for item in raw_events:
            try:
                title = item.get('title', '')
                currency = item.get('currency', '').upper()
                date_str = item.get('date', '')
                time_str = item.get('time', '')
                impact = item.get('impact', 'low')
                forecast = str(item.get('forecast', ''))
                previous = str(item.get('previous', ''))
                actual = str(item.get('actual', ''))
                
                if not title or not currency or not date_str:
                    continue
                
                impact_str = str(impact).capitalize()
                if impact_str not in ['High', 'Medium', 'Low']:
                    impact_str = 'Low'
                
                try:
                    parsed_date = datetime.strptime(date_str[:10], '%Y-%m-%d').date()
                except:
                    continue
                
                time_only = time_str
                if time_str:
                    try:
                        m = re.match(r'(\d{1,2}):(\d{2})(am|pm)?', time_str.lower())
                        if m:
                            hour = int(m.group(1))
                            minute = m.group(2)
                            ampm = m.group(3)
                            if ampm == 'pm' and hour < 12:
                                hour += 12
                            elif ampm == 'am' and hour == 12:
                                hour = 0
                            time_only = f"{hour:02d}:{minute}"
                    except:
                        pass
                
                events.append({
                    'title': title.strip(),
                    'currency': currency,
                    'date': date_str,
                    'parsed_date': parsed_date,
                    'time': time_only,
                    'impact': impact_str,
                    'forecast': forecast,
                    'previous': previous,
                    'actual': actual,
                })
            except Exception:
                continue
        
        print(f"[DEBUG] Parsed {len(events)} events", flush=True)
        return events
        
    except Exception as e:
        print(f"[DEBUG] Fetch error: {e}", flush=True)
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


def _get_currency_weight(currency):
    """
    وزن ارز: USD بیشترین تأثیر رو روی طلا داره
    """
    if currency == 'USD':
        return 2.0
    elif currency == 'EUR':
        return 1.2
    elif currency in ['GBP', 'JPY', 'CNY']:
        return 1.0
    else:
        return 0.6


def analyze_sentiment(events):
    """
    تحلیل هوشمند Sentiment با تشخیص Hawkish/Dovish
    
    منطق:
        - اگه actual داریم → استفاده کن (دقیق‌ترین)
        - وگرنه از forecast استفاده کن
        - هر خبر بر اساس وزن ارز و اهمیت امتیاز می‌گیره
        - Hawkish/Dovish بر اساس جهت تغییر
    """
    if not events:
        return {
            'bias': 'neutral', 'score': 0, 'bullish': 0, 'bearish': 0,
            'analyzed_count': 0, 'hawkish_count': 0, 'dovish_count': 0,
            'market_mood': 'neutral',
            'events': [], 'summary': _format_summary([], 'neutral', 0, 0, 'neutral', 0, 0, 0)
        }
    
    bull = 0
    bear = 0
    analyzed_count = 0
    hawkish_count = 0
    dovish_count = 0
    
    for ev in events:
        title_lower = ev['title'].lower()
        impact = ev.get('impact', 'low')
        currency = ev.get('currency', '')
        
        # فقط High و Medium
        if impact == 'low':
            continue
        
        forecast = _parse_value(ev.get('forecast', ''))
        previous = _parse_value(ev.get('previous', ''))
        actual = _parse_value(ev.get('actual', ''))
        
        # انتخاب مقدار مقایسه: actual در اولویت
        compare_value = actual if actual is not None else forecast
        
        if compare_value is None or previous is None:
            continue
        
        # وزن ارز
        weight = _get_currency_weight(currency)
        
        # جهت تغییر
        diff = compare_value - previous
        
        # آستانه‌ی ناچیز
        if previous != 0 and abs(diff / previous) < 0.001:
            continue  # تغییر ناچیز
        
        # ========== دسته‌بندی اخبار ==========
        
        # ۱. اشتغال (NFP/ADP)
        if any(k in title_lower for k in ['non-farm', 'adp', 'employment change']):
            analyzed_count += 1
            if diff > 0:
                bear += int(3 * weight)  # اشتغال قوی → Hawkish
                hawkish_count += 1
            else:
                bull += int(3 * weight)  # اشتغال ضعیف → Dovish
                dovish_count += 1
        
        # ۲. تورم (CPI/PPI)
        elif any(k in title_lower for k in ['cpi', 'ppi', 'inflation']):
            analyzed_count += 1
            if diff > 0:
                bear += int(2 * weight)  # تورم بالا → Hawkish
                hawkish_count += 1
            else:
                bull += int(2 * weight)  # تورم کم → Dovish
                dovish_count += 1
        
        # ۳. نرخ بهره (Interest Rate/FOMC)
        elif any(k in title_lower for k in ['interest rate', 'fomc', 'federal funds', 'bank rate', 'policy rate']):
            analyzed_count += 1
            if diff > 0:
                bear += int(3 * weight)  # افزایش نرخ → Hawkish
                hawkish_count += 1
            elif diff < 0:
                bull += int(3 * weight)  # کاهش نرخ → Dovish
                dovish_count += 1
        
        # ۴. رشد اقتصادی (GDP)
        elif 'gdp' in title_lower:
            analyzed_count += 1
            if diff > 0:
                bear += int(2 * weight)
                hawkish_count += 1
            else:
                bull += int(2 * weight)
                dovish_count += 1
        
        # ۵. بیکاری (Unemployment)
        elif 'unemployment' in title_lower:
            analyzed_count += 1
            if diff < 0:  # بیکاری کمتر
                bear += int(2 * weight)
                hawkish_count += 1
            else:
                bull += int(2 * weight)
                dovish_count += 1
        
        # ۶. بیمه بیکاری (Jobless Claims)
        elif 'jobless' in title_lower or 'claims' in title_lower:
            analyzed_count += 1
            if diff < 0:  # claims کمتر → اشتغال قوی
                bear += int(2 * weight)
                hawkish_count += 1
            else:
                bull += int(2 * weight)
                dovish_count += 1
        
        # ۷. خرده‌فروشی (Retail Sales)
        elif 'retail sales' in title_lower:
            analyzed_count += 1
            if diff > 0:
                bear += int(1 * weight)
                hawkish_count += 1
            else:
                bull += int(1 * weight)
                dovish_count += 1
        
        # ۸. PMI/Manufacturing
        elif any(k in title_lower for k in ['pmi', 'manufacturing', 'industrial production']):
            analyzed_count += 1
            # PMI بالای ۵۰ = رشد
            if compare_value > 50 and diff > 0:
                bear += int(1 * weight)
                hawkish_count += 1
            elif compare_value < 50 and diff < 0:
                bull += int(1 * weight)
                dovish_count += 1
    
    # ===== محاسبه بایاس =====
    net = bull - bear
    
    if net >= 4:
        bias = 'bullish'
    elif net <= -4:
        bias = 'bearish'
    else:
        bias = 'neutral'
    
    # ===== تشخیص Mood بازار =====
    if hawkish_count > dovish_count + 1:
        market_mood = 'hawkish'
    elif dovish_count > hawkish_count + 1:
        market_mood = 'dovish'
    else:
        market_mood = 'neutral'
    
    print(f"[DEBUG] Sentiment: bull={bull}, bear={bear}, net={net}, "
          f"analyzed={analyzed_count}, hawkish={hawkish_count}, dovish={dovish_count}, "
          f"mood={market_mood}", flush=True)
    
    return {
        'bias': bias,
        'score': net,
        'bullish': bull,
        'bearish': bear,
        'analyzed_count': analyzed_count,
        'hawkish_count': hawkish_count,
        'dovish_count': dovish_count,
        'market_mood': market_mood,
        'events': events,
        'summary': _format_summary(
            events, bias, bull, bear, market_mood,
            analyzed_count, hawkish_count, dovish_count
        )
    }


def _format_summary(events, bias, bull, bear, market_mood, analyzed, hawkish, dovish):
    bias_map = {'bullish': '🟢 صعودی', 'bearish': '🔴 نزولی', 'neutral': '⚪ خنثی'}
    mood_map = {
        'hawkish': '🦅 Hawkish (انقباضی)',
        'dovish': '🕊️ Dovish (انبساطی)',
        'neutral': '⚖️ Neutral (خنثی)'
    }
    
    msg = "📰 **تحلیل فاندامنتال**\n"
    msg += "━━━━━━━━━━━━━━━━━━━━\n"
    msg += f"**بایاس کلی:** {bias_map.get(bias, '⚪ خنثی')}\n"
    msg += f"**حالت بازار:** {mood_map.get(market_mood, '⚖️ Neutral')}\n\n"
    
    # خلاصه‌ی تحلیل
    msg += f"📊 **آمار:**\n"
    msg += f"  • تعداد اخبار تحلیل‌شده: `{analyzed}`\n"
    msg += f"  • سیگنال‌های Hawkish: `{hawkish}` 🦅\n"
    msg += f"  • سیگنال‌های Dovish: `{dovish}` 🕊️\n"
    msg += f"  • امتیاز صعودی: `{bull}`\n"
    msg += f"  • امتیاز نزولی: `{bear}`\n\n"
    
    if not events:
        msg += "⚠️ **خبری در این بازه پیدا نشد.**\n\n"
        msg += "⚠️ _این تحلیل صرفاً آماری است و توصیه مالی نیست._"
        return msg
    
    today = datetime.now().date()
    msg += f"📋 **{len(events)} خبر در این بازه:**\n\n"
    
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
            if ev.get('time'):
                msg += f" | ⏰ `{ev['time']}`"
            msg += "\n"
        
        explanation = get_news_explanation(ev['title'])
        if explanation:
            msg += f"   📖 {explanation['desc']}\n"
            msg += f"   💡 {explanation['effect']}\n"
            msg += f"   🥇 طلا: {explanation['gold']} | 💵 دلار: {explanation['dollar']}\n"
        
        if ev['forecast'] and ev['forecast'] != 'None':
            msg += f"   📊 پیش‌بینی: `{ev['forecast']}`"
            if ev['previous'] and ev['previous'] != 'None':
                msg += f" | قبلی: `{ev['previous']}`"
            if ev['actual'] and ev['actual'] != 'None':
                msg += f" | واقعی: `{ev['actual']}`"
            msg += "\n"
        
        msg += "   ───────────────────\n"
    
    if len(events) > 20:
        msg += f"\n... و {len(events) - 20} خبر دیگر"
    
    msg += "\n⚠️ _این تحلیل صرفاً آماری است و توصیه مالی نیست._"
    return msg
