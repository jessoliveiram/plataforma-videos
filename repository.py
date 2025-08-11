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
            student_id TEXT,
            class_id TEXT,
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
            client_ip TEXT,
            extra_json TEXT
        )
        '''
    )


def _ensure_columns(cursor):
    """Garante colunas extras em bancos já criados (migração leve)."""
    cursor.execute("PRAGMA table_info(player_events)")
    cols = {row[1] for row in cursor.fetchall()}
    required = [
        ("student_id", "TEXT"),
        ("class_id", "TEXT"),
        ("extra_json", "TEXT"),
    ]
    for name, ctype in required:
        if name not in cols:
            cursor.execute(f"ALTER TABLE player_events ADD COLUMN {name} {ctype}")

def _ensure_indexes_and_views(cursor):
    """Cria índices e views úteis para análises sem alterar o esquema de dados."""
    # Índices para filtros e agrupamentos comuns
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_title_event_time ON player_events(video_title, event, current_time)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_event ON player_events(event)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_username ON player_events(username)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_student ON player_events(student_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_class ON player_events(class_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_session ON player_events(session_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_timestamp ON player_events(timestamp)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_seek_times ON player_events(event, to_time, from_time, video_title)")

    # Views de heatmap (bucket de 10s)
    cursor.execute(
        """
        CREATE VIEW IF NOT EXISTS heatmap_pause_10s AS
        SELECT
            video_title,
            CAST(ROUND(current_time/10)*10 AS INTEGER) AS bucket_s,
            COUNT(*) AS hits
        FROM player_events
        WHERE event = 'pause' AND current_time IS NOT NULL
        GROUP BY video_title, bucket_s
        ORDER BY video_title, bucket_s
        """
    )
    cursor.execute(
        """
        CREATE VIEW IF NOT EXISTS heatmap_seek_backward_10s AS
        SELECT
            video_title,
            CAST(ROUND(to_time/10)*10 AS INTEGER) AS bucket_s,
            COUNT(*) AS hits
        FROM player_events
        WHERE event = 'seek' AND from_time IS NOT NULL AND to_time IS NOT NULL AND from_time > to_time
        GROUP BY video_title, bucket_s
        ORDER BY video_title, bucket_s
        """
    )
    cursor.execute(
        """
        CREATE VIEW IF NOT EXISTS heatmap_seek_forward_10s AS
        SELECT
            video_title,
            CAST(ROUND(to_time/10)*10 AS INTEGER) AS bucket_s,
            COUNT(*) AS hits
        FROM player_events
        WHERE event = 'seek' AND from_time IS NOT NULL AND to_time IS NOT NULL AND from_time < to_time
        GROUP BY video_title, bucket_s
        ORDER BY video_title, bucket_s
        """
    )

    # Heatmap de watch (tempo assistido) baseado em amostras de timeupdate
    cursor.execute(
        """
        CREATE VIEW IF NOT EXISTS heatmap_watch_10s AS
        SELECT
            video_title,
            CAST(ROUND(current_time/10)*10 AS INTEGER) AS bucket_s,
            COUNT(*) AS hits
        FROM player_events
        WHERE event = 'timeupdate' AND current_time IS NOT NULL
        GROUP BY video_title, bucket_s
        ORDER BY video_title, bucket_s
        """
    )




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
    _ensure_columns(c)
    _ensure_indexes_and_views(c)

    for ev in events:
        # Mapear campos esperados com valores padrão
        session_id = ev.get('session_id')
        username = ev.get('username')
        student_id = ev.get('student_id')
        class_id = ev.get('class_id')
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

        # Captura quaisquer campos extras para persistir no JSON flexível
        known_keys = {
            'session_id','username','student_id','class_id','video_src','video_title','event',
            'current_time','from_time','to_time','buffering','bufferDuration','width','height',
            'bandwidth','bitrate','playback_rate','error_code','error_message','user_agent',
            'device_type'
        }
        extra = {k: v for k, v in ev.items() if k not in known_keys}
        extra_json = json.dumps(extra, ensure_ascii=False) if extra else None

        c.execute(
            '''
            INSERT INTO player_events (
                session_id, username, student_id, class_id, video_src, video_title, event, current_time,
                from_time, to_time, buffering, bufferDuration, width, height, bandwidth,
                playback_rate, error_code, error_message, user_agent, device_type, client_ip, extra_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''',
            (
                session_id, username, student_id, class_id, video_src, video_title, event, current_time,
                from_time, to_time, buffering, bufferDuration, width, height, bandwidth,
                playback_rate, error_code, error_message, user_agent, device_type, client_ip, extra_json
            )
        )

    conn.commit()
    conn.close()
    return True, None


