import os
import librosa
import soundfile as sf
from glob import glob
import numpy as np
from datetime import datetime


def split_audio_file(input_file, output_dir, segment_duration=2, sr=16000):
    """
    Разбивает аудиофайл на сегменты заданной длительности и сохраняет в формате WAV

    Args:
        input_file (str): Путь к входному аудиофайлу
        output_dir (str): Директория для сохранения сегментов
        segment_duration (float): Длительность каждого сегмента в секундах
        sr (int): Частота дискретизации
    """
    try:
        # Загружаем аудиофайл (librosa автоматически конвертирует в нужный формат)
        y, sr = librosa.load(input_file, sr=sr)

        # Вычисляем длину сегмента в сэмплах
        segment_samples = int(segment_duration * sr)

        # Получаем имя файла без расширения
        base_name = os.path.splitext(os.path.basename(input_file))[0]

        # Разбиваем на сегменты
        num_segments = len(y) // segment_samples

        if num_segments == 0:
            print(f"Файл {input_file} слишком короткий для разбиения (длительность: {len(y) / sr:.2f} секунд)")
            return 0

        for i in range(num_segments):
            start_sample = i * segment_samples
            end_sample = start_sample + segment_samples

            # Извлекаем сегмент
            segment = y[start_sample:end_sample]

            # Создаем имя для нового файла (всегда WAV)
            timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S%f')
            output_file = os.path.join(output_dir, f"{base_name}_part{i + 1}_{timestamp}.wav")

            # Сохраняем сегмент в формате WAV
            sf.write(output_file, segment, sr, format='WAV')
            print(f"Создан файл WAV: {output_file}")

        # Обрабатываем оставшуюся часть, если она больше 50% от сегмента
        remaining_samples = len(y) % segment_samples
        if remaining_samples > segment_samples * 0.5:
            start_sample = num_segments * segment_samples
            segment = y[start_sample:]

            # Дополняем нулями до нужной длины
            if len(segment) < segment_samples:
                segment = np.pad(segment, (0, segment_samples - len(segment)))

            timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S%f')
            output_file = os.path.join(output_dir, f"{base_name}_part{num_segments + 1}_{timestamp}.wav")
            sf.write(output_file, segment, sr, format='WAV')
            print(f"Создан файл WAV (с дополнением нулями): {output_file}")
            num_segments += 1

        return num_segments
    except Exception as e:
        print(f"Ошибка при обработке файла {input_file}: {e}")
        return 0


def process_negative_folder(input_dir="data/negative_raw", output_dir="data/negative_split", segment_duration=2,
                            sr=16000):
    """
    Обрабатывает все аудиофайлы в папке negative и создает их сегментированные версии в формате WAV

    Args:
        input_dir (str): Директория с исходными файлами
        output_dir (str): Директория для сохранения сегментов
        segment_duration (float): Длительность каждого сегмента в секундах
        sr (int): Частота дискретизации
    """
    # Создаем директорию для выходных файлов, если её нет
    os.makedirs(output_dir, exist_ok=True)

    # Поддерживаемые форматы аудиофайлов
    audio_extensions = ['*.wav', '*.mp3', '*.flac', '*.aac', '*.m4a', '*.ogg']

    total_segments = 0
    processed_files = 0

    print(f"Поиск аудиофайлов в директории: {input_dir}")

    # Обрабатываем все аудиофайлы в директории
    all_files = []
    for extension in audio_extensions:
        pattern = os.path.join(input_dir, extension)
        files = glob(pattern)
        all_files.extend(files)

    if not all_files:
        print(f"Аудиофайлы не найдены в директории {input_dir}")
        return

    print(f"Найдено файлов для обработки: {len(all_files)}")

    for file_path in all_files:
        print(f"\nОбработка файла: {file_path}")
        segments_created = split_audio_file(file_path, output_dir, segment_duration, sr)
        total_segments += segments_created
        if segments_created > 0:
            processed_files += 1

    print(f"\n" + "=" * 50)
    print(f"Обработано файлов: {processed_files}")
    print(f"Создано сегментов WAV: {total_segments}")
    print(f"Результаты сохранены в: {output_dir}")
    print("=" * 50)


def move_split_files_to_negative():
    """
    Перемещает разбитые файлы в основную директорию negative
    """
    import shutil

    source_dir = "data/negative_split"
    target_dir = "data/negative"

    if not os.path.exists(source_dir):
        print(f"Директория {source_dir} не существует")
        return

    moved_files = 0
    for file_name in os.listdir(source_dir):
        source_path = os.path.join(source_dir, file_name)
        target_path = os.path.join(target_dir, file_name)

        # Проверяем, что это файл формата WAV
        if os.path.isfile(source_path) and file_name.lower().endswith('.wav'):
            shutil.move(source_path, target_path)
            moved_files += 1
            print(f"Перемещен файл: {file_name}")
        elif os.path.isfile(source_path):
            print(f"Пропущен файл (не WAV): {file_name}")

    print(f"Перемещено файлов WAV: {moved_files}")

    # Удаляем пустую директорию (если она пуста)
    try:
        os.rmdir(source_dir)
        print(f"Удалена директория: {source_dir}")
    except OSError:
        print(f"Директория {source_dir} не пуста, не удалена")


if __name__ == "__main__":
    print("Скрипт для разбиения аудиофайлов на сегменты по 2 секунды")
    print("=" * 60)

    # Запрашиваем у пользователя действие
    print("Выберите действие:")
    print("1. Разбить файлы из data/negative на сегменты WAV")
    print("2. Переместить разбитые файлы WAV в data/negative")
    print("3. Выполнить полный цикл (разбить и переместить)")

    choice = input("Введите номер действия (1-3): ").strip()

    if choice == "1":
        # Запускаем обработку
        process_negative_folder()
        print("\nОбработка завершена!")
        print("Файлы сохранены в директории: data/negative_split")
        print("Все файлы сохранены в формате WAV")
        print("Чтобы использовать их в обучении, переместите в data/negative")

    elif choice == "2":
        move_split_files_to_negative()
        print("Файлы перемещены!")

    elif choice == "3":
        # Выполняем полный цикл
        process_negative_folder()
        move_split_files_to_negative()
        print("Полный цикл завершен!")

    else:
        print("Неверный выбор. Запустите скрипт снова и выберите действие от 1 до 3.")
