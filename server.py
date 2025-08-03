
# --- Servidor HTTP que serve arquivos do MinIO ---
from minio import Minio
from minio.error import S3Error
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import unquote
import os

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
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
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