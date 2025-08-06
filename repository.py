import sqlite3
import json

def save_metrics_to_db(metrics_json):
    try:
        data = json.loads(metrics_json)
    except Exception:
        return False, "Erro ao decodificar JSON"
    conn = sqlite3.connect('metrics.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS player_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            bitrate REAL,
            width INTEGER,
            height INTEGER,
            playTime REAL,
            bufferingTime REAL,
            percentWatched REAL
        )
    ''')
    c.execute('''
        INSERT INTO player_metrics (bitrate, width, height, playTime, bufferingTime, percentWatched)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        data.get('streamBandwidth'),
        data.get('width'),
        data.get('height'),
        data.get('playTime'),
        data.get('bufferingTime'),
        data.get('percentWatched')
    ))
    conn.commit()
    conn.close()
    return True, None
