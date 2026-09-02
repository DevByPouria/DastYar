import sqlite3
import jdatetime

def get_db():
    conn = sqlite3.connect('data.db')
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
