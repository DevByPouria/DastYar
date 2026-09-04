import sqlite3

DB_NAME = 'bot_data.db'

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # جدول لیست خرید (Wishlist)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS wishlist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            product_title TEXT,
            product_price INTEGER,
            product_link TEXT
        )
    ''')
    
    # جدول هشدارهای قیمت
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS price_alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            product_title TEXT,
            target_price INTEGER,
            product_link TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

# --- توابع مربوط به Wishlist ---
def add_to_wishlist_db(user_id, title, price, link):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO wishlist (user_id, product_title, product_price, product_link) VALUES (?, ?, ?, ?)',
                   (user_id, title, price, link))
    conn.commit()
    conn.close()

def get_user_wishlist(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT product_title, product_price, product_link FROM wishlist WHERE user_id = ?', (user_id,))
    items = cursor.fetchall()
    conn.close()
    return items

def clear_user_wishlist(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM wishlist WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()
