
import os
import sys
import glob
import subprocess
from minio_server import upload_files


def process_videos_final():
    """
    Gera um stream DASH com estrutura de manifesto e ABR corretos.
    """
    os.makedirs("output", exist_ok=True)
    video_files = glob.glob("input/*.mp4")

    if not video_files:
        print("Nenhum vídeo .mp4 encontrado na pasta 'input'.")
        return

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
                upload_files(base_name)
            else:
                print(f"\n❌ Erro ao processar o arquivo {video_path}.")

        except Exception as e:
            print(f"\n❌ Ocorreu um erro: {e}")

if __name__ == "__main__":
    process_videos_final()