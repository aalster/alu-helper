import sqlite3

DB_FILE = "app.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("""
                CREATE TABLE IF NOT EXISTS records (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   name TEXT NOT NULL
                )
                """)
    conn.commit()
    conn.close()

def add_record(name: str):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("INSERT INTO records (name) VALUES (?)", (name,))
    conn.commit()
    conn.close()

def get_records():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("SELECT * FROM records")
    rows = cur.fetchall()
    conn.close()
    return rows
