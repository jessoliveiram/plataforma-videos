import os
import glob
import subprocess
import shutil
from minio_server import upload_files
import cv2


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
        output_path = f"/app/output/{base_name}/{base_name}.mpd"
        os.makedirs(f"/app/output/{base_name}", exist_ok=True)

        cap = cv2.VideoCapture(video_path)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        cap.release()
        print(f"📏 Resolução do vídeo: {width}x{height}")

        command = [
            'ffmpeg',
            '-i', video_path,
        ]

        # Adiciona 360p se o vídeo de entrada for pelo menos 640x360
        if width >= 640 and height >= 360:
            command += [
            # Vídeo 1 - 360p
            '-map', '0:v:0', '-map', '0:a:0',
            '-c:v:0', 'libx264', '-b:v:0', '400k', '-s:v:0', '640x360', '-profile:v:0', 'baseline',
            '-aspect:v:0', '16:9', '-vf:v:0', 'scale=640:360,setsar=1:1',
            ]

        # Adiciona 480p se o vídeo de entrada for pelo menos 854x480
        if width >= 854 and height >= 480:
            command += [
            # Vídeo 2 - 480p
            '-map', '0:v:0', '-map', '0:a:0',
            '-c:v:1', 'libx264', '-b:v:1', '800k', '-s:v:1', '854x480', '-profile:v:1', 'main',
            '-aspect:v:1', '16:9', '-vf:v:1', 'scale=854:480,setsar=1:1',
            ]

        # Adiciona 720p se o vídeo de entrada for pelo menos 1280x720
        if width >= 1280 and height >= 720:
            command += [
            # Vídeo 3 - 720p
            '-map', '0:v:0', '-map', '0:a:0',
            '-c:v:2', 'libx264', '-b:v:2', '1800k', '-s:v:2', '1280x720', '-profile:v:2', 'high',
            '-aspect:v:2', '16:9', '-vf:v:2', 'scale=1280:720,setsar=1:1',
            ]

        # Adiciona 1080p se o vídeo de entrada for pelo menos 1920x1080
        if width >= 1920 and height >= 1080:
            command += [
            # Vídeo 4 - 1080p
            '-map', '0:v:0', '-map', '0:a:0',
            '-c:v:3', 'libx264', '-b:v:3', '3500k', '-s:v:3', '1920x1080', '-profile:v:3', 'high',
            '-aspect:v:3', '16:9', '-vf:v:3', 'scale=1920:1080,setsar=1:1',
            ]

        # Áudio e DASH
        command += [
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
            local_path = f"/app/output/{bucket_name}"
            try:
                upload_files(bucket_name, local_path)
                if os.path.exists(local_path):
                    shutil.rmtree(local_path)
                    print(f"🧹 Pasta {local_path} limpa após upload!")
            finally:
                if os.path.exists(local_path):
                    shutil.rmtree(local_path)
                    print(f"🧹 Pasta {local_path} limpa após erro no upload.")

        except Exception as e:
            print(f"\n❌ Ocorreu um erro: {e}")


if __name__ == "__main__":
    process_videos_final()