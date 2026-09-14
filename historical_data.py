import sqlite3
import requests
import pandas as pd
from datetime import datetime, timedelta
import jdatetime
import zoneinfo

DB_PATH = 'price_history.db'
HEADERS = {'User-Agent': 'Mozilla/5.0'}

# نمادهای Yahoo Finance برای هر دارایی
YAHOO_SYMBOLS = {
    'gold_gram18': 'GC=F',      # آتی طلا (اونس)
    'gold_ons': 'GC=F',         # اونس طلا
    'silver': 'SI=F',           # نقره
    'oil': 'CL=F',              # نفت
    'dollar': 'IRR=X',          # دلار (اگه موجود باشه)
    'bitcoin': 'BTC-USD',       # بیت کوین
    'ethereum': 'ETH-USD',      # اتریوم
    'eur': 'EURUSD=X',          # یورو/دلار
}

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS price_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            asset_key TEXT,
            price INTEGER,
            timestamp TEXT,
            date_shamsi TEXT
        )
    ''')
    conn.execute('''
        CREATE INDEX IF NOT EXISTS idx_asset_time
        ON price_snapshots(asset_key, timestamp)
    ''')
    conn.commit()
    conn.close()

def save_snapshot(asset_key, price):
    """ذخیره یک قیمت در دیتابیس"""
    if not price:
        return
    try:
        tehran = zoneinfo.ZoneInfo("Asia/Tehran")
        now = datetime.now(tehran)
        conn = sqlite3.connect(DB_PATH)
        conn.execute(
            "INSERT INTO price_snapshots (asset_key, price, timestamp, date_shamsi) VALUES (?, ?, ?, ?)",
            (asset_key, int(price), now.isoformat(), now.strftime("%Y/%m/%d %H:%M"))
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Save snapshot error: {e}")

def fetch_yahoo_history(symbol, days=200):
    """
    دریافت داده‌های تاریخی از Yahoo Finance
    برمی‌گرداند لیستی از تاپل‌های (timestamp, price)
    """
    try:
        period1 = int((datetime.now() - timedelta(days=days)).timestamp())
        period2 = int(datetime.now().timestamp())
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
        params = {
            'period1': period1,
            'period2': period2,
            'interval': '1d',
        }
        res = requests.get(url, params=params, headers=HEADERS, timeout=15)
        res.raise_for_status()
        data = res.json()
        
        result = data.get('chart', {}).get('result', [])
        if not result:
            return []
        
        timestamps = result[0].get('timestamp', [])
        quotes = result[0].get('indicators', {}).get('quote', [{}])[0]
        closes = quotes.get('close', [])
        
        rows = []
        for ts, close in zip(timestamps, closes):
            if close is not None:
                rows.append((int(ts), float(close)))
        return rows
    except Exception as e:
        print(f"Yahoo fetch error for {symbol}: {e}")
        return []

def get_history(asset_key, limit=200):
    """
    دریافت تاریخچه قیمت‌ها.
    اگر داده داخلی کم بود، از Yahoo Finance می‌گیریم.
    """
    # ۱. اول دیتابیس داخلی را چک کن
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.execute(
        "SELECT price, timestamp FROM price_snapshots WHERE asset_key = ? ORDER BY timestamp DESC LIMIT ?",
        (asset_key, limit)
    )
    rows = cursor.fetchall()
    conn.close()
    
    # اگه داده کافی داریم، همون رو برگردون
    if len(rows) >= 30:
        return list(reversed(rows))
    
    # ۲. اگه کم بود، از Yahoo Finance بگیر
    symbol = YAHOO_SYMBOLS.get(asset_key)
    if symbol:
        yahoo_rows = fetch_yahoo_history(symbol, days=200)
        if yahoo_rows:
            # ذخیره در دیتابیس برای استفاده بعدی
            for ts, price in yahoo_rows[-limit:]:
                try:
                    conn = sqlite3.connect(DB_PATH)
                    dt = datetime.fromtimestamp(ts, tz=zoneinfo.ZoneInfo("Asia/Tehran"))
                    conn.execute(
                        "INSERT INTO price_snapshots (asset_key, price, timestamp, date_shamsi) VALUES (?, ?, ?, ?)",
                        (asset_key, int(price), dt.isoformat(), dt.strftime("%Y/%m/%d %H:%M"))
                    )
                    conn.commit()
                    conn.close()
                except:
                    pass
            
            # برگردوندن به فرمت یکسان
            return [(price, datetime.fromtimestamp(ts).isoformat()) for ts, price in yahoo_rows[-limit:]]
    
    return []

def get_data_count(asset_key):
    """تعداد رکوردهای ذخیره شده"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.execute(
        "SELECT COUNT(*) FROM price_snapshots WHERE asset_key = ?",
        (asset_key,)
    )
    count = cursor.fetchone()[0]
    conn.close()
    return count
