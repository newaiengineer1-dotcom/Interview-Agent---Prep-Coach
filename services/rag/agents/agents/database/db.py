import sqlite3, json

def init_db():
    conn = sqlite3.connect('interview_coach.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS sessions
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT, role TEXT, score REAL, data TEXT)''')
    conn.commit()
    conn.close()

def save_session(timestamp, role, score, data):
    conn = sqlite3.connect('interview_coach.db')
    c = conn.cursor()
    c.execute("INSERT INTO sessions (timestamp, role, score, data) VALUES (?, ?, ?, ?)",
              (timestamp, role, score, json.dumps(data)))
    conn.commit()
    conn.close()
