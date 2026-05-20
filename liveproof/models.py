import sqlite3

DB_FILE = "liveproof.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS verified_users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        aadhaar TEXT NOT NULL,
        email TEXT NOT NULL,
        verified_at TEXT NOT NULL
    )
    """)
    conn.commit()
    conn.close()

def save_verified_user(name, aadhaar, email):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO verified_users (name,aadhaar,email,verified_at) VALUES (?,?,?,datetime('now'))",
              (name, aadhaar, email))
    conn.commit()
    conn.close()
