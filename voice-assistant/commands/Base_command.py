# commands/Base_command.py
import random
import os
from abc import ABC, abstractmethod
from typing import List, Union


class BaseCommand(ABC):
    name = ""
    aliases: List[str] = []  # для точного совпадения
    keywords: List[str] = []  # для поиска по ключевым словам
    match_type: str = "exact"  # "exact", "keyword", "fuzzy", "contains"

    def __init__(self, assistant=None, sound_player=None):
        self.assistant = assistant
        self.sound_player = sound_player
        self.default_extensions = ['.wav', '.mp3', '.ogg']

    def match(self, text: str) -> bool:
        """Улучшенная проверка совпадения команды с текстом"""
        text_lower = text.lower().strip()

        if self.match_type == "exact":
            return self._match_exact(text_lower)
        elif self.match_type == "keyword":
            return self._match_keyword(text_lower)
        elif self.match_type == "contains":
            return self._match_contains(text_lower)
        elif self.match_type == "fuzzy":
            return self._match_fuzzy(text_lower)
        else:
            return self._match_exact(text_lower)  # fallback

    def _match_exact(self, text: str) -> bool:
        """Точное совпадение с алиасами"""
        return any(alias == text for alias in self.aliases)

    def _match_keyword(self, text: str) -> bool:
        """Поиск ключевых слов в тексте"""
        return any(keyword in text for keyword in self.keywords)

    def _match_contains(self, text: str) -> bool:
        """Поиск алиасов как подстрок в тексте"""
        return any(alias in text for alias in self.aliases)

    def _match_fuzzy(self, text: str) -> bool:
        """Нечеткое совпадение (используется в NLU)"""
        # Базовая реализация использует поиск подстроки.
        return self._match_contains(text)

    @abstractmethod
    def execute(self, text: str, converted_text: str = None, *args, **kwargs):
        """Действие при выполнении команды"""
        pass

    def say(self, text: str):
        if self.assistant and hasattr(self.assistant, 'say'):
            self.assistant.say(text)
        else:
            print(f"[Ассистент] {text}")

    def play_sound(self, sound_path, volume=1.0):
        """Вспомогательный метод для воспроизведения звуков"""
        if self.sound_player and hasattr(self.sound_player, 'play_sound'):
            self.sound_player.play_sound(sound_path, volume=volume)
        else:
            print(f"[SOUND] {sound_path} (volume: {volume})")

    def _find_file_with_extension(self, base_path, filename):
        """
        Ищет файл с расширением, если имя файла указано без расширения.
        """
        # Если у файла уже есть расширение - возвращаем как есть
        if os.path.splitext(filename)[1]:
            return filename

        # Ищем файл с разными расширениями
        for ext in self.default_extensions:
            candidate = filename + ext
            candidate_path = os.path.join(base_path, candidate)

            # Проверяем существует ли файл (если base_path абсолютный)
            if os.path.isabs(base_path):
                if os.path.exists(candidate_path):
                    return candidate

            # Если base_path относительный, предполагаем что файл существует
            else:
                return candidate  # предполагаем что файл существует

        # Если не нашли с расширениями, возвращаем оригинальное имя
        return filename

    def _get_all_files_in_folder(self, folder_path, extensions=None):
        """
        Получает все файлы из папки с указанными расширениями.

        Args:
            folder_path (str): Путь к папке (относительный от base_dir)
            extensions (list): Список расширений (None = все файлы)

        Returns:
            list: Список имен файлов
        """
        if extensions is None:
            extensions = self.default_extensions

        try:
            # Формируем полный путь к папке
            full_folder_path = os.path.join(self.sound_player.base_dir, folder_path)

            # Проверяем существует ли папка
            if not os.path.exists(full_folder_path):
                print(f"[SOUND] Папка не существует: {full_folder_path}")
                return []

            # Получаем все файлы из папки
            files = os.listdir(full_folder_path)

            # Фильтруем по расширениям и только файлы (не папки)
            filtered_files = []
            for file in files:
                file_path = os.path.join(full_folder_path, file)
                if os.path.isfile(file_path):  # проверяем что это файл, а не папка
                    if any(file.lower().endswith(ext.lower()) for ext in extensions):
                        filtered_files.append(file)

            print(f"[SOUND] В папке {folder_path} найдено {len(filtered_files)} файлов: {filtered_files}")
            return filtered_files

        except Exception as e:
            print(f"[SOUND] Ошибка чтения папки {folder_path}: {e}")
            return []

    def get_random_sound(self, folder_path, *filenames, default_extension='.wav', use_all_files=False):
        """
        Возвращает случайный звуковой файл из списка или всей папки.

        Args:
            folder_path (str): Путь к папке со звуками
            *filenames (str): Имена файлов для случайного выбора (с расширением или без)
            default_extension (str): Расширение по умолчанию если файл не найден
            use_all_files (bool): Если True, использует все файлы в папке, игнорируя filenames

        Returns:
            str: Относительный путь к случайному файлу

        Example:
            # Использование конкретных файлов
            sound = self.get_random_sound("responses", "ok1", "ok2.wav")

            # Использование всех файлов в папке
            sound = self.get_random_sound("music", use_all_files=True)

            # Смешанное использование (если файлов нет, использует все из папки)
            sound = self.get_random_sound("sounds", "specific", use_all_files=True)
        """
        # Если use_all_files=True или не указаны конкретные файлы
        if use_all_files or not filenames:
            all_files = self._get_all_files_in_folder(folder_path)
            if all_files:
                chosen_file = random.choice(all_files)
                return os.path.join(folder_path, chosen_file)
            elif not filenames:
                raise ValueError(f"В папке {folder_path} не найдено файлов и не указаны конкретные файлы")

        # Обрабатываем конкретные файлы
        processed_filenames = []
        for filename in filenames:
            # Для конкретных файлов используем базовую логику
            full_folder_path = os.path.join(self.sound_player.base_dir, folder_path)
            processed_filename = self._find_file_with_extension(full_folder_path, filename)
            processed_filenames.append(processed_filename)

        # Выбираем случайный файл из обработанных
        chosen_file = random.choice(processed_filenames)

        # Формируем полный относительный путь
        return os.path.join(folder_path, chosen_file)

    def play_random_sound(self, folder_path, *filenames, volume=1.0, default_extension='.wav', use_all_files=False):
        """
        Воспроизводит случайный звуковой файл из списка или всей папки.

        Args:
            folder_path (str): Путь к папке со звуками
            *filenames (str): Имена файлов для случайного выбора (с расширением или без)
            volume (float): Громкость звука (0.0 - 1.0)
            default_extension (str): Расширение по умолчанию
            use_all_files (bool): Если True, использует все файлы в папке

        Returns:
            bool: Успешно ли воспроизведен звук

        Example:
            # Все файлы в папке
            self.play_random_sound("music", use_all_files=True)

            # Конкретные файлы
            self.play_random_sound("responses", "ok1", "ok2")

            # Автоматическое fallback: если файлов нет, использует все из папки
            self.play_random_sound("sounds", "specific", use_all_files=True)
        """
        try:
            sound_path = self.get_random_sound(
                folder_path,
                *filenames,
                default_extension=default_extension,
                use_all_files=use_all_files
            )
            self.play_sound(sound_path, volume=volume)
            return True
        except Exception as e:
            print(f"[SOUND] Error playing random sound: {e}")
            return False

    def get_sound_path(self, folder_path, filename, default_extension='.wav'):
        """
        Возвращает путь к звуковому файлу с автоматическим добавлением расширения.
        """
        filename_with_ext = self._find_file_with_extension(folder_path, filename)
        return os.path.join(folder_path, filename_with_ext)

    def _get_all_files_in_folder(self, folder_path, extensions=None):
        """
        Получает все файлы из папки с указанными расширениями.

        Args:
            folder_path (str): Путь к папке (относительный от base_dir)
            extensions (list): Список расширений (None = все файлы)

        Returns:
            list: Список имен файлов
        """
        if extensions is None:
            extensions = self.default_extensions

        try:
            # Формируем полный путь к папке
            full_folder_path = os.path.join(self.sound_player.base_dir, folder_path)

            # Проверяем существует ли папка
            if not os.path.exists(full_folder_path):
                print(f"[SOUND] Папка не существует: {full_folder_path}")
                return []

            # Получаем все файлы из папки
            files = os.listdir(full_folder_path)

            # Фильтруем по расширениям и только файлы (не папки)
            filtered_files = []
            for file in files:
                file_path = os.path.join(full_folder_path, file)
                if os.path.isfile(file_path):  # проверяем что это файл, а не папка
                    if any(file.lower().endswith(ext.lower()) for ext in extensions):
                        filtered_files.append(file)

            print(f"[SOUND] В папке {folder_path} найдено {len(filtered_files)} файлов: {filtered_files}")
            return filtered_files

        except Exception as e:
            print(f"[SOUND] Ошибка чтения папки {folder_path}: {e}")
            return []

    def get_random_sound(self, folder_path, *filenames, default_extension='.wav', use_all_files=False):
        """
        Возвращает случайный звуковой файл из списка или всей папки.
        """
        # Если use_all_files=True или не указаны конкретные файлы
        if use_all_files or not filenames:
            all_files = self._get_all_files_in_folder(folder_path)
            if all_files:
                chosen_file = random.choice(all_files)
                return os.path.join(folder_path, chosen_file)
            elif not filenames:
                raise ValueError(f"В папке {folder_path} не найдено файлов и не указаны конкретные файлы")

        # Обрабатываем конкретные файлы
        processed_filenames = []
        for filename in filenames:
            # Для конкретных файлов используем базовую логику
            full_folder_path = os.path.join(self.sound_player.base_dir, folder_path)
            processed_filename = self._find_file_with_extension(full_folder_path, filename)
            processed_filenames.append(processed_filename)

        # Выбираем случайный файл из обработанных
        chosen_file = random.choice(processed_filenames)

        # Формируем полный относительный путь
        return os.path.join(folder_path, chosen_file)
