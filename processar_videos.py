import os
import glob
import subprocess
import shutil
from minio_server import upload_files


def process_videos_final():
    """
    Gera um stream DASH com estrutura de manifesto e ABR corretos.
    """
    video_files = glob.glob("input/*.mp4")

    if not video_files:
        print("Nenhum vídeo .mp4 encontrado na pasta 'input'.")
        return

    for video_path in video_files:
        print(f"▶️  Processando: {video_path} com o método final...")

        base_name = os.path.splitext(os.path.basename(video_path))[0]
        output_path = f"output/{base_name}/{base_name}.mpd"
        os.makedirs(f"output/{base_name}", exist_ok=True)

        command = [
            'ffmpeg',
            '-i', video_path,
            '-map', '0:v:0',
            '-map', '0:a:0',
            '-c:v', 'libx264', '-preset', 'medium', '-g', '48', '-sc_threshold', '0', '-keyint_min', '48',
            '-b:v:0', '800k',  '-s:v:0', '854x480',  '-profile:v:0', 'baseline',
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
            print(f"\n✅ Arquivo {video_path} processado com sucesso!")
            bucket_name = base_name.lower()
            local_path = f"output/{bucket_name}"
            try:
                upload_files(bucket_name, local_path)
                if os.path.exists(local_path):
                    shutil.rmtree(local_path)
                    print(f"🧹 Pasta {local_path} limpa após upload!")
            except Exception as e:
                print(f"❌ Erro ao fazer upload para o MinIO: {e}")
            finally:
                if os.path.exists(local_path):
                    shutil.rmtree(local_path)
                    print(f"🧹 Pasta {local_path} limpa após erro no upload.")

        except Exception as e:
            print(f"\n❌ Ocorreu um erro: {e}")


if __name__ == "__main__":
    process_videos_final()