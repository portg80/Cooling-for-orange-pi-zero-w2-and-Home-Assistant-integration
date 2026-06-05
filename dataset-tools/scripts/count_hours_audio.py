import os
import subprocess
import shutil
from pathlib import Path


FFPROBE_CMD = "ffprobe"  # можно заменить на полный путь к ffprobe.exe при желании


def check_ffprobe_available() -> bool:
    """Проверяет, что ffprobe есть в PATH."""
    return shutil.which(FFPROBE_CMD) is not None


def get_duration_seconds_ffprobe(path: Path) -> float:
    """
    Возвращает длительность аудиофайла в секундах с помощью ffprobe.
    Требует установленного ffmpeg/ffprobe и его наличия в PATH.
    """
    try:
        result = subprocess.run(
            [
                FFPROBE_CMD,
                "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                str(path)
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        if result.returncode != 0:
            print(f"Не удалось прочитать через ffprobe: {path}")
            # Если хочешь увидеть, что именно не понравилось ffprobe, раскомментируй:
            # print("stderr ffprobe:", result.stderr)
            return 0.0

        output = result.stdout.strip()
        if not output:
            print(f"ffprobe не вернул длительность: {path}")
            return 0.0

        return float(output)
    except Exception as e:
        print(f"Ошибка при обработке файла {path}: {e}")
        return 0.0


def format_hms(seconds: float) -> str:
    total_seconds = int(round(seconds))
    h = total_seconds // 3600
    m = (total_seconds % 3600) // 60
    s = total_seconds % 60
    return f"{h:02d}:{m:02d}:{s:02d}"


def main():
    script_dir = Path(__file__).resolve().parent

    print(f"Скрипт запущен из папки: {script_dir}")
    print("Проверяю наличие ffprobe...")

    if not check_ffprobe_available():
        print("\nОШИБКА: ffprobe не найден в PATH.")
        print("Проверь, что ffmpeg/ffprobe установлен и его папка добавлена в переменную PATH.")
        print("Либо пропиши полный путь к ffprobe.exe в переменной FFPROBE_CMD в начале скрипта.")
        return

    print("ffprobe найден. Начинаю обход папок...\n")

    total_seconds = 0.0
    file_count = 0
    processed_files = 0

    for root, _, files in os.walk(script_dir):
        for name in files:
            if name.lower().endswith(".wav"):
                wav_path = Path(root) / name
                file_count += 1

    print(f"Найдено WAV-файлов (по расширению): {file_count}")
    print("Считаю длительность...\n")

    for root, _, files in os.walk(script_dir):
        for name in files:
            if name.lower().endswith(".wav"):
                wav_path = Path(root) / name
                processed_files += 1

                # Немного прогресса в консоли
                print(f"[{processed_files}/{file_count}] Обработка: {wav_path}")

                duration = get_duration_seconds_ffprobe(wav_path)
                if duration > 0:
                    total_seconds += duration

    print("\n==== РЕЗУЛЬТАТ ====")
    print(f"Всего WAV-файлов (по расширению): {file_count}")
    print(f"Суммарная учтённая длительность (секунды): {int(round(total_seconds))}")
    print(f"Суммарная учтённая длительность (часы:минуты:секунды): {format_hms(total_seconds)}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        # Ловим любые неожиданные ошибки, чтобы окно не закрывалось молча
        print("\nПроизошла непредвиденная ошибка:")
        print(e)
    input("\nГотово. Нажмите Enter, чтобы закрыть окно...")
