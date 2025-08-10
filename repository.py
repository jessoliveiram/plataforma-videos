import sqlite3
import json


def _ensure_event_table(cursor):
    cursor.execute(
        '''
        CREATE TABLE IF NOT EXISTS player_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            session_id TEXT,
            username TEXT,
            video_src TEXT,
            video_title TEXT,
            event TEXT,
            current_time REAL,
            from_time REAL,
            to_time REAL,
            buffering INTEGER,
            bufferDuration REAL,
            width INTEGER,
            height INTEGER,
            bandwidth REAL,
            playback_rate REAL,
            error_code TEXT,
            error_message TEXT,
            user_agent TEXT,
            device_type TEXT,
            client_ip TEXT
        )
        '''
    )


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
            username TEXT,
            bitrate REAL,
            width INTEGER,
            height INTEGER,
            playTime REAL,
            bufferingTime REAL,
            percentWatched REAL
        )
    ''')
    c.execute('''
        INSERT INTO player_metrics (username, bitrate, width, height, playTime, bufferingTime, percentWatched)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        data.get('username'),
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


def save_events_to_db(events_json, client_ip=None):
    """Salva um ou mais eventos de player no banco.
    Aceita um objeto único, uma lista de objetos, ou um wrapper {"events": [...]}.
    """
    try:
        data = json.loads(events_json)
    except Exception:
        return False, "Erro ao decodificar JSON"

    # Normalizar para lista de eventos
    if isinstance(data, dict) and 'events' in data and isinstance(data['events'], list):
        events = data['events']
    elif isinstance(data, list):
        events = data
    elif isinstance(data, dict):
        events = [data]
    else:
        return False, "Formato de eventos inválido"

    conn = sqlite3.connect('metrics.db')
    c = conn.cursor()
    _ensure_event_table(c)

    for ev in events:
        # Mapear campos esperados com valores padrão
        session_id = ev.get('session_id')
        username = ev.get('username')
        video_src = ev.get('video_src')
        video_title = ev.get('video_title')
        event = ev.get('event')
        current_time = ev.get('current_time')
        from_time = ev.get('from_time')
        to_time = ev.get('to_time')
        buffering = ev.get('buffering')
        bufferDuration = ev.get('bufferDuration')
        width = ev.get('width')
        height = ev.get('height')
        bandwidth = ev.get('bandwidth') or ev.get('bitrate')
        playback_rate = ev.get('playback_rate')
        error_code = ev.get('error_code')
        error_message = ev.get('error_message')
        user_agent = ev.get('user_agent')
        device_type = ev.get('device_type')

        c.execute(
            '''
            INSERT INTO player_events (
                session_id, username, video_src, video_title, event, current_time,
                from_time, to_time, buffering, bufferDuration, width, height, bandwidth,
                playback_rate, error_code, error_message, user_agent, device_type, client_ip
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''',
            (
                session_id, username, video_src, video_title, event, current_time,
                from_time, to_time, buffering, bufferDuration, width, height, bandwidth,
                playback_rate, error_code, error_message, user_agent, device_type, client_ip
            )
        )

    conn.commit()
    conn.close()
    return True, None


