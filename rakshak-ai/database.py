import os
import sqlite3
from datetime import datetime
import numpy as np

# Use BASE_DIR for safe file paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

class Database:
    def __init__(self, db_name=None):
        # Default DB path inside project base dir
        if db_name:
            self.db_name = db_name
        else:
            self.db_name = os.path.join(BASE_DIR, 'accidents.db')
        self.create_table()

    def create_table(self):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS accidents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                latitude REAL,
                longitude REAL,
                severity INTEGER,
                description TEXT
            )
        ''')
        conn.commit()
        conn.close()

    def log_accident(self, latitude=None, longitude=None, severity=1, description='Accident detected'):
        if latitude is None:
            latitude = 28.6139 + (np.random.random() - 0.5) * 0.1  # Dummy random lat around Delhi
        if longitude is None:
            longitude = 77.2090 + (np.random.random() - 0.5) * 0.1  # Dummy random lng around Delhi
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('INSERT INTO accidents (timestamp, latitude, longitude, severity, description) VALUES (?, ?, ?, ?, ?)',
                       (timestamp, latitude, longitude, severity, description))
        conn.commit()
        conn.close()

    def get_logs(self):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM accidents ORDER BY timestamp DESC')
        logs = cursor.fetchall()
        conn.close()
        return logs

    def get_accident_count(self):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM accidents')
        count = cursor.fetchone()[0]
        conn.close()
        return count
