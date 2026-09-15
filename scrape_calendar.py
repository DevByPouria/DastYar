"""
اسکرپر تقویم اقتصادی ForexFactory
روی GitHub Actions اجرا میشه (نه روی Render)
"""
import asyncio
import json
import re
from datetime import datetime, timedelta
from pathlib import Path

from playwright.async_api import async_playwright


# ==================== تنظیمات ====================
OUTPUT_FILE = "calendar.json"
DAYS_AHEAD = 10  # اخبار ۱۰ روز آینده

MONTHS = {
    'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
    'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12,
    'january': 1, 'february': 2, 'march': 3, 'april': 4, 'june': 6,
    'july': 7, 'august': 8, 'september': 9, 'october': 10,
    'november': 11, 'december': 12,
}


def parse_date(date_str: str):
    """پارس تاریخ از فرمت‌های مختلف ForexFactory"""
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


async def scrape_forexfactory():
    """اسکرپ تقویم ForexFactory"""
    events = []
    
    async with async_playwright() as p:
        print("[INFO] Launching browser...")
        browser = await p.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-dev-shm-usage']
        )
        
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                       'AppleWebKit/537.36 (KHTML, like Gecko) '
                       'Chrome/128.0.0.0 Safari/537.36',
            locale='en-US',
            timezone_id='America/New_York',
        )
        
        page = await context.new_page()
        
        print("[INFO] Loading ForexFactory calendar...")
        await page.goto(
            "https://www.forexfactory.com/calendar?week=this",
            wait_until="domcontentloaded",
            timeout=60000
        )
        
        try:
            await page.wait_for_selector("table.calendar__table", timeout=30000)
            print("[INFO] Calendar table loaded")
        except Exception as e:
            print(f"[ERROR] Table not found: {e}")
            html = await page.content()
            print(f"[DEBUG] HTML length: {len(html)}")
            Path("debug_calendar.html").write_text(html, encoding='utf-8')
            await browser.close()
            return []
        
        html_content = await page.content()
        Path("debug_calendar.html").write_text(html_content, encoding='utf-8')
        print(f"[INFO] Saved debug HTML ({len(html_content)} chars)")
        
        rows = await page.query_selector_all("tr.calendar__row")
        print(f"[INFO] Found {len(rows)} rows")
        
        today = datetime.now().date()
        max_date = today + timedelta(days=DAYS_AHEAD)
        current_date = today
        
        for row in rows:
            try:
                date_cell = await row.query_selector("td.calendar__date")
                if date_cell:
                    date_text = (await date_cell.inner_text()).strip()
                    if date_text:
                        parsed = parse_date(date_text)
                        if parsed:
                            current_date = datetime.fromisoformat(parsed).date()
                
                currency_cell = await row.query_selector("td.calendar__currency")
                if not currency_cell:
                    continue
                currency = (await currency_cell.inner_text()).strip().upper()
                if not currency:
                    continue
                
                event_cell = await row.query_selector("td.calendar__event")
                if not event_cell:
                    continue
                title = (await event_cell.inner_text()).strip()
                if not title:
                    continue
                
                if not (today <= current_date <= max_date):
                    continue
                
                impact_cell = await row.query_selector("td.calendar__impact span")
                impact = "low"
                if impact_cell:
                    classes = (await impact_cell.get_attribute("class")) or ""
                    if "high" in classes.lower():
                        impact = "high"
                    elif "medium" in classes.lower():
                        impact = "medium"
                    elif "low" in classes.lower():
                        impact = "low"
                    elif "holiday" in classes.lower():
                        impact = "holiday"
                
                time_cell = await row.query_selector("td.calendar__time")
                time_str = (await time_cell.inner_text()).strip() if time_cell else ""
                
                actual_cell = await row.query_selector("td.calendar__actual")
                forecast_cell = await row.query_selector("td.calendar__forecast")
                previous_cell = await row.query_selector("td.calendar__previous")
                
                actual = (await actual_cell.inner_text()).strip() if actual_cell else ""
                forecast = (await forecast_cell.inner_text()).strip() if forecast_cell else ""
                previous = (await previous_cell.inner_text()).strip() if previous_cell else ""
                
                events.append({
                    "date": current_date.isoformat(),
                    "time": time_str,
                    "currency": currency,
                    "impact": impact,
                    "title": title,
                    "actual": actual,
                    "forecast": forecast,
                    "previous": previous,
                })
            except Exception as e:
                print(f"[WARN] Row error: {e}")
                continue
        
        await browser.close()
    
    seen = set()
    unique = []
    for ev in events:
        key = (ev['title'], ev['currency'], ev['date'], ev['time'])
        if key not in seen:
            seen.add(key)
            unique.append(ev)
    
    print(f"[INFO] Total unique events: {len(unique)}")
    return unique


def main():
    print("=" * 60)
    print(f"Scraping started at {datetime.now().isoformat()}")
    print("=" * 60)
    
    events = asyncio.run(scrape_forexfactory())
    
    output = {
        "scraped_at": datetime.now().isoformat(),
        "count": len(events),
        "events": events,
    }
    
    Path(OUTPUT_FILE).write_text(
        json.dumps(output, ensure_ascii=False, indent=2),
        encoding='utf-8'
    )
    
    print(f"[INFO] Saved {len(events)} events to {OUTPUT_FILE}")
    print("=" * 60)


if __name__ == "__main__":
    main()
