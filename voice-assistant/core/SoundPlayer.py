import pygame
import threading
import os
import time
from pathlib import Path
import subprocess
import sys


class SoundPlayer:
    def __init__(self, base_dir="media"):
        self.base_dir = base_dir
        self.lock = threading.Lock()
        self._initialized = False
        self._cache = {}

        # Поддерживаемые форматы для конвертации
        self.supported_input_formats = ['.mp3', '.ogg', '.flac', '.m4a', '.aac', '.wma']
        self.output_format = '.wav'

        # Отладочная информация
        print(f"[SOUND] SoundPlayer initialized with base_dir: {os.path.abspath(base_dir)}")
        if not os.path.exists(self.base_dir):
            print(f"[SOUND] Base directory does not exist: {self.base_dir}")

    def _ensure_init(self):
        if not self._initialized:
            pygame.mixer.init()
            self._initialized = True

    def is_ffmpeg_available(self):
        """Проверяет, установлен ли ffmpeg в системе"""
        try:
            subprocess.run(['ffmpeg', '-version'],
                           capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def convert_audio_file(self, input_path, output_path):
        """
        Конвертирует аудиофайл в WAV используя ffmpeg
        """
        try:
            cmd = [
                'ffmpeg', '-i', input_path,
                '-acodec', 'pcm_s16le',  # 16-bit PCM
                '-ar', '22050',  # Sample rate
                '-ac', '2',  # Stereo
                '-y',  # Overwrite output file
                output_path
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                print(f"[CONVERT] Успешно: {os.path.basename(input_path)} → {os.path.basename(output_path)}")
                return True
            else:
                print(f"[CONVERT] Ошибка конвертации {input_path}: {result.stderr}")
                return False

        except Exception as e:
            print(f"[CONVERT] Исключение при конвертации {input_path}: {e}")
            return False

    def convert_all_audio_in_folder(self, folder_path=None, overwrite=False):
        """
        Рекурсивно конвертирует все аудиофайлы в папке и подпапках в WAV

        Args:
            folder_path (str): Путь к папке (None = base_dir)
            overwrite (bool): Перезаписывать существующие WAV файлы
        """
        if folder_path is None:
            folder_path = self.base_dir

        if not os.path.exists(folder_path):
            print(f"[CONVERT] Папка не существует: {folder_path}")
            return

        if not self.is_ffmpeg_available():
            print("[CONVERT] ffmpeg не найден. Установите ffmpeg для конвертации аудио.")
            print("[CONVERT] Скачать: https://ffmpeg.org/download.html")
            return

        print(f"[CONVERT] Сканирую папку: {folder_path}")

        converted_count = 0
        skipped_count = 0

        # Рекурсивно обходим все файлы
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                file_ext = os.path.splitext(file)[1].lower()

                # Пропускаем уже WAV файлы
                if file_ext == self.output_format:
                    continue

                # Проверяем поддерживаемый ли формат
                if file_ext in self.supported_input_formats:
                    # Создаем путь для конвертированного файла
                    wav_filename = os.path.splitext(file)[0] + self.output_format
                    wav_path = os.path.join(root, wav_filename)

                    # Проверяем существует ли уже WAV версия
                    if os.path.exists(wav_path) and not overwrite:
                        print(f"[CONVERT] ⏭️ Пропускаем (уже существует): {file}")
                        skipped_count += 1
                        continue

                    print(f"[CONVERT] Конвертирую: {file} → {wav_filename}")
                    if self.convert_audio_file(file_path, wav_path):
                        converted_count += 1
                    else:
                        print(f"[CONVERT] Не удалось конвертировать: {file}")

        print(f"[CONVERT] Результат: {converted_count} сконвертировано, {skipped_count} пропущено")

    def find_audio_file(self, relative_path):
        """
        Ищет аудиофайл, автоматически конвертируя если нужно

        Returns:
            str: Путь к WAV файлу (оригинальному или сконвертированному)
        """
        # Полный путь к исходному файлу
        full_path = os.path.join(self.base_dir, relative_path)

        # Если файл уже WAV - возвращаем как есть
        if os.path.splitext(full_path)[1].lower() == self.output_format:
            return full_path

        # Если файл существует и это не WAV - проверяем есть ли WAV версия
        if os.path.exists(full_path):
            wav_path = os.path.splitext(full_path)[0] + self.output_format

            # Если WAV версия уже существует - используем её
            if os.path.exists(wav_path):
                return wav_path
            # Иначе конвертируем
            else:
                print(f"[SOUND] Автоконвертация: {relative_path}")
                if self.convert_audio_file(full_path, wav_path):
                    return wav_path
                else:
                    print(f"[SOUND] Используется оригинальный файл (возможны проблемы): {relative_path}")
                    return full_path

        return full_path

    def play_sound(self, relative_path, block=False, volume=1.0, auto_convert=True):
        """
        Воспроизводит звук, автоматически конвертируя если нужно

        Args:
            relative_path (str): Относительный путь к файлу
            block (bool): Блокировать выполнение до окончания звука
            volume (float): Громкость (0.0-1.0)
            auto_convert (bool): Автоматически конвертировать в WAV
        """
        if auto_convert:
            # Используем умный поиск с автоконвертацией
            full_path = self.find_audio_file(relative_path)
        else:
            # Используем оригинальный путь
            full_path = os.path.join(self.base_dir, relative_path)

        print(f"[SOUND] Looking for sound: {full_path}")
        print(f"[SOUND] Base dir: {self.base_dir}")
        print(f"[SOUND] Relative path: {relative_path}")

        # Проверка существования
        if not os.path.exists(full_path):
            print(f"[SOUND] File not found: {full_path}")
            # Покажем какие файлы есть в директории
            if os.path.exists(self.base_dir):
                print(f"[SOUND] Files in {self.base_dir}:")
                for root, dirs, files in os.walk(self.base_dir):
                    for file in files:
                        rel_path = os.path.relpath(os.path.join(root, file), self.base_dir)
                        print(f"  {rel_path}")
            return

        self._ensure_init()

        def _play():
            try:
                with self.lock:
                    if full_path not in self._cache:
                        self._cache[full_path] = pygame.mixer.Sound(full_path)
                    sound = self._cache[full_path]
                    sound.set_volume(volume)
                    sound.play()
                    print(f"[SOUND] ▶️ Playing: {relative_path} (vol={volume})")
                    if block:
                        time.sleep(sound.get_length())
            except Exception as e:
                print(f"[SOUND] Error while playing {relative_path}: {e}")
                # Если ошибка с оригинальным файлом, пробуем конвертировать и воспроизвести снова
                if auto_convert and not full_path.endswith(self.output_format):
                    print(f"[SOUND] Retrying with conversion...")
                    wav_path = os.path.splitext(full_path)[0] + self.output_format
                    if self.convert_audio_file(full_path, wav_path):
                        self.play_sound(
                            os.path.relpath(wav_path, self.base_dir),
                            block, volume, auto_convert=False
                        )

        threading.Thread(target=_play, daemon=True).start()

    def batch_convert_folder(self, folder_path=None, overwrite=False):
        """
        Пакетная конвертация всей папки (удобно для инициализации)
        """
        print("[CONVERT] Запуск пакетной конвертации...")
        self.convert_all_audio_in_folder(folder_path, overwrite)
        print("[CONVERT] Пакетная конвертация завершена")

    def get_conversion_stats(self, folder_path=None):
        """
        Показывает статистику по аудиофайлам в папке
        """
        if folder_path is None:
            folder_path = self.base_dir

        stats = {
            'total_files': 0,
            'wav_files': 0,
            'convertible_files': 0,
            'other_files': 0
        }

        for root, dirs, files in os.walk(folder_path):
            for file in files:
                stats['total_files'] += 1
                file_ext = os.path.splitext(file)[1].lower()

                if file_ext == self.output_format:
                    stats['wav_files'] += 1
                elif file_ext in self.supported_input_formats:
                    stats['convertible_files'] += 1
                else:
                    stats['other_files'] += 1

        print(f"[STATS] Статистика аудиофайлов в {folder_path}:")
        print(f"        Всего файлов: {stats['total_files']}")
        print(f"        WAV файлов: {stats['wav_files']}")
        print(f"        Конвертируемых: {stats['convertible_files']}")
        print(f"        Прочих: {stats['other_files']}")

        return stats
