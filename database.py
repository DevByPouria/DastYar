import sqlite3
import jdatetime
import json

def get_db():
    conn = sqlite3.connect('data.db')
    
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            phone_number TEXT,
            language_code TEXT,
            is_bot BOOLEAN,
            first_seen TEXT,
            last_seen TEXT,
            total_interactions INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 1,
            user_data TEXT
        )
    ''')
    
    conn.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            amount INTEGER,
            category TEXT,
            description TEXT,
            trans_type TEXT,
            date_shamsi TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    return conn

def save_user(user):
    conn = get_db()
    today = jdatetime.date.today().strftime("%Y/%m/%d %H:%M")
    
    extra_data = {
        'is_premium': getattr(user, 'is_premium', False),
        'added_to_attachment_menu': getattr(user, 'added_to_attachment_menu', False),
        'can_join_groups': getattr(user, 'can_join_groups', True),
        'can_read_all_group_messages': getattr(user, 'can_read_all_group_messages', False),
        'supports_inline_queries': getattr(user, 'supports_inline_queries', False)
    }
    
    cursor = conn.execute("SELECT user_id FROM users WHERE user_id = ?", (user.id,))
    existing = cursor.fetchone()
    
    if existing:
        conn.execute('''
            UPDATE users SET 
                username = ?, first_name = ?, last_name = ?, language_code = ?,
                is_bot = ?, last_seen = ?, total_interactions = total_interactions + 1,
                is_active = 1, user_data = ?
            WHERE user_id = ?
        ''', (user.username, user.first_name, user.last_name, user.language_code,
              user.is_bot, today, json.dumps(extra_data), user.id))
    else:
        conn.execute('''
            INSERT INTO users (
                user_id, username, first_name, last_name, phone_number,
                language_code, is_bot, first_seen, last_seen,
                total_interactions, is_active, user_data
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user.id, user.username, user.first_name, user.last_name, None,
              user.language_code, user.is_bot, today, today, 1, 1, json.dumps(extra_data)))
    
    conn.commit()
    conn.close()

def update_user_phone(user_id, phone_number):
    conn = get_db()
    conn.execute("UPDATE users SET phone_number = ? WHERE user_id = ?", (phone_number, user_id))
    conn.commit()
    conn.close()

def get_all_users():
    conn = get_db()
    cursor = conn.execute('''
        SELECT user_id, username, first_name, last_name, phone_number,
               language_code, is_bot, first_seen, last_seen,
               total_interactions, is_active, user_data
        FROM users WHERE is_active = 1 ORDER BY first_seen DESC
    ''')
    users = cursor.fetchall()
    conn.close()
    return users

def get_user_count():
    conn = get_db()
    cursor = conn.execute("SELECT COUNT(*) FROM users WHERE is_active = 1")
    count = cursor.fetchone()[0]
    conn.close()
    return count

def get_today_users():
    today = jdatetime.date.today().strftime("%Y/%m/%d")
    conn = get_db()
    cursor = conn.execute("SELECT COUNT(*) FROM users WHERE first_seen LIKE ? || '%'", (today,))
    count = cursor.fetchone()[0]
    conn.close()
    return count

def add_transaction(user_id, amount, category, description, trans_type):
    conn = get_db()
    today = jdatetime.date.today().strftime("%Y/%m/%d")
    conn.execute(
        "INSERT INTO transactions (user_id, amount, category, description, trans_type, date_shamsi) VALUES (?, ?, ?, ?, ?, ?)",
        (user_id, amount, category, description, trans_type, today)
    )
    conn.commit()
    conn.close()

def get_monthly_summary(user_id):
    conn = get_db()
    cursor = conn.execute(
        "SELECT trans_type, SUM(amount) FROM transactions WHERE user_id = ? AND strftime('%m', timestamp) = strftime('%m', 'now') GROUP BY trans_type",
        (user_id,)
    )
    data = cursor.fetchall()
    conn.close()
    
    total_income = 0
    total_expense = 0
    for trans_type, amount in data:
        if trans_type == 'income':
            total_income = amount or 0
        elif trans_type == 'expense':
            total_expense = amount or 0
    return total_income, total_expense

def get_all_transactions(user_id):
    conn = get_db()
    cursor = conn.execute(
        "SELECT amount, category, description, trans_type, date_shamsi FROM transactions WHERE user_id = ? ORDER BY timestamp DESC LIMIT 20",
        (user_id,)
    )
    data = cursor.fetchall()
    conn.close()
    return data
