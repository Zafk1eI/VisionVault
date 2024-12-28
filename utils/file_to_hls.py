from io import BytesIO
import os
import subprocess
import json
import uuid

# время видео
def format_duration(seconds: float) -> str:
    seconds = int(seconds)

    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    if hours > 0:
        return f"{hours:02}:{minutes:02}:{seconds:02}"
    else:
        return f"{minutes:02}:{seconds:02}"

def get_video_duration(input_file: BytesIO):
    
    command = [
        'ffprobe', 
        '-v', 'error', 
        '-select_streams', 'v:0', 
        '-show_entries', 'format=duration', 
        '-of', 'json', 
        'pipe:0'
    ]
    
    process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate(input=input_file.getvalue())

    if process.returncode != 0:
        print(f"Ошибка при извлечении длительности видео:\n{stderr.decode('utf-8')}")
        raise Exception("Ошибка в ffprobe процессе.")

    video_info = json.loads(stdout.decode('utf-8'))
    duration = float(video_info['format']['duration']) 
    return duration

def convert_video_to_hls(input_file: BytesIO, thumbnail: BytesIO):
    try:
        video_id = str(uuid.uuid4())
        output_dir = os.path.join("videos", video_id)
        os.makedirs(output_dir, exist_ok=True)

        video_duration = get_video_duration(input_file)
        formatted_duration = format_duration(video_duration)
        
        resolutions = [
            {'resolution': '144', 'bitrate': '300k', 'folder': '144p', 'width': '256'},
            {'resolution': '360', 'bitrate': '700k', 'folder': '360p', 'width': '640'},
            {'resolution': '480', 'bitrate': '1500k', 'folder': '480p', 'width': '854'},
        ]

    
        for item in resolutions:
            # Создаем папку для текущего разрешения
            resolution_folder = os.path.join(output_dir, item['folder'])
            os.makedirs(resolution_folder, exist_ok=True)

            # Команда ffmpeg
            command = [
                'ffmpeg', '-i', 'pipe:0',
                '-c:v', 'libx264',  # Кодек видео
                '-preset', 'veryfast',  # Быстрая скорость кодирования
                '-vf', f'scale={item["width"]}:{item["resolution"]}',  # Масштабирование видео
                '-b:v', f'{item["bitrate"]}',  # Битрейт
                '-movflags', '+faststart',  # Оптимизация для веба
                '-hls_time', '10',  # Длина сегмента
                '-hls_list_size', '0',  # Не удалять сегменты из плейлиста
                '-hls_flags', 'independent_segments',  # Каждый сегмент может быть декодирован независимо
                '-f', 'hls',  # Принудительный формат HLS
                '-hls_segment_filename', os.path.join(output_dir, item['folder'], f'segment_{item["resolution"]}_%03d.ts'),  # Путь для сегментов
                os.path.join(output_dir, f'{item["folder"]}/output_{item["resolution"]}.m3u8')  # Путь для плейлиста
            ]

            process = subprocess.Popen(command, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = process.communicate(input=input_file.getvalue())

            if process.returncode != 0:
                print(f"Ошибка при обработке разрешения {item['resolution']}:\n{stderr.decode('utf-8')}")
                raise Exception("Ошибка в ffmpeg процессе.")
            
        # Генерация мастер-плейлиста
        master_playlist = os.path.join(output_dir, 'master.m3u8')
        with open(master_playlist, 'w') as f:
            f.write('#EXTM3U\n')
            f.write('#EXT-X-VERSION:6\n')
            for item in resolutions:
                resolution = item["resolution"]
                bitrate = item["bitrate"]
                playlist_path = f'{item["folder"]}/output_{resolution}.m3u8'
                f.write(f'#EXT-X-STREAM-INF:BANDWIDTH={bitrate},RESOLUTION={item["width"]}x{resolution}\n')
                f.write(f'{playlist_path}\n')

        print(f"Видео преобразовано в HLS формат и сохранено в {output_dir}")

        with open(os.path.join(output_dir, "thumbnail.jpg"), 'wb') as f:
            f.write(thumbnail.getvalue())
        
        return (output_dir, video_id, formatted_duration)
        
    except Exception as e:
        print(f"Произошла ошибка: {e}")
        return None

    