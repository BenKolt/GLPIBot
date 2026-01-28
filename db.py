import sqlite3

conn = sqlite3.connect("users.db")
cursor = conn.cursor()

# создаём таблицу пользователей, если её нет
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    glpi_token TEXT
)
""")
conn.commit()


def set_user_token(user_id: int, token: str):
    cursor.execute("INSERT OR REPLACE INTO users(user_id, glpi_token) VALUES (?, ?)", (user_id, token))
    conn.commit()


def get_user_token(user_id: int):
    cursor.execute("SELECT glpi_token FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    return row[0] if row else None
