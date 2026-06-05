# core/web_interface/audio_stream.py
import pyaudio
import numpy as np
import threading
import time
import queue


class AudioStreamService:
    """Сервис для потоковой передачи аудио данных для визуализации"""

    def __init__(self, sample_rate=16000, chunk_size=256, device_index=8):  # уменьшил chunk_size
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.device_index = device_index
        self.is_running = False
        self.audio_processor = None
        self.audio_queue = queue.Queue()

    def start_stream(self, audio_processor):
        """Запуск аудио потока"""
        if self.is_running:
            return

        self.audio_processor = audio_processor
        self.is_running = True

        # Запускаем два отдельных потока: один читает микрофон, другой обрабатывает данные
        mic_thread = threading.Thread(target=self._mic_loop, daemon=True)
        process_thread = threading.Thread(target=self._process_loop, daemon=True)

        mic_thread.start()
        process_thread.start()

        print("[🎤] Аудио поток для визуализации запущен")

    def _mic_loop(self):
        """Поток для чтения микрофона"""
        p = pyaudio.PyAudio()
        stream = None

        try:
            # СОЗДАЕМ ОТДЕЛЬНЫЙ ПОТОК ДЛЯ МИКРОФОНА визуализации
            stream = p.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=self.sample_rate,
                input=True,
                input_device_index=self.device_index,
                frames_per_buffer=self.chunk_size
            )

            print(f"[🎤] Микрофон визуализации запущен (chunk_size: {self.chunk_size})")

            while self.is_running:
                try:
                    # Читаем данные без блокировки
                    data = stream.read(self.chunk_size, exception_on_overflow=False)
                    # Немедленно кладем в очередь для обработки
                    if self.audio_queue.qsize() < 5:  # ограничиваем размер очереди
                        self.audio_queue.put(data)
                    else:
                        # Если очередь переполнена, очищаем её чтобы избежать задержек
                        try:
                            while not self.audio_queue.empty():
                                self.audio_queue.get_nowait()
                        except:
                            pass

                except Exception as e:
                    print(f"[ERROR] Ошибка чтения микрофона визуализации: {e}")
                    time.sleep(0.01)

        except Exception as e:
            print(f"[ERROR] Ошибка инициализации микрофона визуализации: {e}")
        finally:
            if stream:
                stream.stop_stream()
                stream.close()
            if p:
                p.terminate()

    def _process_loop(self):
        """Поток для обработки и отправки аудио данных"""
        while self.is_running:
            try:
                # Берем данные из очереди без ожидания
                try:
                    data = self.audio_queue.get_nowait()
                except queue.Empty:
                    time.sleep(0.01)  # короткая пауза если очередь пуста
                    continue

                # Быстрая обработка данных
                audio_data = np.frombuffer(data, dtype=np.int16)
                normalized = audio_data / 32768.0

                # Немедленная отправка
                if self.audio_processor:
                    self.audio_processor(normalized.tolist())

            except Exception as e:
                print(f"[ERROR] Ошибка обработки аудио: {e}")
                time.sleep(0.01)

    def stop_stream(self):
        """Остановка аудио потока"""
        self.is_running = False
        # Очищаем очередь
        try:
            while not self.audio_queue.empty():
                self.audio_queue.get_nowait()
        except:
            pass
        print("[🎤] Аудио поток визуализации остановлен")
