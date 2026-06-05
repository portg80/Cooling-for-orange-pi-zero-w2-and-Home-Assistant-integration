import os
import wave
import threading
import time
from datetime import datetime
import pyaudio
import re

pattern = re.compile(r'^[A-Za-zА-Яа-я0-9_ ]+$')

while True:
    name = input("Введите название папки для записей: ").strip()

    if not name:
        print("Ошибка: название не может быть пустым.")
        continue

    if not pattern.match(name):
        print("Ошибка: допустимы только буквы (рус/англ), цифры, пробел и _")
        continue

    break

OUT_DIR = f"data/ЗАПИСИ/{name}"

os.makedirs(OUT_DIR, exist_ok=True)
print("Папка создана/существует:", OUT_DIR)

DURATION = 2
SR = 16000
CHANNELS = 1
FORMAT = pyaudio.paInt16
CHUNK = 2048

# Предустановленные индексы устройств
DEVICE_INDEXES = [3, 5, 8]


class AudioRecorder:
    def __init__(self):
        self.audio_instances = {}
        self.lock = threading.Lock()

    def get_audio_instance(self, device_id):
        """Получаем или создаем экземпляр PyAudio для устройства"""
        with self.lock:
            if device_id not in self.audio_instances:
                try:
                    self.audio_instances[device_id] = pyaudio.PyAudio()
                except Exception as e:
                    print(f"Ошибка создания PyAudio для устройства {device_id}: {e}")
                    return None
            return self.audio_instances[device_id]

    def cleanup(self):
        """Очистка всех ресурсов PyAudio"""
        with self.lock:
            for device_id, audio_instance in self.audio_instances.items():
                try:
                    audio_instance.terminate()
                except:
                    pass
            self.audio_instances.clear()


# Глобальный экземпляр рекордера
recorder = AudioRecorder()


def list_audio_devices():
    """Список всех аудиоустройств"""
    p = pyaudio.PyAudio()
    print("\nДоступные устройства записи:\n")
    for i in range(p.get_device_count()):
        info = p.get_device_info_by_index(i)
        if info['maxInputChannels'] > 0:
            print(f"[{i}] {info['name']} (входы: {info['maxInputChannels']})")
    print("-" * 50)
    p.terminate()


def validate_devices(device_indexes):
    """Проверка доступности устройств"""
    p = pyaudio.PyAudio()
    valid_devices = []

    for idx in device_indexes:
        try:
            info = p.get_device_info_by_index(idx)
            if info['maxInputChannels'] >= CHANNELS:
                print(f"[OK] [{idx}] {info['name']}")
                valid_devices.append(idx)
            else:
                print(f"[ERROR] [{idx}] {info['name']} - недостаточно входных каналов")
        except Exception as e:
            print(f"[ERROR] [{idx}] Ошибка: {e}")

    p.terminate()
    return valid_devices


def record_single_device(device_index, phrase, timestamp, start_event, recording_started, stop_event):
    """Запись с одного устройства"""
    audio = None
    stream = None

    try:
        # Получаем экземпляр PyAudio для этого устройства
        audio = recorder.get_audio_instance(device_index)
        if audio is None:
            return

        # Открываем поток
        stream = audio.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=SR,
            input=True,
            input_device_index=device_index,
            frames_per_buffer=CHUNK,
            start=False
        )

        # Ждем команды старта
        start_event.wait()

        # Запускаем поток и сразу сообщаем о начале записи
        stream.start_stream()
        recording_started.set()

        # Записываем данные
        frames = []
        total_frames = int(SR / CHUNK * DURATION)

        for i in range(total_frames):
            if stop_event.is_set():
                break
            try:
                data = stream.read(CHUNK, exception_on_overflow=False)
                frames.append(data)
            except Exception as e:
                # Добавляем тишину вместо потерянных данных
                frames.append(b'\x00' * CHUNK * 2)

        # Останавливаем поток
        if stream.is_active():
            stream.stop_stream()

        # Сохраняем файл
        if frames:
            filename = os.path.join(OUT_DIR, f"{phrase}_dev{device_index}_{timestamp}.wav")
            with wave.open(filename, 'wb') as wf:
                wf.setnchannels(CHANNELS)
                wf.setsampwidth(audio.get_sample_size(FORMAT))
                wf.setframerate(SR)
                wf.writeframes(b''.join(frames))

    except Exception as e:
        print(f"Ошибка записи с устройства {device_index}: {e}")
    finally:
        # Аккуратно закрываем поток
        if stream:
            try:
                if not stream.is_stopped():
                    stream.stop_stream()
                stream.close()
            except:
                pass


