
from minio import Minio
from dotenv import load_dotenv
import os
import subprocess
import time

load_dotenv()

LOCAL_FILE_PATH = os.environ.get('LOCAL_FILE_PATH')
ACCESS_KEY = os.environ.get('ACCESS_KEY')
SECRET_KEY = os.environ.get('SECRET_KEY')
MINIO_API_HOST = "http://localhost:9000"

def start_minio_server():
    # Verifica se o MinIO já está rodando
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect(("localhost", 9000))
        s.close()
        print("MinIO já está rodando em localhost:9000")
        return None
    except Exception:
        print("Iniciando o servidor MinIO em background...")
        # Inicia o MinIO em background (diretório ./minio_data)
        proc = subprocess.Popen([
            "minio", "server", "./minio_data"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        # Aguarda o MinIO subir
        time.sleep(5)
        return proc

MINIO_CLIENT = Minio("localhost:9000", access_key=ACCESS_KEY, secret_key=SECRET_KEY, secure=False)


def upload_files(directory):
    found = MINIO_CLIENT.bucket_exists(directory)
    if not found:
        MINIO_CLIENT.make_bucket(directory)
    else:
        print("Bucket already exists")
    MINIO_CLIENT.fput_object(directory, "input/go.png", LOCAL_FILE_PATH)
    print("It is successfully uploaded to bucket")


if __name__ == "__main__":
    proc = start_minio_server()
    upload_files()
    print("File uploaded successfully")
    print("Você pode conferir no MinIO web em http://localhost:9000")
    if proc:
        print("Servidor MinIO iniciado pelo script. Ele continuará rodando até que você encerre manualmente (Ctrl+C ou kill no terminal).")
        try:
            proc.wait()
        except KeyboardInterrupt:
            print("\nEncerrando o servidor MinIO...")
            proc.terminate()
