"""
دریافت و ذخیره‌ی داده‌های تاریخی قیمت
با ترکیب داده‌های داخلی و Yahoo Finance
"""
import sqlite3
import requests
import pandas as pd
from datetime import datetime, timedelta
import zoneinfo

DB_PATH = 'price_history.db'

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                  '(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
}

# ============================================================
# نمادهای Yahoo Finance
# ============================================================
# توضیحات:
#  - GC=F     : Gold Futures (آتی طلا)
#  - XAUUSD=X : Spot Gold (نقدی طلا) — دقیق‌تره
#  - SI=F     : Silver Futures
#  - CL=F     : Crude Oil Futures
#  - BTC-USD  : Bitcoin
#  - ETH-USD  : Ethereum
#  - EURUSD=X : Euro/USD
# ============================================================
YAHOO_SYMBOLS = {
    # طلا و فلزات
    'gold_gram18': 'XAUUSD=X',      # طلای نقدی (به جای آتی)
    'gold_ons': 'XAUUSD=X',         # اونس طلا
    'silver': 'SI=F',               # نقره
    'oil': 'CL=F',                  # نفت

    # ارز
    'dollar': 'USDIRR=X',           # دلار ایران (اگه موجود باشه)
    'eur': 'EURUSD=X',              # یورو/دلار
    'gbp': 'GBPUSD=X',              # پوند/دلار
    'jpy': 'USDJPY=X',              # دلار/ین

    # کریپتو
    'bitcoin': 'BTC-USD',
    'ethereum': 'ETH-USD',

    # شاخص‌ها
    'sp500': '^GSPC',
    'dxy': 'DX-Y.NYB',              # شاخص دلار
}

# ============================================================
# روزهای داده‌ی تاریخی برای تحلیل تکنیکال
# ============================================================
#  - برای SMA 200 حداقل 200 رکورد نیاز داریم
#  - 500 روز ≈ 1.5 سال، کافیه
# ============================================================
HISTORY_DAYS = 500
MIN_RECORDS_FOR_ANALYSIS = 100  # حداقل رکورد برای شروع تحلیل
MIN_RECORDS_FOR_SMA200 = 220    # حداقل رکورد برای SMA 200


