import sqlite3

def initialize_database(db_path='recordings.db'):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject_id TEXT,
            session_id TEXT,
            timestamp TEXT,
            frame_count INTEGER,
            file_base TEXT
        )
    ''')
    conn.commit()
    return conn

def insert_session_metadata(conn, subject_id, session_id, timestamp, frame_count, file_base):
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO sessions (subject_id, session_id, timestamp, frame_count, file_base)
        VALUES (?, ?, ?, ?, ?)
    ''', (subject_id, session_id, timestamp, frame_count, file_base))
    conn.commit()
