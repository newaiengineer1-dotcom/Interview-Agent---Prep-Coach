import os
import sqlite3
import json

# Streamlit Cloud allows writing to /tmp
DB_PATH = "/tmp/interview_coach.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS sessions
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT, role TEXT, score REAL, data TEXT)''')
    conn.commit()
    conn.close()

def save_session(timestamp, role, score, data):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("INSERT INTO sessions (timestamp, role, score, data) VALUES (?, ?, ?, ?)",
                  (timestamp, role, score, json.dumps(data)))
        conn.commit()
        conn.close()
    except Exception as e:
        # If the database fails, just print the error and don't crash the app
        print(f"Database error: {e}")
