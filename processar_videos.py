
import os
import sys
import glob
import subprocess
from minio import Minio
from minio.error import S3Error

MINIO_ENDPOINT = "localhost:9000"
MINIO_ACCESS_KEY = "minioadmin"
MINIO_SECRET_KEY = "minioadmin"
MINIO_BUCKET = "videos-output"

# Inicializa o cliente MinIO
client = Minio(
    MINIO_ENDPOINT,
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=False
)

def criar_bucket_se_nao_existir(bucket_name):
    if not client.bucket_exists(bucket_name):
        client.make_bucket(bucket_name)
        print(f"Bucket '{bucket_name}' criado.")
    else:
        print(f"Bucket '{bucket_name}' já existe.")



def upload_todos_arquivos_output_para_minio(bucket_name, pasta_output="output"):
    arquivos = [f for f in os.listdir(pasta_output) if os.path.isfile(os.path.join(pasta_output, f))]
    if not arquivos:
        print(f"Nenhum arquivo encontrado em {pasta_output}")
        return
    for file in arquivos:
        caminho_arquivo = os.path.join(pasta_output, file)
        caminho_no_bucket = file  # Envia para a raiz do bucket
        print(f"Enviando {caminho_arquivo} para {bucket_name}/{caminho_no_bucket}")
        client.fput_object(
            bucket_name,
            caminho_no_bucket,
            caminho_arquivo
        )
    print(f"Upload de todos os arquivos da pasta {pasta_output} para MinIO concluído!")

def process_videos_final():
    """
    Gera um stream DASH com estrutura de manifesto e ABR corretos.
    """
    os.makedirs("output", exist_ok=True)
    video_files = glob.glob("input/*.mp4")

    if not video_files:
        print("Nenhum vídeo .mp4 encontrado na pasta 'input'.")
        return

    criar_bucket_se_nao_existir(MINIO_BUCKET)

    for video_path in video_files:
        base_name = os.path.splitext(os.path.basename(video_path))[0]
        output_path = f"output/{base_name}.mpd"

        print(f"▶️  Processando: {video_path} com o método final...")

        command = [
            'ffmpeg',
            '-i', video_path,
            '-map', '0:v:0', '-map', '0:v:0', '-map', '0:v:0', '-map', '0:a:0',
            '-c:v', 'libx264', '-preset', 'medium', '-g', '48', '-sc_threshold', '0', '-keyint_min', '48',
            '-b:v:0', '5000k', '-s:v:0', '1920x1080', '-profile:v:0', 'high',
            '-b:v:1', '2500k', '-s:v:1', '1280x720', '-profile:v:1', 'main',
            '-b:v:2', '800k',  '-s:v:2', '854x480',  '-profile:v:2', 'baseline',
            '-c:a', 'aac', '-b:a', '128k', '-strict', '-2',
            '-f', 'dash',
            '-seg_duration', '4',
            '-adaptation_sets', 'id=0,streams=v id=1,streams=a',
            output_path
        ]

        try:
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8', bufsize=1)
            for line in process.stdout:
                print(line, end='')
            process.wait()
            if process.returncode == 0:
                print(f"\n✅ Arquivo {video_path} processado com sucesso!")
                # Após processar, faz upload dos arquivos gerados desse vídeo
                upload_todos_arquivos_output_para_minio(MINIO_BUCKET, pasta_output="output")
            else:
                print(f"\n❌ Erro ao processar o arquivo {video_path}.")

        except Exception as e:
            print(f"\n❌ Ocorreu um erro: {e}")

if __name__ == "__main__":
    process_videos_final()