def init_db():
    """ساخت جدول دیتابیس"""
    conn = sqlite3.connect(DB_PATH)
    
    # چک کن جدول قدیمی هست یا نه
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='price_snapshots'"
    )
    table_exists = cursor.fetchone() is not None
    
    if table_exists:
        # چک ساختار
        cursor = conn.execute("PRAGMA table_info(price_snapshots)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'source' not in columns:
            print("[DEBUG] Old table detected — recreating", flush=True)
            conn.execute("DROP TABLE price_snapshots")
            table_exists = False
    
    if not table_exists:
        conn.execute('''
            CREATE TABLE price_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                asset_key TEXT,
                price REAL,
                timestamp TEXT,
                date_shamsi TEXT,
                source TEXT DEFAULT 'live'
            )
        ''')
    
    conn.execute('''
        CREATE INDEX IF NOT EXISTS idx_asset_time
        ON price_snapshots(asset_key, timestamp)
    ''')
    conn.commit()
    conn.close()
    print("[DEBUG] Database initialized", flush=True)


def save_snapshot(asset_key, price):
    """ذخیره یک قیمت لحظه‌ای در دیتابیس"""
    if not price:
        return
    try:
        tehran = zoneinfo.ZoneInfo("Asia/Tehran")
        now = datetime.now(tehran)
        conn = sqlite3.connect(DB_PATH)
        conn.execute(
            "INSERT INTO price_snapshots (asset_key, price, timestamp, date_shamsi, source) "
            "VALUES (?, ?, ?, ?, ?)",
            (asset_key, float(price), now.isoformat(),
             now.strftime("%Y/%m/%d %H:%M"), 'live')
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[DEBUG] Save snapshot error: {e}", flush=True)


def fetch_yahoo_history(symbol, days=HISTORY_DAYS):
    """
    دریافت داده‌های تاریخی از Yahoo Finance
    
    Returns:
        list of (unix_timestamp, price)
    """
    try:
        period1 = int((datetime.now() - timedelta(days=days)).timestamp())
        period2 = int(datetime.now().timestamp())

        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
        params = {
            'period1': period1,
            'period2': period2,
            'interval': '1d',
            'events': 'div,splits',
        }

        print(f"[DEBUG] Fetching Yahoo: {symbol} ({days} days)", flush=True)
        res = requests.get(url, params=params, headers=HEADERS, timeout=20)
        print(f"[DEBUG] Yahoo status: {res.status_code}", flush=True)

        if res.status_code != 200:
            print(f"[DEBUG] Yahoo error body: {res.text[:200]}", flush=True)
            return []

        data = res.json()
        result = data.get('chart', {}).get('result', [])
        if not result:
            print(f"[DEBUG] No Yahoo result for {symbol}", flush=True)
            return []

        timestamps = result[0].get('timestamp', [])
        quotes = result[0].get('indicators', {}).get('quote', [{}])[0]
        closes = quotes.get('close', [])

        rows = []
        for ts, close in zip(timestamps, closes):
            if close is not None and close > 0:
                rows.append((int(ts), float(close)))

        print(f"[DEBUG] Yahoo returned {len(rows)} rows for {symbol}", flush=True)
        return rows

    except Exception as e:
        print(f"[DEBUG] Yahoo fetch error for {symbol}: {e}", flush=True)
        import traceback
        traceback.print_exc()
        return []


def _save_historical_to_db(asset_key, rows):
    """ذخیره داده‌های تاریخی در دیتابیس (بدون تکرار)"""
    if not rows:
        return

    try:
        conn = sqlite3.connect(DB_PATH)
        # چک کنیم که آیا قبلاً ذخیره شده
        cursor = conn.execute(
            "SELECT COUNT(*) FROM price_snapshots WHERE asset_key = ? AND source = 'yahoo'",
            (asset_key,)
        )
        existing = cursor.fetchone()[0]

        if existing >= MIN_RECORDS_FOR_SMA200:
            print(f"[DEBUG] Yahoo data already cached for {asset_key} ({existing} rows)", flush=True)
            conn.close()
            return

        # حذف داده‌های قدیمی یاهو (اگه ناقص بودن)
        if existing > 0:
            conn.execute(
                "DELETE FROM price_snapshots WHERE asset_key = ? AND source = 'yahoo'",
                (asset_key,)
            )

        tehran = zoneinfo.ZoneInfo("Asia/Tehran")
        inserted = 0

        for ts, price in rows:
            try:
                dt = datetime.fromtimestamp(ts, tz=tehran)
                conn.execute(
                    "INSERT INTO price_snapshots "
                    "(asset_key, price, timestamp, date_shamsi, source) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (asset_key, float(price), dt.isoformat(),
                     dt.strftime("%Y/%m/%d"), 'yahoo')
                )
                inserted += 1
            except Exception as e:
                continue

        conn.commit()
        conn.close()
        print(f"[DEBUG] Saved {inserted} Yahoo rows for {asset_key}", flush=True)

    except Exception as e:
        print(f"[DEBUG] Save historical error: {e}", flush=True)


def get_history(asset_key, limit=HISTORY_DAYS):
    """
    دریافت تاریخچه قیمت‌ها
    
    اولویت:
        ۱. داده‌های Yahoo ذخیره‌شده (اگه کافی باشن)
        ۲. دریافت تازه از Yahoo
        ۳. داده‌های لحظه‌ای داخلی (به‌عنوان fallback)
    
    Returns:
        list of (price, timestamp_string)
    """
    # ===== ۱. چک دیتابیس =====
    conn = sqlite3.connect(DB_PATH)

    # اول Yahoo
    cursor = conn.execute(
        "SELECT price, timestamp FROM price_snapshots "
        "WHERE asset_key = ? AND source = 'yahoo' "
        "ORDER BY timestamp ASC LIMIT ?",
        (asset_key, limit)
    )
    yahoo_rows = cursor.fetchall()
    conn.close()

    if len(yahoo_rows) >= MIN_RECORDS_FOR_ANALYSIS:
        print(f"[DEBUG] Using {len(yahoo_rows)} cached Yahoo rows for {asset_key}", flush=True)
        return yahoo_rows

    # ===== ۲. دریافت از Yahoo =====
    symbol = YAHOO_SYMBOLS.get(asset_key)
    if symbol:
        yahoo_data = fetch_yahoo_history(symbol, days=HISTORY_DAYS)
        if yahoo_data:
            _save_historical_to_db(asset_key, yahoo_data)

            # برگردوندن به فرمت (price, timestamp)
            tehran = zoneinfo.ZoneInfo("Asia/Tehran")
            result = []
            for ts, price in yahoo_data[-limit:]:
                dt = datetime.fromtimestamp(ts, tz=tehran)
                result.append((price, dt.isoformat()))

            print(f"[DEBUG] Returning {len(result)} fresh Yahoo rows for {asset_key}", flush=True)
            return result

    # ===== ۳. Fallback به داده لحظه‌ای داخلی =====
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.execute(
        "SELECT price, timestamp FROM price_snapshots "
        "WHERE asset_key = ? AND source = 'live' "
        "ORDER BY timestamp DESC LIMIT ?",
        (asset_key, limit)
    )
    live_rows = cursor.fetchall()
    conn.close()

    if live_rows:
        print(f"[DEBUG] Fallback to {len(live_rows)} live rows for {asset_key}", flush=True)
        return list(reversed(live_rows))

    print(f"[DEBUG] No data available for {asset_key}", flush=True)
    return []


def get_data_count(asset_key):
    """تعداد رکوردهای ذخیره شده"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.execute(
            "SELECT COUNT(*) FROM price_snapshots WHERE asset_key = ?",
            (asset_key,)
        )
        count = cursor.fetchone()[0]
        conn.close()
        return count
    except:
        return 0


def get_data_info(asset_key):
    """اطلاعات کامل درباره داده‌ی موجود"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.execute(
            "SELECT source, COUNT(*) FROM price_snapshots "
            "WHERE asset_key = ? GROUP BY source",
            (asset_key,)
        )
        rows = cursor.fetchall()
        conn.close()

        info = {
            'total': sum(r[1] for r in rows),
            'yahoo': 0,
            'live': 0,
        }
        for source, count in rows:
            if source in info:
                info[source] = count

        return info
    except:
        return {'total': 0, 'yahoo': 0, 'live': 0}
