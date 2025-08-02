
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
        path = unquote(self.path)
        if path.startswith("/"):
            path = path[1:]
        if path == "":
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"<h1>Servidor DASH via MinIO</h1>")
            return
        try:
            # Busca o arquivo no bucket output, incluindo subpastas (ex: output/base_name/arquivo.ext)
            response = client.get_object(MINIO_BUCKET, path)
            data = response.read()
            mime = guess_mime_type(path)
            self.send_response(200)
            self.send_header("Content-type", mime)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        except S3Error as e:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(f"Arquivo não encontrado: {path}".encode())

if __name__ == "__main__":
    print(f"Servidor DASH via MinIO rodando em http://localhost:{PORT}")
    print(f"Bucket: {MINIO_BUCKET} | Endpoint: {MINIO_ENDPOINT}")
    server = HTTPServer(("", PORT), MinioDASHHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor encerrado.")
        server.server_close()