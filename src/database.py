import sqlite3
import os
from datetime import datetime

DB_PATH = "d:/contentaai/data/history.db"

class CreativeDatabase:
    def __init__(self):
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        self.conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        self.create_tables()

    def create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_manual_prompt TEXT,
                gemini_generated_prompt TEXT,
                local_image_path TEXT,
                phone_image_path TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self.conn.commit()

    def add_entry(self, manual_prompt, generated_prompt, local_path, phone_path):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO history (user_manual_prompt, gemini_generated_prompt, local_image_path, phone_image_path)
            VALUES (?, ?, ?, ?)
        ''', (manual_prompt, generated_prompt, local_path, phone_path))
        self.conn.commit()
        return cursor.lastrowid

    def get_latest_entries(self, limit=10):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM history ORDER BY timestamp DESC LIMIT ?', (limit,))
        return cursor.fetchall()

    def close(self):
        self.conn.close()

# Singleton instance
db = CreativeDatabase()
