"""Поместите в папку с аудио. Конвертирует все аудио в той же папке в которой лежит в WAV"""

import os
import subprocess

# Все возможные расширения, которые ffmpeg обычно поддерживает
AUDIO_EXTENSIONS = [
    ".mp3", ".ogg", ".flac", ".aac", ".m4a", ".wma", ".aiff", ".aif",
    ".au", ".wav", ".opus", ".mp2", ".amr", ".caf", ".snd"
]

def convert_to_wav(input_path, output_path):
    """Конвертация одного файла в wav с помощью ffmpeg."""
    try:
        subprocess.run(
            ["ffmpeg", "-y", "-i", input_path, output_path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        print(f"[OK] {input_path} → {output_path}")
    except Exception as e:
        print(f"[ERROR] Не удалось конвертировать {input_path}: {e}")

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    result_dir = os.path.join(base_dir, "result")

    os.makedirs(result_dir, exist_ok=True)

    for filename in os.listdir(base_dir):
        file_path = os.path.join(base_dir, filename)

        # Файлы только в текущей папке и только с нужными расширениями
        if not os.path.isfile(file_path):
            continue

        ext = os.path.splitext(filename)[1].lower()
        if ext in AUDIO_EXTENSIONS:
            output_name = os.path.splitext(filename)[0] + ".wav"
            output_path = os.path.join(result_dir, output_name)

            convert_to_wav(file_path, output_path)

    print("\nГотово! Все конвертации выполнены.")

if __name__ == "__main__":
    main()