def simultaneous_recording(phrase, device_indexes):
    """Одновременная запись с нескольких устройств"""

    timestamp = datetime.now().strftime('%Y%m%d%H%M%S%f')[:-3]

    # События для управления записью
    start_event = threading.Event()
    recording_started = threading.Event()
    stop_event = threading.Event()

    threads = []

    # Запускаем потоки записи
    for device_idx in device_indexes:
        thread = threading.Thread(
            target=record_single_device,
            args=(device_idx, phrase, timestamp, start_event, recording_started, stop_event),
            daemon=True
        )
        thread.start()
        threads.append(thread)
        time.sleep(0.05)

    # Даем время на инициализацию
    time.sleep(0.5)

    # Очищаем экран и начинаем запись
    os.system('cls')
    print("ГОВОРИТЕ!")
    start_event.set()

    # Ждем пока все потоки реально начнут запись
    recording_started.wait()

    # Таймер с обновлением в реальном времени
    start_time = time.time()
    update_interval = 0.05  # Обновление каждые 50мс

    while time.time() - start_time < DURATION:
        remaining = DURATION - (time.time() - start_time)
        # Обновляем строку с оставшимся временем
        os.system('cls')
        print(f"ГОВОРИТЕ! ({remaining:.2f} сек)")
        time.sleep(update_interval)

    # Завершение записи
    stop_event.set()

    # Ждем завершения всех потоков
    for thread in threads:
        thread.join(timeout=1.0)

    # Очищаем экран и показываем результат
    os.system('cls')
    print("КОНЕЦ ЗАПИСИ!")

    # Выводим информацию о сохраненных файлах
    print(f"\nЗапись завершена. Сохранено {len(device_indexes)} файлов")

    time.sleep(1)


def main():
    """Основная функция"""
    print("Система многоканальной записи аудио")
    print("=" * 50)

    # Используем глобальную переменную
    global DEVICE_INDEXES

    # Показываем доступные устройства
    list_audio_devices()

    # Проверяем и выбираем устройства
    if DEVICE_INDEXES:
        print(f"\nНайдены предустановленные устройства: {DEVICE_INDEXES}")
        show = input("Показать информацию об устройствах? (y/n): ").strip().lower()
        if show == 'y':
            valid_devices = validate_devices(DEVICE_INDEXES)
            if len(valid_devices) != len(DEVICE_INDEXES):
                print("Некоторые устройства недоступны!")
                use_anyway = input("Все равно использовать? (y/n): ").strip().lower()
                if use_anyway != 'y':
                    DEVICE_INDEXES = valid_devices
    else:
        print("\nПредустановленные устройства не найдены")
        user_input = input("Введите индексы через запятую: ").strip()
        DEVICE_INDEXES = [int(x.strip()) for x in user_input.split(',')]

    # Финальная проверка устройств
    valid_devices = validate_devices(DEVICE_INDEXES)
    if not valid_devices:
        print("Нет доступных устройств для записи!")
        return

    DEVICE_INDEXES = valid_devices

    # Ввод фразы для записи
    phrase = input("\nВведите метку/фразу для записи: ").strip()
    if not phrase:
        phrase = "audio_sample"

    # Основной цикл записи
    session_count = 0
    while True:
        print(f"\nСессия записи #{session_count + 1}")
        print("-" * 30)

        cmd = input("Enter - начать запись, 'q' - выход: ").strip().lower()
        if cmd == 'q':
            break

        simultaneous_recording(phrase, DEVICE_INDEXES)
        session_count += 1

        # Перезапуск PyAudio каждые 2 записи для предотвращения утечек памяти
        if session_count % 2 == 0:
            recorder.cleanup()
            time.sleep(0.5)


if __name__ == "__main__":
    try:
        main()
        print("\nПрограмма завершена")
    except KeyboardInterrupt:
        print("\n\n⏹️  Программа прервана пользователем")
    except Exception as e:
        print(f"\nКритическая ошибка: {e}")
        import traceback

        traceback.print_exc()
    finally:
        # Всегда очищаем ресурсы при выходе
        recorder.cleanup()
