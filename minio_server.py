

from minio import Minio
from dotenv import load_dotenv
import os
import subprocess
import time
import json

load_dotenv()


LOCAL_FILE_PATH = os.environ.get('LOCAL_FILE_PATH')
ACCESS_KEY = "minioadmin"
SECRET_KEY = "minioadmin"
MINIO_API_HOST = "http://localhost:9000"

# Prints para depuração
print("[DEBUG] ACCESS_KEY:", ACCESS_KEY)
print("[DEBUG] SECRET_KEY:", SECRET_KEY)
print("[DEBUG] MINIO_API_HOST:", MINIO_API_HOST)

def start_minio_server():
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect(("localhost", 9000))
        s.close()
        print("MinIO já está rodando em localhost:9000")
        return None
    except Exception:
        print("Iniciando o servidor MinIO em background...")
        proc = subprocess.Popen([
            "minio", "server", "./minio_data"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        # Aguarda alguns segundos para garantir que o MinIO esteja pronto
        time.sleep(5)
        return proc

MINIO_CLIENT = Minio("localhost:9000", access_key=ACCESS_KEY, secret_key=SECRET_KEY, secure=False)


def upload_files(bucket_name, local_path):
    found = MINIO_CLIENT.bucket_exists(bucket_name)
    if not found:
        MINIO_CLIENT.make_bucket(bucket_name)
        with open('read_write_policy.json', 'r') as policy_file:
            policy_full = json.load(policy_file)
            # Substitui o nome do bucket no campo Resource
            policy_full["Statement"][0]["Resource"] = [f"arn:aws:s3:::{bucket_name}/*"]
            MINIO_CLIENT.set_bucket_policy(bucket_name, json.dumps(policy_full))
        print("Policy de leitura e escrita aplicada ao bucket.")
    else:
        print("Bucket already exists")
    for filename in os.listdir(local_path):
        file_path = os.path.join(local_path, filename)
        if os.path.isfile(file_path):
            MINIO_CLIENT.fput_object(bucket_name, filename, file_path)
            print(f"Uploaded {filename} to bucket {bucket_name}")
    print("It is successfully uploaded to bucket")
    

if __name__ == "__main__":
    proc = start_minio_server()
    print("Você pode conferir no MinIO web em http://localhost:9000")
    if proc:
        print("Servidor MinIO iniciado pelo script. Ele continuará rodando até que você encerre manualmente (Ctrl+C ou kill no terminal).")
        try:
            proc.wait()
        except KeyboardInterrupt:
            print("\nEncerrando o servidor MinIO...")
            proc.terminate()
