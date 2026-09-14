import sqlite3
import jdatetime
from datetime import datetime
import zoneinfo

DB_PATH = 'price_history.db'

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

def get_history(asset_key, limit=200):
    """دریافت تاریخچه قیمت‌ها"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.execute(
        "SELECT price, timestamp FROM price_snapshots WHERE asset_key = ? ORDER BY timestamp DESC LIMIT ?",
        (asset_key, limit)
    )
    rows = cursor.fetchall()
    conn.close()
    # برگرداندن به ترتیب زمانی صعودی
    return list(reversed(rows))

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
