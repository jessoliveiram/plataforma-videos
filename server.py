from minio import Minio
from minio.error import S3Error
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import unquote
import os
import json

PORT = 8000
MINIO_ENDPOINT = os.environ.get("MINIO_ENDPOINT", "localhost:9000")
MINIO_ACCESS_KEY = os.environ.get("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.environ.get("MINIO_SECRET_KEY", "minioadmin")
MINIO_BUCKET = os.environ.get("MINIO_BUCKET", "output")

client = Minio(
    MINIO_ENDPOINT,
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=False
)

MIME_MAP = {
    ".mpd": "application/dash+xml",
    ".m4s": "video/mp4",
    ".mp4": "video/mp4",
    ".webm": "video/webm",
    ".mp3": "audio/mpeg",
    ".aac": "audio/aac",
    ".ts": "video/MP2T",
    ".json": "application/json",
    ".xml": "application/xml",
}

def guess_mime_type(filename):
    ext = os.path.splitext(filename)[1]
    return MIME_MAP.get(ext, "application/octet-stream")

class MinioDASHHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        from repository import save_metrics_to_db, save_events_to_db
        path = unquote(self.path)
        if path.startswith("/"):
            path = path[1:]
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)

        if path == "shaka_metrics.json":
            success, error = save_metrics_to_db(post_data.decode('utf-8'))
            if not success:
                self.send_response(400)
                self.send_cors_headers()
                self.end_headers()
                self.wfile.write(error.encode())
                return
            self.send_response(200)
            self.send_cors_headers()
            self.end_headers()
            self.wfile.write(b"Metricas recebidas e salvas no banco de dados.")
            print(f"[DEBUG] Métricas recebidas e salvas no banco de dados.")
            return

        if path == "player_events.json":
            # Enriquecer com user-agent e IP do cliente
            client_ip = self.client_address[0]
            user_agent = self.headers.get('User-Agent')
            try:
                data = json.loads(post_data.decode('utf-8'))
                # Normalizar para lista dentro de um wrapper para adicionar user_agent
                if isinstance(data, dict) and 'events' in data:
                    for ev in data['events']:
                        ev.setdefault('user_agent', user_agent)
                elif isinstance(data, list):
                    data = {'events': [{**ev, 'user_agent': ev.get('user_agent', user_agent)} for ev in data]}
                elif isinstance(data, dict):
                    data = {'events': [{**data, 'user_agent': data.get('user_agent', user_agent)}]}
                else:
                    raise ValueError('Formato inválido')
                payload = json.dumps(data)
            except Exception as e:
                self.send_response(400)
                self.send_cors_headers()
                self.end_headers()
                self.wfile.write(f"Erro no corpo da requisição: {e}".encode())
                return

            success, error = save_events_to_db(payload, client_ip=client_ip)
            if not success:
                self.send_response(400)
                self.send_cors_headers()
                self.end_headers()
                self.wfile.write(error.encode())
                return
            self.send_response(200)
            self.send_cors_headers()
            self.end_headers()
            self.wfile.write(b"Eventos recebidos e salvos no banco de dados.")
            print(f"[DEBUG] Eventos recebidos de {client_ip}.")
            return

        self.send_response(404)
        self.send_cors_headers()
        self.end_headers()
        self.wfile.write(b"Not found")

    def do_GET(self):
        import mimetypes
        path = unquote(self.path)
        if path.startswith("/"):
            path = path[1:]
        # Servir arquivos estáticos locais se existirem
        if os.path.isfile(path):
            self.send_response(200)
            mime, _ = mimetypes.guess_type(path)
            self.send_header("Content-type", mime or "application/octet-stream")
            self.send_cors_headers()
            self.end_headers()
            with open(path, "rb") as f:
                self.wfile.write(f.read())
            return
        if path == "":
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.send_cors_headers()
            self.end_headers()
            self.wfile.write(b"<h1>Servidor DASH via MinIO</h1>")
            return
        # Path no formato bucket/arquivo.ext
        parts = path.split("/", 1)
        if len(parts) != 2 or not parts[0] or not parts[1]:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Not found")
            return
        bucket, obj_path = parts
        try:
            response = client.get_object(bucket, obj_path)
            data = response.read()
            mime = guess_mime_type(obj_path)
            self.send_response(200)
            self.send_header("Content-type", mime)
            self.send_header("Content-Length", str(len(data)))
            self.send_cors_headers()
            self.end_headers()
            print(f"[DEBUG] Servindo {bucket}/{obj_path} com Content-Type: {mime}")
            self.wfile.write(data)
        except S3Error as e:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(f"Arquivo não encontrado: {bucket}/{obj_path}".encode())

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_cors_headers()
        self.end_headers()

    def send_cors_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')


if __name__ == "__main__":
    print(f"Servidor DASH via MinIO rodando em http://localhost:{PORT}")
    print(f"Bucket: {MINIO_BUCKET} | Endpoint: {MINIO_ENDPOINT}")
    server = HTTPServer(("", PORT), MinioDASHHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor encerrado.")
        server.server_close()