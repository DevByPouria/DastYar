"""
اسکرپر ForexFactory - نسخه دیباگ کامل
"""
import json
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from pathlib import Path

import requests


OUTPUT_FILE = "calendar.json"
DAYS_AHEAD = 10

XML_URLS = [
    "https://nfs.faireconomy.media/ff_calendar_thisweek.xml",
]

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                  'AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/131.0.0.0 Safari/537.36',
}

MONTHS = {
    'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
    'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12,
    'january': 1, 'february': 2, 'march': 3, 'april': 4, 'june': 6,
    'july': 7, 'august': 8, 'september': 9, 'october': 10,
    'november': 11, 'december': 12,
}


def parse_date(date_str):
    """پارس تاریخ - نسخه مقاوم"""
    if not date_str:
        return None
    
    original = date_str.strip()
    
    # فرمت 1: ISO
    m = re.match(r'(\d{4})-(\d{2})-(\d{2})', original)
    if m:
        try:
            return datetime(int(m.group(1)), int(m.group(2)), int(m.group(3))).date().isoformat()
        except:
            pass
    
    # فرمت 2: MM/DD/YYYY یا MM-DD-YYYY
    m = re.match(r'(\d{1,2})[/\-](\d{1,2})[/\-](\d{2,4})', original)
    if m:
        try:
            a, b, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
            if y < 100:
                y += 2000
            # اگه a > 12، روزه
            if a > 12:
                return datetime(y, b, a).date().isoformat()
            else:
                return datetime(y, a, b).date().isoformat()
        except:
            pass
    
    # فرمت 3: متنی (Sep 15 یا 15 Sep یا Tue Sep 15)
    clean = original.lower().replace(',', '').replace('.', ' ')
    parts = clean.split()
    
    month = None
    day = None
    year = None
    
    for part in parts:
        part = part.strip()
        if part in MONTHS:
            month = MONTHS[part]
        elif part.isdigit():
            n = int(part)
            if n > 31:
                year = n
            elif day is None:
                day = n
    
    if month and day:
        if year is None:
            year = datetime.now().year
        try:
            return datetime(year, month, day).date().isoformat()
        except:
            pass
    
    return None


def scrape_via_xml():
    """دریافت داده از XML فید"""
    print("[INFO] Trying XML feed method...")
    events = []
    
    for url in XML_URLS:
        try:
            print(f"[INFO] Fetching: {url}")
            res = requests.get(url, headers=HEADERS, timeout=30)
            print(f"[INFO] Status: {res.status_code}, Size: {len(res.content)}")
            
            if res.status_code != 200:
                continue
            
            if b'<weeklyevents' not in res.content[:500]:
                print(f"[WARN] Not XML! First 300 chars: {res.content[:300]}")
                continue
            
            root = ET.fromstring(res.content)
            all_events = root.findall('.//event')
            print(f"[INFO] Found {len(all_events)} event elements")
            
            # ⬇️ چاپ نمونه اول برای دیباگ
            if all_events:
                sample = all_events[0]
                print("[DEBUG] ===== SAMPLE EVENT =====")
                print(f"[DEBUG] title: {sample.findtext('title')}")
                print(f"[DEBUG] country: {sample.findtext('country')}")
                print(f"[DEBUG] date: '{sample.findtext('date')}'")
                print(f"[DEBUG] time: '{sample.findtext('time')}'")
                print(f"[DEBUG] impact: {sample.findtext('impact')}")
                print(f"[DEBUG] forecast: {sample.findtext('forecast')}")
                print(f"[DEBUG] previous: {sample.findtext('previous')}")
                print("[DEBUG] =========================")
                
                # چاپ ۵ تاریخ اول برای دیباگ
                print("[DEBUG] First 5 dates:")
                for i, ev in enumerate(all_events[:5]):
                    print(f"[DEBUG]   {i}: '{ev.findtext('date')}'")
            
            count_ok = 0
            count_skip_title = 0
            count_skip_date_parse = 0
            count_skip_currency = 0
            
            for ev in all_events:
                title = (ev.findtext('title') or '').strip()
                currency = (ev.findtext('country') or '').strip()
                date_str = (ev.findtext('date') or '').strip()
                time_str = (ev.findtext('time') or '').strip()
                impact = (ev.findtext('impact') or 'Low').strip()
                forecast = (ev.findtext('forecast') or '').strip()
                previous = (ev.findtext('previous') or '').strip()
                actual = (ev.findtext('actual') or '').strip()
                
                if not title:
                    count_skip_title += 1
                    continue
                if not currency:
                    count_skip_currency += 1
                    continue
                
                parsed_date = parse_date(date_str)
                if not parsed_date:
                    count_skip_date_parse += 1
                    continue
                
                events.append({
                    "date": parsed_date,
                    "time": time_str,
                    "currency": currency.upper(),
                    "impact": impact.lower(),
                    "title": title,
                    "actual": actual,
                    "forecast": forecast,
                    "previous": previous,
                })
                count_ok += 1
            
            print(f"[INFO] === PARSING STATS ===")
            print(f"[INFO] OK: {count_ok}")
            print(f"[INFO] Skipped (no title): {count_skip_title}")
            print(f"[INFO] Skipped (no currency): {count_skip_currency}")
            print(f"[INFO] Skipped (date parse fail): {count_skip_date_parse}")
            print(f"[INFO] ======================")
            
            if events:
                print(f"[SUCCESS] Got {len(events)} events")
                break
                
        except Exception as e:
            print(f"[ERROR] XML fetch error: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    return events


def filter_by_date(events):
    """فیلتر بر اساس بازه تاریخی"""
    today = datetime.now().date()
    max_date = today + timedelta(days=DAYS_AHEAD)
    
    print(f"[INFO] Filter: today={today}, max={max_date}")
    
    filtered = []
    skipped_old = 0
    skipped_future = 0
    
    for ev in events:
        try:
            ev_date = datetime.fromisoformat(ev['date']).date()
            if ev_date < today:
                skipped_old += 1
            elif ev_date > max_date:
                skipped_future += 1
            else:
                filtered.append(ev)
        except Exception as e:
            print(f"[WARN] Filter error for date {ev['date']}: {e}")
            continue
    
    print(f"[INFO] Filtered: {len(filtered)} (skipped_old={skipped_old}, skipped_future={skipped_future})")
    return filtered


def main():
    print("=" * 60)
    print(f"Scraping started at {datetime.now().isoformat()}")
    print("=" * 60)
    
    events = scrape_via_xml()
    print(f"[DEBUG] After XML scrape: {len(events)} events")
    
    events = filter_by_date(events)
    print(f"[DEBUG] After date filter: {len(events)} events")
    
    # حذف تکراری‌ها
    seen = set()
    unique = []
    for ev in events:
        key = (ev['title'], ev['currency'], ev['date'], ev['time'])
        if key not in seen:
            seen.add(key)
            unique.append(ev)
    
    unique.sort(key=lambda x: (x['date'], x['time']))
    
    output = {
        "scraped_at": datetime.now().isoformat(),
        "count": len(unique),
        "events": unique,
    }
    
    Path(OUTPUT_FILE).write_text(
        json.dumps(output, ensure_ascii=False, indent=2),
        encoding='utf-8'
    )
    
    print(f"[INFO] Saved {len(unique)} events to {OUTPUT_FILE}")
    print("=" * 60)


if __name__ == "__main__":
    main()
