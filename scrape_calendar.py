"""
اسکرپر تقویم ForexFactory - نسخه ۲
اول XML فید رو امتحان می‌کنه، اگه نشد Playwright با Stealth
"""
import asyncio
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
    "https://nfs.faireconomy.media/ff_calendar_nextweek.xml",
]

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                  'AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/131.0.0.0 Safari/537.36',
    'Accept': 'application/xml,text/xml,*/*',
    'Accept-Language': 'en-US,en;q=0.9',
}

MONTHS = {
    'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
    'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12,
    'january': 1, 'february': 2, 'march': 3, 'april': 4, 'june': 6,
    'july': 7, 'august': 8, 'september': 9, 'october': 10,
    'november': 11, 'december': 12,
}


def parse_date(date_str):
    if not date_str:
        return None
    clean = date_str.strip().lower().replace(',', '')
    parts = clean.split()
    
    month = None
    day = None
    year = None
    
    for part in parts:
        part = part.strip('.')
        if part in MONTHS:
            month = MONTHS[part]
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
        return datetime(year, month, day).date().isoformat()
    except:
        return None


def scrape_via_xml():
    """دریافت داده از XML فید (بدون مرورگر)"""
    print("[INFO] Trying XML feed method...")
    events = []
    
    for url in XML_URLS:
        try:
            print(f"[INFO] Fetching: {url}")
            res = requests.get(url, headers=HEADERS, timeout=30)
            print(f"[INFO] Status: {res.status_code}, Size: {len(res.content)}")
            
            if res.status_code != 200:
                print(f"[WARN] Bad status: {res.status_code}")
                continue
            
            # چک کن که XML معتبره (نه صفحه HTML)
            if b'<weeklyevents' not in res.content[:500]:
                print(f"[WARN] Not XML content. Preview: {res.content[:200]}")
                continue
            
            root = ET.fromstring(res.content)
            all_events = root.findall('.//event')
            print(f"[INFO] Found {len(all_events)} event elements")
            
            for ev in all_events:
                title = (ev.findtext('title') or '').strip()
                currency = (ev.findtext('country') or '').strip()
                date_str = (ev.findtext('date') or '').strip()
                time_str = (ev.findtext('time') or '').strip()
                impact = (ev.findtext('impact') or 'Low').strip()
                forecast = (ev.findtext('forecast') or '').strip()
                previous = (ev.findtext('previous') or '').strip()
                actual = (ev.findtext('actual') or '').strip()
                
                parsed_date = parse_date(date_str)
                if not title or not currency or not parsed_date:
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
            
            if events:
                print(f"[SUCCESS] XML method worked! Got {len(events)} events")
                break
                
        except Exception as e:
            print(f"[WARN] XML fetch error for {url}: {e}")
            continue
    
    return events


def filter_by_date(events):
    """فیلتر کردن رویدادها بر اساس بازه تاریخی"""
    today = datetime.now().date()
    max_date = today + timedelta(days=DAYS_AHEAD)
    
    filtered = []
    for ev in events:
        try:
            ev_date = datetime.fromisoformat(ev['date']).date()
            if today <= ev_date <= max_date:
                filtered.append(ev)
        except:
            continue
    
    return filtered


def main():
    print("=" * 60)
    print(f"Scraping started at {datetime.now().isoformat()}")
    print("=" * 60)
    
    # امتحان XML اول
    events = scrape_via_xml()
    
    # فیلتر بر اساس تاریخ
    events = filter_by_date(events)
    
    # حذف تکراری‌ها
    seen = set()
    unique = []
    for ev in events:
        key = (ev['title'], ev['currency'], ev['date'], ev['time'])
        if key not in seen:
            seen.add(key)
            unique.append(ev)
    
    # مرتب‌سازی
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
